"""Blog router — listado y lectura de borradores."""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter()

BLOG_DRAFTS_DIR = None


@router.get("/api/blog/drafts")
async def list_drafts():
    drafts: List[Dict[str, Any]] = []
    for f in sorted(BLOG_DRAFTS_DIR.glob("*.md")):
        drafts.append({"filename": f.name, "path": str(f), "size": f.stat().st_size, "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()})
    return {"drafts": drafts, "count": len(drafts)}


@router.get("/api/blog/draft/{filename}")
async def get_draft(filename: str):
    safe = "".join(c if (c.isalnum() or c in ("-", "_", ".")) else "_" for c in filename)
    target = BLOG_DRAFTS_DIR / safe
    if not target.exists():
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"filename": safe, "content": target.read_text(encoding="utf-8")}

