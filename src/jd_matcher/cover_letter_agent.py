import json, time
from .config import client, MODEL, TEMPERATURES
from .metrics import new_metrics, record_llm_call

COVER_LETTER_PROMPT = """You are a professional career coach writing cover letters.
You will receive a scorecard produced by a resume-screening AI and the original job description.
You do NOT have access to the raw resume -- only what the screening agent decided to pass forward.

Write a concise, confident cover letter (3 paragraphs) that:
- Opens by directly addressing the role and the candidate's strongest match points (from strengths)
- Acknowledges gaps honestly and reframes them as growth areas (from scope_of_improvement)
- Closes with a call to action

Return plain text only -- no subject line, no "Dear Hiring Manager" boilerplate, just the 3 paragraphs."""


def generate_cover_letter(scorecard: dict, jd_text: str):
    """
    Agent 2 — receives the scorecard from Agent 1 and the JD.
    Never sees the original resume. That is the handoff.
    Returns (cover_letter_text, metrics).
    """
    handoff_payload = {
        "fit_score": scorecard.get("fit_score"),
        "strengths": scorecard.get("strengths", []),
        "scope_of_improvement": scorecard.get("scope_of_improvement", []),
        "missing_keywords": scorecard.get("missing_keywords", []),
    }

    messages = [
        {"role": "system", "content": COVER_LETTER_PROMPT},
        {
            "role": "user",
            "content": (
                f"SCREENING SCORECARD (from Agent 1):\n{json.dumps(handoff_payload, indent=2)}"
                f"\n\nJOB DESCRIPTION:\n{jd_text}"
            ),
        },
    ]

    metrics = new_metrics()
    run_start = time.time()

    t0 = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURES["cover_letter"],
        messages=messages,
    )
    llm_latency_ms = (time.time() - t0) * 1000

    record_llm_call(metrics, MODEL, response, llm_latency_ms, turn=1)
    metrics["turn_count"] = 1
    metrics["total_wall_time_ms"] = (time.time() - run_start) * 1000

    print(f"\n[cover letter] LLM call took {llm_latency_ms:.0f} ms, "
          f"tokens={response.usage.total_tokens if response.usage else 0}, "
          f"cost=${metrics['total_cost_usd']:.6f}\n")

    return response.choices[0].message.content, metrics
