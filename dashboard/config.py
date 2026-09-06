"""AMD.AI Dashboard - Configuración centralizada de rutas y entornos."""
import os
from pathlib import Path

# Raíz del proyecto (auto-detectada desde este archivo)
BASE_DIR = Path(__file__).parent

# Rutas internas del dashboard
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
BLOG_DRAFTS_DIR = DATA_DIR / "blog_drafts"
GENERATED_BATS_DIR = DATA_DIR / "generated_bats"

# Rutas externas (sobrescribibles con variables de entorno)
MODELS_DIR = Path(os.environ.get("AMD_MODELS_DIR", r"G:\Proyectos\AMD.AI\models"))
SKILL_SCRIPTS_DIR = Path(os.environ.get("AMD_SKILL_SCRIPTS_DIR", r"G:\Proyectos\AMD.AI\skills\local-ai-use\scripts"))

# Rutas llama.cpp (vulkan/rocm)
LLAMA_BIN_DIR = Path(os.environ.get("AMD_LLAMA_BIN_DIR", r"G:\llama.cpp\bin"))
LLAMA_SRC_DIR = Path(os.environ.get("AMD_LLAMA_SRC_DIR", r"G:\llama.cpp-src"))
LLAMA_HIP_BUILD_DIR = LLAMA_SRC_DIR / "build-hip"

# Directorios de trabajo
WORK_DIR = BASE_DIR / "data"

# Validar que las rutas críticas existan (o al menos que el padre exista)
for d in (MODELS_DIR, SKILL_SCRIPTS_DIR, LLAMA_BIN_DIR, WORK_DIR):
    if d and not d.exists():
        d.mkdir(parents=True, exist_ok=True)

# Rutas por defecto para generación de .bat (fallback si no se detectan)
DEFAULT_VULKAN_SERVER = LLAMA_BIN_DIR / "llama-b10712-bin-win-vulkan-x64" / "llama-server.exe"
DEFAULT_HIP_SERVER = LLAMA_HIP_BUILD_DIR / "bin" / "llama-server.exe"
