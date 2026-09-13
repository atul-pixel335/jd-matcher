import re

INJECTION_PATTERNS = [
    # "ignore previous / prior / above / all instructions"
    r"ignore\s+(the\s+)?(previous|prior|above|all|earlier|any)\s+(instructions?|prompts?|rules?|directives?)",

    # "disregard the system prompt / instructions"
    r"disregard\s+(the\s+)?(previous|prior|above|any|all|earlier)?\s*(system|prompt|instructions?|rules?)",

    # "forget everything / all instructions"
    r"forget\s+(everything|all|the)\s*(instructions?|rules?|above|prior)?",

    # "override / bypass instructions"
    r"(override|bypass)\s+.{0,30}(instructions?|rules?|system|prompt)",

    # "give / assign this resume a score of N" (rating manipulation)
    r"(give|assign|set|make)\s+.{0,40}(score|rating|grade)\s+.{0,10}\d+",

    # "you are now a ___"  (role reprogramming)
    r"you\s+are\s+now\s+(a|an|the)\s+",

    # Explicit role/act commands
    r"act\s+as\s+(a|an|the)\s+",
    r"pretend\s+(you\s+are|to\s+be)",

    # Chat-template escapes
    r"<\|(im_start|im_end|system|user|assistant|end_of_turn)\|>",
    r"\[/?INST\]|\[/?SYS\]|\[SYSTEM\]",

    # "reveal / print your system prompt"
    r"(reveal|print|show|output|display|repeat)\s+(your|the)\s+(system\s+)?(prompt|instructions?|rules?)",

    # New-instruction hijack
    r"new\s+instructions?\s*[:\-]",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def detect_prompt_injection(text: str) -> tuple[bool, str]:

    if not text:
        return True, ""

    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            snippet = match.group(0)
            return False, f"Blocked suspicious phrase: '{snippet}'"

    return True, ""

def validate_jd_looks_real(jd_text: str) -> tuple[bool, str]:

    if not jd_text or not jd_text.strip():
        return False, "Job description is empty."

    word_count = len(jd_text.split())
    if word_count < 20:
        return False, f"Job description is too short ({word_count} words). Please paste a full JD."

    # Look for JD-signal keywords
    jd_signals = [
        "responsibilities", "requirements", "experience", "skills",
        "role", "position", "must have", "years of", "we are looking",
        "qualifications", "duties", "job", "candidate", "team",
    ]
    hits = sum(1 for kw in jd_signals if kw.lower() in jd_text.lower())
    if hits < 2:
        return False, "This doesn't look like a job description (missing typical JD phrasing)."

    return True, ""

def run_all_input_guardrails(resume_text: str, jd_text: str) -> tuple[bool, str]:

    # 1. JD structural sanity
    ok, reason = validate_jd_looks_real(jd_text)
    if not ok:
        return False, f"[GR:JD-SHAPE] {reason}"

    # 2. Prompt injection in JD
    ok, reason = detect_prompt_injection(jd_text)
    if not ok:
        return False, f"[GR:INJECTION in JD] {reason}"

    # 3. Prompt injection in resume (attackers hide in PDFs too)
    ok, reason = detect_prompt_injection(resume_text)
    if not ok:
        return False, f"[GR:INJECTION in RESUME] {reason}"

    return True, ""