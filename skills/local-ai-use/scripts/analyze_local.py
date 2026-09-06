#!/usr/bin/env python3
"""
analyze_local.py - Análisis de rendimiento llama.cpp (Vulkan + HIP)

Análisis basado en benchmarks parametrizados ya que:
- ROCm SDK no incluye rocprof/roc-tracer
- Build actual tiene GGML_HIP_EXPORT_METRICS=OFF
- Vulkan validation layers disponibles pero requieren app instrumentada

Uso:
    python analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis
    python analyze_local.py --model Qwen3.5-9B --backend vulkan --trace-chrome
    python analyze_local.py --model Qwen3.5-9B --backend both --compare-configs
    python analyze_local.py --model Qwen3.5-9B --backend hip --prometheus
    python analyze_local.py --list-analyses
"""

import json
import subprocess
import sys
import os
import re
import platform
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
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
    "gguf_models": r"G:\llama.cpp\gguf",
    "baselines_dir": r"G:\Proyectos\AMD.AI\docs\baselines",
    "traces_dir": r"G:\Proyectos\AMD.AI\docs\traces",
}

ROCM_SDK_BIN = Path(r"C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin")


def parse_config_arg(arg: str) -> Dict:
    """Parsea config desde JSON string o @archivo.json"""
    if arg.startswith("@"):
        path = Path(arg[1:])
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError(f"Config file not found: {path}")
    return json.loads(arg)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class BenchmarkPoint:
    config: Dict
    prefill_tok_s: Optional[float]
    decode_tok_s: Optional[float]
    prefill_ms: Optional[float]
    decode_ms: Optional[float]
    success: bool
    error: Optional[str] = None

@dataclass
class ScalingAnalysis:
    backend: str
    model_name: str
    scaling_type: str  # "strong" | "weak" | "batch" | "context"
    variable: str
    values: List[Any]
    prefill_throughput: List[Optional[float]]
    decode_throughput: List[Optional[float]]
    speedup: List[float]
    efficiency: List[float]
    bottlenecks: List[str]
    recommendations: List[str]

@dataclass
class ComparisonResult:
    backend: str
    config_a: Dict
    config_b: Dict
    prefill_change_pct: float
    decode_change_pct: float
    verdict: str  # "A better", "B better", "Similar"
    details: List[str]


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
                models.append({"name": f.stem, "path": str(f), "size_gb": round(size_gb, 2)})
    seen = set()
    unique = []
    for m in models:
        if m["name"] not in seen:
            seen.add(m["name"])
            unique.append(m)
    return unique


def run_bench(llama_bench: Path, model_path: str, backend: str, config: Dict) -> BenchmarkPoint:
    env = get_env_for_backend(backend)
    
    cmd = [
        str(llama_bench),
        "-m", model_path,
        "-ngl", str(config["n_gpu_layers"]),
        "-p", str(config["prompt_size"]),
        "-n", str(config["gen_size"]),
        "-b", str(config["batch_size"]),
        "-fa", config["flash_attn"],
        "-ctk", config["cache_type"],
        "-ctv", config["cache_type"],
        "-r", "2",
        "-o", "json",
        "--no-warmup",
    ]
    
    rc, stdout, stderr = run_cmd(cmd, env=env, timeout=600)
    
    if rc != 0:
        return BenchmarkPoint(
            config=config,
            prefill_tok_s=None,
            decode_tok_s=None,
            prefill_ms=None,
            decode_ms=None,
            success=False,
            error=stderr[:500],
        )
    
    prefill_tok_s = None
    decode_tok_s = None
    prefill_ms = None
    decode_ms = None
    
    try:
        json_data = json.loads(stdout)
        for entry in json_data:
            n_prompt = entry.get("n_prompt", 0)
            n_gen = entry.get("n_gen", 0)
            avg_ts = entry.get("avg_ts", 0)
            if n_prompt > 0 and n_gen == 0:
                prefill_tok_s = (n_prompt * 1000) / avg_ts if avg_ts > 0 else None
                prefill_ms = avg_ts
            elif n_prompt == 0 and n_gen > 0:
                decode_tok_s = (n_gen * 1000) / avg_ts if avg_ts > 0 else None
                decode_ms = avg_ts
    except:
        pass
    
    return BenchmarkPoint(
        config=config,
        prefill_tok_s=prefill_tok_s,
        decode_tok_s=decode_tok_s,
        prefill_ms=prefill_ms,
        decode_ms=decode_ms,
        success=True,
    )


def run_sweep(
    llama_bench: Path,
    model_path: str,
    backend: str,
    base_config: Dict,
    variable: str,
    values: List[Any],
) -> List[BenchmarkPoint]:
    """Ejecuta barrido de un parámetro."""
    results = []
    for v in values:
        config = base_config.copy()
        config[variable] = v
        print(f"  Testing {variable}={v}...")
        results.append(run_bench(llama_bench, model_path, backend, config))
    return results


def analyze_scaling(results: List[BenchmarkPoint], variable: str, scaling_type: str) -> ScalingAnalysis:
    """Analiza resultados de escalabilidad."""
    values = [r.config[variable] for r in results]
    prefill = [r.prefill_tok_s for r in results]
    decode = [r.decode_tok_s for r in results]
    
    # Calcular speedup relativo al primer punto
    speedup = []
    efficiency = []
    
    baseline_prefill = prefill[0] if prefill[0] else 1
    baseline_decode = decode[0] if decode[0] else 1
    
    for i in range(len(results)):
        if prefill[i] and baseline_prefill:
            sp = prefill[i] / baseline_prefill
            speedup.append(sp)
            # Eficiencia = speedup / (resources_ratio)
            if scaling_type == "batch" and values[0] != 0:
                eff = sp / (values[i] / values[0])
                efficiency.append(eff)
            else:
                efficiency.append(sp)
        else:
            speedup.append(0)
            efficiency.append(0)
    
    # Detectar bottlenecks
    bottlenecks = []
    recommendations = []
    
    # Verificar si speedup se satura
    if len(speedup) >= 3:
        last_improvement = speedup[-1] - speedup[-2]
        if last_improvement < 0.1:
            bottlenecks.append(f"Saturación en {variable}={values[-2]}: speedup marginal {last_improvement:.2f}x")
            recommendations.append(f"No aumentar {variable} más allá de {values[-2]}")
    
    # Verificar eficiencia
    avg_eff = sum(e for e in efficiency if e > 0) / max(1, len([e for e in efficiency if e > 0]))
    if avg_eff < 0.7:
        bottlenecks.append(f"Eficiencia baja ({avg_eff:.1%}): overhead de paralelización")
        recommendations.append(f"Revisar {variable}: posible contention de memoria o sincronización")
    
    # Verificar si prefill o decode son el límite
    prefill_trend = [p for p in prefill if p]
    decode_trend = [d for d in decode if d]
    
    if len(prefill_trend) >= 2 and len(decode_trend) >= 2:
        prefill_growth = prefill_trend[-1] / prefill_trend[0] if prefill_trend[0] else 0
        decode_growth = decode_trend[-1] / decode_trend[0] if decode_trend[0] else 0
        
        if prefill_growth < decode_growth * 0.5:
            bottlenecks.append("Prefill no escala igual que decode: posible bottleneck en atención")
            recommendations.append("Considerar flash-attn=on, reducir prompt_size, o aumentar batch para prefill")
    
    return ScalingAnalysis(
        backend="",
        model_name="",
        scaling_type=scaling_type,
        variable=variable,
        values=values,
        prefill_throughput=prefill,
        decode_throughput=decode,
        speedup=speedup,
        efficiency=efficiency,
        bottlenecks=bottlenecks,
        recommendations=recommendations,
    )


def compare_configs(results_a: List[BenchmarkPoint], results_b: List[BenchmarkPoint]) -> List[ComparisonResult]:
    """Compara dos conjuntos de configuraciones."""
    comparisons = []
    
    for r1 in results_a:
        for r2 in results_b:
            if not r1.success or not r2.success:
                continue
            
            prefill_change = 0
            decode_change = 0
            
            if r1.prefill_tok_s and r2.prefill_tok_s:
                prefill_change = ((r2.prefill_tok_s - r1.prefill_tok_s) / r1.prefill_tok_s) * 100
            if r1.decode_tok_s and r2.decode_tok_s:
                decode_change = ((r2.decode_tok_s - r1.decode_tok_s) / r1.decode_tok_s) * 100
            
            details = []
            if abs(prefill_change) > 5:
                details.append(f"Prefill: {prefill_change:+.1f}%")
            if abs(decode_change) > 5:
                details.append(f"Decode: {decode_change:+.1f}%")
            
            if decode_change > 5 and prefill_change > -5:
                verdict = "B better"
            elif decode_change < -5 and prefill_change < 5:
                verdict = "A better"
            else:
                verdict = "Similar"
            
            comparisons.append(ComparisonResult(
                backend="",
                config_a=r1.config,
                config_b=r2.config,
                prefill_change_pct=prefill_change,
                decode_change_pct=decode_change,
                verdict=verdict,
                details=details,
            ))
    
    return comparisons


def generate_chrome_trace_from_timings(
    model_name: str,
    backend: str,
    config: Dict,
    prefill_ms: float,
    decode_ms: float,
    output_path: Path,
):
    """Genera Chrome Trace sintético a partir de timings."""
    trace_events = []
    
    trace_events.append({
        "name": "process_name",
        "ph": "M",
        "pid": 1,
        "args": {"name": f"llama.cpp {backend} - {model_name}"},
    })
    
    trace_events.append({
        "name": "thread_name",
        "ph": "M",
        "pid": 1,
        "tid": 1,
        "args": {"name": "Main Thread"},
    })
    
    # Prefill event
    if prefill_ms > 0:
        trace_events.append({
            "name": "Prefill",
            "cat": "inference",
            "ph": "X",
            "ts": 0,
            "dur": prefill_ms * 1000,  # us
            "pid": 1,
            "tid": 1,
            "args": {
                "prompt_tokens": config["prompt_size"],
                "tok_s": config["prompt_size"] / (prefill_ms / 1000) if prefill_ms > 0 else 0,
                "batch_size": config["batch_size"],
            },
        })
    
    # Decode event
    if decode_ms > 0:
        trace_events.append({
            "name": "Decode",
            "cat": "inference",
            "ph": "X",
            "ts": prefill_ms * 1000,
            "dur": decode_ms * 1000,
            "pid": 1,
            "tid": 1,
            "args": {
                "gen_tokens": config["gen_size"],
                "tok_s": config["gen_size"] / (decode_ms / 1000) if decode_ms > 0 else 0,
                "batch_size": config["batch_size"],
            },
        })
    
    # Config metadata
    trace_events.append({
        "name": "config",
        "ph": "M",
        "pid": 1,
        "args": {"config": json.dumps(config)},
    })
    
    trace_data = {
        "traceEvents": trace_events,
        "displayTimeUnit": "us",
        "metadata": {
            "model": model_name,
            "backend": backend,
            "config": config,
        },
    }
    
    output_path.write_text(json.dumps(trace_data, indent=2), encoding="utf-8")


def generate_prometheus_metrics(
    model_name: str,
    backend: str,
    results: List[BenchmarkPoint],
    output_path: Path,
):
    """Genera métricas Prometheus."""
    lines = [
        f'# HELP llama_prefill_tokens_per_second Prefill throughput',
        f'# TYPE llama_prefill_tokens_per_second gauge',
    ]
    
    for r in results:
        if r.success and r.prefill_tok_s:
            labels = ",".join([f'{k}="{v}"' for k, v in r.config.items()])
            lines.append(f'llama_prefill_tokens_per_second{{model="{model_name}",backend="{backend}",{labels}}} {r.prefill_tok_s}')
    
    lines.extend([
        f'# HELP llama_decode_tokens_per_second Decode throughput',
        f'# TYPE llama_decode_tokens_per_second gauge',
    ])
    
    for r in results:
        if r.success and r.decode_tok_s:
            labels = ",".join([f'{k}="{v}"' for k, v in r.config.items()])
            lines.append(f'llama_decode_tokens_per_second{{model="{model_name}",backend="{backend}",{labels}}} {r.decode_tok_s}')
    
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Análisis de rendimiento llama.cpp")
    parser.add_argument("--model", help="Nombre del modelo (substring)")
    parser.add_argument("--backend", choices=["vulkan", "hip", "both"], default="both")
    parser.add_argument("--config", choices=["default", "large_context", "cpu_only"], default="default")
    parser.add_argument("--scaling-analysis", action="store_true", help="Análisis de escalabilidad")
    parser.add_argument("--variable", choices=["n_gpu_layers", "prompt_size", "gen_size", "batch_size", "flash_attn", "cache_type"],
                       help="Variable para barrido (requiere --scaling-analysis)")
    parser.add_argument("--values", help="Valores para barrido (coma-separados)")
    parser.add_argument("--compare-configs", action="store_true", help="Comparar configuraciones A vs B")
    parser.add_argument("--config-a", help="JSON config A para comparación (o @archivo.json)")
    parser.add_argument("--config-b", help="JSON config B para comparación (o @archivo.json)")
    parser.add_argument("--trace-chrome", action="store_true", help="Generar Chrome Trace")
    parser.add_argument("--prometheus", action="store_true", help="Generar métricas Prometheus")
    parser.add_argument("--save-baseline", help="Guardar resultados como baseline")
    parser.add_argument("--list-analyses", action="store_true", help="Listar análisis disponibles")
    parser.add_argument("--output", "-o", help="Archivo JSON de salida")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirmar")
    args = parser.parse_args()
    
    if args.list_analyses:
        print("Análisis disponibles:")
        print("  --scaling-analysis --variable batch_size --values 512,1024,2048,4096")
        print("  --scaling-analysis --variable n_gpu_layers --values -1,0,10,20,30,40")
        print("  --scaling-analysis --variable prompt_size --values 512,1024,2048,4096,8192")
        print("  --compare-configs --config-a '{\"n_gpu_layers\":-1}' --config-b '{\"n_gpu_layers\":20}'")
        print("  --trace-chrome  (genera trace sintético)")
        print("  --prometheus    (genera métricas Prometheus)")
        return
    
    if not args.model:
        parser.error("--model es requerido")
    
    base_configs = {
        "default": {"n_gpu_layers": -1, "prompt_size": 512, "gen_size": 256, "batch_size": 2048, "flash_attn": "auto", "cache_type": "q4_0"},
        "large_context": {"n_gpu_layers": -1, "prompt_size": 2048, "gen_size": 256, "batch_size": 1024, "flash_attn": "auto", "cache_type": "q4_0"},
        "cpu_only": {"n_gpu_layers": 0, "prompt_size": 512, "gen_size": 256, "batch_size": 2048, "flash_attn": "off", "cache_type": "f16"},
    }
    base_config = base_configs[args.config]
    
    print("=" * 70)
    print(f"ANÁLISIS RENDIMIENTO: {args.model} | Config: {args.config} | Backend: {args.backend}")
    print("=" * 70)
    
    # Encontrar modelo
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
    print(f"Modelo: {model['name']} ({model['size_gb']} GB)")
    
    # Backends
    backends = []
    if args.backend in ["vulkan", "both"]:
        for vb in LLAMA_CPP_PATHS["vulkan_builds"]:
            p = Path(vb)
            if (p / "llama-bench.exe").exists():
                backends.append(("vulkan", p / "llama-bench.exe"))
    
    if args.backend in ["hip", "both"]:
        hp = Path(LLAMA_CPP_PATHS["hip_build"])
        if (hp / "llama-bench.exe").exists():
            backends.append(("hip", hp / "llama-bench.exe"))
    
    if not backends:
        print("[FAIL] No hay backends validos")
        return
    
    all_results = {}
    
    # Ejecutar análisis
    for backend_name, llama_bench in backends:
        print(f"\n{'='*50}")
        print(f"ANALISIS BACKEND: {backend_name.upper()}")
        print(f"{'='*50}")
        
        backend_results = []
        
        if args.scaling_analysis and args.variable and args.values:
            # Análisis de escalabilidad
            values = [float(v) if '.' in v else int(v) for v in args.values.split(",")]
            print(f"Barrido {args.variable}: {values}")
            
            results = run_sweep(llama_bench, model["path"], backend_name, base_config, args.variable, values)
            backend_results = results
            
            # Análisis
            analysis = analyze_scaling(results, args.variable, "batch" if args.variable == "batch_size" else "strong")
            analysis.backend = backend_name
            analysis.model_name = model["name"]
            
            print(f"\n[CHART] ESCALABILIDAD {args.variable.upper()}:")
            print(f"{'Valor':>10} | {'Prefill':>10} | {'Decode':>10} | {'Speedup':>8} | {'Eff':>6}")
            print("-" * 55)
            for i, r in enumerate(results):
                if r.success:
                    sp = analysis.speedup[i] if i < len(analysis.speedup) else 0
                    eff = analysis.efficiency[i] if i < len(analysis.efficiency) else 0
                    print(f"{values[i]:>10} | {r.prefill_tok_s:>10.1f} | {r.decode_tok_s:>10.1f} | {sp:>7.2f}x | {eff:>5.1%}")
            
            if analysis.bottlenecks:
                print(f"\n[WARN] CUELLOS DE BOTELLA:")
                for b in analysis.bottlenecks:
                    print(f"  - {b}")
            
            if analysis.recommendations:
                print(f"\n[IDEA] RECOMENDACIONES:")
                for r in analysis.recommendations:
                        print(f"  - {r}")

        elif args.compare_configs and args.config_a and args.config_b:
            # Comparación A vs B
            try:
                config_a = parse_config_arg(args.config_a)
                config_b = parse_config_arg(args.config_b)
            except Exception as e:
                print(f"[FAIL] Error parseando configs: {e}")
                return
            
            config_a_full = {**base_config, **config_a}
            config_b_full = {**base_config, **config_b}
            
            print(f"Config A: {config_a}")
            print(f"Config B: {config_b}")
            
            result_a = run_bench(llama_bench, model["path"], backend_name, config_a_full)
            result_b = run_bench(llama_bench, model["path"], backend_name, config_b_full)
            
            backend_results = [result_a, result_b]
            
            if result_a.success and result_b.success:
                comp = ComparisonResult(
                    backend=backend_name,
                    config_a=config_a_full,
                    config_b=config_b_full,
                    prefill_change_pct=((result_b.prefill_tok_s - result_a.prefill_tok_s) / result_a.prefill_tok_s * 100) if result_a.prefill_tok_s else 0,
                    decode_change_pct=((result_b.decode_tok_s - result_a.decode_tok_s) / result_a.decode_tok_s * 100) if result_a.decode_tok_s else 0,
                    verdict="",
                    details=[],
                )
                
                if comp.decode_change_pct > 5 and comp.prefill_change_pct > -5:
                    comp.verdict = "B better"
                elif comp.decode_change_pct < -5 and comp.prefill_change_pct < 5:
                    comp.verdict = "A better"
                else:
                    comp.verdict = "Similar"
                
                if abs(comp.prefill_change_pct) > 5:
                    comp.details.append(f"Prefill: {comp.prefill_change_pct:+.1f}%")
                if abs(comp.decode_change_pct) > 5:
                    comp.details.append(f"Decode: {comp.decode_change_pct:+.1f}%")
                
                print(f"\n[COMPARE] COMPARACION A vs B:")
                print(f"  Veredicto: {comp.verdict}")
                for d in comp.details:
                    print(f"  - {d}")
        
        else:
            # Benchmark simple
            print(f"Benchmark base: {base_config}")
            result = run_bench(llama_bench, model["path"], backend_name, base_config)
            backend_results = [result]
            
            if result.success:
                print(f"[OK] Prefill: {result.prefill_tok_s:.1f} tok/s ({result.prefill_ms:.1f} ms)")
                print(f"[OK] Decode: {result.decode_tok_s:.1f} tok/s ({result.decode_ms:.1f} ms)")
            else:
                print(f"[FAIL] {result.error}")
        
        # Trace Chrome
        if args.trace_chrome and backend_results:
            output_dir = Path(LLAMA_CPP_PATHS["traces_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for r in backend_results:
                if r.success:
                    trace_path = output_dir / f"{model['name']}_{backend_name}_{args.config}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.chrome_trace.json"
                    generate_chrome_trace_from_timings(
                        model["name"], backend_name, r.config,
                        r.prefill_ms or 0, r.decode_ms or 0,
                        trace_path
                    )
                    print(f"\n[WEB] Chrome Trace: {trace_path}")
                    print(f"   Abrir en: chrome://tracing -> Load")
        
        # Prometheus
        if args.prometheus and backend_results:
            output_dir = Path(LLAMA_CPP_PATHS["traces_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            prom_path = output_dir / f"{model['name']}_{backend_name}_{args.config}.prometheus.metrics"
            generate_prometheus_metrics(model["name"], backend_name, backend_results, prom_path)
            print(f"\n[DISK] Prometheus metrics: {prom_path}")
        
        # Guardar baseline
        if args.save_baseline and backend_results:
            baselines_dir = Path(LLAMA_CPP_PATHS["baselines_dir"])
            baselines_dir.mkdir(parents=True, exist_ok=True)
            baseline_path = baselines_dir / f"{args.save_baseline}.json"
            with open(baseline_path, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in backend_results], f, indent=2, ensure_ascii=False)
            print(f"\n[DISK] Baseline guardado: {baseline_path}")
        
        all_results[backend_name] = backend_results
    
    # Guardar resultados
    if args.output:
        output_data = {
            "model": model["name"],
            "config": args.config,
            "backend": args.backend,
            "results": {k: [asdict(r) for r in v] for k, v in all_results.items()},
            "timestamp": datetime.now().isoformat(),
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Resultados guardados en: {args.output}")


if __name__ == "__main__":
    main()