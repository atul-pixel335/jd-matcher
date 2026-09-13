import os
import json
import streamlit as st

from .agent import extract_text_from_pdf, score_resume
from .cover_letter_agent import generate_cover_letter
from .config import UI, LIMITS

def render():
    st.set_page_config(
        page_title=UI["page_title"],
        page_icon=UI["page_icon"],
        layout=UI["layout"],
    )
    st.title("JD Matcher")
    st.caption("Upload a resume PDF and paste a Job Description to get an AI-powered fit score.")

    if not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY not found. Create a .env file with your Groq API key.")
        st.stop()

    # ── Inputs ────────────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)
    with col_left:
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    with col_right:
        jd_text = st.text_area("Paste Job Description", height=300)

    resume_text = extract_text_from_pdf(uploaded_file)

    # ── Agent 1 button ────────────────────────────────────────────────────────
    ready = bool(resume_text and jd_text.strip())
    if st.button("Score this match", disabled=not ready):
        with st.spinner("Agent 1 analyzing resume vs JD..."):
            scorecard, messages, metrics = score_resume(resume_text, jd_text)
        st.session_state.scorecard = scorecard
        st.session_state.jd_text = jd_text
        st.session_state.messages = messages
        st.session_state.metrics_scoring = metrics
        st.session_state.cover_letter = None
        st.session_state.metrics_cover = None

    # ── Guardrail block screen ────────────────────────────────────────────────
    scorecard_state = getattr(st.session_state, "scorecard", None)
    if scorecard_state and scorecard_state.get("blocked_by_guardrail"):
        st.divider()
        st.error("🛡️ **PROMPT INJECTION DETECTED** — request blocked before it reached the LLM")

        reason = scorecard_state.get("error", "Unknown")
        st.markdown(f"### Why was this blocked?")
        st.code(reason, language="text")

        return  # skip the rest of the render — nothing more to show

    # ── Scorecard ─────────────────────────────────────────────────────────────
    if scorecard_state:
        _render_scorecard(scorecard_state)
        _render_audit_log(st.session_state.messages)

        # ── Agent 2 ───────────────────────────────────────────────────────────
        st.divider()
        st.markdown("### Multi-Agent Handoff")
        st.caption(
            "Agent 2 receives only the scorecard above -- it never sees your resume. "
            "That structured summary is the handoff between the two agents."
        )

        if st.button("Generate Cover Letter"):
            with st.spinner("Agent 2 writing cover letter from scorecard..."):
                cover_letter, cover_metrics = generate_cover_letter(
                    st.session_state.scorecard,
                    st.session_state.jd_text,
                )
            st.session_state.cover_letter = cover_letter
            st.session_state.metrics_cover = cover_metrics

        if getattr(st.session_state, "cover_letter", None):
            st.markdown("#### Generated Cover Letter")
            st.markdown(st.session_state.cover_letter)

    # ── Observability sidebar (always visible if we have any metrics) ────────
    _render_metrics_sidebar()


def _render_scorecard(scorecard: dict):
    st.divider()

    st.metric("Fit Score", f"{scorecard.get('fit_score', '?')} / 10")

    col_s, col_i = st.columns(2)
    with col_s:
        st.markdown("### Strengths")
        for item in scorecard.get("strengths", []):
            st.markdown(f"- {item}")
    with col_i:
        st.markdown("### Scope of Improvement")
        for item in scorecard.get("scope_of_improvement", []):
            st.markdown(f"- {item}")

    missing = scorecard.get("missing_keywords", [])
    if missing:
        st.markdown("### Missing Keywords")
        st.markdown(" ".join(f"`{kw}`" for kw in missing))


def _render_audit_log(messages: list):
    st.divider()
    st.markdown("### Agent Conversation Log")
    st.caption("Every message exchanged -- this is the agent's full memory.")

    user_preview = LIMITS["audit_user_preview_chars"]

    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        tool_calls = msg.get("tool_calls") or []

        if role == "system":
            with st.expander(f"[{i}] SYSTEM -- instructions given to the LLM"):
                st.text(msg.get("content", ""))
        elif role == "user":
            with st.expander(f"[{i}] USER -- resume + JD sent to the LLM"):
                content = str(msg.get("content", ""))
                st.text(content[:user_preview] + ("..." if len(content) > user_preview else ""))
        elif role == "assistant" and tool_calls:
            for tc in tool_calls:
                fn = tc.get("function", {})
                fn_name = fn.get("name", "unknown")
                fn_args = fn.get("arguments", "{}")
                with st.expander(f"[{i}] ASSISTANT -- called tool: {fn_name}"):
                    st.markdown("**Arguments passed to the tool:**")
                    try:
                        st.json(json.loads(fn_args))
                    except Exception:
                        st.code(fn_args)
        elif role == "assistant" and not tool_calls:
            with st.expander(f"[{i}] ASSISTANT -- final response (no more tools needed)"):
                content = msg.get("content") or ""
                try:
                    st.json(json.loads(content))
                except Exception:
                    st.text(content)
        elif role == "tool":
            with st.expander(f"[{i}] TOOL RESULT -- what Python returned to the LLM"):
                try:
                    st.json(json.loads(msg.get("content", "{}")))
                except Exception:
                    st.text(msg.get("content", ""))


def _render_metrics_sidebar():
    metrics_scoring = getattr(st.session_state, "metrics_scoring", None)
    metrics_cover = getattr(st.session_state, "metrics_cover", None)

    if not metrics_scoring and not metrics_cover:
        return

    with st.sidebar:
        st.header("Metrics")
        st.caption("Cost and latency metrics for this session.")

        # ── Cumulative session totals ────────────────────────────────────────
        total_tokens = 0
        total_cost = 0.0
        total_wall_ms = 0.0
        total_llm_calls = 0

        for m in (metrics_scoring, metrics_cover):
            if not m:
                continue
            total_tokens    += m["total_tokens"]
            total_cost      += m["total_cost_usd"]
            total_wall_ms   += m["total_wall_time_ms"]
            total_llm_calls += len(m["llm_calls"])

        st.subheader("Session Totals")
        st.metric("Total Tokens", f"{total_tokens:,}")
        st.metric("Estimated Cost", f"${total_cost:.6f}")
        st.metric("Total Wall Time", f"{total_wall_ms:.0f} ms")
        st.metric("Total LLM Calls", total_llm_calls)

        st.divider()

        # ── Agent 1 breakdown ────────────────────────────────────────────────
        if metrics_scoring:
            st.subheader("Agent 1 (Scorer)")
            m = metrics_scoring
            st.markdown(
                f"- **Turns:** {m['turn_count']}\n"
                f"- **Tokens:** {m['total_tokens']:,} "
                f"(prompt {m['total_prompt_tokens']:,} / completion {m['total_completion_tokens']:,})\n"
                f"- **Cost:** ${m['total_cost_usd']:.6f}\n"
                f"- **LLM latency:** {m['total_llm_latency_ms']:.0f} ms\n"
                f"- **Tool latency:** {m['total_tool_latency_ms']:.2f} ms\n"
                f"- **Wall time:** {m['total_wall_time_ms']:.0f} ms"
            )

            # Turn-by-turn LLM calls table
            if m["llm_calls"]:
                st.markdown("**LLM calls (per turn):**")
                st.dataframe(m["llm_calls"], width='stretch', hide_index=True)

            if m["tool_calls"]:
                st.markdown("**Tool calls:**")
                st.dataframe(m["tool_calls"], width='stretch', hide_index=True)

        # ── Agent 2 breakdown ────────────────────────────────────────────────
        if metrics_cover:
            st.divider()
            st.subheader("Agent 2 (Writer)")
            m = metrics_cover
            st.markdown(
                f"- **Tokens:** {m['total_tokens']:,}\n"
                f"- **Cost:** ${m['total_cost_usd']:.6f}\n"
                f"- **LLM latency:** {m['total_llm_latency_ms']:.0f} ms\n"
                f"- **Wall time:** {m['total_wall_time_ms']:.0f} ms"
            )
