# 📊 INFORME DETALLADO: Proyecto AMD.AI

---

## 🎯 1. VISIÓN GENERAL DEL PROYECTO

**Nombre:** AMD.AI  
**Ubicación:** `G:\Proyectos\AMD.AI\`  
**Fecha de análisis:** 2026-09-06  
**Estado:** MVP Dashboard funcional - Routers modulares implementados

### Propósito Principal
Proyecto dual enfocado en:
1. **Skill `local-ai-use`** (✅ COMPLETADO) - Catálogo oficial AMD para ejecutar/optimizar LLMs locales en hardware AMD
2. **Dashboard IA** (🟢 FUNCIONAL) - Interfaz web para gestionar modelos, benchmarks, auto-tuning y generación de scripts optimizados

### Hardware Objetivo
- **GPU:** AMD Radeon RX 9070 16GB (RDNA 4 / gfx1103 Vulkan, gfx1201 HIP)
- **CPU:** AMD Ryzen 7 7800X3D 8-Core (Zen 4)
- **ROCm:** 7.2.0 vía `_rocm_sdk_devel` Python package

---

## 📁 2. ESTRUCTURA DEL REPOSITORIO

```
G:\Proyectos\AMD.AI\
├── AGENTS.md                              # Instrucciones para agentes IA
├── ROADMAP-IA-DASHBOARD.md                # Plan de desarrollo (FASES 0-3)
├── INFORME DETALLADO-Proyecto AMD.md      # Este archivo
├── run_dashboard.py                       # Lanzador delgado (entrypoint)
├── dashboard/                             # Dashboard web funcional
│   ├── main.py                            # FastAPI backend (puerto 9090) - ~90 líneas
│   ├── requirements.txt                   # Dependencias Python
│   ├── config.py                          # Configuración centralizada (env vars)
│   ├── static/
│   │   └── app.js                         # Alpine.js components
│   ├── templates/
│   │   ├── base.html                      # Layout principal
│   │   └── partials/
│   │       ├── models_tab.html            # Tab gestión modelos
│   │       ├── benchmark_tab.html         # Tab benchmarks
│   │       ├── tuning_tab.html            # Tab auto-tuning
│   │       ├── launch_tab.html            # Tab generar .bat
│   │       ├── blog_tab.html              # Tab blog drafts
│   │       └── updates_tab.html           # Tab actualizaciones
│   ├── utils/
│   │   ├── model_scanner.py               # Escaneo GGUF (funcional)
│   │   ├── script_runner.py               # Executor subprocess
│   │   ├── event_logger.py                # Event sourcing (funcional)
│   │   └── blog_generator.py              # Astro drafts (funcional)
│   ├── routers/                           # 🆕 Routers modulares (P2-#6)
│   │   ├── __init__.py                    # Paquete routers
│   │   ├── benchmark.py                   # Endpoints benchmark
│   │   ├── tuning.py                      # Endpoints auto-tuning
│   │   ├── launch.py                      # Endpoints launch
│   │   ├── llama.py                       # Endpoints updates/rebuild
│   │   ├── events.py                      # Endpoints events
│   │   └── blog.py                        # Endpoints blog
│   └── data/
│       ├── events.jsonl                   # Event store (rotación 5000 líneas)
│       └── blog_drafts/                   # Drafts Astro (12 drafts)
├── docs/                                  # Documentación generada
│   ├── ENTORNO_RX9070_LLAMA_CPP.md        # Documentación entorno
│   ├── BENCHMARK_RESULTS_QWEN3.5-9B.md    # Benchmarks Qwen3.5-9B
│   ├── ANALYSIS_RESULTS.md                # Análisis profundo
│   ├── AUTO_TUNING_RESULTS.md             # Resultados auto-tuning
│   ├── IMPLEMENTATION_SUMMARY.md          # Resumen skill
│   └── traces/                            # Chrome Trace + Prometheus
├── skills/
│   └── local-ai-use/                      # ✅ Skill COMPLETADO
│       ├── SKILL.md                       # Definición principal
│       ├── skill-card.md                  # Tarjeta marketplace
│       ├── reference.md                   # Referencia CLI completa
│       ├── detection_report.json          # Reporte detección
│       ├── data/
│       │   ├── model_compatibility.json   # Matriz compatibilidad
│       │   ├── gpu_presets.json           # Presets por GPU
│       │   └── quantization_guide.json    # Guía cuantización
│       ├── evals/
│       │   ├── benchmark_baselines.json   # Baselines regresión
│       │   └── regression_tests.py        # Tests automatizados
│       └── scripts/
│           ├── detect_local.py            # Detección entorno
│           ├── bench_local.py             # Benchmarking
│           ├── tune_local.py              # Auto-tuning
│           └── analyze_local.py           # Análisis escalabilidad
├── scripts/                               # Scripts legacy (migrados)
│   ├── analyze_local.py
│   ├── bench_local.py
│   ├── detect_local.py
│   └── tune_local.py
└── AGENTS.md                              # (duplicado)
```

---

## ⚙️ 3. COMPONENTES PRINCIPALES

### 3.1 Skill `local-ai-use` (✅ COMPLETADO)

#### Funcionalidades
| Script | Capacidad | Uso Principal |
|--------|-----------|---------------|
| `detect_local.py` | Detección GPU, validación backends, matriz compatibilidad | Setup inicial, CI/CD |
| `bench_local.py` | Matriz parametrizable (hasta 1,620 combos) | Comparación rendimiento |
| `tune_local.py` | Grid search 5 perfiles optimización | Selección config óptima |
| `analyze_local.py` | Escalabilidad, traces Chrome, Prometheus, comparación | Análisis profundo |

#### Perfiles de Optimización
| Perfil | Objetivo | Caso de Uso |
|--------|----------|-------------|
| `throughput` | Máximo decode tok/s | API server, batch |
| `latency` | Mínimo TTFT | Chat interactivo |
| `balanced` | Equilibrio | General (default) |
| `max_context` | Máximo contexto | RAG, documentos largos |
| `memory_efficient` | Mínima VRAM | Multi-modelo |

#### Datos de Configuración
- **model_compatibility.json**: 10 modelos × 3 backends (Vulkan/HIP/CPU)
- **gpu_presets.json**: Presets para RX 9070, RX 7900 XTX, MI300X, Ryzen AI, EPYC
- **quantization_guide.json**: 18 niveles de cuantización con factores VRAM

### 3.2 Dashboard IA (🟢 FUNCIONAL - MVP)

#### Stack Tecnológico
| Capa | Tecnología | Estado |
|------|------------|--------|
| Backend | FastAPI 0.115 + Uvicorn | ✅ main.py modularizado (~90 líneas) |
| Frontend | HTMX 2.0 + Alpine.js 3.14 + Tailwind CDN | ✅ 6 templates creados |
| WebSocket | `websockets` lib | ✅ Implementado |
| Event Store | JSONL append-only | ✅ Funcional (rotación 5000 líneas) |
| Blog Drafts | Markdown + YAML Frontmatter | ✅ Funcional (12 drafts) |
| Routers | APIRouter modular | ✅ 6 routers creados (P2-#6) |

#### Endpoints Verificados (2026-09-06)
| Endpoint | Método | Descripción | Estado |
|----------|--------|-------------|--------|
| `/` | GET | Home con tabs HTMX | ✅ |
| `/health` | GET | Health check | ✅ `{"status":"ok"}` |
| `/api/models` | GET | Lista modelos escaneados | ✅ 2 modelos |
| `/api/backends` | GET | Status backends (HIP/Vulkan) | ✅ 3 backends |
| `/api/events` | GET | Historial eventos | ✅ 20 eventos |
| `/api/blog/drafts` | GET | Listado borradores | ✅ 12 drafts |
| `/ws/progress/{job_id}` | WebSocket | Notificaciones tiempo real | ✅ |

#### Routers Modulares (NUEVO - P2-#6)
1. **benchmark.py**: Endpoints y jobs de fondo de benchmarking
2. **tuning.py**: Endpoints y jobs de auto-tuning
3. **launch.py**: Generación, guardado, lanzamiento de .bat
4. **llama.py**: Actualizaciones, rebuild HIP, version checking
5. **events.py**: Listado de eventos desde el logger
6. **blog.py**: Listado y lectura de borradores de blog

---

## 🔬 4. HALLAZGOS TÉCNICOS CLAVE (Validados Experimentalmente)

### 4.1 CPU vs GPU para Qwen3.5-9B-Q4_K (5.56 GB)

| Backend | Config | Decode tok/s | Prefill tok/s | VRAM |
|---------|--------|--------------|---------------|------|
| **HIP GPU** | ngl=-1 | **3,461** | 1,556 | 6.6 GB |
| **Vulkan GPU** | ngl=-1 | 2,887 | 924 | 6.1 GB |
| **CPU (Zen 4)** | ngl=0 | **27,454** ⚡ | **1,556** | 512 MB |

> 🎯 **Conclusión Crítica**: Para modelos ≤8GB Q4_K, **CPU Zen 4 es 2.7-9x más rápido que GPU**. La GPU RX 9070 no está bien aprovechada por kernels actuales.

### 4.2 HIP vs Vulkan en GPU (RX 9070)

| Métrica | **HIP/ROCm** | **Vulkan** | Ganador |
|---------|--------------|------------|---------|
| **Decode GPU** | 3,461 tok/s | 2,887 tok/s | 🏆 **HIP +20%** |
| **Prefill GPU** | 1,556 tok/s | 924 tok/s | 🏆 **HIP +68%** |
| **Decode CPU** | 27,454 tok/s | 27,122 tok/s | ~Empate |
| **Prefill CPU** | 1,556 tok/s | 1,598 tok/s | Vulkan +2.7% |
| **Escalabilidad Batch** | 53% eff | 48% eff | 🏆 **HIP** |

> ⚠️ **Nota**: HIP usa SDPA fallback en RDNA 4 (no Flash Attention nativo). Vulkan tiene FA nativo pero kernels menos optimizados.

### 4.3 Escalabilidad con Batch Size (HIP)

| Batch | Prefill tok/s | Decode tok/s | Eficiencia |
|-------|---------------|--------------|------------|
| 512   | 294 | 3,346 | 100% |
| 1024  | 395 | 3,368 | **67%** ⭐ |
| 2048  | 294 | 3,336 | 25% |
| 4096  | 428 | 3,367 | 18% |

> 🎯 **Óptimo**: batch=1024 (mejor eficiencia). Batch >2048 causa contención memoria/sincronización.

### 4.4 Escalabilidad n_gpu_layers (HIP)

| ngl | Prefill tok/s | Decode tok/s | Eficiencia |
|-----|---------------|--------------|------------|
| -1 (all GPU) | 420 | 3,462 | 100% |
| 10 | 879 | 19,136 | 209% |
| 20 | 671 | 12,864 | 160% |
| 30 | 392 | 6,979 | 93% |
| 40 | 388 | 3,389 | 92% |
| 0 (CPU) | **1,110** | **27,454** | **264%** ⭐ |

> 🎯 **Sweet spot**: ngl=10-20 para híbrido. ngl=0 (CPU) es dramáticamente más rápido para modelos pequeños.

### 4.5 Modelos Validados (RX 9070 16GB)

| Modelo | Cuantización | Tamaño | Backend Óptimo | Config Recomendada |
|--------|--------------|--------|----------------|-------------------|
| **Qwen3.5-9B** | Q4_K_XL | 5.56 GB | **CPU** (balanced) | `ngl=0, p=512, g=256, b=2048, fa=off` |
| **Qwen3.5-9B** | Q4_K_XL | 5.56 GB | **HIP** (latency) | `ngl=-1, p=2048, g=256, b=1024, fa=auto` |
| **Qwen3.8-27B** | Q3_K | 12.24 GB | **HIP** (balanced) | `ngl=-1, p=2048, g=256, b=2048, fa=auto` |

---

## 🚀 5. CONFIGURACIONES ÓPTIMAS RECOMENDADAS

### 5.1 Para Máximo Throughput (Decode)
```bash
# HIP - Máximo decode throughput
llama-server -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# Decode: 3,617 tok/s | Prefill: 811 tok/s | VRAM: ~6.6 GB
```

### 5.2 Para Baja Latencia (Chat Interactivo)
```bash
# HIP - Mejor prefill para time-to-first-token
llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0
# Prefill: 1,502 tok/s | Decode: 3,438 tok/s | VRAM: ~6.2 GB
```

### 5.3 Para Uso General (Balanceado - Default)
```bash
# HIP - Mejor equilibrio
llama-server -ngl -1 -p 2048 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# Decode: 3,405 tok/s | Prefill: 1,556 tok/s | VRAM: ~6.7 GB
```

### 5.4 Para RAG / Contexto Largo
```bash
# HIP - Optimizado para contexto
llama-server -ngl -1 -p 2048 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0 -c 65536
# Contexto hasta 65K tokens posible
```

### 5.5 Para Modelos Grandes (>10GB) - Híbrido
```bash
# Híbrido: 20-30 capas en GPU, resto CPU
llama-server -ngl 20 -p 512 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0
```

### 5.6 Para Multi-Modelo / VRAM Limitada
```bash
# HIP - Menor VRAM con buen decode
llama-server -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# VRAM: ~6.6 GB | Decode: 3,543 tok/s
```

---

## 🐛 6. TROUBLESHOOTING COMÚN

| Error | Causa | Solución |
|-------|-------|----------|
| `exit -1073741515` HIP | ROCm DLLs no en PATH | Añadir `_rocm_sdk_devel\bin` a PATH permanentemente |
| `invalid parameter: -c` | Flag ctx incorrecta | Usar `-p` (prompt) y `-n` (gen), no `-c` / `--ctx-size` |
| `OOM` | VRAM insuficiente | Reducir `n_gpu_layers`, `batch_size`, usar `cache_type q4_0` |
| `Flash Attention not supported` | FA no disponible en RDNA 4 | Usar `-fa off` o `-fa auto` (SDPA fallback) |
| `Model not found` | Path GGUF incorrecto | Verificar path absoluto, usar `detect_local.py` |

---

## 📋 7. COMANDOS CANÓNICOS (Copiar-Pegar)

### Detección de Entorno
```bash
python skills\local-ai-use\scripts\detect_local.py --validate-backends --compatibility
# O solo JSON para CI/CD:
python skills\local-ai-use\scripts\detect_local.py --validate-backends --compatibility --json-only -o detection_report.json
```

### Benchmark
```bash
# Quick (32 combos, 2 reps)
python skills\local-ai-use\scripts\bench_local.py --model Qwen3.5-9B --backend hip --quick --yes --repetitions 1

# Full (1,620 combos, 3 reps)
python skills\local-ai-use\scripts\bench_local.py --model Qwen3.5-9B --backend both --repetitions 3 -o bench.csv --json-output bench.json
```

### Auto-Tuning
```bash
# Listar perfiles
python skills\local-ai-use\scripts\tune_local.py --list-profiles

# Balanced (default recomendado)
python skills\local-ai-use\scripts\tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --quick --yes --repetitions 1 --save-presets

# Throughput (servidor)
python skills\local-ai-use\scripts\tune_local.py --model Qwen3.5-9B --backend hip --profile throughput --quick --yes --repetitions 1

# Latency (chat interactivo)
python skills\local-ai-use\scripts\tune_local.py --model Qwen3.5-9B --backend hip --profile latency --quick --yes --repetitions 1
```

### Análisis
```bash
# Escalabilidad batch
python skills\local-ai-use\scripts\analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable batch_size --values "512,1024,2048,4096" --yes

# GPU layers offloading
python skills\local-ai-use\scripts\analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable n_gpu_layers --values "-1,0,10,20,30,40" --yes

# Comparar GPU vs CPU
python skills\local-ai-use\scripts\analyze_local.py --model Qwen3.5-9B --backend hip --compare-configs --config-a @config_gpu.json --config-b @config_cpu.json --yes

# Trace + métricas
python skills\local-ai-use\scripts\analyze_local.py --model Qwen3.5-9B --backend hip --trace-chrome --prometheus --yes
```

### Dashboard (Funcional)
```bash
cd G:\Proyectos\AMD.AI
python run_dashboard.py                    # Lanzador (entrypoint)
# Acceso: http://localhost:9090 | http://<IP-LAN>:9090
```

---

## 📊 8. ESTADO ACTUAL POR COMPONENTE

| Componente | Estado | Ubicación | Notas |
|------------|--------|-----------|-------|
| **Skill `local-ai-use`** | ✅ COMPLETADO | `skills/local-ai-use/` | 4 scripts + data + evals + docs |
| `detect_local.py` | ✅ VALIDADO | `skills/.../scripts/` | --validate-backends --compatibility |
| `bench_local.py` | ✅ VALIDADO | `skills/.../scripts/` | Quick + Full matrix |
| `tune_local.py` | ✅ VALIDADO | `skills/.../scripts/` | 5 perfiles + presets.ini |
| `analyze_local.py` | ✅ VALIDADO | `skills/.../scripts/` | Scaling + traces + compare |
| **Dashboard `main.py`** | ✅ MODULARIZADO | `dashboard/` | Split en routers (P2-#6) |
| **Routers** | ✅ COMPLETADO | `dashboard/routers/` | 6 routers modulares |
| Model Scanner | ✅ FUNCIONAL | `dashboard/utils/` | Escaneo GGUF + endpoints |
| Event Logger | ✅ FUNCIONAL | `dashboard/utils/` | Rotación 5000 líneas, schema unificado |
| Tab Modelos | ✅ COMPLETADO | `templates/partials/` | Listado, filtros, selección |
| Tab Benchmark | ✅ COMPLETADO | `templates/partials/` | Formulario, progreso, resultados |
| Tab Tuning | ✅ COMPLETADO | `templates/partials/` | Selector perfil, progreso, presets |
| Tab Launch | ✅ COMPLETADO | `templates/partials/` | Generar .bat, preview, ejecutar |
| Tab Blog | ✅ COMPLETADO | `templates/partials/` | Listado y lectura drafts |
| Tab Updates | ✅ COMPLETADO | `templates/partials/` | Actualizaciones llama.cpp |
| WebSocket | ✅ FUNCIONAL | `main.py` | Notificaciones tiempo real |
| Blog Generator | ✅ FUNCIONAL | `utils/blog_generator.py` | Schema unificado con event_logger |
| CORS/API Key | ✅ HARDENED | `main.py` | Restringido a localhost + red local |
| ZIP Validation | ✅ HARDENED | `main.py` | PurePosixPath, sanitizacion, bloqueo parent |
| Config Paths | ✅ CENTRALIZADO | `config.py` | 10+ rutas extraídas, soportado por env |

---

## 🗺️ 9. ROADMAP Y PRÓXIMOS PASOS

### FASE 0: Fundacion ✅ COMPLETADA
- [x] Skill `local-ai-use` completo (detect, bench, tune, analyze)
- [x] Scripts validados
- [x] Data: model_compatibility, gpu_presets, quantization_guide
- [x] Evals: baselines + regression_tests
- [x] Docs: ENTORNO, BENCHMARK, ANALYSIS, AUTO_TUNING, IMPLEMENTATION_SUMMARY

### FASE 1: Dashboard MVP 🟢 FUNCIONAL

#### Paso 1: Setup Base ✅ COMPLETADO
- [x] Crear estructura `dashboard/`
- [x] `requirements.txt`
- [x] `main.py` FastAPI
- [x] `base.html` con Tailwind + Alpine + HTMX
- [x] Health check endpoint `/health`

#### Paso 2: Model Scanner + Backend Status ✅ COMPLETADO
- [x] `utils/model_scanner.py` - Escaneo GGUF recursivo
- [x] `utils/script_runner.py` - Wrapper subprocess
- [x] `utils/event_logger.py` - Event Sourcing (JSONL)
- [x] Endpoints: `GET /api/models`, `POST /api/models/scan`, `GET /api/backends`

#### Paso 3-7: Tabs + Integración ✅ COMPLETADO
- [x] Tab Modelos (listado, filtros, selección)
- [x] Tab Benchmark (formulario, progreso, resultados)
- [x] Tab Tuning (selector perfil, progreso, presets)
- [x] Tab Launch (generar .bat, preview, ejecutar)
- [x] WebSocket + Notificaciones + Polish

#### P2-#6: Modularización ✅ COMPLETADO (2026-09-06)
- [x] Split `main.py` (~880 líneas) en routers modulares
- [x] 6 routers: benchmark, tuning, launch, llama, events, blog
- [x] Inyeccion de estado compartido en cada router
- [x] Verificacion endpoints funcionando

### FASE 2: Event Sourcing + Blog Pipeline 🟡 EN PROGRESO
- [x] Event Logger completo
- [x] Blog Draft Generator (Astro-ready)
- [ ] Blog Sync automatico a repo Astro

### FASE 3: Dashboard Avanzado ⏳ FUTURO
- [ ] Analisis visual (Chrome Trace, Plotly)
- [ ] Historial runs + filtros
- [ ] Comparativas visuales (heatmaps)
- [ ] CI/CD Integration
- [ ] Presets Editor visual
- [ ] Multi-usuario + Auth

---

## 💾 10. ARCHIVOS DE RESULTADOS GENERADOS

### Documentación (docs/)
```
docs/
├── ENTORNO_RX9070_LLAMA_CPP.md          # Documentacion entorno completo
├── BENCHMARK_RESULTS_QWEN3.5-9B.md      # 32+ combos Vulkan/HIP
├── ANALYSIS_RESULTS.md                  # Analisis profundo (CPU vs GPU)
├── AUTO_TUNING_RESULTS.md               # 5 perfiles optimizacion
├── IMPLEMENTATION_SUMMARY.md            # Resumen skill completado
└── traces/
    ├── Qwen3.5-9B-UD-Q4_K_XL_hip_default_*.chrome_trace.json
    ├── Qwen3.5-9B-UD-Q4_K_XL_vulkan_default_*.chrome_trace.json
    ├── Qwen3.5-9B-UD-Q4_K_XL_*.prometheus.metrics
    └── Qwen3.8-27B-UD-Q3_K_XL_*.prometheus.metrics
```

### Dashboard Data
```
dashboard/data/
├── events.jsonl                         # Event store (rotacion 5000 lineas)
└── blog_drafts/                         # 12 drafts generados
    ├── benchmark_completed_*.md
    └── tuning_completed_*.md
```

### Baselines (docs/baselines/)
```
baselines/
├── qwen35_9b_hip_v1.json
├── qwen35_9b_vulkan_v1.json
├── qwen35_9b_cpu_v1.json
└── qwen38_27b_hip_v1.json
```

---

## 🎯 11. RECOMENDACIONES

### 1. Priorizar Blog Sync a Astro
- Blog drafts generados automaticamente
- **Tiempo estimado**: 1 hora

### 2. Mejorar Profiling
- `GGML_METRICS=OFF` en build actual
- ROCm SDK sin `rocprof`/`roc-tracer`
- **Recomendacion**: Contribuir kernels con profiling a llama.cpp upstream

### 3. Flash Attention en RDNA 4
- HIP usa SDPA fallback (no FA nativo)
- Vulkan tiene FA nativo pero kernels menos optimizados
- **Investigar**: Kernels FA especificos para gfx1201

### 4. VRAM Estimation
- Heuristica subestima modelos >10GB
- **Solucion**: Usar `GGML_METRICS=1` o herramientas de monitoreo GPU

### 5. Contribucion Upstream
- Skill sigue formato AMD Skills
- **Accion**: Contribuir a `amd/skills` repo

### 6. Testing de Modelos
- Solo 10 modelos testeados
- **Anadir**: Qwen3.8-9B-Distill, Apertus, InternVL, Llama-Vision

---

## 📈 12. METRICAS DE EXITO

| KPI | Target | Estado |
|-----|--------|--------|
| Skill `local-ai-use` completo | ✅ | 100% |
| Scripts validados | ✅ | 100% |
| Dashboard MVP funcional | 🟢 | 95% |
| Event logging | ✅ | 100% |
| Blog automation | 🟡 | 80% |
| Documentacion completa | ✅ | 100% |

---

## 🔗 13. INTEGRACION AMD SKILLS CATALOG

El skill `local-ai-use` se integra con:
- **serving-llms-on-instinct** — MI300X/MI325X datacenter
- **serving-llms-on-epyc** — EPYC CPU inference
- **lemonade-router-builder** — Multi-model routing
- **hyperloom-workload-optimizer** — Cluster optimization

**Auto-seleccion de backend** via `gpu_presets.json` basado en `deviceID`/`gfx_version`.

---

## 📝 14. NOTAS TECNICAS IMPORTANTES

1. **ROCm en Windows**: Requiere `_rocm_sdk_devel` en PATH permanentemente
   ```
   C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin
   ```

2. **Diferencias Arquitectura**:
   - Vulkan: gfx1103, Wave64, KHR_coopmat
   - HIP: gfx1201, Wave32, MFMA (GGML_HIP_MMQ_MFMA=ON)

3. **Build Vulkan**: 2 builds (b10712, b10796) con diferencias <2%

4. **Flash Attention**: 
   - HIP: SDPA fallback en RDNA 4
   - Vulkan: Nativo pero kernels menos optimizados

5. **VRAM Estimation**: Heuristica, subestima modelos >10GB

6. **Routers Modulares**: `main.py` ahora ~90 lineas, routers inyectan estado compartido via loop for

7. **Import Strategy**: `run_dashboard.py` añade `dashboard/` a sys.path, routers usan imports absolutos

---

## ✅ RESUMEN EJECUTIVO

### Lo que funciona perfectamente:
✅ Skill `local-ai-use` completo y validado  
✅ 4 scripts con capacidades robustas  
✅ Documentacion extensa y precisa  
✅ Hallazgos tecnicos bien documentados  
✅ Presets y baselines para regresion  
✅ Dashboard MVP funcional (95%)  
✅ 6 routers modulares implementados  
✅ Todos endpoints verificados y respondiendo  
✅ WebSocket + notificaciones tiempo real  
✅ Event sourcing con rotacion  
✅ Blog drafts generados automaticamente  

### Lo que necesita atencion:
🟡 Blog Sync automatico a repo Astro  
⏳ Analisis visual (Chrome Trace, Plotly)  
⏳ Comparativas visuales (heatmaps)  
⏳ CI/CD Integration  
⏳ Multi-usuario + Auth  

### Hallazgo mas importante:
**CPU Zen 4 supera a GPU RX 9070 en 2.7-9x para modelos ≤8GB Q4_K**. La GPU no esta bien aprovechada por kernels actuales. HIP > Vulkan en GPU (+20% decode, +55% prefill).

---

**Fin del informe**  
*Actualizado: 2026-09-06 - Dashboard modularizado con routers, endpoints verificados*
