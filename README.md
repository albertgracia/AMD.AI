# AMD.AI
Proyecto dual enfocado en:  Skill local-ai-use (✅ COMPLETADO) - Catálogo oficial AMD para ejecutar/optimizar LLMs locales en hardware AMD Dashboard IA (🟡 EN PROGRESO) - Interfaz web para gestionar modelos, benchmarks, auto-tuning y generación de scripts optimizados

🎯 1. VISIÓN GENERAL DEL PROYECTO
Nombre: AMD.AI
Ubicación: G:\Proyectos\AMD.AI\
Fecha de análisis: 2026-09-05
Estado: En progreso - MVP Dashboard en desarrollo

Propósito Principal
Proyecto dual enfocado en:

Skill local-ai-use (✅ COMPLETADO) - Catálogo oficial AMD para ejecutar/optimizar LLMs locales en hardware AMD
Dashboard IA (🟡 EN PROGRESO) - Interfaz web para gestionar modelos, benchmarks, auto-tuning y generación de scripts optimizados
Hardware Objetivo
GPU: AMD Radeon RX 9070 16GB (RDNA 4 / gfx1103 Vulkan, gfx1201 HIP)
CPU: AMD Ryzen 7 7800X3D 8-Core (Zen 4)
ROCm: 7.2.0 vía _rocm_sdk_devel Python package


📁 2. ESTRUCTURA DEL REPOSITORIO
text

G:\Proyectos\AMD.AI\
├── AGENTS.md                              # Instrucciones para agentes IA
├── ROADMAP-IA-DASHBOARD.md                # Plan de desarrollo (FASES 0-3)
├── dashboard/                             # Dashboard web en desarrollo
│   ├── main.py                            # FastAPI backend (puerto 9090)
│   ├── requirements.txt                   # Dependencias Python
│   ├── static/
│   │   └── app.js                         # Alpine.js components
│   ├── templates/
│   │   ├── base.html                      # Layout principal
│   │   └── partials/
│   │       ├── models_tab.html            # Tab gestión modelos
│   │       ├── benchmark_tab.html         # Tab benchmarks
│   │       ├── tuning_tab.html            # Tab auto-tuning
│   │       └── launch_tab.html            # Tab generar .bat
│   ├── utils/
│   │   ├── model_scanner.py               # Escaneo GGUF (pendiente)
│   │   ├── script_runner.py               # Executor subprocess
│   │   ├── event_logger.py                # Event sourcing (pendiente)
│   │   └── blog_generator.py              # Astro drafts (pendiente)
│   └── data/
│       ├── events.jsonl                   # Event store (pendiente)
│       └── blog_drafts/                   # Drafts Astro (pendiente)
├── docs/                                  # Documentación generada
│   ├── ENTORNO_RX9070_LLAMA_CPP.md        # Documentación entorno
│   ├── BENCHMARK_RESULTS_QWEN3.5-9B.md    # Benchmarks Qwen3.5-9B
│   ├── ANALYSIS_RESULTS.md                # Análisis profundo
│   ├── AUTO_TUNING_RESULTS.md             # Resultados auto-tuning
│   ├── IMPLEMENTATION_SUMMARY.md          # Resumen skill
│   ├── BENCHMARK_RESULTS_QWEN3.5-9B.md    # Detalles benchmarks
│   ├── tune_*.json                        # Configuraciones tuning
│   ├── analyze_*.json                     # Resultados análisis
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
├── AGENTS.md                              # (duplicado)
├── encoding_check.txt                     # Verificación encoding
├── fix_indent.py                          # Utilidad indentación
├── *.url                                  # Enlaces a documentación AMD
└── skills/local-ai-use/evals/regression_tests.py



⚙️ 3. COMPONENTES PRINCIPALES


3.1 Skill local-ai-use (✅ COMPLETADO)

Funcionalidades
Script	Capacidad	Uso Principal
detect_local.py	Detección GPU, validación backends, matriz compatibilidad	Setup inicial, CI/CD
bench_local.py	Matriz parametrizable (hasta 1,620 combos)	Comparación rendimiento
tune_local.py	Grid search 5 perfiles optimización	Selección config óptima
analyze_local.py	Escalabilidad, traces Chrome, Prometheus, comparación	Análisis profundo
Perfiles de Optimización
Perfil	Objetivo	Caso de Uso
throughput	Máximo decode tok/s	API server, batch
latency	Mínimo TTFT	Chat interactivo
balanced	Equilibrio	General (default)
max_context	Máximo contexto	RAG, documentos largos
memory_efficient	Mínima VRAM	Multi-modelo
Datos de Configuración
model_compatibility.json: 10 modelos × 3 backends (Vulkan/HIP/CPU)
gpu_presets.json: Presets para RX 9070, RX 7900 XTX, MI300X, Ryzen AI, EPYC
quantization_guide.json: 18 niveles de cuantización con factores VRAM

3.2 Dashboard IA (🟡 EN PROGRESO - MVP)


Stack Tecnológico
Capa	Tecnología	Estado
Backend	FastAPI 0.115 + Uvicorn	✅ main.py creado
Frontend	HTMX 2.0 + Alpine.js 3.14 + Tailwind CDN	✅ Templates creados
WebSocket	websockets lib	⏳ Pendiente
Event Store	JSONL append-only	⏳ Pendiente
Blog Drafts	Markdown + YAML Frontmatter	⏳ Pendiente
Endpoints Planificados
Endpoint	Método	Descripción
/	GET	Home con tabs HTMX
/health	GET	Health check
/api/models	GET	Lista modelos escaneados
/api/models/scan	POST	Escaneo GGUF recursivo
/api/backends	GET	Status backends (HIP/Vulkan/CPU)
/api/benchmark/start	POST	Iniciar benchmark (background)
/api/benchmark/status/{job_id}	GET	Polling progreso
/api/benchmark/results/{job_id}	GET	Resultados JSON/CSV
/api/tune/start	POST	Iniciar auto-tuning
/api/tune/results/{job_id}	GET	Resultados tuning
/api/launch/generate	POST	Generar .bat optimizado
/ws/progress/{job_id}	WebSocket	Notificaciones tiempo real
Partial Templates (4 Tabs)
models_tab.html: Lista modelos, filtros, selección, export CSV
benchmark_tab.html: Formulario benchmark, progreso, resultados
tuning_tab.html: Selector perfil, progreso, resultados presets
launch_tab.html: Selector modelo/preset, preview .bat, ejecutar


🔬 4. HALLAZGOS TÉCNICOS CLAVE (Validados Experimentalmente)
4.1 CPU vs GPU para Qwen3.5-9B-Q4_K (5.56 GB)
Backend	Config	Decode tok/s	Prefill tok/s	VRAM
HIP GPU	ngl=-1	3,461	1,556	6.6 GB
Vulkan GPU	ngl=-1	2,887	924	6.1 GB
CPU (Zen 4)	ngl=0	27,454 ⚡	1,556	512 MB


🎯 Conclusión Crítica: Para modelos ≤8GB Q4_K, CPU Zen 4 es 2.7-9x más rápido que GPU. La GPU RX 9070 no está bien aprovechada por kernels actuales.

4.2 HIP vs Vulkan en GPU (RX 9070)
Métrica	HIP/ROCm	Vulkan	Ganador
Decode GPU	3,461 tok/s	2,887 tok/s	🏆 HIP +20%
Prefill GPU	1,556 tok/s	924 tok/s	🏆 HIP +68%
Decode CPU	27,454 tok/s	27,122 tok/s	~Empate
Prefill CPU	1,556 tok/s	1,598 tok/s	Vulkan +2.7%
Escalabilidad Batch	53% eff	48% eff	🏆 HIP
⚠️ Nota: HIP usa SDPA fallback en RDNA 4 (no Flash Attention nativo). Vulkan tiene FA nativo pero kernels menos optimizados.

4.3 Escalabilidad con Batch Size (HIP)
Batch	Prefill tok/s	Decode tok/s	Eficiencia
512	294	3,346	100%
1024	395	3,368	67% ⭐
2048	294	3,336	25%
4096	428	3,367	18%


🎯 Óptimo: batch=1024 (mejor eficiencia). Batch >2048 causa contención memoria/sincronización.

4.4 Escalabilidad n_gpu_layers (HIP)
ngl	Prefill tok/s	Decode tok/s	Eficiencia
-1 (all GPU)	420	3,462	100%
10	879	19,136	209%
20	671	12,864	160%
30	392	6,979	93%
40	388	3,389	92%
0 (CPU)	1,110	27,454	264% ⭐


🎯 Sweet spot: ngl=10-20 para híbrido. ngl=0 (CPU) es dramáticamente más rápido para modelos pequeños.

4.5 Modelos Validados (RX 9070 16GB)
Modelo	Cuantización	Tamaño	Backend Óptimo	Config Recomendada
Qwen3.5-9B	Q4_K_XL	5.56 GB	CPU (balanced)	ngl=0, p=512, g=256, b=2048, fa=off
Qwen3.5-9B	Q4_K_XL	5.56 GB	HIP (latency)	ngl=-1, p=2048, g=256, b=1024, fa=auto
Qwen3.8-27B	Q3_K	12.24 GB	HIP (balanced)	ngl=-1, p=2048, g=256, b=2048, fa=auto


🚀 5. CONFIGURACIONES ÓPTIMAS RECOMENDADAS
5.1 Para Máximo Throughput (Decode)
bash

# HIP - Máximo decode throughput
llama-server -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# Decode: 3,617 tok/s | Prefill: 811 tok/s | VRAM: ~6.6 GB
5.2 Para Baja Latencia (Chat Interactivo)
bash

# HIP - Mejor prefill para time-to-first-token
llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0
# Prefill: 1,502 tok/s | Decode: 3,438 tok/s | VRAM: ~6.2 GB
5.3 Para Uso General (Balanceado - Default)
bash

# HIP - Mejor equilibrio
llama-server -ngl -1 -p 2048 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# Decode: 3,405 tok/s | Prefill: 1,556 tok/s | VRAM: ~6.7 GB
5.4 Para RAG / Contexto Largo
bash

# HIP - Optimizado para contexto
llama-server -ngl -1 -p 2048 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0 -c 65536
# Contexto hasta 65K tokens posible
5.5 Para Modelos Grandes (>10GB) - Híbrido
bash

# Híbrido: 20-30 capas en GPU, resto CPU
llama-server -ngl 20 -p 512 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0
5.6 Para Multi-Modelo / VRAM Limitada
bash

# HIP - Menor VRAM con buen decode
llama-server -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0
# VRAM: ~6.6 GB | Decode: 3,543 tok/s



🐛 6. TROUBLESHOOTING COMÚN
Error	Causa	Solución
exit -1073741515 HIP	ROCm DLLs no en PATH	Añadir _rocm_sdk_devel\bin a PATH permanentemente
invalid parameter: -c	Flag ctx incorrecta	Usar -p (prompt) y -n (gen), no -c / --ctx-size
OOM	VRAM insuficiente	Reducir n_gpu_layers, batch_size, usar cache_type q4_0
Flash Attention not supported	FA no disponible en RDNA 4	Usar -fa off o -fa auto (SDPA fallback)
Model not found	Path GGUF incorrecto	Verificar path absoluto, usar detect_local.py


📋 7. COMANDOS CANÓNICOS (Copiar-Pegar)
Detección de Entorno
bash

python skills\local-ai-use\scripts\detect_local.py --validate-backends --compatibility
# O solo JSON para CI/CD:
python skills\local-ai-use\scripts\detect_local.py --validate-backends --compatibility --json-only -o detection_report.json
Benchmark
bash

# Quick (32 combos, 2 reps)
python skills\local-ai-use\scripts\bench_local.py --model Qwen3.5-9B --backend hip --quick --yes --repetitions 1

# Full (1,620 combos, 3 reps)
python skills\local-ai-use\scripts\bench_local.py --model Qwen3.5-9B --backend both --repetitions 3 -o bench.csv --json-output bench.json
Auto-Tuning
bash

# Listar perfiles
python skills\local-ai-use\scripts\tune_local.py --list-profiles

# Balanced (default recomendado)
python skills\local-ai-use\scripts\tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --quick --yes --repetitions 1 --save-presets

# Throughput (servidor)
python skills\local-ai-use\scripts\tune_local.py --model Qwen3.5-9B --backend hip --profile throughput --quick --yes --repetitions 1

# Latency (chat interactivo)
python skills\local-ai-use\scripts\tune_local.py --model Qwen3.5-9B --backend hip --profile latency --quick --yes --repetitions 1
Análisis
bash

# Escalabilidad batch
python skills\local-ai-use\scripts\analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable batch_size --values "512,1024,2048,4096" --yes

# GPU layers offloading
python skills\local-ai-use\scripts\analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable n_gpu_layers --values "-1,0,10,20,30,40" --yes

# Comparar GPU vs CPU
python skills\local-ai-use\scripts\analyze_local.py --model Qwen3.5-9B --backend hip --compare-configs --config-a @config_gpu.json --config-b @config_cpu.json --yes

# Trace + métricas
python skills\local-ai-use\scripts\analyze_local.py --model Qwen3.5-9B --backend hip --trace-chrome --prometheus --yes
Dashboard (Cuando Esté Listo)
bash

cd dashboard
pip install -r requirements.txt
python main.py                    # Desarrollo
uvicorn main:app --host 0.0.0.0 --port 9090 --reload  # Producción LAN

# Acceso: http://localhost:9090 | http://<IP-LAN>:9090


📊 8. ESTADO ACTUAL POR COMPONENTE
Componente	Estado	Ubicación	Notas
Skill local-ai-use	✅ COMPLETADO	skills/local-ai-use/	4 scripts + data + evals + docs
detect_local.py	✅ VALIDADO	skills/.../scripts/	--validate-backends --compatibility
bench_local.py	✅ VALIDADO	skills/.../scripts/	Quick + Full matrix
tune_local.py	✅ VALIDADO	skills/.../scripts/	5 perfiles + presets.ini
analyze_local.py	✅ VALIDADO	skills/.../scripts/	Scaling + traces + compare
Dashboard main.py	⏳ EN PROGRESO	dashboard/	Paso 1-2: Setup base + utils
Model Scanner	⏳ PENDIENTE	dashboard/utils/	Paso 2
Event Logger	⏳ PENDIENTE	dashboard/utils/	Paso 2 (crítico)
Tab Modelos	⏳ PENDIENTE	templates/partials/	Paso 3
Tab Benchmark	⏳ PENDIENTE	templates/partials/	Paso 4
Tab Tuning	⏳ PENDIENTE	templates/partials/	Paso 5
Tab Launch	⏳ PENDIENTE	templates/partials/	Paso 6
WebSocket	⏳ PENDIENTE	main.py	Paso 7
Blog Generator	⏳ PENDIENTE	utils/blog_generator.py	Paso 2


🗺️ 9. ROADMAP Y PRÓXIMOS PASOS

FASE 0: Fundacion ✅ COMPLETADA
 Skill local-ai-use completo (detect, bench, tune, analyze)
 Scripts validados
 Data: model_compatibility, gpu_presets, quantization_guide
 Evals: baselines + regression_tests
 Docs: ENTORNO, BENCHMARK, ANALYSIS, AUTO_TUNING, IMPLEMENTATION_SUMMARY
 
FASE 1: Dashboard MVP 🟡 EN PROGRESO
Paso 1: Setup Base ⏳ PENDIENTE
 Crear estructura dashboard/ (ya existe)
 requirements.txt (ya creado)
 main.py FastAPI (ya creado)
 base.html con Tailwind + Alpine + HTMX (ya creado)
 Health check endpoint /health
Paso 2: Model Scanner + Backend Status ⏳ PENDIENTE
 utils/model_scanner.py - Escaneo GGUF recursivo
 utils/script_runner.py - Wrapper subprocess
 utils/event_logger.py - Event Sourcing (JSONL)
 Endpoints: GET /api/models, POST /api/models/scan, GET /api/backends
Paso 3-7: Tabs + Integración ⏳ PENDIENTE
 Tab Modelos (listado, filtros, selección)
 Tab Benchmark (formulario, progreso, resultados)
 Tab Tuning (selector perfil, progreso, presets)
 Tab Launch (generar .bat, preview, ejecutar)
 WebSocket + Notificaciones + Polish
 
FASE 2: Event Sourcing + Blog Pipeline ⏳ FUTURO
 Event Logger completo
 Blog Draft Generator (Astro-ready)
 Blog Sync automático a repo Astro
 
FASE 3: Dashboard Avanzado ⏳ FUTURO
 Análisis visual (Chrome Trace, Plotly)
 Historial runs + filtros
 Comparativas visuales (heatmaps)
 CI/CD Integration
 Presets Editor visual
 Multi-usuario + Auth


💾 10. ARCHIVOS DE RESULTADOS GENERADOS
Documentación (docs/)
text

docs/
├── ENTORNO_RX9070_LLAMA_CPP.md          # Documentación entorno completo
├── BENCHMARK_RESULTS_QWEN3.5-9B.md      # 32+ combos Vulkan/HIP
├── ANALYSIS_RESULTS.md                  # Análisis profundo (CPU vs GPU)
├── AUTO_TUNING_RESULTS.md               # 5 perfiles optimización
├── IMPLEMENTATION_SUMMARY.md            # Resumen skill completado
├── BENCHMARK_RESULTS_QWEN3.5-9B.md      # Detalles benchmarks
├── tune_throughput.json                 # Perfil throughput
├── tune_latency.json                    # Perfil latency
├── tune_balanced.json                   # Perfil balanced
├── tune_maxctx.json                     # Perfil max_context
├── tune_mem.json                        # Perfil memory_efficient
├── tune_qwen27b.json                    # Qwen3.8-27B
├── analyze_scaling_batch.json           # Batch scaling analysis
├── analyze_scaling_ngl.json             # n_gpu_layers sweep
├── analyze_scaling_prompt.json          # Prompt size scaling
├── analyze_compare.json                 # HIP vs CPU
├── analyze_compare_vulkan.json          # Vulkan comparison
└── analyze_comprehensive.json           # Both backends
Traces (docs/traces/)
text

traces/
├── Qwen3.5-9B-UD-Q4_K_XL_hip_default_*.chrome_trace.json
├── Qwen3.5-9B-UD-Q4_K_XL_vulkan_default_*.chrome_trace.json
├── Qwen3.5-9B-UD-Q4_K_XL_*.prometheus.metrics
└── Qwen3.8-27B-UD-Q3_K_XL_*.prometheus.metrics
Baselines (docs/baselines/)
text

baselines/
├── qwen35_9b_hip_v1.json
├── qwen35_9b_vulkan_v1.json
├── qwen35_9b_cpu_v1.json
└── qwen38_27b_hip_v1.json


🎯 11. RECOMENDACIONES
1. Priorizar Dashboard MVP (Paso 1-2)
Estructura y main.py ya existen
Faltan: utils (scanner, runner, logger) + endpoints
Tiempo estimado: 2-3 horas
2. Mejorar Profiling
GGML_METRICS=OFF en build actual
ROCm SDK sin rocprof/roc-tracer
Recomendación: Contribuir kernels con profiling a llama.cpp upstream
3. Flash Attention en RDNA 4
HIP usa SDPA fallback (no FA nativo)
Vulkan tiene FA nativo pero kernels menos optimizados
Investigar: Kernels FA específicos para gfx1201
4. VRAM Estimation
Heurística subestima modelos >10GB
Solución: Usar GGML_METRICS=1 o herramientas de monitoreo GPU
5. Contribución Upstream
Skill sigue formato AMD Skills
Acción: Contribuir a amd/skills repo
6. Testing de Modelos
Solo 10 modelos testeados
Añadir: Qwen3.8-9B-Distill, Apertus, InternVL, Llama-Vision



📈 12. METRICAS DE ÉXITO
KPI	Target	Estado
Skill local-ai-use completo	✅	100%
Scripts validados	✅	100%
Dashboard MVP funcional	🟡	30%
Event logging	⏳	0%
Blog automation	⏳	0%
Documentación completa	✅	100%


🔗 13. INTEGRACIÓN AMD SKILLS CATALOG
El skill local-ai-use se integra con:

serving-llms-on-instinct — MI300X/MI325X datacenter
serving-llms-on-epyc — EPYC CPU inference
lemonade-router-builder — Multi-model routing
hyperloom-workload-optimizer — Cluster optimization
Auto-selección de backend vía gpu_presets.json basado en deviceID/gfx_version.

📝 14. NOTAS TÉCNICAS IMPORTANTES
ROCm en Windows: Requiere _rocm_sdk_devel en PATH permanentemente

C:\Users\user\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin

Diferencias Arquitectura:

Vulkan: gfx1103, Wave64, KHR_coopmat
HIP: gfx1201, Wave32, MFMA (GGML_HIP_MMQ_MFMA=ON)
Build Vulkan: 2 builds (b10712, b10796) con diferencias <2%

Flash Attention:

HIP: SDPA fallback en RDNA 4
Vulkan: Nativo pero kernels menos optimizados
VRAM Estimation: Heurística, subestima modelos >10GB

✅ RESUMEN EJECUTIVO
Lo que funciona perfectamente:
✅ Skill local-ai-use completo y validado
✅ 4 scripts con capacidades robustas
✅ Documentación extensa y precisa
✅ Hallazgos técnicos bien documentados
✅ Presets y baselines para regresión

Lo que necesita atención:
🟡 Dashboard MVP (30% completado)
⏳ Event sourcing + Blog pipeline
⏳ WebSocket + notificaciones tiempo real
⏳ Integración CI/CD

Hallazgo más importante:
CPU Zen 4 supera a GPU RX 9070 en 2.7-9x para modelos ≤8GB Q4_K. La GPU no está bien aprovechada por kernels actuales. HIP > Vulkan en GPU (+20% decode, +55% prefill).

