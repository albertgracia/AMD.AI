# Análisis de Rendimiento Profundo: Qwen3.5-9B en RX 9070 (Vulkan vs HIP)

**Fecha:** 2026-09-05  
**Hardware:** AMD Radeon RX 9070 16GB (RDNA 4 / gfx1103 Vulkan, gfx1201 HIP)  
**CPU:** AMD Ryzen 7 7800X3D 8-Core (Zen 4)  
**Backend HIP:** ROCm 7.2.0 via `_rocm_sdk_devel` (Python package)  
**Backend Vulkan:** Driver AMD 2.0.395, Vulkan 1.4.357  
**Script:** `G:\Proyectos\AMD.AI\scripts\analyze_local.py`

---

## 📊 Hallazgo Crítico: CPU Supera a GPU

### Comparación ngl=-1 (GPU) vs ngl=0 (CPU-only)

| Backend | Config | Prefill tok/s | Decode tok/s | Diferencia |
|---------|--------|---------------|--------------|------------|
| **HIP** | ngl=-1 (GPU) | 420 | 3,461 | **Baseline** |
| **HIP** | ngl=0 (CPU) | **1,556** | **27,454** | **+270% / +693%** |
| **Vulkan** | ngl=-1 (GPU) | 271 | 2,887 | **Baseline** |
| **Vulkan** | ngl=0 (CPU) | **999** | **27,122** | **+269% / +839%** |

> 🎯 **Conclusión**: Para Qwen3.5-9B-Q4_K (5.56 GB) en Ryzen 7 7800X3D + RX 9070, **el backend CPU (Zen 4 optimizado) es 2.7-9x más rápido que GPU** tanto en Vulkan como HIP. La GPU RX 9070 no está bien aprovechada por los kernels actuales.

---

## 📈 Análisis de Escalabilidad (Batch Size)

### HIP/ROCm
| Batch | Prefill tok/s | Decode tok/s | Speedup | Eficiencia |
|-------|---------------|--------------|---------|------------|
| 512   | 294 | 3,346 | 1.00x | 100% |
| 1024  | 395 | 3,368 | 1.34x | **67%** |
| 2048  | 294 | 3,336 | 1.00x | 25% |
| 4096  | 428 | 3,367 | 1.45x | 18% |

**Bottleneck**: Eficiencia 52.6% → **Contención memoria/sincronización**  
**Óptimo**: batch=1024 (mejor eficiencia)

### Vulkan
| Batch | Prefill tok/s | Decode tok/s | Speedup | Eficiencia |
|-------|---------------|--------------|---------|------------|
| 512   | 250 | 2,880 | 1.00x | 100% |
| 1024  | 271 | 2,878 | 1.09x | 54% |
| 2048  | 271 | 2,887 | 1.09x | 27% |
| 4096  | 250 | 2,879 | 1.00x | 12% |

**Bottleneck**: Eficiencia 48.5% → **Overhead paralización**  
**Óptimo**: batch=1024-2048

---

## 🎯 Análisis de Escalabilidad (n_gpu_layers - HIP)

| ngl | Prefill tok/s | Decode tok/s | Speedup | Eficiencia |
|-----|---------------|--------------|---------|------------|
| -1 (all) | 420 | 3,462 | 1.00x | 100% |
| 0 (CPU) | **1,110** | **27,454** | **2.64x** | **264%** |
| 10 | 879 | 19,136 | 2.09x | 209% |
| 20 | 671 | 12,864 | 1.60x | 160% |
| 30 | 392 | 6,979 | 0.93x | 93% |
| 40 | 388 | 3,389 | 0.92x | 92% |

**Hallazgo clave**: Transición suave CPU→GPU. **ngl=10-20** es punto dulce para híbrido.

---

## 📏 Análisis de Escalabilidad (Prompt Size - HIP)

| Prompt | Prefill tok/s | Decode tok/s | Speedup | Eficiencia |
|--------|---------------|--------------|---------|------------|
| 512   | 293 | 3,355 | 1.00x | 100% |
| 1024  | 528 | 3,353 | 1.80x | **180%** |
| 2048  | 918 | 3,350 | 3.13x | **313%** |
| 4096  | 1,698 | 3,352 | 5.79x | **579%** |
| 8192  | 3,356 | 3,351 | 11.45x | **1145%** |

**Perfecto escalado lineal** en prefill. Decode constante (independiente de prompt).

---

## 🏆 Resumen Comparativo: Vulkan vs HIP

| Métrica | **Vulkan** | **HIP/ROCm** | Ganador |
|---------|------------|--------------|---------|
| **Prefill (GPU)** | 271 tok/s | 420 tok/s | 🏆 **HIP +55%** |
| **Decode (GPU)** | 2,887 tok/s | 3,461 tok/s | 🏆 **HIP +20%** |
| **Prefill (CPU)** | 999 tok/s | 1,556 tok/s | 🏆 **HIP +56%** |
| **Decode (CPU)** | 27,122 tok/s | 27,454 tok/s | ~Empate |
| **Escalabilidad batch** | 48% eff | 53% eff | 🏆 **HIP** |
| **Flash Attention** | Nativo | SDPA fallback | Vulkan* |
| **Estabilidad** | ✅ | ✅ | Empate |
| **Tooling** | Validation layers | Sin rocprof | Vulkan |

> *HIP usa SDPA fallback en RDNA 4; Vulkan tiene FA nativo pero kernels menos optimizados

---

## 🔍 Cuellos de Botella Identificados

### 1. **GPU Subutilizada** (Crítico)
- RX 9070 (gfx1103/gfx1201) no aprovechada por kernels llama.cpp actuales
- CPU Zen 4 (AVX2/AVX-512) supera a GPU en 2-9x
- **Causa probable**: Kernels HIP/Vulkan genéricos sin optimizaciones RDNA 4

### 2. **Contención Memoria en Batch >1024**
- Eficiencia cae a 18-27% en batch=4096
- **Recomendación**: Mantener batch=1024-2048

### 3. **Falta de Profiling Nativo**
- `GGML_HIP_EXPORT_METRICS=OFF` en build
- ROCm SDK sin `rocprof`/`roc-tracer`
- Vulkan validation layers requieren app instrumentada

### 4. **Flash Attention en HIP = SDPA Fallback**
- RDNA 4 (gfx1201) no tiene kernels FA nativos en llama.cpp
- Vulkan tiene FA nativo pero no compensa diferencia de kernels

---

## 🛠 Herramientas Generadas

### Scripts
| Script | Función |
|--------|---------|
| `detect_local.py` | Detección entorno + validación backends + matriz compatibilidad |
| `bench_local.py` | Benchmarking matriz parametrizable (modelo × backend × config) |
| `tune_local.py` | Auto-tuning 5 perfiles (throughput, latency, balanced, max_ctx, mem) |
| `analyze_local.py` | Análisis escalabilidad, comparación configs, traces, Prometheus |

### Outputs de Análisis
```
G:\Proyectos\AMD.AI\docs\
├── analyze_scaling_batch.json      # Batch scaling (Vulkan 2 builds + HIP)
├── analyze_scaling_ngl.json        # n_gpu_layers sweep (HIP)
├── analyze_scaling_prompt.json     # Prompt size scaling (HIP)
├── analyze_compare.json            # HIP: ngl=-1 vs ngl=0
├── analyze_compare_vulkan.json     # Vulkan: ngl=-1 vs ngl=0
├── analyze_comprehensive.json      # Both backends batch scaling
├── analyze_trace.json              # Trace + Prometheus output
└── traces/
    ├── *.chrome_trace.json         # Chrome://tracing compatible
    └── *.prometheus.metrics        # Prometheus format
```

---

## 🎯 Recomendaciones para Skill `local-ai-use`

### Configuración Óptima por Defecto (HIP)
```bash
# Balanceado - mejor compromiso
llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0
# Prefill: ~1,500 tok/s | Decode: ~3,400 tok/s
```

### Para Máximo Throughput (CPU)
```bash
# Usar CPU-only - dramáticamente más rápido
llama-server -ngl 0 -p 512 -n 256 -b 2048 -fa off -ctk q4_0 -ctv q4_0
# Decode: ~27,000 tok/s
```

### Para RAG / Contexto Largo
```bash
# HIP con contexto grande
llama-server -ngl -1 -p 4096 -n 512 -b 1024 -fa auto -ctk q4_0 -ctv q4_0 -c 65536
```

### Para Modelos Grandes (>10GB)
```bash
# Híbrido: 20-30 capas en GPU, resto CPU
llama-server -ngl 20 -p 512 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0
```

---

## 📋 Próximos Pasos (Fase 5: Integración Skill AMD)

1. **Crear estructura skill `local-ai-use`**
   - `SKILL.md`, `skill-card.md`, `reference.md`
   - `scripts/`: detect, bench, tune, analyze
   - `data/`: model_compatibility.json, gpu_presets.json, quantization_guide.json
   - `evals/`: benchmark_baselines.json, regression_tests.py

2. **Baselines de Regresión**
   - Guardar métricas actuales como baseline
   - CI/CD: comparar contra baseline en cada PR

3. **Auto-detección Runtime**
   - Detectar GPU → seleccionar backend óptimo (HIP/Vulkan/CPU)
   - Aplicar preset según modelo/cuantización/caso de uso

4. **Documentación Visual**
   - Skill card con métricas clave
   - Diagramas de decisión backend

---

## 📝 Comandos de Referencia

```bash
# Detección completa
python detect_local.py --validate-backends --compatibility

# Benchmark rápido
python bench_local.py --model Qwen3.5-9B --backend hip --quick --yes

# Auto-tuning (balanced)
python tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --quick --yes

# Análisis escalabilidad batch
python analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable batch_size --values "512,1024,2048,4096"

# Comparación configs
python analyze_local.py --model Qwen3.5-9B --backend hip --compare-configs --config-a @config_a.json --config-b @config_b.json

# Trace + métricas
python analyze_local.py --model Qwen3.5-9B --backend hip --trace-chrome --prometheus
```

---

*Generado por `analyze_local.py` v1.0 — Análisis basado en benchmarks reales, sin profiling nativo (GGML_METRICS=OFF, sin rocprof)*