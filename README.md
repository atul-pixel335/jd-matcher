JD MATCHER
===============================================================================

An agentic AI application that scores a resume against a job description, and
hands the result to a second agent that writes a tailored cover letter.

-------------------------------------------------------------------------------
WHAT IT DOES
-------------------------------------------------------------------------------

1. You upload a resume as a PDF and paste a job description.

2. Agent 1 (scorer) reads both, calls Python tools to gather hard evidence
   from the resume, and returns a structured scorecard as JSON.

3. The full agent conversation is displayed as an audit log - every message,
   every tool call, every tool result.

4. Agent 2 (writer) optionally takes ONLY the scorecard and the job
   description - never the raw resume - and writes a three-paragraph cover
   letter.

5. A sidebar shows tokens, estimated cost, and latency for every LLM call and
   tool call.

-------------------------------------------------------------------------------
PREREQUISITES
-------------------------------------------------------------------------------

  - Python 3.11 or newer (developed against 3.13)
  - A Groq API key

SETUP
-------------------------------------------------------------------------------

  1. Create and activate a virtual environment:

         python -m venv .venv
         .venv\Scripts\activate           (Windows)
         source .venv/bin/activate        (macOS / Linux)

  2. Install dependencies:

         pip install -r requirements.txt

  3. Create your .env from the template:

         copy .env.example .env           (Windows)
         cp .env.example .env             (macOS / Linux)

  4. Edit .env and paste in your real key:

         GROQ_API_KEY=your_actual_key_here

-------------------------------------------------------------------------------
RUNNING THE APP
-------------------------------------------------------------------------------

         streamlit run main.py

