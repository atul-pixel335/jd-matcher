from .config import PRICING

def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Return estimated cost in USD for one LLM call."""
    price = PRICING.get(model)
    if not price:
        return 0.0
    return (
        (prompt_tokens / 1_000_000) * price["input_per_million"] +
        (completion_tokens / 1_000_000) * price["output_per_million"]
    )

def new_metrics() -> dict:
    """Empty metrics dict — a fresh 'receipt' for one scoring run."""
    return {
        "llm_calls": [],       # list of dicts, one per LLM call
        "tool_calls": [],      # list of dicts, one per tool invocation
        "total_tokens": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_cost_usd": 0.0,
        "total_llm_latency_ms": 0.0,
        "total_tool_latency_ms": 0.0,
        "total_wall_time_ms": 0.0,
        "turn_count": 0,
    }

def record_llm_call(metrics: dict, model: str, response, latency_ms: float, turn: int):
    """Append one LLM call's stats to the metrics dict."""
    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    total_tokens = prompt_tokens + completion_tokens
    cost = estimate_cost(model, prompt_tokens, completion_tokens)

    metrics["llm_calls"].append({
        "turn": turn,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost,
        "latency_ms": round(latency_ms, 1),
    })

    metrics["total_prompt_tokens"]     += prompt_tokens
    metrics["total_completion_tokens"] += completion_tokens
    metrics["total_tokens"]            += total_tokens
    metrics["total_cost_usd"]          += cost
    metrics["total_llm_latency_ms"]    += latency_ms

def record_tool_call(metrics: dict, name: str, latency_ms: float, turn: int):
    """Append one tool invocation's stats."""
    metrics["tool_calls"].append({
        "turn": turn,
        "name": name,
        "latency_ms": round(latency_ms, 2),
    })
    metrics["total_tool_latency_ms"] += latency_ms
