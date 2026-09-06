"""AMD.AI Dashboard - FastAPI + HTMX + Alpine.js (puerto 9090, LAN ready)."""
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import benchmark, blog, events, launch, llama, tuning
from utils import model_scanner, event_logger, script_runner
from config import BASE_DIR, TEMPLATES_DIR, STATIC_DIR, DATA_DIR, BLOG_DRAFTS_DIR, GENERATED_BATS_DIR, MODELS_DIR, SKILL_SCRIPTS_DIR, LLAMA_BIN_DIR, LLAMA_SRC_DIR, LLAMA_HIP_BUILD_DIR, DEFAULT_VULKAN_SERVER, DEFAULT_HIP_SERVER

# CORS: permitir localhost + red local (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
ALLOWED_ORIGINS = os.environ.get(
    "AMD_ALLOWED_ORIGINS",
    "http://localhost:9090,http://127.0.0.1:9090,http://0.0.0.0:9090,http://192.168.0.*,http://192.168.1.*,http://192.168.2.*,http://10.0.0.*,http://10.0.1.*,http://172.16.*,http://172.17.*,http://172.18.*,http://172.19.*,http://172.20.*,http://172.21.*,http://172.22.*,http://172.23.*,http://172.24.*,http://172.25.*,http://172.26.*,http://172.27.*,http://172.28.*,http://172.29.*,http://172.30.*,http://172.31.*"
).split(",")

app = FastAPI(title="AMD.AI Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/partials", StaticFiles(directory=str(TEMPLATES_DIR / "partials")), name="partials")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Estado compartido (jobs, ws, servers)
jobs: Dict[str, Dict[str, Any]] = {}
ws_connections: Dict[str, List[WebSocket]] = {}
servers: Dict[str, Dict[str, Any]] = {}

# Inyectar estado y rutas en cada router
for _r in [benchmark, tuning, launch, llama, events, blog]:
    _r.jobs = jobs
    _r.ws_connections = ws_connections
    _r.MODELS_DIR = MODELS_DIR
    _r.SKILL_SCRIPTS_DIR = SKILL_SCRIPTS_DIR
    _r.DATA_DIR = DATA_DIR
    _r.BLOG_DRAFTS_DIR = BLOG_DRAFTS_DIR
    _r.GENERATED_BATS_DIR = GENERATED_BATS_DIR
    _r.LLAMA_BIN_DIR = LLAMA_BIN_DIR
    _r.LLAMA_SRC_DIR = LLAMA_SRC_DIR
    _r.LLAMA_HIP_BUILD_DIR = LLAMA_HIP_BUILD_DIR
    _r.DEFAULT_VULKAN_SERVER = DEFAULT_VULKAN_SERVER
    _r.DEFAULT_HIP_SERVER = DEFAULT_HIP_SERVER
    _r.servers = servers
    _r.model_scanner = model_scanner
    _r.event_logger = event_logger
    _r.script_runner = script_runner
    _r.datetime = datetime
    _r.Path = Path
    _r.HTTPException = __import__("fastapi", fromlist=["HTTPException"]).HTTPException
    _r.BackgroundTasks = __import__("fastapi", fromlist=["BackgroundTasks"]).BackgroundTasks
    _r.Request = Request
    _r.WebSocket = WebSocket
    _r.WebSocketDisconnect = WebSocketDisconnect

app.include_router(benchmark.router)
app.include_router(tuning.router)
app.include_router(launch.router)
app.include_router(llama.router)
app.include_router(events.router)
app.include_router(blog.router)


@app.get("/", response_class="HTMLResponse")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AMD.AI Dashboard is running"}


@app.get("/api/models")
def get_models():
    models = model_scanner.scan_models(str(MODELS_DIR))
    return {"models": models, "count": len(models)}


@app.post("/api/models/scan")
def scan_models_trigger():
    models = model_scanner.scan_models(str(MODELS_DIR))
    event_logger = __import__("utils.event_logger", fromlist=["log_event"]).log_event
    event_logger("model.discovered", {"count": len(models), "dir": str(MODELS_DIR)})
    return {"status": "success", "count": len(models), "models": models}


@app.get("/api/backends")
def list_backends():
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
    return {"backends": backends}


@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    ws_connections.setdefault(job_id, []).append(websocket)
    try:
        if job_id in jobs:
            job = jobs[job_id]
            await websocket.send_json({"job_id": job_id, "status": job["status"], "progress": job["progress"], "message": job.get("message", "")})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass  # Ignorar caídas de conexión, errores de red, etc.
    finally:
        if websocket in ws_connections.get(job_id, []):
            ws_connections[job_id].remove(websocket)


@app.get("/api/jobs")
async def list_jobs():
    return {"jobs": list(jobs.values())}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9090, reload=False)
