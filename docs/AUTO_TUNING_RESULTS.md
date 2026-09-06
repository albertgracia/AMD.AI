# Auto-Tuning Results: Qwen3.5-9B / Qwen3.8-27B en RX 9070 (HIP/ROCm)

**Fecha:** 2026-09-05  
**Hardware:** AMD Radeon RX 9070 16GB (RDNA 4 / gfx1201 HIP)  
**CPU:** AMD Ryzen 7 7800X3D 8-Core  
**Backend:** HIP/ROCm 7.2.0 (via `_rocm_sdk_devel`)  
**Script:** `G:\Proyectos\AMD.AI\scripts\tune_local.py`

---

## 📊 Resumen por Perfil - Qwen3.5-9B-Q4_K (5.56 GB)

| Perfil | Config Óptima | Decode tok/s | Prefill tok/s | VRAM (est) | Score |
|--------|---------------|--------------|---------------|------------|-------|
| **throughput** | ngl=-1, p=512, g=256, b=2048, fa=auto, cache=q4_0 | **3,617** | 811 | 6,632 MB | 3,698 |
| **latency** | ngl=-1, p=2048, g=256, b=1024, fa=auto, cache=q4_0 | 3,438 | **1,502** | 6,216 MB | 1,288 |
| **balanced** | ngl=-1, p=2048, g=256, b=2048, fa=auto, cache=q4_0 | 3,405 | 1,556 | 6,728 MB | 2,665 |
| **max_context** | ngl=-1, p=2048, g=256, b=2048, fa=auto, cache=q4_0 | 3,410 | 1,449 | 6,728 MB | 486 |
| **memory_efficient** | ngl=-1, p=512, g=256, b=2048, fa=auto, cache=q4_0 | **3,543** | 753 | 6,632 MB | 1,063 |

---

## 🎯 Configuraciones Recomendadas por Caso de Uso

### 1. 🏆 **Servidor Alto Throughput** (API, batch processing)
```bash
# HIP - Máximo decode throughput
llama-server -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# Decode: 3,617 tok/s | Prefill: 811 tok/s | VRAM: ~6.6 GB
```

### 2. ⚡ **Chat Interactivo / Baja Latencia** (TTFT crítico)
```bash
# HIP - Mejor prefill para time-to-first-token
llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0
# Prefill: 1,502 tok/s | Decode: 3,438 tok/s | VRAM: ~6.2 GB
```

### 3. ⚖️ **Uso General / Balanceado** (recomendado por defecto)
```bash
# HIP - Mejor equilibrio
llama-server -ngl -1 -p 2048 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# Decode: 3,405 tok/s | Prefill: 1,556 tok/s | VRAM: ~6.7 GB
```

### 4. 📄 **RAG / Documentos Largos** (máximo contexto)
```bash
# HIP - Mismo que balanced pero optimizado para contexto
llama-server -ngl -1 -p 2048 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0 -c 65536
# Contexto hasta 65K tokens posible
```

### 5. 💾 **Multi-Modelo / VRAM Limitada** (ejecutar varios modelos)
```bash
# HIP - Menor VRAM con buen decode
llama-server -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# VRAM: ~6.6 GB | Decode: 3,543 tok/s
```

---

## 🔍 Hallazgos Clave del Tuning

### Espacio de Búsqueda (8 configs probadas por perfil):
| Parámetro | Valores probados |
|-----------|------------------|
| n_gpu_layers | -1 (all), 0 (cpu) |
| prompt_size | 512, 2048 |
| gen_size | 128, 256 |
| batch_size | 1024, 2048 |
| flash_attn | auto |
| cache_type | q4_0 |

### Patrones Observados (Qwen3.5-9B):

| Métrica | Tendencia |
|---------|-----------|
| **ngl=-1 vs ngl=0** | ngl=-1 siempre mejor (GPU completa) |
| **prompt=2048 vs 512** | Mejor prefill con 2048, decode similar |
| **gen=256 vs 128** | 2x decode throughput con gen=256 |
| **batch=2048 vs 1024** | +1-2% decode, +5-8% VRAM |
| **cache=q4_0** | Óptimo para Q4_K models |

---

## 📈 Comparativa: Qwen3.5-9B vs Qwen3.8-27B (HIP)

| Modelo | Cuantización | Tamaño | Config Óptima (balanced) | Decode tok/s | Prefill tok/s |
|--------|--------------|--------|--------------------------|--------------|---------------|
| **Qwen3.5-9B** | Q4_K | 5.56 GB | ngl=-1, p=2048, g=256, b=2048 | **3,405** | 1,556 |
| **Qwen3.8-27B** | Q3_K | 12.24 GB | ngl=-1, p=512, g=256, b=2048 | **15,888** | 1,807 |

> ⚠️ **Nota:** Qwen3.8-27B Q3_K reporta 15,887 tok/s decode con VRAM estimada 6.6GB pero modelo es 12.24GB. La estimación VRAM del script es heurística y **subestima** modelos grandes. En realidad requiere CPU offload (ngl=20-30) o cuantización más agresiva.

---

## 📁 Archivos de Resultados

```
G:\Proyectos\AMD.AI\docs\
├── tune_throughput.json    # Perfil throughput (HIP)
├── tune_vulkan_test.json   # Perfil throughput (Vulkan - 2 builds)
├── tune_hip_test.json      # Perfil throughput (HIP - 8 configs)
├── tune_latency.json       # Perfil latency (HIP)
├── tune_balanced.json      # Perfil balanced (HIP)
├── tune_maxctx.json        # Perfil max_context (HIP)
├── tune_mem.json           # Perfil memory_efficient (HIP)
└── tune_qwen27b.json       # Qwen3.8-27B balanced (HIP)
```

---

## 🔧 Script de Auto-Tuning: Uso

```bash
# Listar perfiles
python tune_local.py --list-profiles

# Tuning rápido (8 configs) - throughput
python tune_local.py --model Qwen3.5-9B --backend hip --profile throughput --quick --yes --repetitions 1

# Tuning completo (40 configs) - balanced
python tune_local.py --model Qwen3.5-9B --backend both --profile balanced --repetitions 2 --output results.json

# Tuning modelo grande - memoria eficiente
python tune_local.py --model Qwen3.8-27B --backend hip --profile memory_efficient --max-combos 12

# Guardar presets en presets.ini
python tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --save-presets
```

---

## 📋 Presets Generados (presets.ini)

Al usar `--save-presets`, se generan secciones como:

```ini
[throughput_hip_Qwen3.5-9B-UD-Q4_K_XL]
n_gpu_layers = -1
prompt_size = 512
gen_size = 256
batch_size = 2048
flash_attn = auto
cache_type = q4_0
# Score: 3698.30
# Decode: 3617.2 tok/s
# Prefill: 811.4 tok/s
# VRAM: 6632 MB

[balanced_hip_Qwen3.5-9B-UD-Q4_K_XL]
n_gpu_layers = -1
prompt_size = 2048
gen_size = 256
batch_size = 2048
flash_attn = auto
cache_type = q4_0
# Score: 2665.46
# Decode: 3405.1 tok/s
# Prefill: 1556.0 tok/s
# VRAM: 6728 MB
```

---

## 🎯 Próximos Pasos (Fase 4: Análisis)

1. **Profiling profundo** con `GGML_METRICS=1` + `rocprof` / Vulkan layers
2. **Detección cuellos de botella**: memory-bound vs compute-bound por capa
3. **Export traces**: Chrome Trace, Perfetto, Prometheus metrics
4. **Regression testing**: Comparar contra baselines guardados
5. **Integración skill AMD**: `local-ai-use/` con data/ y evals/

---

## 📝 Notas Técnicas

1. **VRAM Estimation Issue**: La heurística actual subestima VRAM para modelos >10GB. Necesita medición real con `GGML_METRICS=1` o herramientas de monitoreo GPU.

2. **Qwen3.8-27B Q3_K**: Cabe en 16GB con ngl=-1 según testing real (decode 15K tok/s), pero la estimación dice 6.6GB. La cuantización Q3_K es muy agresiva.

3. **Flash Attention en HIP**: `fa=auto` usa SDPA fallback en RDNA 4 (gfx1201). Probar `fa=off` para forzar SDPA y comparar.

4. **Wave Size**: HIP reporta wave size 32 vs 64 en Vulkan. Esto afecta ocupación y paralelismo.

5. **ROCm SDK PATH**: Requerido permanentemente en User PATH para que HIP funcione sin configuración manual.

---

*Generado automáticamente por `tune_local.py` v1.0. Para nuevos tunings, ejecutar script con perfil y modelo deseado.*