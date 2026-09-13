#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# scaffold.sh — create the JD Matcher folder structure with empty files.
# Run this from INSIDE the (empty) folder where you want the project to live:
#
#     bash scaffold.sh
#
# It creates all folders and empty files in dependency order, ready to paste
# code into. It will NOT overwrite files that already have content.
# ─────────────────────────────────────────────────────────────────────────────

set -e  # stop on first error

echo "Creating folders..."
mkdir -p config
mkdir -p src/jd_matcher

echo "Creating empty files (in build order)..."

# ── Phase 1 — foundation (no code dependencies) ─────────────────────────────
touch .env
touch requirements.txt
touch config/config.yaml

# .env.example — committed template showing which vars are needed (no real key).
# Copy it to .env and replace the placeholder with your actual Groq key.
echo "GROQ_API_KEY=***Your key is written***" > .env.example

# ── Phase 2 — the package, in dependency order (bottom-up) ──────────────────
touch src/jd_matcher/__init__.py          # 1. marks it a package
touch src/jd_matcher/config.py            # 2. reads config.yaml + .env
touch src/jd_matcher/prompts.py           # 3. system prompt (no deps)
touch src/jd_matcher/tools.py             # 4. tool schemas + functions (no deps)
touch src/jd_matcher/metrics.py           # 5. needs config
touch src/jd_matcher/agent.py             # 6. needs config, prompts, tools, metrics
touch src/jd_matcher/cover_letter_agent.py # 7. needs config, metrics
touch src/jd_matcher/ui.py                # 8. needs agent, cover_letter_agent, config

# ── Phase 3 — the entry point (last; triggers the whole import chain) ────────
touch main.py

echo ""
echo "Done. Structure created:"
echo ""
echo "  ."
echo "  |-- main.py                     <- (step 12)"
echo "  |-- requirements.txt            <- step 2"
echo "  |-- .env                        <- step 1"
echo "  |-- .env.example                "
echo "  |-- config/"
echo "  |   \`-- config.yaml            <- step 3"
echo "  \`-- src/"
echo "      \`-- jd_matcher/"
echo "          |-- __init__.py         <- step 4"
echo "          |-- config.py           <- step 5"
echo "          |-- prompts.py          <- step 6"
echo "          |-- tools.py            <- step 7"
echo "          |-- metrics.py          <- step 8"
echo "          |-- agent.py            <- step 9"
echo "          |-- cover_letter_agent.py <- step 10"
echo "          \`-- ui.py               <- step 11"
echo ""

