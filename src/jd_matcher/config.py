import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI

# ── Locate the project root (…/jd-matcher) from this file's location ─────────
# config.py lives at:  <root>/src/jd_matcher/config.py
# parents[0] = jd_matcher, parents[1] = src, parents[2] = <root>
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.yaml"

# ── Load NON-SECRET settings from config.yaml ────────────────────────────────
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

# ── Load SECRETS from .env (kept out of config.yaml and out of git) ──────────
load_dotenv(_PROJECT_ROOT / ".env")

# ── Model + connection ───────────────────────────────────────────────────────
MODEL = CONFIG["model"]["name"]
BASE_URL = CONFIG["model"]["base_url"]

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=BASE_URL,
)

# ── Convenience accessors for the rest of the app ────────────────────────────
TEMPERATURES = CONFIG["temperatures"]
PRICING = CONFIG["pricing"]
LIMITS = CONFIG["limits"]
UI = CONFIG["ui"]
