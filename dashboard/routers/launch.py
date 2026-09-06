"""Launch router — generacion, guardado y lanzamiento de .bat."""
import subprocess as _sp
import uuid as _uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from utils import event_logger

router = APIRouter()

# Referencias a estado compartido
GENERATED_BATS_DIR = None
servers: Dict[str, Dict[str, Any]] = {}
jobs: Dict[str, Dict[str, Any]] = {}
ws_connections: Dict[str, list] = {}
LLAMA_BIN_DIR = None
LLAMA_HIP_BUILD_DIR = None


def _resolve_complementary(mode: str, detected: Optional[str], kind: str) -> Optional[str]:
    mode = (mode or "auto").lower()
    if mode == "off":
        return None
    if mode == "on":
        if not detected:
            raise HTTPException(status_code=400, detail=f"{kind} forzado a on pero el modelo no trae fichero detectado")
        return detected
    return detected


def _get_backends() -> list:
    import re as _re3
    backends = []
    bin_root = LLAMA_BIN_DIR
    found = []
    try:
        for child in sorted(bin_root.iterdir()):
            if not child.is_dir():
                continue
            m = _re3.fullmatch(r"llama-b(\d+)-bin-win-(vulkan|rocm)-x64", child.name.lower())
            if m and (child / "llama-bench.exe").exists():
                found.append((int(m.group(1)), m.group(2), child))
    except Exception:
        found = []
    for _build, _kind, _path in sorted(found):
        backends.append({"name": _kind, "path": str(_path), "build": _path.name})
    if not backends:
        for p in [LLAMA_BIN_DIR / "llama-b10712-bin-win-vulkan-x64", LLAMA_BIN_DIR / "llama-b10796-bin-win-vulkan-x64"]:
            if p.exists() and (p / "llama-bench.exe").exists():
                backends.append({"name": "vulkan", "path": str(p), "build": p.name})
    hip_path = LLAMA_HIP_BUILD_DIR / "bin"
    if (hip_path / "llama-bench.exe").exists():
        backends.append({"name": "hip", "path": str(hip_path), "build": "build-hip"})
    return backends


def _build_bat(model_name: str, model_path: str, preset: str, custom: Optional[Dict[str, Any]], backend: str = "hip", mmproj: Optional[str] = None, mtp_draft: Optional[str] = None, vision: str = "auto", mtp: str = "auto", host: str = "127.0.0.1", port: int = 8080) -> str:
    presets = {
        "balanced": {"ngl": -1, "prompt": 2048, "gen": 256, "batch": 1024, "fa": "auto", "cache": "q4_0", "ctx": 65536},
        "throughput": {"ngl": -1, "prompt": 512, "gen": 256, "batch": 2048, "fa": "auto", "cache": "q4_0", "ctx": 65536},
        "latency": {"ngl": -1, "prompt": 2048, "gen": 256, "batch": 1024, "fa": "auto", "cache": "q4_0", "ctx": 65536},
        "max_context": {"ngl": -1, "prompt": 4096, "gen": 512, "batch": 1024, "fa": "auto", "cache": "q4_0", "ctx": 131072},
        "memory_efficient": {"ngl": -1, "prompt": 512, "gen": 256, "batch": 2048, "fa": "auto", "cache": "q4_0", "ctx": 65536},
        "cpu_only": {"ngl": 0, "prompt": 512, "gen": 256, "batch": 2048, "fa": "off", "cache": "q4_0", "ctx": 65536},
    }
    cfg = dict(presets.get(preset, presets["balanced"]))
    if custom:
        for key in ("ngl", "prompt", "gen", "batch", "fa", "cache", "ctx"):
            if key in custom and custom[key] not in (None, ""):
                cfg[key] = custom[key]
    backends_dict = {b["name"]: b for b in _get_backends()}
    if preset == "cpu_only" or backend == "cpu":
        exe = str(LLAMA_BIN_DIR / "llama-b10712-bin-win-vulkan-x64" / "llama-server.exe")
    elif backend in backends_dict:
        exe = str(Path(backends_dict[backend]["path"]) / "llama-server.exe")
    else:
        exe = str(LLAMA_HIP_BUILD_DIR / "bin" / "llama-server.exe")
    lines = [
        "@echo off",
        "",
        f"REM AMD.AI Dashboard - {model_name} [{preset}] ({backend})",
        f'"{exe}" ^',
        f'  --model "{model_path}" ^',
    ]
    mmproj_final = _resolve_complementary(vision, mmproj, "Vision (mmproj)")
    mtp_final = _resolve_complementary(mtp, mtp_draft, "MTP (model-draft)")
    if mmproj_final:
        lines.append(f'  --mmproj "{mmproj_final}" ^')
    if mtp_final:
        lines.append(f'  --model-draft "{mtp_final}" ^')
        lines.append("  --spec-type draft-mtp ^")
        lines.append("  --spec-draft-n-max 4 ^")
    lines += [
        f'  --n-gpu-layers {cfg["ngl"]} ^',
        f'  --predict {cfg["gen"]} ^',
        f'  --batch-size {cfg["batch"]} ^',
        f'  --flash-attn {cfg["fa"]} ^',
        f'  --cache-type-k {cfg["cache"]} ^',
        f'  --cache-type-v {cfg["cache"]} ^',
        f'  --ctx-size {cfg["ctx"]} ^',
        f"  --host {host if host in ('127.0.0.1', 'localhost', '0.0.0.0') else '127.0.0.1'} ^",
        f"  --port {port if isinstance(port, int) and 1 <= port <= 65535 else 8080} ^",
        f'  --api-key "{os.environ.get("AMD_LLAMA_API_KEY", "anything")}" ^',
        f"  --alias {model_name} ^",
        "  --log-verbosity 4",
        "",
        "pause",
    ]
    return "\n".join(lines)


import os


@router.post("/api/launch/generate-bat")
async def generate_bat(request: Request):
    body = await request.json() or {}
    model = str(body.get("model", "")).strip()
    preset = str(body.get("preset", "balanced") or "balanced")
    backend = str(body.get("backend", "hip") or "hip")
    custom = body.get("custom_config") or body.get("custom") or {}
    if not isinstance(custom, dict):
        custom = {}
    if not model:
        raise HTTPException(status_code=400, detail="Falta 'model'")
    from utils import model_scanner
    info = None
    for m in model_scanner.scan_models(str(model_scanner.BASE_DIR.parent / "models")):
        if m.get("name") == model or m.get("path") == model:
            info = m
            break
    if not info:
        lowered = model.lower()
        for m in model_scanner.scan_models(str(model_scanner.BASE_DIR.parent / "models")):
            if lowered in str(m.get("name", "")).lower():
                info = m
                break
    if not info:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    vision = str(body.get("vision", "auto") or "auto")
    mtp = str(body.get("mtp", "auto") or "auto")
    host = str(body.get("host", "127.0.0.1") or "127.0.0.1")
    if host not in ("127.0.0.1", "localhost", "0.0.0.0"):
        raise HTTPException(status_code=400, detail="Host no valido (usa 127.0.0.1 o 0.0.0.0)")
    try:
        port = int(body.get("port", 8080) or 8080)
    except Exception:
        port = 8080
    if not 1 <= port <= 65535:
        raise HTTPException(status_code=400, detail="Puerto no valido (1-65535)")
    bat = _build_bat(info["name"], info["path"], preset, custom, backend, info.get("mmproj"), info.get("mtp_draft"), vision, mtp, host, port)
    event_logger.log_event("bat.generated", {"model": info["name"], "preset": preset, "backend": backend, "config": custom, "vision": vision, "mtp": mtp, "host": host, "port": port, "mmproj": info.get("mmproj"), "mtp_draft": info.get("mtp_draft")})
    return {"model": info["name"], "preset": preset, "backend": backend, "vision": vision, "mtp": mtp, "host": host, "port": port, "mmproj": info.get("mmproj"), "mtp_draft": info.get("mtp_draft"), "bat_content": bat, "download_url": ""}


@router.post("/api/launch/save-bat")
async def save_bat(request: Request):
    body = await request.json() or {}
    filename = str(body.get("filename", "run_model.bat"))
    content = str(body.get("content", body.get("bat_content", "")))
    safe = "".join(c if (c.isalnum() or c in ("-", "_", ".")) else "_" for c in filename) or "run_model.bat"
    if not safe.lower().endswith(".bat"):
        safe += ".bat"
    path = GENERATED_BATS_DIR / safe
    path.write_text(content, encoding="utf-8")
    return {"status": "success", "path": str(path), "filename": safe}


@router.post("/api/launch/launch")
async def launch_bat(request: Request):
    body = await request.json() or {}
    path = str(body.get("path", "")).strip()
    port = int(body.get("port", 8080) or 8080)
    if not path:
        raise HTTPException(status_code=400, detail="Falta 'path'")
    target = Path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Archivo .bat no encontrado")
    if target.suffix.lower() != ".bat" or GENERATED_BATS_DIR not in target.parents:
        raise HTTPException(status_code=400, detail="Solo se pueden lanzar .bat generados por el dashboard")
    try:
        creationflags = getattr(_sp, "CREATE_NEW_CONSOLE", 0)
        proc = _sp.Popen(["cmd", "/c", str(target)], cwd=str(target.parent), creationflags=creationflags)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo lanzar: {exc}")
    server_id = _uuid.uuid4().hex[:8]
    servers[server_id] = {"id": server_id, "path": str(target), "pid": proc.pid, "port": port, "url": f"http://localhost:{port}", "started": datetime.now().isoformat(), "status": "running"}
    jobs[f"server-{server_id}"] = {"id": f"server-{server_id}", "type": "server", "status": "running", "progress": 100, "message": f"llama-server lanzado (PID {proc.pid})", "payload": {"path": str(target)}, "result": None, "created": datetime.now().isoformat()}
    event_logger.log_event("launch.requested", {"path": str(target), "pid": proc.pid, "port": port})
    return {"status": "success", "server_id": server_id, "pid": proc.pid, "path": str(target), "url": f"http://localhost:{port}"}


@router.get("/api/launch/download-bat/{filename}")
async def download_bat(filename: str):
    safe = "".join(c if (c.isalnum() or c in ("-", "_", ".")) else "_" for c in filename)
    bat_path = GENERATED_BATS_DIR / safe
    if not bat_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(str(bat_path), filename=safe, media_type="application/x-msdownload")


def _pid_alive(pid: int) -> bool:
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        kernel32.CloseHandle(handle)
        return True
    except Exception:
        return False


@router.get("/api/servers")
async def list_servers():
    for sid, srv in list(servers.items()):
        try:
            import psutil
            alive = psutil.pid_exists(srv["pid"])
        except Exception:
            alive = _pid_alive(srv["pid"])
        srv["status"] = "running" if alive else "stopped"
    return {"servers": list(servers.values())}


@router.post("/api/servers/stop")
async def stop_server(request: Request):
    body = await request.json() or {}
    server_id = str(body.get("server_id", "") or "")
    srv = servers.get(server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    try:
        _sp.run(["taskkill", "/PID", str(srv["pid"]), "/F"], capture_output=True, timeout=15)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo parar: {exc}")
    srv["status"] = "stopped"
    event_logger.log_event("launch.stopped", {"server_id": server_id, "pid": srv["pid"]})
    return {"status": "stopped", "server_id": server_id}

