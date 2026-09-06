#!/usr/bin/env python3
"""
tune_local.py - Auto-tuning de configuraciones llama.cpp para AMD GPU

Uso:
    python tune_local.py --model Qwen3.5-9B                 # Auto-tune un modelo
    python tune_local.py --model Qwen3.5-9B --backend hip   # Solo backend específico
    python tune_local.py --model Qwen3.5-9B --profile throughput  # Perfil objetivo
    python tune_local.py --model Qwen3.5-9B --quick         # Tuning rápido
    python tune_local.py --list-profiles                    # Listar perfiles disponibles
"""

import json
import subprocess
import sys
import os
import re
import platform
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from itertools import product


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

LLAMA_CPP_PATHS = {
    "vulkan_builds": [
        r"G:\llama.cpp\bin\llama-b10712-bin-win-vulkan-x64",
        r"G:\llama.cpp\bin\llama-b10796-bin-win-vulkan-x64",
    ],
    "hip_build": r"G:\llama.cpp-src\build-hip\bin",
    "gguf_models": r"G:\Proyectos\AMD.AI\models",
    "presets_file": r"G:\llama.cpp\presets.ini",
}

ROCM_SDK_BIN = Path(r"C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin")

# Perfiles de optimización predefinidos
TUNING_PROFILES = {
    "throughput": {
        "description": "Máximo throughput (tokens/segundo) para servidor/batch",
        "objective": "maximize_decode",
        "weights": {"decode_tok_s": 1.0, "prefill_tok_s": 0.1, "vram_mb": -0.001},
        "constraints": {"min_decode_tok_s": 100, "max_vram_mb": 14000},
    },
    "latency": {
        "description": "Mínima latencia (time-to-first-token) para interactivo",
        "objective": "minimize_prefill_ms",
        "weights": {"prefill_ms": -1.0, "decode_tok_s": 0.2, "vram_mb": -0.001},
        "constraints": {"max_prefill_ms": 500, "max_vram_mb": 14000},
    },
    "balanced": {
        "description": "Equilibrio throughput/latencia para uso general",
        "objective": "balanced_score",
        "weights": {"decode_tok_s": 0.6, "prefill_tok_s": 0.4, "vram_mb": -0.001},
        "constraints": {"min_decode_tok_s": 50, "max_prefill_ms": 1000, "max_vram_mb": 14000},
    },
    "max_context": {
        "description": "Máximo contexto posible (para RAG/documentos largos)",
        "objective": "maximize_context",
        "weights": {"ctx_size": 1.0, "decode_tok_s": 0.1, "prefill_tok_s": 0.1},
        "constraints": {"min_decode_tok_s": 20, "min_prefill_tok_s": 50},
    },
    "memory_efficient": {
        "description": "Mínimo uso VRAM (para modelos grandes / multi-modelo)",
        "objective": "minimize_vram",
        "weights": {"vram_mb": -1.0, "decode_tok_s": 0.3},
        "constraints": {"max_vram_mb": 8000, "min_decode_tok_s": 30},
    },
}

# Espacio de búsqueda por defecto
DEFAULT_SEARCH_SPACE = {
    "n_gpu_layers": [-1, 0, 10, 20, 30, 40, 50, 60, 70, 80, 999],
    "prompt_size": [512, 1024, 2048, 4096],
    "gen_size": [128, 256, 512],
    "batch_size": [512, 1024, 2048],
    "flash_attn": ["auto", "on", "off"],
    "cache_type": ["q4_0", "q8_0", "f16"],
}

QUICK_SEARCH_SPACE = {
    "n_gpu_layers": [-1, 0, 20, 40, 999],
    "prompt_size": [512, 2048],
    "gen_size": [128, 256],
    "batch_size": [1024, 2048],
    "flash_attn": ["auto"],
    "cache_type": ["q4_0"],
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TuningConfig:
    n_gpu_layers: int
    prompt_size: int
    gen_size: int
    batch_size: int
    flash_attn: str
    cache_type: str

@dataclass
class TuningResult:
    config: TuningConfig
    backend: str
    model_name: str
    prefill_tok_s: Optional[float]
    decode_tok_s: Optional[float]
    prefill_ms: Optional[float]
    decode_ms: Optional[float]
    vram_used_mb: Optional[float]
    vram_peak_mb: Optional[float]
    score: float
    success: bool
    error: Optional[str] = None

@dataclass
class BestConfig:
    profile: str
    backend: str
    model_name: str
    config: TuningConfig
    metrics: Dict[str, float]
    score: float
    timestamp: str


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def run_cmd(cmd: List[str], env: Dict[str, str] = None, timeout: int = 300) -> tuple[int, str, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout ({timeout}s)"
    except Exception as e:
        return -1, "", str(e)


def get_env_for_backend(backend: str) -> Dict[str, str]:
    env = os.environ.copy()
    if backend == "hip" and ROCM_SDK_BIN.exists():
        env["PATH"] = str(ROCM_SDK_BIN) + ";" + env["PATH"]
    return env


def find_models(models_dir: Path) -> List[Dict]:
    models = []
    if models_dir.exists():
        for f in models_dir.rglob("*.gguf"):
            name_lower = f.name.lower()
            if any(skip in name_lower for skip in ["imatrix", "mmproj", ".imatrix", ".mmproj"]):
                continue
            if re.search(r"(Q[2-8]_?[KM]?|q[2-8]_?[km]?|UD|GSQ|IQ[1-4]|BF16|F16|F32|MXFP4)", name_lower):
                size_gb = f.stat().st_size / (1024**3)
                models.append({
                    "name": f.stem,
                    "path": str(f),
                    "size_gb": round(size_gb, 2),
                })
    seen = set()
    unique = []
    for m in models:
        if m["name"] not in seen:
            seen.add(m["name"])
            unique.append(m)
    return unique


def run_single_bench(
    llama_bench: Path,
    model_path: str,
    backend: str,
    config: TuningConfig,
    repetitions: int = 2,
) -> Tuple[bool, Dict, str]:
    env = get_env_for_backend(backend)
    
    cmd = [
        str(llama_bench),
        "-m", model_path,
        "-ngl", str(config.n_gpu_layers),
        "-p", str(config.prompt_size),
        "-n", str(config.gen_size),
        "-b", str(config.batch_size),
        "-fa", config.flash_attn,
        "-ctk", config.cache_type,
        "-ctv", config.cache_type,
        "-r", str(repetitions),
        "-o", "json",
        "--no-warmup",
    ]
    
    rc, stdout, stderr = run_cmd(cmd, env=env, timeout=600)
    
    if rc != 0:
        return False, {}, stderr[:500]
    
    # Parse JSON output
    metrics = {"prefill_tok_s": None, "decode_tok_s": None, "prefill_ms": None, "decode_ms": None}
    try:
        json_data = json.loads(stdout)
        if isinstance(json_data, list):
            for entry in json_data:
                n_prompt = entry.get("n_prompt", 0)
                n_gen = entry.get("n_gen", 0)
                avg_ts = entry.get("avg_ts", 0)
                if n_prompt > 0 and n_gen == 0:
                    metrics["prefill_tok_s"] = (n_prompt * 1000) / avg_ts if avg_ts > 0 else None
                    metrics["prefill_ms"] = avg_ts / n_prompt if n_prompt > 0 else None
                elif n_prompt == 0 and n_gen > 0:
                    metrics["decode_tok_s"] = (n_gen * 1000) / avg_ts if avg_ts > 0 else None
                    metrics["decode_ms"] = avg_ts / n_gen if n_gen > 0 else None
    except:
        pass
    
    # Estimar VRAM (heurística)
    metrics["vram_used_mb"] = estimate_vram(config, metrics)
    
    return True, metrics, stdout


def estimate_vram(config: TuningConfig, metrics: Dict) -> float:
    """Estima VRAM usada basada en configuración."""
    base_model_mb = 5560  # Qwen3.5-9B Q4_K ~5.5GB
    
    # KV cache estimation
    # tokens * layers * hidden_size * bytes_per_param
    # Simplificado: ~2 bytes/token para Q4_K
    kv_tokens = config.prompt_size + config.gen_size
    kv_mb = kv_tokens * 2 * 32 / 1024  # 32 layers approx
    
    # Overhead por batch
    batch_mb = config.batch_size * 0.5
    
    # GPU layers factor
    if config.n_gpu_layers == -1 or config.n_gpu_layers == 999:
        gpu_factor = 1.0
    elif config.n_gpu_layers == 0:
        gpu_factor = 0.1  # Solo KV cache en GPU
    else:
        gpu_factor = config.n_gpu_layers / 32  # 32 layers total
    
    total = base_model_mb * gpu_factor + kv_mb + batch_mb
    return min(total, 16384)  # Cap at 16GB


def calculate_score(metrics: Dict, profile: Dict) -> float:
    """Calcula score según perfil de optimización."""
    weights = profile["weights"]
    score = 0.0
    
    for metric, weight in weights.items():
        value = metrics.get(metric)
        if value is not None:
            if weight > 0:
                score += value * weight
            else:
                # Para métricas negativas (minimizar), invertir
                score += (1.0 / (value + 1)) * abs(weight) * 1000
    
    return score


def check_constraints(metrics: Dict, constraints: Dict) -> bool:
    """Verifica si una configuración cumple constraints."""
    for constraint, limit in constraints.items():
        value = metrics.get(constraint)
        if value is not None:
            if constraint.startswith("min_") and value < limit:
                return False
            if constraint.startswith("max_") and value > limit:
                return False
    return True


def generate_configs(space: Dict) -> List[TuningConfig]:
    """Genera todas las combinaciones del espacio de búsqueda."""
    keys = list(space.keys())
    values = [space[k] for k in keys]
    
    configs = []
    for combo in product(*values):
        config = TuningConfig(*combo)
        configs.append(config)
    return configs


def save_presets(presets: Dict[str, BestConfig], presets_file: Path):
    """Guarda mejores configuraciones en presets.ini"""
    lines = ["# Auto-generated presets by tune_local.py", f"# Generated: {datetime.now().isoformat()}", ""]
    
    for profile_name, best in presets.items():
        lines.append(f"[{profile_name}_{best.backend}_{best.model_name}]")
        lines.append(f"n_gpu_layers = {best.config.n_gpu_layers}")
        lines.append(f"prompt_size = {best.config.prompt_size}")
        lines.append(f"gen_size = {best.config.gen_size}")
        lines.append(f"batch_size = {best.config.batch_size}")
        lines.append(f"flash_attn = {best.config.flash_attn}")
        lines.append(f"cache_type = {best.config.cache_type}")
        lines.append(f"# Score: {best.score:.2f}")
        lines.append(f"# Decode: {best.metrics.get('decode_tok_s', 0):.1f} tok/s")
        lines.append(f"# Prefill: {best.metrics.get('prefill_tok_s', 0):.1f} tok/s")
        lines.append(f"# VRAM: {best.metrics.get('vram_used_mb', 0):.0f} MB")
        lines.append("")
    
    presets_file.write_text("\n".join(lines), encoding="utf-8")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Auto-tuning llama.cpp para AMD GPU")
    parser.add_argument("--model", help="Nombre del modelo (substring)")
    parser.add_argument("--backend", choices=["vulkan", "hip", "both"], default="both")
    parser.add_argument("--profile", choices=list(TUNING_PROFILES.keys()), default="balanced")
    parser.add_argument("--quick", action="store_true", help="Tuning rápido (espacio reducido)")
    parser.add_argument("--repetitions", type=int, default=2, help="Repeticiones por test")
    parser.add_argument("--max-combos", type=int, help="Máximo combinaciones a testear")
    parser.add_argument("--list-profiles", action="store_true", help="Listar perfiles y salir")
    parser.add_argument("--save-presets", action="store_true", help="Guardar en presets.ini")
    parser.add_argument("--output", "-o", help="Archivo JSON con resultados")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirmar (no interactivo)")
    args = parser.parse_args()
    
    if args.list_profiles:
        print("Perfiles de optimización disponibles:")
        for name, profile in TUNING_PROFILES.items():
            print(f"  {name}: {profile['description']}")
            print(f"    Objetivo: {profile['objective']}")
            print(f"    Pesos: {profile['weights']}")
        return
    
    if not args.model:
        parser.error("--model es requerido")
    
    space = QUICK_SEARCH_SPACE if args.quick else DEFAULT_SEARCH_SPACE
    profile = TUNING_PROFILES[args.profile]
    
    print("=" * 70)
    print(f"AUTO-TUNING: {args.model} | Perfil: {args.profile} | Backend: {args.backend}")
    print("=" * 70)
    print(f"Objetivo: {profile['description']}")
    print(f"Función objetivo: {profile['objective']}")
    
    # 1. Encontrar modelo
    models_dir = Path(LLAMA_CPP_PATHS["gguf_models"])
    models = find_models(models_dir)
    _mp = Path(args.model)
    if _mp.is_file() and _mp.suffix.lower() == ".gguf":
        models = [{"name": _mp.stem, "path": str(_mp), "size_gb": round(_mp.stat().st_size / (1024**3), 2)}]
    else:
        models = [m for m in models if args.model.lower() in m["name"].lower()]
    
    if not models:
        print(f"[FAIL] Modelo '{args.model}' no encontrado")
        return
    
    model = models[0]
    print(f"\nModelo: {model['name']} ({model['size_gb']} GB)")
    
    # 2. Descubrir backends
    backends = []
    if args.backend in ["vulkan", "both"]:
        for vb in LLAMA_CPP_PATHS["vulkan_builds"]:
            p = Path(vb)
            if (p / "llama-bench.exe").exists():
                backends.append(("vulkan", p))
    
    if args.backend in ["hip", "both"]:
        hp = Path(LLAMA_CPP_PATHS["hip_build"])
        if (hp / "llama-bench.exe").exists():
            backends.append(("hip", hp))
    
    if not backends:
        print("[FAIL] No hay backends válidos")
        return
    
    # 3. Generar configuraciones
    configs = generate_configs(space)
    if args.max_combos:
        configs = configs[:args.max_combos]
    
    total = len(configs) * len(backends)
    print(f"\nEspacio de búsqueda: {len(configs)} configs x {len(backends)} backends = {total} combinaciones")
    print(f"Repeticiones por test: {args.repetitions}")
    print(f"Tiempo estimado: {total * args.repetitions * 10 / 60:.1f} min")
    
    # 4. Ejecutar tuning
    all_results: List[TuningResult] = []
    best_by_backend: Dict[str, TuningResult] = {}
    
    for backend_name, backend_path in backends:
        print(f"\n{'='*50}")
        print(f"TUNING BACKEND: {backend_name.upper()}")
        print(f"{'='*50}")
        
        llama_bench = backend_path / "llama-bench.exe"
        backend_best = None
        backend_best_score = -float('inf')
        
        for i, config in enumerate(configs, 1):
            print(f"\n[{i}/{len(configs)}] {backend_name} | ngl={config.n_gpu_layers} | prompt={config.prompt_size} | gen={config.gen_size} | batch={config.batch_size} | fa={config.flash_attn} | cache={config.cache_type}")
            
            success, metrics, raw = run_single_bench(
                llama_bench, model["path"], backend_name, config, args.repetitions
            )
            
            if success:
                # Verificar constraints
                if not check_constraints(metrics, profile["constraints"]):
                    print(f"  [WARN]️  No cumple constraints: {metrics}")
                    score = -1
                else:
                    score = calculate_score(metrics, profile)
                
                result = TuningResult(
                    config=config,
                    backend=backend_name,
                    model_name=model["name"],
                    prefill_tok_s=metrics.get("prefill_tok_s"),
                    decode_tok_s=metrics.get("decode_tok_s"),
                    prefill_ms=metrics.get("prefill_ms"),
                    decode_ms=metrics.get("decode_ms"),
                    vram_used_mb=metrics.get("vram_used_mb"),
                    vram_peak_mb=metrics.get("vram_peak_mb"),
                    score=score,
                    success=True,
                )
                all_results.append(result)
                
                print(f"  [OK] Score: {score:.2f} | Decode: {metrics.get('decode_tok_s', 0):.1f} | Prefill: {metrics.get('prefill_tok_s', 0):.1f} | VRAM: {metrics.get('vram_used_mb', 0):.0f}MB")
                
                if score > backend_best_score:
                    backend_best_score = score
                    backend_best = result
            else:
                result = TuningResult(
                    config=config,
                    backend=backend_name,
                    model_name=model["name"],
                    prefill_tok_s=None,
                    decode_tok_s=None,
                    prefill_ms=None,
                    decode_ms=None,
                    vram_used_mb=None,
                    vram_peak_mb=None,
                    score=-1,
                    success=False,
                    error=raw[:200],
                )
                all_results.append(result)
                print(f"  [FAIL] Error: {raw[:100]}")
        
        if backend_best:
            best_by_backend[backend_name] = backend_best
            print(f"\n[BEST] MEJOR {backend_name.upper()}: Score={backend_best_score:.2f}")
            print(f"   Config: ngl={backend_best.config.n_gpu_layers}, prompt={backend_best.config.prompt_size}, gen={backend_best.config.gen_size}, batch={backend_best.config.batch_size}, fa={backend_best.config.flash_attn}, cache={backend_best.config.cache_type}")
            print(f"   Decode: {backend_best.decode_tok_s:.1f} tok/s | Prefill: {backend_best.prefill_tok_s:.1f} tok/s | VRAM: {backend_best.vram_used_mb:.0f}MB")
    
    # 5. Seleccionar mejor global
    if best_by_backend:
        global_best = max(best_by_backend.values(), key=lambda x: x.score)
        print(f"\n{'='*70}")
        print(f"[BEST] CONFIGURACIÓN ÓPTIMA GLOBAL ({args.profile.upper()})")
        print(f"{'='*70}")
        print(f"Backend: {global_best.backend.upper()}")
        print(f"Modelo: {global_best.model_name}")
        print(f"Score: {global_best.score:.2f}")
        print(f"\nParámetros óptimos:")
        print(f"  --n-gpu-layers {global_best.config.n_gpu_layers}")
        print(f"  --prompt-size {global_best.config.prompt_size}  (via -p)")
        print(f"  --gen-size {global_best.config.gen_size}      (via -n)")
        print(f"  --batch-size {global_best.config.batch_size}")
        print(f"  --flash-attn {global_best.config.flash_attn}")
        print(f"  --cache-type-k {global_best.config.cache_type}")
        print(f"  --cache-type-v {global_best.config.cache_type}")
        print(f"\nMétricas:")
        print(f"  Decode: {global_best.decode_tok_s:.1f} tok/s")
        print(f"  Prefill: {global_best.prefill_tok_s:.1f} tok/s")
        print(f"  VRAM estimada: {global_best.vram_used_mb:.0f} MB")
        
        # 6. Guardar presets si solicitado
        if args.save_presets:
            presets = {}
            for backend_name, best in best_by_backend.items():
                presets[f"{args.profile}_{backend_name}"] = BestConfig(
                    profile=args.profile,
                    backend=backend_name,
                    model_name=model["name"],
                    config=best.config,
                    metrics={
                        "decode_tok_s": best.decode_tok_s or 0,
                        "prefill_tok_s": best.prefill_tok_s or 0,
                        "vram_used_mb": best.vram_used_mb or 0,
                    },
                    score=best.score,
                    timestamp=datetime.now().isoformat(),
                )
            
            presets_file = Path(LLAMA_CPP_PATHS["presets_file"])
            save_presets(presets, presets_file)
            print(f"\n[OK] Presets guardados en: {presets_file}")
    
    # 7. Guardar JSON
    if args.output:
        output_data = {
            "model": model["name"],
            "profile": args.profile,
            "backend": args.backend,
            "search_space": space,
            "results": [asdict(r) for r in all_results],
            "best_by_backend": {k: asdict(v) for k, v in best_by_backend.items()},
            "timestamp": datetime.now().isoformat(),
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Resultados completos guardados en: {args.output}")


if __name__ == "__main__":
    main()