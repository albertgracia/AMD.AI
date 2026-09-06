#!/usr/bin/env python3
"""
bench_local.py - Benchmarking automatizado llama.cpp (Vulkan vs HIP)

Uso:
    python bench_local.py                                    # Benchmark completo
    python bench_local.py --model Qwen3.5-9B                 # Solo un modelo
    python bench_local.py --backend vulkan                   # Solo un backend
    python bench_local.py --quick                            # Benchmark rápido (menos repeticiones)
    python bench_local.py --output results.csv               # Exportar CSV
    python bench_local.py --list-models                      # Listar modelos detectados
"""

import json
import subprocess
import sys
import re
import os
import platform
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import csv


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

LLAMA_CPP_PATHS = {
    "vulkan_builds": [
        r"G:\llama.cpp\bin\llama-b10712-bin-win-vulkan-x64",
        r"G:\llama.cpp\bin\llama-b10796-bin-win-vulkan-x64",
    ],
    "hip_build": r"G:\llama.cpp-src\build-hip\bin",
    "gguf_models": r"G:\llama.cpp\gguf",
}

ROCM_SDK_BIN = Path(r"C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin")

# Matriz de benchmark por defecto
DEFAULT_BENCH_MATRIX = {
    "n_gpu_layers": [-1, 0, 20, 40, 999],      # -1=all, 0=cpu, 999=all
    "prompt_size": [512, 1024, 2048, 4096],
    "gen_size": [128, 256, 512],
    "batch_size": [512, 1024, 2048],
    "flash_attn": ["on", "off", "auto"],
    "cache_type": ["q4_0", "q8_0", "f16"],
    "repetitions": 3,
}

QUICK_BENCH_MATRIX = {
    "n_gpu_layers": [-1, 0],
    "prompt_size": [512, 2048],
    "gen_size": [128, 256],
    "batch_size": [1024, 2048],
    "flash_attn": ["auto"],
    "cache_type": ["q4_0"],
    "repetitions": 2,
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class BenchResult:
    timestamp: str
    hostname: str
    backend: str
    build_path: str
    model_name: str
    model_path: str
    model_size_gb: float
    quantization: str
    n_gpu_layers: int
    prompt_size: int
    gen_size: int
    batch_size: int
    flash_attn: str
    cache_type_k: str
    cache_type_v: str
    # Métricas
    prefill_tok_s: Optional[float] = None
    decode_tok_s: Optional[float] = None
    prefill_ms: Optional[float] = None
    decode_ms: Optional[float] = None
    vram_used_mb: Optional[float] = None
    vram_peak_mb: Optional[float] = None
    # Metadata
    repetitions: int = 3
    success: bool = True
    error: Optional[str] = None
    raw_output: Optional[str] = None


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def run_cmd(cmd: List[str], env: Dict[str, str] = None, timeout: int = 300) -> tuple[int, str, str]:
    """Ejecuta comando con entorno opcional."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=env
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout ({timeout}s)"
    except Exception as e:
        return -1, "", str(e)


def get_env_for_backend(backend: str) -> Dict[str, str]:
    """Prepara entorno para backend específico."""
    env = os.environ.copy()
    if backend == "hip" and ROCM_SDK_BIN.exists():
        env["PATH"] = str(ROCM_SDK_BIN) + ";" + env["PATH"]
    return env


def find_models(models_dir: Path) -> List[Dict]:
    """Encuentra modelos GGUF principales."""
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
                    "quantization": extract_quant(name_lower),
                })
    # Deduplicar
    seen = set()
    unique = []
    for m in models:
        if m["name"] not in seen:
            seen.add(m["name"])
            unique.append(m)
    return unique


def extract_quant(name: str) -> str:
    patterns = [
        r"(Q[2-8]_?[KM]_[SL])", r"(Q[2-8]_?[KM])", r"(Q[2-8]_)",
        r"(UD[-_]?Q[2-8]_?[KM]_[A-Z]+)", r"(GSQ[-_]?RCO[-_]?MTP)",
        r"(IQ[1-4]_[A-Z]+)", r"(BF16|F16|F32|MXFP4)",
    ]
    for p in patterns:
        m = re.search(p, name, re.IGNORECASE)
        if m:
            return m.group(1)
    return "unknown"


def parse_llama_bench_output(output: str) -> Dict[str, Any]:
    """Parsea salida de llama-bench (formato markdown/table)."""
    results = {
        "prefill_tok_s": None,
        "decode_tok_s": None,
        "prefill_ms": None,
        "decode_ms": None,
    }
    
    # Buscar tabla de resultados
    lines = output.split('\n')
    in_table = False
    for line in lines:
        if "|" in line and ("prefill" in line.lower() or "decode" in line.lower() or "tok/s" in line.lower()):
            in_table = True
        if in_table and "|" in line and not line.strip().startswith("|---"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 4:
                # Formato típico: | test | n | t/s | ms/token | ...
                try:
                    if "prefill" in parts[0].lower():
                        results["prefill_tok_s"] = float(parts[2]) if parts[2] else None
                        results["prefill_ms"] = float(parts[3]) if parts[3] else None
                    elif "decode" in parts[0].lower() or "generat" in parts[0].lower():
                        results["decode_tok_s"] = float(parts[2]) if parts[2] else None
                        results["decode_ms"] = float(parts[3]) if parts[3] else None
                except (ValueError, IndexError):
                    pass
    
    # También buscar en JSON si se usó --output json
    try:
        json_data = json.loads(output)
        if isinstance(json_data, list) and json_data:
            for entry in json_data:
                # prefill: n_prompt > 0, n_gen == 0
                # decode: n_prompt == 0, n_gen > 0
                n_prompt = entry.get("n_prompt", 0)
                n_gen = entry.get("n_gen", 0)
                avg_ts = entry.get("avg_ts", 0)
                if n_prompt > 0 and n_gen == 0:
                    # prefill: tokens per second = n_prompt / (avg_ts / 1000)
                    results["prefill_tok_s"] = (n_prompt * 1000) / avg_ts if avg_ts > 0 else None
                    results["prefill_ms"] = avg_ts / n_prompt if n_prompt > 0 else None
                elif n_prompt == 0 and n_gen > 0:
                    # decode: tokens per second = n_gen / (avg_ts / 1000)
                    results["decode_tok_s"] = (n_gen * 1000) / avg_ts if avg_ts > 0 else None
                    results["decode_ms"] = avg_ts / n_gen if n_gen > 0 else None
    except:
        pass
    
    return results


def run_benchmark(
    llama_bench: Path,
    model_path: str,
    backend: str,
    n_gpu_layers: int,
    prompt_size: int,
    gen_size: int,
    batch_size: int,
    flash_attn: str,
    cache_type: str,
    repetitions: int,
) -> tuple[bool, Dict, str]:
    """Ejecuta un benchmark individual."""
    
    env = get_env_for_backend(backend)
    
    cmd = [
        str(llama_bench),
        "-m", model_path,
        "-ngl", str(n_gpu_layers),
        "-p", str(prompt_size),
        "-n", str(gen_size),
        "-b", str(batch_size),
        "-fa", flash_attn,
        "-ctk", cache_type,
        "-ctv", cache_type,
        "-r", str(repetitions),
        "-o", "json",
        "--no-warmup",
    ]
    
    rc, stdout, stderr = run_cmd(cmd, env=env, timeout=600)
    
    if rc != 0:
        return False, {}, stderr[:500]
    
    metrics = parse_llama_bench_output(stdout)
    return True, metrics, stdout


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def _write_progress(path, done, total):
    if not path:
        return
    try:
        import json as _pj
        import os as _po
        _tmp = str(path) + ".tmp"
        with open(_tmp, "w", encoding="utf-8") as _f:
            _f.write(_pj.dumps({"done": done, "total": total}))
        _po.replace(_tmp, path)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Benchmarking llama.cpp Vulkan vs HIP")
    parser.add_argument("--model", help="Filtrar por nombre de modelo (substring)")
    parser.add_argument("--backend", choices=["vulkan", "hip", "both"], default="both")
    parser.add_argument("--quick", action="store_true", help="Benchmark rápido (menos combinaciones)")
    parser.add_argument("--output", "-o", help="Archivo CSV de salida")
    parser.add_argument("--json-output", help="Archivo JSON de salida")
    parser.add_argument("--list-models", action="store_true", help="Listar modelos y salir")
    parser.add_argument("--repetitions", type=int, help="Sobrescribir repeticiones")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirmar (no interactivo)")
    parser.add_argument("--progress-file", help="Archivo JSON para progreso (lo lee el dashboard)")
    args = parser.parse_args()
    
    matrix = QUICK_BENCH_MATRIX if args.quick else DEFAULT_BENCH_MATRIX
    if args.repetitions:
        matrix["repetitions"] = args.repetitions
    
    print("=" * 70)
    print("BENCHMARKING LLAMA.CPP - VULKAN vs HIP")
    print("=" * 70)
    
    # 1. Descubrir modelos
    models_dir = Path(LLAMA_CPP_PATHS["gguf_models"])
    models = find_models(models_dir)
    
    if args.model:
        _mp = Path(args.model)
        if _mp.is_file() and _mp.suffix.lower() == ".gguf":
            models = [{"name": _mp.stem, "path": str(_mp), "size_gb": round(_mp.stat().st_size / (1024**3), 2), "quantization": extract_quant(_mp.name.lower())}]
        else:
            models = [m for m in models if args.model.lower() in m["name"].lower()]
    
    if args.list_models:
        print(f"\nModelos encontrados ({len(models)}):")
        for m in models:
            print(f"  - {m['name']} ({m['size_gb']} GB, {m['quantization']})")
        return
    
    if not models:
        print("[FAIL] No se encontraron modelos GGUF")
        return
    
    print(f"\nModelos a testear: {len(models)}")
    for m in models:
        print(f"  - {m['name']} ({m['size_gb']} GB, {m['quantization']})")
    
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
    
    print(f"\nBackends a testear: {len(backends)}")
    for b, p in backends:
        print(f"  - {b.upper()}: {p}")
    
    # 3. Generar combinaciones
    total_combos = (
        len(models) * 
        len(backends) * 
        len(matrix["n_gpu_layers"]) * 
        len(matrix["prompt_size"]) * 
        len(matrix["gen_size"]) * 
        len(matrix["batch_size"]) * 
        len(matrix["flash_attn"]) * 
        len(matrix["cache_type"])
    )
    print(f"\nTotal combinaciones: {total_combos}")
    print(f"Repeticiones por combo: {matrix['repetitions']}")
    print(f"Tiempo estimado: {total_combos * matrix['repetitions'] * 15 / 60:.1f} min")
    
    if not args.yes:
        confirm = input("\n¿Continuar? (s/N): ").strip().lower()
        if confirm != 's':
            print("Cancelado.")
            return
    
    # 4. Ejecutar benchmarks
    results: List[BenchResult] = []
    combo_num = 0
    
    for model in models:
        for backend_name, backend_path in backends:
            llama_bench = backend_path / "llama-bench.exe"
            
            for ngl in matrix["n_gpu_layers"]:
                for ps in matrix["prompt_size"]:
                    for gs in matrix["gen_size"]:
                        for batch in matrix["batch_size"]:
                            for fa in matrix["flash_attn"]:
                                for ct in matrix["cache_type"]:
                                    combo_num += 1
                                    print(f"\n[{combo_num}/{total_combos}] {model['name']} | {backend_name} | ngl={ngl} | prompt={ps} | gen={gs} | batch={batch} | fa={fa} | cache={ct}")
                                    
                                    success, metrics, raw = run_benchmark(
                                        llama_bench, model["path"], backend_name,
                                        ngl, ps, gs, batch, fa, ct, matrix["repetitions"]
                                    )
                                    
                                    result = BenchResult(
                                        timestamp=datetime.now().isoformat(),
                                        hostname=platform.node(),
                                        backend=backend_name,
                                        build_path=str(backend_path),
                                        model_name=model["name"],
                                        model_path=model["path"],
                                        model_size_gb=model["size_gb"],
                                        quantization=model["quantization"],
                                        n_gpu_layers=ngl,
                                        prompt_size=ps,
                                        gen_size=gs,
                                        batch_size=batch,
                                        flash_attn=fa,
                                        cache_type_k=ct,
                                        cache_type_v=ct,
                                        prefill_tok_s=metrics.get("prefill_tok_s"),
                                        decode_tok_s=metrics.get("decode_tok_s"),
                                    prefill_ms=metrics.get("prefill_ms"),
                                    decode_ms=metrics.get("decode_ms"),
                                    repetitions=matrix["repetitions"],
                                    success=success,
                                    error=None if success else raw,
                                    raw_output=raw if not success else None,
                                )
                                results.append(result)
                                
                                if success:
                                    print(f"  [OK] Pre-fill: {metrics.get('prefill_tok_s', 'N/A'):.1f} tok/s | Decode: {metrics.get('decode_tok_s', 'N/A'):.1f} tok/s")
                                else:
                                    print(f"  [FAIL] Error: {raw[:100]}")
                                _write_progress(args.progress_file, combo_num, total_combos)
    
    # 5. Guardar resultados
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "hostname", "backend", "build_path",
                "model_name", "model_path", "model_size_gb", "quantization",
                "n_gpu_layers", "prompt_size", "gen_size", "batch_size", "flash_attn",
                "cache_type_k", "cache_type_v",
                "prefill_tok_s", "decode_tok_s", "prefill_ms", "decode_ms",
                "repetitions", "success", "error"
            ])
            for r in results:
                writer.writerow([
                    r.timestamp, r.hostname, r.backend, r.build_path,
                    r.model_name, r.model_path, r.model_size_gb, r.quantization,
                    r.n_gpu_layers, r.prompt_size, r.gen_size, r.batch_size, r.flash_attn,
                    r.cache_type_k, r.cache_type_v,
                    r.prefill_tok_s, r.decode_tok_s, r.prefill_ms, r.decode_ms,
                    r.repetitions, r.success, r.error
                ])
        print(f"\n[OK] CSV guardado en: {args.output}")
    
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in results], f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON guardado en: {args.json_output}")
    
    # 6. Resumen
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"\n{'='*70}")
    print(f"RESUMEN: {len(successful)}/{len(results)} exitosos, {len(failed)} fallidos")
    print(f"{'='*70}")
    
    # Top 5 por decode tok/s
    top_decode = sorted(
        [r for r in successful if r.decode_tok_s], 
        key=lambda x: x.decode_tok_s, 
        reverse=True
    )[:5]
    
    print("\n[TOP 5 DECODE THROUGHPUT]:")
    for i, r in enumerate(top_decode, 1):
        print(f"  {i}. {r.model_name} ({r.backend}) ngl={r.n_gpu_layers} prompt={r.prompt_size} gen={r.gen_size} batch={r.batch_size} -> {r.decode_tok_s:.1f} tok/s")
    
    # Top 5 por prefill tok/s
    top_prefill = sorted(
        [r for r in successful if r.prefill_tok_s], 
        key=lambda x: x.prefill_tok_s, 
        reverse=True
    )[:5]
    
    print("\n[TOP 5 PREFILL THROUGHPUT]:")
    for i, r in enumerate(top_prefill, 1):
        print(f"  {i}. {r.model_name} ({r.backend}) ngl={r.n_gpu_layers} prompt={r.prompt_size} gen={r.gen_size} batch={r.batch_size} -> {r.prefill_tok_s:.1f} tok/s")


if __name__ == "__main__":
    main()