"""Tuning router â€” endpoints y jobs de auto-tuning."""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from utils import event_logger, model_scanner, script_runner

router = APIRouter()

# Referencias a estado compartido (se inyectan desde main.py)
jobs: Dict[str, Dict[str, Any]] = {}
ws_connections: Dict[str, List] = {}
MODELS_DIR = None
SKILL_SCRIPTS_DIR = None
DATA_DIR = None


def _find_model(name: str) -> Any:
    for m in model_scanner.scan_models(str(MODELS_DIR)):
        if m.get("name") == name or m.get("path") == name:
            return m
    lowered = name.lower()
    for m in model_scanner.scan_models(str(MODELS_DIR)):
        if lowered in str(m.get("name", "")).lower():
            return m
    return None


def _new_job(job_type: str, payload: Dict[str, Any]) -> str:
    job_id = uuid.uuid4().hex[:8]
    jobs[job_id] = {
        "id": job_id,
        "type": job_type,
        "status": "running",
        "progress": 5,
        "message": "Iniciando...",
        "payload": payload,
        "result": None,
        "created": datetime.now().isoformat(),
    }
    return job_id


async def _update_job(job_id: str, progress: int, message: str, status: str = "running"):
    if job_id in jobs:
        jobs[job_id].update({"progress": progress, "message": message, "status": status})
        for ws in list(ws_connections.get(job_id, [])):
            try:
                await ws.send_json({"job_id": job_id, "progress": progress, "message": message, "status": status})
            except Exception:
                pass


async def _read_body(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        if isinstance(body, dict):
            return body
    except Exception:
        pass
    try:
        form = await request.form()
        return dict(form)
    except Exception:
        return {}


async def _run_tuning_job(job_id: str, model: str, backend: str, profile: str, quick: bool, repetitions: int):
    try:
        await _update_job(job_id, 15, "Ejecutando auto-tuning...")
        script = str(SKILL_SCRIPTS_DIR / "tune_local.py")
        safe_model = "".join(c if (c.isalnum() or c in ("-", "_")) else "_" for c in model) or "model"
        out_json = str(DATA_DIR / f"tune_{safe_model}_{profile}_{job_id}.json")
        _info = _find_model(model)
        _marg = _info["path"] if _info else model
        params: Dict[str, Any] = {"model": _marg, "backend": backend, "profile": profile, "repetitions": repetitions, "output": out_json}
        if quick:
            params["quick"] = True
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: script_runner.run_skill_script(script, params, timeout=1800))
        rows: List[Dict[str, Any]] = []
        best: Dict[str, Any] = {}
        try:
            if Path(out_json).exists():
                data = json.loads(Path(out_json).read_text(encoding="utf-8") or "{}")
                rows = data.get("results", []) or []
                by_backend = data.get("best_by_backend", {}) or {}
                if by_backend:
                    best = sorted(by_backend.values(), key=lambda b: float((b or {}).get("score") or 0), reverse=True)[0]
        except Exception:
            rows, best = [], {}
        try:
            ranked = sorted([r for r in rows if isinstance(r, dict) and r.get("success", True)], key=lambda r: float(r.get("score") or 0), reverse=True)
        except Exception:
            ranked = []
        summary = {"total": len(rows), "ok": len(ranked), "best": best, "json": out_json}
        if not ranked:
            jobs[job_id]["result"] = {"raw": result, "rows": ranked, "summary": summary}
            await _update_job(job_id, 0, "Error: el tuning no produjo resultados (revisa modelo y backend)", "failed")
            return
        jobs[job_id]["result"] = {"raw": result, "rows": ranked, "summary": summary}
        await _update_job(job_id, 100, "Completado", "completed")
        best_config = (best.get("config", {}) or {}) if isinstance(best, dict) else {}
        metrics = (best.get("metrics", {}) or {}) if isinstance(best, dict) else {}
        event_logger.log_event("tuning.completed", {"model": model, "backend": backend, "profile": profile, "best_config": best_config, "metrics": metrics})
    except Exception as exc:
        await _update_job(job_id, 0, f"Error: {exc}", "failed")


@router.post("/api/tune/start")
async def start_tuning(request: Request, background_tasks: BackgroundTasks):
    body = await _read_body(request)
    model = str(body.get("model", "")).strip()
    backend = str(body.get("backend", "hip") or "hip")
    profile = str(body.get("profile", "balanced") or "balanced")
    quick = str(body.get("quick", "true")).lower() not in ("false", "0", "no")
    try:
        repetitions = int(body.get("repetitions", 2))
    except Exception:
        repetitions = 2
    if not model:
        raise HTTPException(status_code=400, detail="Falta 'model'")
    if not _find_model(model):
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    job_id = _new_job("tuning", {"model": model, "backend": backend, "profile": profile})
    background_tasks.add_task(_run_tuning_job, job_id, model, backend, profile, quick, repetitions)
    return {"job_id": job_id, "status": "queued"}


@router.get("/api/tune/status/{job_id}")
def get_tune_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": job["status"], "progress": job["progress"], "message": job.get("message", "")}


@router.get("/api/tune/results/{job_id}")
def get_tune_results(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

