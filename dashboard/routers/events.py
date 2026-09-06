"""Events router — listado de eventos del logger."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter()

DATA_DIR = None


@router.get("/api/events")
async def list_events(limit: int = 20, prefix: str = ""):
    path = DATA_DIR / "events.jsonl"
    events: List[Dict[str, Any]] = []
    try:
        if path.exists():
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            prefixes = [p.strip() for p in (prefix or "").split(",") if p.strip()]
            pool = lines[-300:] if prefixes else lines[-max(1, min(limit, 100)):]
            for line in pool:
                try:
                    evt = json.loads(line)
                except Exception:
                    continue
                if prefixes and not any(str(evt.get("event_type", "")).startswith(p) for p in prefixes):
                    continue
                events.append(evt)
            events.reverse()
            events = events[:max(1, min(limit, 100))]
    except Exception:
        events = []
    return {"events": events, "count": len(events)}

