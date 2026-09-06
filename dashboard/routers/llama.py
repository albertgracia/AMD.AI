"""Llama router — actualizaciones, rebuild HIP y version checking."""
import asyncio
import httpx
import re as _re
import shutil as _shutil
import tempfile as _tempfile
import zipfile as _zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from utils import event_logger

router = APIRouter()

# Referencias a estado compartido
jobs: Dict[str, Dict[str, Any]] = {}
ws_connections: Dict[str, list] = {}
LLAMA_BIN_DIR = None
LLAMA_SRC_DIR = None
LLAMA_HIP_BUILD_DIR = None
UPDATE_URL_PREFIX = "https://github.com/ggml-org/llama.cpp/releases/download/"
UPDATE_DEST_ROOT = LLAMA_BIN_DIR


def _new_job(job_type: str, payload: Dict[str, Any]) -> str:
    import uuid
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


async def _run_llama_update_job(job_id: str, asset_url: str, dirname: str):
    tmpdir = None
    try:
        await _update_job(job_id, 5, "Descargando...")
        tmpdir = Path(_tempfile.mkdtemp(prefix="amdai_update_"))
        zpath = tmpdir / (dirname + ".zip")
        async with httpx.AsyncClient(follow_redirects=True, timeout=3600) as _client:
            async with _client.stream("GET", asset_url, headers={"User-Agent": "amd-ai-dashboard"}) as _r:
                if _r.status_code != 200:
                    raise ValueError(f"Descarga fallo: HTTP {_r.status_code}")
                _total = int(_r.headers.get("content-length") or 0)
                _done = 0
                with open(zpath, "wb") as _f:
                    async for _chunk in _r.aiter_bytes(1024 * 256):
                        _f.write(_chunk)
                        _done += len(_chunk)
                        if _total:
                            await _update_job(job_id, 5 + int(_done / _total * 80), f"Descargando {_done // (1024 * 1024)} MB de {_total // (1024 * 1024)} MB")
        await _update_job(job_id, 88, "Extrayendo...")
        _xdir = tmpdir / "x"
        _xdir.mkdir(exist_ok=True)
        with _zipfile.ZipFile(zpath) as _z:
            for _m in _z.namelist():
                _posix = Path(_m.replace("\\", "/"))
                if _posix.is_absolute() or ".." in _posix.parts or _posix.name.startswith("."):
                    raise ValueError(f"Ruta insegura en ZIP: {_m}")
                _sanitized = "".join(c if c.isalnum() or c in ("-", "_", ".", "/", "\\") else "_" for c in _m)
                if _sanitized != _m:
                    raise ValueError(f"Ruta con caracteres invalidos en ZIP: {_m}")
            _z.extractall(_xdir)
        _src = _xdir / dirname
        if not _src.exists():
            _tops = [p for p in _xdir.iterdir() if p.is_dir()]
            _src = _tops[0] if len(_tops) == 1 else _xdir
        _dest = UPDATE_DEST_ROOT / dirname
        if _dest.exists():
            raise ValueError(f"Ya existe {_dest} (no se sobrescribe)")
        UPDATE_DEST_ROOT.mkdir(parents=True, exist_ok=True)
        _shutil.move(str(_src), str(_dest))
        jobs[job_id]["result"] = {"path": str(_dest), "dirname": dirname}
        await _update_job(job_id, 100, "Completado", "completed")
        event_logger.log_event("update.installed", {"dirname": dirname, "path": str(_dest), "url": asset_url})
    except Exception as exc:
        await _update_job(job_id, 0, f"Error: {exc}", "failed")
    finally:
        try:
            if tmpdir and Path(tmpdir).exists():
                _shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


@router.post("/api/llama/update")
async def start_llama_update(request: Request, background_tasks: BackgroundTasks):
    body = await request.json() or {}
    asset_url = str(body.get("asset_url", "") or "").strip()
    filename = str(body.get("filename", "") or "").strip()
    if not asset_url or not filename:
        raise HTTPException(status_code=400, detail="Falta 'asset_url' o 'filename'")
    if not asset_url.startswith(UPDATE_URL_PREFIX):
        raise HTTPException(status_code=400, detail="URL no permitida (solo releases oficiales de llama.cpp)")
    dirname = filename[:-4] if filename.lower().endswith(".zip") else filename
    if not _re.fullmatch(r"llama-b\d+-bin-win-(vulkan|hip|rocm)-x64", dirname):
        raise HTTPException(status_code=400, detail="Asset no valido para instalacion automatica")
    if (UPDATE_DEST_ROOT / dirname).exists():
        raise HTTPException(status_code=400, detail=f"Ya instalado en {UPDATE_DEST_ROOT / dirname}")
    job_id = _new_job("update", {"asset_url": asset_url, "dirname": dirname})
    background_tasks.add_task(_run_llama_update_job, job_id, asset_url, dirname)
    return {"job_id": job_id, "status": "queued", "dirname": dirname}


@router.get("/api/llama/update/status/{job_id}")
def get_llama_update_status(job_id: str):
    job = jobs.get(job_id)
    if not job or job.get("type") != "update":
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/api/llama/updates")
async def llama_updates():
    local = []
    for p in [LLAMA_BIN_DIR, LLAMA_HIP_BUILD_DIR / "bin"]:
        try:
            for child in sorted(p.iterdir()):
                if child.is_dir() and "llama-" in child.name.lower():
                    m = _re.search(r"llama-b(\d{4,5})-bin", child.name.lower())
                    local.append({"path": str(child), "build": int(m.group(1)) if m else None, "kind": "vulkan" if "vulkan" in child.name.lower() else ("rocm" if "rocm" in child.name.lower() else "hip" if "hip" in child.name.lower() else "custom")})
        except Exception:
            continue
    latest: Dict[str, Any] = {}
    try:
        r = httpx.get("https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=20", timeout=10, headers={"User-Agent": "amd-ai-dashboard"})
        data = {}
        if r.status_code == 200:
            for rel in r.json():
                if _re.fullmatch(r"b\d+", str(rel.get("tag_name") or "")):
                    data = rel
                    break
            else:
                data = {}
        if data:
            assets = []
            for a in data.get("assets", []) or []:
                name = str(a.get("name", ""))
                low = name.lower()
                if "win" in low and ("vulkan" in low or "hip" in low or "rocm" in low):
                    assets.append({"name": name, "size_mb": round((a.get("size") or 0) / (1024 * 1024), 1), "url": a.get("browser_download_url")})
            assets.sort(key=lambda a: ("vulkan" not in a["name"].lower(), "hip" not in a["name"].lower(), a["name"]))
            tag = str(data.get("tag_name") or "")
            mtag = _re.search(r"b(\d+)", tag)
            latest = {
                "tag": tag,
                "build": int(mtag.group(1)) if mtag else None,
                "name": data.get("name"),
                "published_at": data.get("published_at"),
                "url": data.get("html_url"),
                "notes": (data.get("body") or "")[:4000],
                "assets": assets[:12],
                "assets_total": len(data.get("assets", []) or []),
            }
        else:
            latest = {"error": f"GitHub devolvio {r.status_code}"}
    except Exception as exc:
        latest = {"error": f"Sin conexion a GitHub: {exc}"}
    local_max = max([b["build"] for b in local if b.get("build")], default=None)
    return {"local": local, "local_max_build": local_max, "latest": latest, "checked_at": datetime.now().isoformat()}


# HIP Rebuild
HIP_SRC_DIR = LLAMA_SRC_DIR
HIP_BUILD_DIR = LLAMA_HIP_BUILD_DIR


def _hip_prereqs() -> Any:
    if not (HIP_SRC_DIR / ".git").exists():
        return f"No hay repo git en {HIP_SRC_DIR}"
    if not _sh.which("git"):
        return "git no esta en el PATH"
    if not _sh.which("cmake"):
        return "cmake no esta en el PATH"
    try:
        from utils.script_runner import ROCM_SDK_PATH as _sdk
        if not Path(_sdk).exists():
            return f"ROCm SDK no encontrado en {_sdk}"
    except Exception as exc:
        return f"No se pudo localizar ROCm SDK: {exc}"
    return None


async def _run_hip_rebuild_job(job_id: str):
    def _run(cmd, cwd, timeout):
        import subprocess as _sp
        p = _sp.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        tail = ((p.stdout or "") + (p.stderr or ""))[-2000:]
        return p.returncode, tail

    try:
        await _update_job(job_id, 5, "Comprobando requisitos...")
        err = _hip_prereqs()
        if err:
            raise ValueError(err)
        await _update_job(job_id, 10, "git pull en llama.cpp-src...")
        loop = asyncio.get_event_loop()
        code, out = await loop.run_in_executor(None, lambda: _run(["git", "pull", "--ff-only"], HIP_SRC_DIR, 600))
        if code != 0:
            raise ValueError(f"git pull fallo: {out[-500:]}")
        if not (HIP_BUILD_DIR / "CMakeCache.txt").exists():
            await _update_job(job_id, 20, "Configurando CMake (HIP)...")
            from utils.script_runner import ROCM_SDK_PATH as _sdk2
            code, out = await loop.run_in_executor(None, lambda: _run(["cmake", "-S", ".", "-B", "build-hip", "-DGGML_HIP=ON", "-DGGML_HIP_GRAPHS=ON", "-DHIP_PLATFORM=amd", f"-DHIP_PATH={_sdk2}", "-DCMAKE_BUILD_TYPE=Release"], HIP_SRC_DIR, 900))
            if code != 0:
                raise ValueError(f"cmake configure fallo: {out[-500:]}")
        await _update_job(job_id, 30, "Compilando HIP (puede tardar bastante, no cierres el servidor)...")
        code, out = await loop.run_in_executor(None, lambda: _run(["cmake", "--build", "build-hip", "--config", "Release"], HIP_SRC_DIR, 7200))
        if code != 0:
            raise ValueError(f"compilacion fallo: {out[-500:]}")
        _srv = HIP_BUILD_DIR / "bin" / "llama-server.exe"
        _bench = HIP_BUILD_DIR / "bin" / "llama-bench.exe"
        if not _srv.exists() or not _bench.exists():
            raise ValueError("Compilacion termino pero faltan binarios en build-hip\\bin")
        jobs[job_id]["result"] = {"path": str(_srv.parent)}
        await _update_job(job_id, 100, "Completado", "completed")
        event_logger.log_event("update.rebuilt", {"backend": "hip", "path": str(_srv.parent)})
    except Exception as exc:
        await _update_job(job_id, 0, f"Error: {exc}", "failed")


@router.post("/api/llama/rebuild-hip")
async def start_hip_rebuild(background_tasks: BackgroundTasks):
    err = _hip_prereqs()
    if err:
        raise HTTPException(status_code=400, detail=err)
    for j in jobs.values():
        if j.get("type") == "rebuild-hip" and j.get("status") in ("running", "queued"):
            raise HTTPException(status_code=400, detail="Ya hay una recompilacion en curso")
    job_id = _new_job("rebuild-hip", {"backend": "hip"})
    background_tasks.add_task(_run_hip_rebuild_job, job_id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/api/llama/rebuild-hip/status/{job_id}")
def get_hip_rebuild_status(job_id: str):
    job = jobs.get(job_id)
    if not job or job.get("type") != "rebuild-hip":
        raise HTTPException(status_code=404, detail="Job not found")
    return job

