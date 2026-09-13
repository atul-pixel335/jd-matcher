import sys
from pathlib import Path

# Make the src/ layout importable without installing the package.
# This lets `streamlit run main.py` keep working as-is.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from jd_matcher.ui import render

render()
