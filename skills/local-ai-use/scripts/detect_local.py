#!/usr/bin/env python3
"""
detect_local.py - Detección y validación de entorno AMD GPU + llama.cpp

Uso:
    python detect_local.py                    # Detección completa + reporte JSON
    python detect_local.py --json-only        # Solo salida JSON
    python detect_local.py --validate-backends # Validar backends llama.cpp
    python detect_local.py --compatibility    # Matriz compatibilidad modelo×backend×cuantización
"""

import json
import subprocess
import sys
import re
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

# Mapeo deviceID → arquitectura AMD
AMD_DEVICE_MAP = {
    0x7550: {"name": "Radeon RX 9070", "arch": "RDNA 4", "gfx": "gfx1103", "vram_gb": 16},
    0x744C: {"name": "Radeon RX 7900 XTX", "arch": "RDNA 3", "gfx": "gfx1100", "vram_gb": 24},
    0x744D: {"name": "Radeon RX 7900 XT", "arch": "RDNA 3", "gfx": "gfx1100", "vram_gb": 20},
    0x73BF: {"name": "Radeon RX 7800 XT", "arch": "RDNA 3", "gfx": "gfx1100", "vram_gb": 16},
    0x73C0: {"name": "Radeon RX 7700 XT", "arch": "RDNA 3", "gfx": "gfx1100", "vram_gb": 12},
    0x7340: {"name": "Radeon RX 7600", "arch": "RDNA 3", "gfx": "gfx1100", "vram_gb": 8},
    0x73FF: {"name": "Radeon RX 6800 XT", "arch": "RDNA 2", "gfx": "gfx1030", "vram_gb": 16},
    0x73A0: {"name": "Radeon RX 6700 XT", "arch": "RDNA 2", "gfx": "gfx1030", "vram_gb": 12},
}

# Rutas conocidas de llama.cpp en este entorno
LLAMA_CPP_PATHS = {
    "vulkan_builds": [
        r"G:\llama.cpp\bin\llama-b10712-bin-win-vulkan-x64",
        r"G:\llama.cpp\bin\llama-b10796-bin-win-vulkan-x64",
        r"G:\llama.cpp\bin\llama-b96806d-bin-win-vulkan-x64",
    ],
    "hip_build": r"G:\llama.cpp-src\build-hip\bin",
    "gguf_models": r"G:\llama.cpp\gguf",
}

# ROCm SDK path
ROCM_SDK_PATH = Path(r"C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel")
HIPCONFIG_EXE = ROCM_SDK_PATH / "bin" / "hipconfig.exe"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class GPUInfo:
    device_id: str
    device_name: str
    vendor_id: str
    api_version: str
    driver_version: str
    driver_name: str
    gfx_version: str
    architecture: str
    vram_gb: int
    vulkan_instance_version: str
    vulkan_layers: List[str]
    vulkan_extensions: List[str]

@dataclass
class HIPInfo:
    available: bool
    hip_version: str
    hip_path: str
    rocm_path: str
    hip_compiler: str
    hip_platform: str
    hip_runtime: str
    clang_version: str
    clang_path: str

@dataclass
class BackendValidation:
    backend: str
    available: bool
    path: str
    llama_bench_works: bool
    ggml_dll: str
    ggml_dll_size_mb: float
    error: Optional[str] = None

@dataclass
class ModelCompatibility:
    model_name: str
    model_path: str
    size_gb: float
    quantization: str
    vulkan_compatible: bool
    hip_compatible: bool
    recommended_backend: str
    max_context_vulkan: int
    max_context_hip: int
    notes: str

@dataclass
class DetectionReport:
    timestamp: str
    hostname: str
    os: str
    python_version: str
    gpu: GPUInfo
    hip: HIPInfo
    backends: List[BackendValidation]
    models: List[ModelCompatibility]
    recommendations: List[str]


# ============================================================================
# FUNCIONES DE EJECUCIÓN Y PARSING
# ============================================================================

def run_cmd(cmd: List[str], timeout: int = 30) -> tuple[int, str, str]:
    """Ejecuta comando y retorna (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout ({timeout}s)"
    except FileNotFoundError:
        return -1, "", "Command not found"
    except Exception as e:
        return -1, "", str(e)


def parse_vulkaninfo(output: str) -> Dict[str, Any]:
    """Parsea salida de vulkaninfo --summary."""
    info = {
        "instance_version": "",
        "gpu": {},
        "layers": [],
        "extensions": [],
    }
    
    lines = output.split('\n')
    in_device = False
    in_layers = False
    in_extensions = False
    layer_count = 0
    ext_count = 0
    
    for line in lines:
        line_stripped = line.strip()
        
        # Instance version
        if line_stripped.startswith("Vulkan Instance Version:"):
            info["instance_version"] = line_stripped.split(":", 1)[1].strip()
        
        # Device section
        if line_stripped.startswith("GPU0:"):
            in_device = True
            continue
        if in_device and line_stripped.startswith("GPU") and not line_stripped.startswith("GPU0:"):
            in_device = False
        
        if in_device:
            if "=" in line_stripped:
                key, val = line_stripped.split("=", 1)
                info["gpu"][key.strip()] = val.strip()
        
        # Layers
        if line_stripped.startswith("Instance Layers:") or line_stripped.startswith("Layers:"):
            in_layers = True
            # Extract count: "Layers: count = 12"
            if "count" in line_stripped:
                try:
                    layer_count = int(line_stripped.split("=")[1].strip())
                except:
                    pass
            continue
        if in_layers and line_stripped.startswith("VK_LAYER_"):
            # Format: "VK_LAYER_NAME    Description    version    layer_version"
            parts = line_stripped.split()
            if parts:
                info["layers"].append(parts[0])
        if in_layers and line_stripped and not line_stripped.startswith("VK_LAYER_") and not line_stripped.startswith("count"):
            # Check if we've collected expected count or hit empty line
            if len(info["layers"]) >= layer_count and layer_count > 0:
                in_layers = False
            elif not line_stripped:
                in_layers = False
        
        # Extensions
        if line_stripped.startswith("Instance Extensions:") or line_stripped.startswith("Instance Extensions: count"):
            in_extensions = True
            if "count" in line_stripped:
                try:
                    ext_count = int(line_stripped.split("=")[1].strip())
                except:
                    pass
            continue
        if in_extensions and line_stripped.startswith("VK_"):
            # Format: "VK_EXT_name                    : extension revision X"
            if ":" in line_stripped:
                ext_name = line_stripped.split(":")[0].strip()
                info["extensions"].append(ext_name)
        if in_extensions and line_stripped and not line_stripped.startswith("VK_") and not line_stripped.startswith("count"):
            if len(info["extensions"]) >= ext_count and ext_count > 0:
                in_extensions = False
            elif not line_stripped:
                in_extensions = False
    
    return info


def parse_hipconfig(output: str) -> Dict[str, Any]:
    """Parsea salida de hipconfig --full."""
    info = {
        "hip_version": "",
        "hip_path": "",
        "rocm_path": "",
        "hip_compiler": "",
        "hip_platform": "",
        "hip_runtime": "",
        "clang_version": "",
        "clang_path": "",
    }
    
    lines = output.split('\n')
    section = ""
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("HIP version:"):
            info["hip_version"] = line.split(":", 1)[1].strip()
        
        if line == "==hipconfig":
            section = "hipconfig"
            continue
        elif line == "==hip-clang":
            section = "hip-clang"
            continue
        elif line == "== Environment Variables":
            section = "env"
            continue
        elif line == "== Windows Display Drivers":
            section = "drivers"
            continue
        
        if section == "hipconfig" and ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key == "HIP_PATH":
                info["hip_path"] = val
            elif key == "ROCM_PATH":
                info["rocm_path"] = val
            elif key == "HIP_COMPILER":
                info["hip_compiler"] = val
            elif key == "HIP_PLATFORM":
                info["hip_platform"] = val
            elif key == "HIP_RUNTIME":
                info["hip_runtime"] = val
        
        if section == "hip-clang" and "AMD clang version" in line:
            info["clang_version"] = line
        if section == "hip-clang" and "InstalledDir:" in line:
            info["clang_path"] = line.split("InstalledDir:")[1].strip()
    
    return info


def get_gpu_info() -> GPUInfo:
    """Obtiene información completa de la GPU via vulkaninfo."""
    rc, stdout, stderr = run_cmd(["vulkaninfo", "--summary"])
    
    if rc != 0:
        raise RuntimeError(f"vulkaninfo failed: {stderr}")
    
    parsed = parse_vulkaninfo(stdout)
    gpu = parsed.get("gpu", {})
    
    # Mapear deviceID
    device_id_hex = gpu.get("deviceID", "0x0")
    try:
        device_id_int = int(device_id_hex, 16)
    except:
        device_id_int = 0
    
    device_map = AMD_DEVICE_MAP.get(device_id_int, {
        "name": "Unknown AMD GPU",
        "arch": "Unknown",
        "gfx": "unknown",
        "vram_gb": 0
    })
    
    return GPUInfo(
        device_id=device_id_hex,
        device_name=gpu.get("deviceName", "Unknown"),
        vendor_id=gpu.get("vendorID", "0x1002"),
        api_version=gpu.get("apiVersion", ""),
        driver_version=gpu.get("driverVersion", ""),
        driver_name=gpu.get("driverName", ""),
        gfx_version=device_map["gfx"],
        architecture=device_map["arch"],
        vram_gb=device_map["vram_gb"],
        vulkan_instance_version=parsed.get("instance_version", ""),
        vulkan_layers=parsed.get("layers", []),
        vulkan_extensions=parsed.get("extensions", []),
    )


def get_hip_info() -> HIPInfo:
    """Obtiene información de HIP/ROCm via hipconfig."""
    if not HIPCONFIG_EXE.exists():
        return HIPInfo(
            available=False,
            hip_version="",
            hip_path="",
            rocm_path="",
            hip_compiler="",
            hip_platform="",
            hip_runtime="",
            clang_version="",
            clang_path="",
        )
    
    rc, stdout, stderr = run_cmd([str(HIPCONFIG_EXE), "--full"])
    
    if rc != 0:
        return HIPInfo(
            available=False,
            hip_version="",
            hip_path="",
            rocm_path="",
            hip_compiler="",
            hip_platform="",
            hip_runtime="",
            clang_version="",
            clang_path="",
        )
    
    parsed = parse_hipconfig(stdout)
    
    return HIPInfo(
        available=True,
        hip_version=parsed.get("hip_version", ""),
        hip_path=parsed.get("hip_path", ""),
        rocm_path=parsed.get("rocm_path", ""),
        hip_compiler=parsed.get("hip_compiler", ""),
        hip_platform=parsed.get("hip_platform", ""),
        hip_runtime=parsed.get("hip_runtime", ""),
        clang_version=parsed.get("clang_version", ""),
        clang_path=parsed.get("clang_path", ""),
    )


def validate_backend(backend_name: str, build_path: Path) -> BackendValidation:
    """Valida un backend llama.cpp específico."""
    llama_bench = build_path / "llama-bench.exe"
    ggml_dlls = list(build_path.glob("ggml-*.dll"))
    
    # Identificar DLL principal del backend
    backend_dll_map = {
        "vulkan": "ggml-vulkan.dll",
        "hip": "ggml-hip.dll",
    }
    target_dll = backend_dll_map.get(backend_name, "")
    ggml_dll_path = build_path / target_dll
    
    dll_size_mb = 0
    if ggml_dll_path.exists():
        dll_size_mb = ggml_dll_path.stat().st_size / (1024 * 1024)
    
    # Test llama-bench
    bench_works = False
    error = None
    
    if llama_bench.exists():
        # Para HIP, necesitamos ROCm SDK en PATH
        env = os.environ.copy()
        if backend_name == "hip" and ROCM_SDK_PATH.exists():
            rocm_bin = ROCM_SDK_PATH / "bin"
            if rocm_bin.exists():
                env["PATH"] = str(rocm_bin) + ";" + env["PATH"]
        
        # Test rápido: solo ayuda
        try:
            result = subprocess.run(
                [str(llama_bench), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            bench_works = result.returncode == 0
            if not bench_works:
                error = result.stderr[:200]
        except subprocess.TimeoutExpired:
            error = "Timeout (10s)"
        except Exception as e:
            error = str(e)
    else:
        error = "llama-bench.exe not found"
    
    return BackendValidation(
        backend=backend_name,
        available=llama_bench.exists() and ggml_dll_path.exists(),
        path=str(build_path),
        llama_bench_works=bench_works,
        ggml_dll=target_dll,
        ggml_dll_size_mb=round(dll_size_mb, 1),
        error=error,
    )


def find_gguf_models(models_dir: Path) -> List[Path]:
    """Encuentra modelos GGUF en el directorio (archivos principales, no imatrix/mmproj)."""
    models = []
    if models_dir.exists():
        for ext in ["*.gguf", "*.GGUF"]:
            for f in models_dir.rglob(ext):
                # Filtrar archivos auxiliares (imatrix, mmproj, etc.)
                name_lower = f.name.lower()
                if any(skip in name_lower for skip in ["imatrix", "mmproj", ".imatrix", ".mmproj"]):
                    continue
                # Solo archivos modelo principales (tienen cuantización en nombre)
                if re.search(r"(Q[2-8]_?[KM]?|q[2-8]_?[km]?|UD|GSQ|IQ[1-4]|BF16|F16|F32)", name_lower):
                    models.append(f)
    # Deduplicar por stem (nombre base)
    seen = set()
    unique = []
    for m in models:
        stem = m.stem
        if stem not in seen:
            seen.add(stem)
            unique.append(m)
    return unique


def parse_model_info(model_path: Path) -> Dict[str, Any]:
    """Extrae info del nombre de archivo GGUF."""
    name = model_path.stem
    size_gb = model_path.stat().st_size / (1024**3)
    
    # Detectar cuantización del nombre
    quant_patterns = [
        r"(Q[2-8]_?[KM]_[SL])",
        r"(Q[2-8]_[KM])",
        r"(Q[2-8]_)",
        r"(UD[-_]?Q[2-8]_[KM]_[A-Z]+)",
        r"(GSQ[-_]?RCO[-_]?MTP)",
        r"(IQ[1-4]_[A-Z]+)",
        r"(F16|F32|BF16)",
    ]
    
    quantization = "unknown"
    for pattern in quant_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            quantization = match.group(1)
            break
    
    # Detectar modelo base
    model_base = "unknown"
    known_models = [
        "Qwen3.5-9B", "Qwen3.8-27B", "Qwen3.8-9B", "Qwen3.5-9B",
        "Llama3.2-11B", "Llama3.2-3B", "Llama3.1-8B", "Llama3.1-70B",
        "InternVL3-14B", "InternVL2-8B",
        "Qwen2.5-VL-7B", "Qwen2.5-VL-3B",
        "Gemma-3-27B", "Gemma-3-9B", "Gemma-3-4B", "Gemma-3-1B",
        "DeepSeek-R1", "DeepSeek-V3",
        "Apertus-1.5-8B",
        "Mythos", "Qwythos",
    ]
    
    for known in known_models:
        if known.lower() in name.lower():
            model_base = known
            break
    
    return {
        "name": model_base,
        "full_name": name,
        "path": str(model_path),
        "size_gb": round(size_gb, 2),
        "quantization": quantization,
    }


def assess_compatibility(model_info: Dict, gpu: GPUInfo, hip: HIPInfo, 
                         vulkan_ok: bool, hip_ok: bool) -> ModelCompatibility:
    """Evalúa compatibilidad modelo × backend."""
    size_gb = model_info["size_gb"]
    vram_gb = gpu.vram_gb
    
    # Heurística: modelo cabe si size < VRAM * 0.85 (dejar espacio para KV cache)
    fits_vram = size_gb < (vram_gb * 0.85)
    
    # Vulkan: más estable en Windows/RDNA 4
    vulkan_compat = vulkan_ok and fits_vram
    
    # HIP: experimental en Windows/RDNA 4
    hip_compat = hip_ok and hip.available and fits_vram
    
    # Recomendación
    if vulkan_compat and not hip_compat:
        recommended = "vulkan"
    elif hip_compat and not vulkan_compat:
        recommended = "hip"
    elif vulkan_compat and hip_compat:
        recommended = "vulkan (primary) / hip (experimental)"
    else:
        recommended = "cpu-offload required"
    
    # Contexto máximo estimado basado en VRAM disponible para KV cache
    # KV cache size ≈ 2 * layers * hidden_size * ctx_size * bytes_per_param
    # Para Q4_K: ~0.5 bytes/param | Q8: ~1 byte/param | FP16: ~2 bytes/param
    # Estimación simplificada: VRAM_KV = VRAM_total - model_size
    vram_for_kv = vram_gb * 0.85 - size_gb if fits_vram else 0
    
    # Bytes por token de KV cache (aprox para modelos típicos)
    # LLaMA-7B: ~2MB/token | LLaMA-70B: ~20MB/token
    # Escalamos por tamaño de modelo
    if size_gb <= 1:
        kv_per_token_mb = 0.5
    elif size_gb <= 7:
        kv_per_token_mb = 2.0
    elif size_gb <= 14:
        kv_per_token_mb = 4.0
    elif size_gb <= 30:
        kv_per_token_mb = 8.0
    else:
        kv_per_token_mb = 16.0
    
    # Ajustar por cuantización
    quant = model_info["quantization"].lower()
    if "q3" in quant or "iq3" in quant:
        kv_per_token_mb *= 0.6
    elif "q4" in quant:
        kv_per_token_mb *= 0.7
    elif "q5" in quant:
        kv_per_token_mb *= 0.8
    elif "q6" in quant:
        kv_per_token_mb *= 0.9
    elif "q8" in quant or "f16" in quant or "bf16" in quant:
        kv_per_token_mb *= 1.2
    
    max_tokens_vulkan = int((vram_for_kv * 1024) / kv_per_token_mb) if vulkan_compat and vram_for_kv > 0 else 0
    max_tokens_hip = int((vram_for_kv * 1024 * 0.8) / kv_per_token_mb) if hip_compat and vram_for_kv > 0 else 0  # HIP overhead
    
    # Redondear a múltiplos comunes
    max_ctx_vulkan = min((max_tokens_vulkan // 1024) * 1024, 131072) if max_tokens_vulkan > 0 else 0
    max_ctx_hip = min((max_tokens_hip // 1024) * 1024, 131072) if max_tokens_hip > 0 else 0
    
    notes = []
    if not fits_vram:
        notes.append(f"Modelo ({size_gb}GB) > 85% VRAM ({vram_gb}GB) - requiere CPU offload")
    if gpu.gfx_version == "gfx1103" and hip_compat:
        notes.append("RDNA 4 (gfx1103): HIP en early enablement, kernels genéricos")
    if "GSQ" in model_info["quantization"] or "MTP" in model_info["quantization"]:
        notes.append("Cuantización GSQ-RCO-MTP: verificar compatibilidad kernels")
    if max_ctx_vulkan < 4096 and vulkan_compat:
        notes.append(f"Contexto limitado Vulkan: ~{max_ctx_vulkan} tokens")
    if max_ctx_hip < 4096 and hip_compat:
        notes.append(f"Contexto limitado HIP: ~{max_ctx_hip} tokens")
    
    return ModelCompatibility(
        model_name=model_info["name"],
        model_path=model_info["path"],
        size_gb=model_info["size_gb"],
        quantization=model_info["quantization"],
        vulkan_compatible=vulkan_compat,
        hip_compatible=hip_compat,
        recommended_backend=recommended,
        max_context_vulkan=max_ctx_vulkan,
        max_context_hip=max_ctx_hip,
        notes="; ".join(notes) if notes else "OK",
    )


def generate_recommendations(gpu: GPUInfo, hip: HIPInfo, 
                            backends: List[BackendValidation],
                            models: List[ModelCompatibility]) -> List[str]:
    """Genera recomendaciones basadas en la detección."""
    recs = []
    
    # GPU
    if gpu.gfx_version == "gfx1103":
        recs.append("GPU: RX 9070 (RDNA 4/gfx1103) - Vulkan es backend recomendado en Windows")
        recs.append("ROCm/HIP: Soporte limited (early enablement), kernels genéricos sin optimizaciones RDNA 4")
    
    # Backends
    vulkan_ok = any(b.backend == "vulkan" and b.available for b in backends)
    hip_ok = any(b.backend == "hip" and b.available for b in backends)
    
    if vulkan_ok:
        recs.append("Vulkan: Builds funcionales disponibles - usar como backend primario")
    if hip_ok:
        recs.append("HIP: Build funcional en build-hip - usable para testing portabilidad Linux")
    
    # Modelos
    vulkan_models = [m for m in models if m.vulkan_compatible]
    hip_models = [m for m in models if m.hip_compatible]
    cpu_models = [m for m in models if not m.vulkan_compatible and not m.hip_compatible]
    
    if vulkan_models:
        recs.append(f"Modelos compatibles Vulkan ({len(vulkan_models)}): {', '.join(m.model_name for m in vulkan_models)}")
    if hip_models:
        recs.append(f"Modelos compatibles HIP ({len(hip_models)}): {', '.join(m.model_name for m in hip_models)}")
    if cpu_models:
        recs.append(f"Modelos requieren CPU offload ({len(cpu_models)}): {', '.join(m.model_name for m in cpu_models)}")
    
    # Configuración óptima
    recs.append("Configuración recomendada Vulkan: --n-gpu-layers all --flash-attn on --cache-type-k/v q4_0 --ctx-size 65536")
    recs.append("Para HIP: probar --n-gpu-layers all --flash-attn off (SDPA fallback) --ctx-size 32768")
    
    return recs


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Detección entorno AMD GPU + llama.cpp")
    parser.add_argument("--json-only", action="store_true", help="Solo salida JSON")
    parser.add_argument("--validate-backends", action="store_true", help="Validar backends llama.cpp")
    parser.add_argument("--compatibility", action="store_true", help="Matriz compatibilidad")
    parser.add_argument("--output", "-o", help="Archivo JSON de salida")
    args = parser.parse_args()
    
    if not args.json_only:
        print("=" * 60)
        print("DETECCIÓN ENTORNO AMD GPU + LLAMA.CPP")
        print("=" * 60)
        print()
    
    # 1. GPU Info
    if not args.json_only:
        print("[1/5] Detectando GPU via Vulkan...")
    gpu = get_gpu_info()
    
    # 2. HIP Info
    if not args.json_only:
        print("[2/5] Detectando HIP/ROCm...")
    hip = get_hip_info()
    
    # 3. Validar Backends
    backends = []
    if args.validate_backends or args.compatibility:
        if not args.json_only:
            print("[3/5] Validando backends llama.cpp...")
        
        # Vulkan builds
        for vulkan_path in LLAMA_CPP_PATHS["vulkan_builds"]:
            p = Path(vulkan_path)
            if p.exists():
                backends.append(validate_backend("vulkan", p))
        
        # HIP build
        hip_path = Path(LLAMA_CPP_PATHS["hip_build"])
        if hip_path.exists():
            backends.append(validate_backend("hip", hip_path))
    
    # 4. Modelos
    models = []
    if args.compatibility:
        if not args.json_only:
            print("[4/5] Analizando modelos GGUF...")
        
        gguf_dir = Path(LLAMA_CPP_PATHS["gguf_models"])
        model_files = find_gguf_models(gguf_dir)
        
        vulkan_ok = any(b.backend == "vulkan" and b.available for b in backends)
        hip_ok = any(b.backend == "hip" and b.available for b in backends)
        
        for mf in model_files:
            model_info = parse_model_info(mf)
            models.append(assess_compatibility(model_info, gpu, hip, vulkan_ok, hip_ok))
    
    # 5. Recomendaciones
    if not args.json_only:
        print("[5/5] Generando recomendaciones...")
    recommendations = generate_recommendations(gpu, hip, backends, models)
    
    # Compilar reporte
    report = DetectionReport(
        timestamp=datetime.now().isoformat(),
        hostname=platform.node(),
        os=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        gpu=gpu,
        hip=hip,
        backends=backends,
        models=models,
        recommendations=recommendations,
    )
    
    # Salida
    output_json = json.dumps(asdict(report), indent=2, ensure_ascii=False)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        if not args.json_only:
            print(f"\n✅ Reporte guardado en: {args.output}")
    
    if args.json_only:
        print(output_json)
    else:
        # Pretty print
        print("\n" + "=" * 60)
        print("RESULTADOS")
        print("=" * 60)
        
        print(f"\n[GPU] {gpu.device_name} ({gpu.gfx_version}, {gpu.architecture})")
        print(f"   VRAM: {gpu.vram_gb} GB | Driver: {gpu.driver_version}")
        print(f"   Vulkan: {gpu.vulkan_instance_version} | Capas: {len(gpu.vulkan_layers)}")
        
        print(f"\n[HIP/ROCm] {'DISPONIBLE' if hip.available else 'NO DISPONIBLE'}")
        if hip.available:
            print(f"   HIP: {hip.hip_version} | Clang: {hip.clang_version.split()[2] if len(hip.clang_version.split()) > 2 else 'unknown'}")
            print(f"   Runtime: {hip.hip_runtime} | Platform: {hip.hip_platform}")
        
        if backends:
            print(f"\n[BACKENDS LLAMA.CPP]:")
            for b in backends:
                status = "[OK]" if b.available else "[FAIL]"
                print(f"   {status} {b.backend.upper()}: {b.path}")
                print(f"      ggml: {b.ggml_dll} ({b.ggml_dll_size_mb} MB) | bench: {'OK' if b.llama_bench_works else 'FAIL'}")
                if b.error:
                    print(f"      Error: {b.error}")
        
        if models:
            print(f"\n[MODELOS GGUF ({len(models)})]:")
            for m in models:
                v_status = "[OK]" if m.vulkan_compatible else "[NO]"
                h_status = "[OK]" if m.hip_compatible else "[NO]"
                print(f"   {m.model_name} ({m.size_gb}GB, {m.quantization})")
                print(f"      Vulkan: {v_status} | HIP: {h_status} | Rec: {m.recommended_backend}")
                print(f"      Max ctx: Vulkan={m.max_context_vulkan}, HIP={m.max_context_hip}")
                if m.notes != "OK":
                    print(f"      [!] {m.notes}")
        
        print(f"\n[RECOMENDACIONES]:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "=" * 60)
        print("Completado.")
        print("=" * 60)


if __name__ == "__main__":
    main()