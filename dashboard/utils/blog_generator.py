"""
Blog Generator - Genera posts de blog Astro-ready desde eventos
Compatible con Astro Content Collections
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# Rutas
DASHBOARD_ROOT = Path(__file__).parent.parent
BLOG_DRAFTS_DIR = Path(__file__).parent.parent / "data" / "blog_drafts"
EVENTS_FILE = Path(__file__).parent.parent / "data" / "events.jsonl"


@dataclass
class BlogPost:
    """Estructura de un post de blog Astro"""
    title: str
    date: str
    tags: List[str]
    category: str
    hardware: Dict[str, Any]
    models: List[Dict[str, Any]]
    results: Dict[str, Any]
    summary: str
    draft: bool = True
    content: str = ""


def generate_blog_post(event: dict) -> Optional[str]:
    """
    Genera un post de blog completo desde un evento.
    
    Args:
        event: Evento con id, timestamp, type, payload
    
    Returns:
        Contenido del archivo .md o None si error
    """
    payload = event.get("data", {})
    event_type = event.get("event_type", "")
    
    try:
        if event_type == "benchmark.completed":
            return _generate_benchmark_post(event)
        elif event_type == "tuning.completed":
            return _generate_tuning_post(event)
        elif event_type == "analysis.generated":
            return _generate_analysis_post(event)
        elif event_type == "baseline.updated":
            return _generate_baseline_post(event)
        elif event_type == "model.discovered":
            return _generate_model_post(event)
        elif event_type == "bat.generated":
            return _generate_bat_post(event)
    except Exception as e:
        print(f"Error generating blog post: {e}")
    
    return None


def save_blog_post(content: str, category: str = "general") -> Optional[str]:
    """Guarda post en directorio de borradores"""
    BLOG_DRAFTS_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_post.md"
    filepath = BLOG_DRAFTS_DIR / filename
    
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def generate_blog_index() -> str:
    """Genera índice de borradores para navegación"""
    drafts = []
    if BLOG_DRAFTS_DIR.exists():
        for f in BLOG_DRAFTS_DIR.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                # Extraer frontmatter
                if content.startswith("---"):
                    _, fm, _ = content.split("---", 2)
                    import yaml
                    fm_data = yaml.safe_load(fm)
                    drafts.append({
                        "file": f.name,
                        "title": fm_data.get("title", "Untitled"),
                        "date": fm_data.get("date", ""),
                        "category": fm_data.get("category", "general"),
                        "tags": fm_data.get("tags", []),
                        "draft": fm_data.get("draft", True)
                    })
            except Exception:
                pass
    
    # Generar índice markdown
    lines = ["# Borradores de Blog\n", ""]
    for d in sorted(drafts, key=lambda x: x.get("date", ""), reverse=True):
        status = "[DRAFT]" if d.get("draft") else "[OK] Publicado"
        lines.append(f"- [{d['title']}]({d['file']}) - {d['date'][:10]} - {d['category']} - {status}")
    
    return "\n".join(lines)


# Funciones privadas de generación por tipo

def _generate_benchmark_post(event: dict) -> str:
    payload = event.get("data", {})
    model = payload.get("model", "unknown")
    backend = payload.get("backend", "unknown")
    results = payload.get("results", {})
    
    # Find best results (tolerante a varios shapes: list, dict.results, dict.data)
    rows: list = []
    if isinstance(results, list):
        rows = results
    elif isinstance(results, dict):
        for key in ("results", "data", "rows", "benchmarks"):
            val = results.get(key)
            if isinstance(val, list):
                rows = val
                break
    best_decode = 0.0
    best_config = ""
    for r in rows:
        if not isinstance(r, dict):
            continue
        try:
            val = float(r.get("decode_tok_s", 0) or 0)
        except Exception:
            val = 0.0
        if val > best_decode:
            best_decode = val
            best_config = f"ngl={r.get('n_gpu_layers')}, p={r.get('prompt_size')}, g={r.get('gen_size')}, b={r.get('batch_size')}, fa={r.get('flash_attn')}, cache={r.get('cache_type')}"
    
    # Hardware info
    hw = {
        "gpu": "AMD Radeon RX 9070",
        "vram_gb": 16,
        "cpu": "Ryzen 7 7800X3D",
        "driver": "AMD Adrenalin 2.0.395",
        "vulkan_version": "1.4.357",
        "hip_version": "7.2.0"
    }
    
    frontmatter = {
        "title": f"Benchmark: {model} en {backend} ({round(best_decode, 1)} tok/s decode)",
        "date": datetime.utcnow().isoformat() + "Z",
        "tags": ["amd", "rx9070", model.lower().replace(".", "-"), backend, "benchmark", "local-llm"],
        "category": "benchmarks",
        "hardware": hw,
        "models": [{"name": model}],
        "results": {"best_decode_toks": round(best_decode, 1), "config": best_config, "raw": results},
        "summary": f"Benchmark de {model} en {backend}. Mejor decode medido: {round(best_decode, 1)} tok/s ({best_config}).",
        "draft": True
    }
    
    content = f"""# Benchmark: {model} en {backend.upper()}

## Configuración óptima
- Backend: {backend}
- n_gpu_layers: {payload.get('n_gpu_layers', 'all')}
- Prompt size: {payload.get('prompt_size', 512)}
- Gen size: {payload.get('gen_size', 256)}
- Batch size: {payload.get('batch_size', 2048)}
- Flash Attention: {payload.get('flash_attn', 'auto')}
- Cache type: {payload.get('cache_type', 'q4_0')}

## Resultados
- **Decode throughput**: {best_decode:.0f} tok/s
- **Mejor configuración**: {best_config}

## Hardware
- GPU: {hw['gpu']} ({hw['vram_gb']} GB VRAM)
- CPU: {hw['cpu']}
- Driver: {hw['driver']}
- Vulkan: {hw['vulkan_version']}
- HIP/ROCm: {hw['hip_version']}

## Conclusión
{frontmatter['summary']}
"""
    
    return _write_post(frontmatter, content)


def _generate_tuning_post(event: dict) -> str:
    payload = event.get("data", {})
    model = payload.get("model", "unknown")
    profile = payload.get("profile", "balanced")
    best_config = payload.get("best_config", {})
    metrics = payload.get("metrics", {})
    
    frontmatter = {
        "title": f"Auto-Tuning: {model} - Perfil {profile}",
        "date": datetime.utcnow().isoformat() + "Z",
        "tags": ["amd", "tuning", "auto-tuning", model.lower().replace(".", "-")],
        "category": "tuning",
        "hardware": {"gpu": "AMD Radeon RX 9070", "vram_gb": 16},
        "models": [{"name": model, "profile": profile}],
        "results": {"config": best_config, "metrics": metrics},
        "summary": f"Auto-tuning {profile} para {model}. Config óptima: {best_config}",
        "draft": True
    }
    
    content = f"""# Auto-Tuning: {model}

## Perfil: {profile}

## Configuración óptima
- n_gpu_layers: {best_config.get('n_gpu_layers', 'N/A')}
- Prompt size: {best_config.get('prompt_size', 'N/A')}
- Gen size: {best_config.get('gen_size', 'N/A')}
- Batch size: {best_config.get('batch_size', 'N/A')}
- Flash Attention: {best_config.get('flash_attn', 'N/A')}
- Cache type: {best_config.get('cache_type', 'N/A')}

## Métricas
- Score: {best_config.get('score', 'N/A')}
- Decode: {metrics.get('decode_tok_s', 'N/A')} tok/s
- Prefill: {metrics.get('prefill_tok_s', 'N/A')} tok/s
- VRAM: {metrics.get('vram_mb', 'N/A')} MB
"""
    
    return _write_post(frontmatter, content)


def _generate_analysis_post(event: dict) -> str:
    payload = event.get("data", {})
    model = payload.get("model", "unknown")
    analysis_type = payload.get("analysis_type", "scaling")
    findings = payload.get("findings", [])
    
    frontmatter = {
        "title": f"Análisis: {analysis_type} en {model}",
        "date": datetime.utcnow().isoformat() + "Z",
        "tags": ["amd", "analysis", "scaling", model.lower().replace(".", "-")],
        "category": "analysis",
        "models": [{"name": model}],
        "summary": f"Análisis {analysis_type} para {model}. Hallazgos: {len(findings)}",
        "draft": True
    }
    
    content = f"""# Análisis: {analysis_type} en {model}

## Tipo de análisis
{analysis_type}

## Hallazgos
{chr(10).join(f"- {f}" for f in findings) if findings else "Sin hallazgos registrados."}

## Modelo
{model}

## Configuración
{json.dumps(payload.get('config', {}), indent=2, ensure_ascii=False)}
"""
    
    return _write_post(frontmatter, content)


def _generate_baseline_post(event: dict) -> str:
    payload = event.get("data", {})
    model = payload.get("model", "unknown")
    backend = payload.get("backend", "unknown")
    metrics = payload.get("metrics", {})
    
    frontmatter = {
        "title": f"Baseline Actualizada: {model} en {backend}",
        "date": datetime.utcnow().isoformat() + "Z",
        "tags": ["amd", "baseline", "regression", model.lower().replace(".", "-")],
        "category": "baselines",
        "models": [{"name": model, "backend": backend}],
        "results": metrics,
        "summary": f"Nueva baseline para {model} ({backend}): decode {metrics.get('decode_tok_s', 0):.0f} tok/s",
        "draft": True
    }
    
    content = f"""# Baseline: {model}

## Backend
{backend}

## Métricas
- Decode: {metrics.get('decode_tok_s', 0):.0f} tok/s
- Prefill: {metrics.get('prefill_tok_s', 0):.0f} tok/s
- VRAM peak: {metrics.get('vram_peak_mb', 0):.0f} MB

## Configuración
{json.dumps(payload.get('config', {}), indent=2, ensure_ascii=False)}
"""
    
    return _write_post(frontmatter, content)


def _generate_model_post(event: dict) -> str:
    payload = event.get("data", {})
    model = payload.get("model", "unknown")
    size_gb = payload.get("size_gb", 0)
    quantization = payload.get("quantization", "unknown")
    
    frontmatter = {
        "title": f"Nuevo Modelo Descubierto: {model}",
        "date": datetime.utcnow().isoformat() + "Z",
        "tags": ["amd", "model", "discovery", model.lower().replace(".", "-")],
        "category": "models",
        "models": [{"name": model, "size_gb": size_gb, "quantization": quantization}],
        "summary": f"Nuevo modelo GGUF detectado: {model} ({size_gb} GB, {quantization})",
        "draft": True
    }
    
    content = f"""# Nuevo Modelo: {model}

## Detalles
- Tamaño: {size_gb} GB
- Cuantización: {quantization}

## Notas
Modelo GGUF detectado automáticamente durante el escaneo de modelos.
"""
    
    return _write_post(frontmatter, content)


def _generate_bat_post(event: dict) -> str:
    payload = event.get("data", {})
    model = payload.get("model", "unknown")
    preset = payload.get("preset", "balanced")
    config = payload.get("config", {})
    
    frontmatter = {
        "title": f"Script .bat Generado: {model} - {preset}",
        "date": datetime.utcnow().isoformat() + "Z",
        "tags": ["amd", "bat", "launch", model.lower().replace(".", "-")],
        "category": "scripts",
        "models": [{"name": model, "preset": preset}],
        "results": {"config": config},
        "summary": f"Script .bat generado para {model} con preset {preset}",
        "draft": True
    }
    
    content = f"""# Script .bat: {model}

## Preset
{preset}

## Configuración
- n_gpu_layers: {config.get('ngl', 'N/A')}
- Prompt size: {config.get('prompt_size', 'N/A')}
- Gen size: {config.get('gen_size', 'N/A')}
- Batch size: {config.get('batch_size', 'N/A')}
- Flash Attention: {config.get('fa', 'N/A')}
- Cache type: {config.get('cache_type', 'N/A')}
- Context size: {config.get('ctx', 'N/A')}
"""
    
    return _write_post(frontmatter, content)


def _frontmatter_yaml(frontmatter: dict) -> str:
    try:
        import yaml

        return yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    except Exception:
        lines = []
        for key, value in frontmatter.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            elif isinstance(value, bool):
                lines.append(f"{key}: {str(value).lower()}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)


def _write_post(frontmatter: dict, content: str) -> str:
    """Construye el archivo markdown completo"""
    return "---\n" + _frontmatter_yaml(frontmatter) + "\n---\n\n" + content + "\n"


# CLI para testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python blog_generator.py <command>")
        print("Commands: index, generate <event_type> <json>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "index":
        print(generate_blog_index())
    elif cmd == "generate" and len(sys.argv) >= 4:
        event_type = sys.argv[2]
        payload = json.loads(sys.argv[3])
        event = {"type": event_type, "payload": payload, "timestamp": datetime.utcnow().isoformat()}
        # Would generate post here
        print("Generated")
    else:
        print("Unknown command")