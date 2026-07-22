"""Pytest bootstrap: backend modules live in py_modules/ (Decky CLI layout)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "py_modules"))
