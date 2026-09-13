import re
from datetime import datetime

# ── JSON schema the LLM reads to know what tools exist ──────────────────────
TOOLS = [
    {
        "type": "function", # Tells the API that this is a callable function
        "function": {
            "name": "count_keywords",
            "description": "Count how many times each keyword appears in the resume.",
            "parameters": {
                "type": "object", # JSON object / dictionary
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keywords to count in the resume text.",
                    },
                    "resume_text": {
                        "type": "string",
                        "description": "Full resume text to search.",
                    },
                },
                "required": ["keywords", "resume_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_years_of_experience",
            "description": "Parse the resume for years of experience -- either explicit 'X years' phrases or date ranges like 'January 2023 - Present'. Returns total years as a JSON object.",
            "parameters": {
                "type": "object", # JSON object
                "properties": {
                    "resume_text": {
                        "type": "string",
                        "description": "Full resume text to scan for experience mentions.",
                    }
                },
                "required": ["resume_text"],
            },
        },
    },
]


# ── Whole-word matching helpers ─────────────────────────────────────────────

_TOKEN_LEAD = r"[A-Za-z0-9+#._]"
_TOKEN_TRAIL = r"[A-Za-z0-9+#]"

# # # VERSION 2 — whole-word matching (see _keyword_pattern above).
# def _keyword_pattern(keyword: str) -> str:
#     words = re.split(r"[\s\-]+", keyword.strip())

#     parts = []
#     for word in words:
#         if word:
#             parts.append(re.escape(word))

#     if not parts:
#         return ""
#     core = r"[\s\-]*".join(parts)
#     return rf"(?<!{_TOKEN_LEAD}){core}(?!{_TOKEN_TRAIL})"

# def count_keywords(keywords: list[str], resume_text: str) -> dict:
#     """Return keyword -> whole-word occurrence count (case-insensitive)."""
#     result = {}
#     for kw in keywords:
#         pattern = _keyword_pattern(kw)
#         result[kw] = len(re.findall(pattern, resume_text, re.IGNORECASE)) if pattern else 0

#     print(f"[tool] count_keywords -> {result}")
#     return result

# ── Python functions the LLM asks us to run ─────────────────────────────────
# VERSION 1 — naive substring counting.
def count_keywords(keywords: list[str], resume_text: str) -> dict:
    """Return keyword -> count (case-insensitive) dictionary."""
    result = {}
    for kw in keywords:
        count = resume_text.lower().count(kw.lower())
        result[kw] = count
    print(f"[tool] count_keywords -> {result}")
    return result


# Month name -> number, for the Strategy 2 date-range parsing below.
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _to_date(month_name: str, year: str) -> datetime | None:
    """'January', '2024' -> datetime(2024, 1, 1). None if it is not a real month.

    Resumes never give a day, so every date is normalised to the 1st.
    The regexes match any word, so "Python, 2024" reaches here and must
    be rejected rather than raise.
    """
    month = MONTHS.get(month_name.lower())
    return datetime(int(year), month, 1) if month else None


def check_years_of_experience(resume_text: str) -> dict:
    """
    Two strategies to find total years of experience:
    1. Explicit mentions: '5 years', '10+ years'
    2. Date ranges: 'January, 2024 - July, 2024' or 'September, 2024 - Present'
       Each range is measured on its own and the durations are added up.
    Returns a dict (Groq requires tool results to be JSON objects, not bare numbers).
    """
    # Strategy 1 -- explicit "X years" phrases
    explicit = re.findall(r"(\d+)\+?\s+years?", resume_text, re.IGNORECASE)
    max_explicit = max((int(m) for m in explicit), default=0)

    # Strategy 2 -- one (start, end) pair per job found in the text
    spans = []

    # 2a -- "Month YYYY - Month YYYY"  e.g. "January, 2024 - July, 2024"
    pattern_range = r"([A-Za-z]+),?\s+(\d{4})\s*-\s*([A-Za-z]+),?\s+(\d{4})"
    for start_m, start_y, end_m, end_y in re.findall(pattern_range, resume_text):
        start = _to_date(start_m, start_y)
        end = _to_date(end_m, end_y)
        if start and end and end > start:
            spans.append((start, end))

    # 2b -- "Month YYYY - Present"     e.g. "September, 2024 - Present"
    pattern_present = r"([A-Za-z]+),?\s+(\d{4})\s*-\s*[Pp]resent"
    now = datetime.now()
    for start_m, start_y in re.findall(pattern_present, resume_text):
        start = _to_date(start_m, start_y)
        if start and now > start:
            spans.append((start, now))

    # Sum each job's own length, so career gaps are not counted as experience.
    total_days = sum((end - start).days for start, end in spans)
    max_from_dates = round(total_days / 365, 1)

    total = max(max_explicit, max_from_dates)
    print(f"[tool] check_years_of_experience -> {total} years "
          f"(explicit={max_explicit}, from date ranges={max_from_dates})")
    return {"years_of_experience": total}


# ── Dispatcher: maps a tool name to its Python function ─────────────────────
TOOL_REGISTRY = {
    "count_keywords": count_keywords,
    "check_years_of_experience": check_years_of_experience,
}
