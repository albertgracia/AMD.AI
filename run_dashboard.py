"""Lanzador delgado del dashboard (evita drift con dashboard/main.py)."""
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE / "dashboard"))

from main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=False)
