"""Benchmark router â€” endpoints y jobs de benchmarking."""
import asyncio
import json
import uuid
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


async def _run_benchmark_job(job_id: str, model: str, backend: str, quick: bool, repetitions: int):
    try:
        await _update_job(job_id, 15, "Ejecutando benchmark...")
        script = str(SKILL_SCRIPTS_DIR / "bench_local.py")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model = "".join(c if (c.isalnum() or c in ("-", "_")) else "_" for c in model) or "model"
        out_csv = str(DATA_DIR / f"bench_{safe_model}_{job_id}.csv")
        out_json = str(DATA_DIR / f"bench_{safe_model}_{job_id}.json")
        _info = _find_model(model)
        _marg = _info["path"] if _info else model
        params: Dict[str, Any] = {"model": _marg, "backend": backend, "repetitions": repetitions, "output": out_csv, "json_output": out_json}
        if quick:
            params["quick"] = True
        try:
            params["yes"] = True
        except Exception:
            pass
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: script_runner.run_skill_script(script, params, timeout=1800))
        rows: List[Dict[str, Any]] = []
        try:
            if Path(out_json).exists():
                rows = json.loads(Path(out_json).read_text(encoding="utf-8") or "[]")
        except Exception:
            rows = []
        summary: Dict[str, Any] = {}
        try:
            ok_rows = [r for r in rows if isinstance(r, dict) and r.get("success", True)]
            best_d = max(ok_rows, key=lambda r: float(r.get("decode_tok_s") or 0)) if ok_rows else {}
            best_p = max(ok_rows, key=lambda r: float(r.get("prefill_tok_s") or 0)) if ok_rows else {}
            summary = {
                "total": len(rows),
                "ok": len(ok_rows),
                "best_decode_tok_s": (best_d or {}).get("decode_tok_s"),
                "best_decode_config": {k: (best_d or {}).get(k) for k in ("n_gpu_layers", "prompt_size", "gen_size", "batch_size", "flash_attn", "cache_type_k", "cache_type_v")},
                "best_prefill_tok_s": (best_p or {}).get("prefill_tok_s"),
                "csv": out_csv,
                "json": out_json,
            }
        except Exception:
            summary = {"csv": out_csv, "json": out_json}
        _ok = [r for r in rows if isinstance(r, dict) and r.get("success", True) and (r.get("decode_tok_s") or r.get("prefill_tok_s"))]
        if not _ok:
            jobs[job_id]["result"] = {"raw": result, "rows": rows, "summary": summary}
            await _update_job(job_id, 0, "Error: el benchmark no produjo resultados (revisa modelo y backend)", "failed")
            return
        jobs[job_id]["result"] = {"raw": result, "rows": rows, "summary": summary}
        await _update_job(job_id, 100, "Completado", "completed")
        event_logger.log_event("benchmark.completed", {"model": model, "backend": backend, "results": {"results": rows, "summary": summary}})
    except Exception as exc:
        await _update_job(job_id, 0, f"Error: {exc}", "failed")


@router.post("/api/benchmark/start")
async def start_benchmark(request: Request, background_tasks: BackgroundTasks):
    body = await _read_body(request)
    model = str(body.get("model", "") or body.get("job_id", "") or "").strip()
    backend = str(body.get("backend", "hip") or "hip")
    quick = str(body.get("quick", "true")).lower() not in ("false", "0", "no")
    try:
        repetitions = int(body.get("repetitions", 2))
    except Exception:
        repetitions = 2
    if not model:
        raise HTTPException(status_code=400, detail="Falta 'model'")
    if not _find_model(model):
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    job_id = _new_job("benchmark", {"model": model, "backend": backend})
    background_tasks.add_task(_run_benchmark_job, job_id, model, backend, quick, repetitions)
    return {"job_id": job_id, "status": "queued"}


@router.get("/api/benchmark/status/{job_id}")
def get_benchmark_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": job["status"], "progress": job["progress"], "message": job.get("message", "")}


@router.get("/api/benchmark/results/{job_id}")
def get_benchmark_results(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

