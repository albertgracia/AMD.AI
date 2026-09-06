# ROADMAP: Dashboard IA + Blog Automation

**Proyecto:** AMD.AI - Local AI Dashboard + Auto-Blog Pipeline  
**Ubicacion:** G:\Proyectos\AMD.AI\  
**Estado:** EN PROGRESO - MVP Dashboard funcional + hardening inicial (P1+P2+P3 completados 2026-09-06)  
**Ultima actualizacion:** 2026-09-06  
**Proxima sesion:** P2-#7 (analizar endpoints pendientes) + P3 (testeo integration)

---

## Vision General

| Componente | Estado | Descripcion |
|------------|--------|-------------|
| Skill `local-ai-use` | COMPLETADO | 4 scripts, data/, evals/, docs/ |
| Dashboard MVP | EN PROGRESO | FastAPI + HTMX + Alpine.js (puerto 9090) + hardening aplicado |
| Event Sourcing + Blog Pipeline | EN PROGRESO | Event logger + blog_generator unificados (2026-09-06) |
| Blog Astro Automation | FUTURO | Sync automatico a repo Astro |
| Hardening Seguridad | EN PROGRESO | CORS, API key, ZIP validation, path config (P1-#1, #4, #5) |

---

## FASES DEL PROYECTO

### FASE 0: Fundacion (COMPLETADA)
- [x] Skill `local-ai-use` completo (detect, bench, tune, analyze)
- [x] Scripts validados: detect, bench, tune, analyze
- [x] Data: model_compatibility, gpu_presets, quantization_guide
- [x] Evals: baselines + regression_tests
- [x] Docs: ENTORNO, BENCHMARK, ANALYSIS, AUTO_TUNING, IMPLEMENTATION_SUMMARY

---

### FASE 1: Dashboard MVP (EN PROGRESO)

#### Paso 1: Setup Base (15 min) -- COMPLETADO 2026-09-06
- [x] Crear estructura `dashboard/`
- [ ] `requirements.txt` (fastapi, uvicorn, httpx, jinja2, pyyaml, ulid, python-multipart, websockets)
- [ ] `main.py` FastAPI + static + templates + CORS (0.0.0.0:9090)
- [ ] `base.html` con Tailwind CDN + Alpine.js CDN + HTMX CDN
- [ ] Health check endpoint `/health`

#### Paso 2: Model Scanner + Backend Status (20 min) -- COMPLETADO 2026-09-06
- [x] `utils/model_scanner.py` - Escaneo GGUF recursivo + metadata (nombre, tamano, cuantizacion, path)
- [ ] `utils/script_runner.py` - Wrapper subprocess con timeout, env, JSON output parsing
- [ ] `utils/event_logger.py` - Event Sourcing (append-only JSONL + auto-blog drafts)
- [ ] Endpoints: `GET /api/models`, `POST /api/models/scan`, `GET /api/backends`

#### Paso 3: Tab Modelos (20 min)
- [ ] Partial `partials/models_tab.html` + HTMX load
- [ ] Lista tarjetas: nombre, tamano, cuantizacion, fav, seleccionar
- [ ] Filtros cliente (Alpine.js): busqueda, slider tamano, select cuantizacion
- [ ] Boton "Refrescar escaneo" -> `POST /api/models/scan`

#### Paso 4: Tab Benchmark (30 min)
- [ ] Partial `partials/benchmark_tab.html`
- [ ] Formulario: multi-select modelos, select backend (vulkan/hip/both/cpu), quick/full, reps
- [ ] `POST /api/benchmark/start` -> Background task + job_id
- [ ] Polling `GET /api/benchmark/status/{job_id}` (HTMX `hx-trigger="every 2s"`)
- [ ] Resultados: `GET /api/benchmark/results/{job_id}` -> tabla sortable + export CSV/JSON
- [ ] Comparativa Vulkan vs HIP side-by-side

#### Paso 5: Tab Tuning (20 min)
- [ ] Partial `partials/tuning_tab.html`
- [ ] Selector: modelo, backend, 5 perfiles (throughput, latency, balanced, max_context, memory_efficient)
- [ ] Quick toggle, reps, save presets
- [ ] `POST /api/tune/start` -> Background + polling
- [ ] Resultados: config optima + metricas + boton "Guardar en presets.ini"

#### Paso 6: Tab Generar .bat (20 min)
- [ ] Partial `partials/launch_tab.html`
- [ ] Selector modelo + preset (5 perfiles + Custom)
- [ ] Si Custom: formulario completo (ngl, prompt, gen, batch, fa, cache, ctx)
- [ ] Preview `.bat` generado (syntax highlight)
- [ ] Botones: "Copiar al portapapeles", "Guardar .bat", "Lanzar ahora"

#### Paso 7: Integracion + Polish (20 min)
- [ ] WebSocket `/ws/progress/{job_id}` para tiempo real
- [ ] Notificaciones toast (Alpine store)
- [ ] Dark mode toggle + responsive
- [ ] CORS LAN ready + Basic Auth opcional

---

### FASE 2: Event Sourcing + Blog Pipeline (Post-MVP)

#### Event Logger (Critico - Implementar en Paso 2)
- [ ] `utils/event_logger.py` - Append-only JSONL (`dashboard/data/events.jsonl`)
- [ ] Eventos: `environment.detected`, `model.discovered`, `benchmark.completed`, `tuning.completed`, `analysis.generated`, `bat.generated`, `baseline.updated`
- [ ] Auto-generar borradores Astro en `dashboard/data/blog_drafts/`

#### Blog Draft Generator
- [ ] `utils/blog_generator.py` - Frontmatter Astro valido
- [ ] Schema: title, date, tags, category, hardware, models, results, summary, draft
- [ ] Un .md por evento "publicable"

#### Blog Sync (Futuro)
- [ ] Script `sync_to_astro.sh` (rsync drafts -> repo Astro)
- [ ] GitHub Action para auto-publish programado

---

### FASE 3: Dashboard Avanzado (Bajo Demanda)

- [ ] Analisis visual: Iframe chrome://tracing, graficos Plotly escalabilidad
- [ ] Historial runs: Tabla paginada, filtros, export
- [ ] Comparativas visuales: Heatmaps, side-by-side Vulkan/HIP/CPU
- [ ] CI/CD Integration: Boton "Run Regression", status GitHub Actions
- [ ] Presets Editor: Editor visual `presets.ini` con validacion
- [ ] Multi-usuario: Auth, roles, proyectos separados

---

## Arquitectura Tecnica

### Stack Confirmado
| Capa | Tecnologia | Version |
|------|------------|---------|
| Backend | FastAPI | 0.115+ |
| Server | Uvicorn | 0.32+ |
| Frontend | HTMX 2.0 + Alpine.js 3.14 + Tailwind CSS 3.4 (CDN) |
| WebSocket | `websockets` lib | 12+ |
| Background Tasks | `asyncio` nativo | Python 3.13 |
| Event Store | JSONL (append-only) | `dashboard/data/events.jsonl` |
| Blog Drafts | Markdown + Frontmatter | `dashboard/data/blog_drafts/` |

### Estructura de Archivos Objetivo
```
G:\Proyectos\AMD.AI\
├── AGENTS.md                           # Instrucciones agentes
├── ROADMAP-IA-DASHBOARD.md             # ESTE ARCHIVO
├── dashboard/
│   ├── main.py                         # FastAPI app
│   ├── requirements.txt
│   ├── static/
│   │   └── app.js                      # Alpine components
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── partials/
│   │       ├── models_tab.html
│   │       ├── benchmark_tab.html
│   │       ├── tuning_tab.html
│   │       └── launch_tab.html
│   ├── utils/
│   │   ├── model_scanner.py
│   │   ├── script_runner.py
│   │   ├── event_logger.py             # Event sourcing
│   │   └── blog_generator.py           # Astro drafts
│   └── data/
│       ├── events.jsonl                # Event sourcing
│       └── blog_drafts/                # Astro-ready drafts
├── skills/local-ai-use/                # COMPLETADO
└── scripts/                            # COMPLETADO
```

---

## Configuracion LAN + Seguridad

| Aspecto | Configuracion |
|---------|---------------|
| Host | `0.0.0.0:9090` |
| CORS | `allow_origins=["*"]` (desarrollo) -> restringir en prod |
| Auth LAN | Basic Auth opcional (env `DASHBOARD_USER`, `DASHBOARD_PASS`) |
| HTTPS LAN | Self-signed cert + `uvicorn --ssl-keyfile --ssl-certfile` (futuro) |
| Firewall | Regla entrante Puerto 9090 (Windows Defender) |

---

## Metricas de Exito MVP

| KPI | Target |
|-----|--------|
| Tiempo setup -> primer benchmark | < 5 min |
| Latencia polling -> resultados | < 2s |
| Generar .bat valido | 100% |
| Event logging coverage | 100% eventos clave |
| Blog draft valido Astro | 100% |

---

## Estado Actual por Componente

| Componente | Estado | Ubicacion | Notas |
|------------|--------|-----------|-------|
| Skill `local-ai-use` | COMPLETADO | `skills/local-ai-use/` | 4 scripts + data + evals + docs |
| `detect_local.py` | VALIDADO | `skills/.../scripts/` | --validate-backends --compatibility |
| `bench_local.py` | VALIDADO | `skills/.../scripts/` | Quick + Full matrix |
| `tune_local.py` | VALIDADO | `skills/.../scripts/` | 5 perfiles + presets.ini |
| `analyze_local.py` | VALIDADO | `skills/.../scripts/` | Scaling + traces + compare |
| Dashboard `main.py` | COMPLETADO | `dashboard/` | Split en routers modulares + WS cleanup (2026-09-06) |
| Model Scanner | PENDIENTE | `dashboard/utils/` | Paso 2 |
| Event Logger | COMPLETADO | `dashboard/utils/` | Rotación aplicada (5000 líneas), schema unificado |
| Tab Modelos | PENDIENTE | `templates/partials/` | Paso 3 |
| Tab Benchmark | PENDIENTE | `templates/partials/` | Paso 4 |
| Tab Tuning | PENDIENTE | `templates/partials/` | Paso 5 |
| Tab Launch | PENDIENTE | `templates/partials/` | Paso 6 |
| Blog Generator | COMPLETADO | `dashboard/utils/` | Schema unificado con event_logger (2026-09-06) |
| `setup_files.py` | ELIMINADO | `dashboard/` | Archivo obsoleto eliminado (2026-09-06) |
| Hardening CORS/API key | COMPLETADO | `dashboard/main.py` | CORS restringido a localhost + red local (env `AMD_ALLOWED_ORIGINS`), API key desde env (2026-09-06) |
| Hardening ZIP validation | COMPLETADO | `dashboard/main.py` | PurePosixPath + sanitizacion + bloqueo de rutas absolutas/parent/ocultas (2026-09-06) |
| Hardening paths -> config.py | COMPLETADO | `dashboard/config.py` | Extraido 10+ hardcoded paths, soportado por env vars (2026-09-06) |

---

## Proximos Comandos a Ejecutar

```bash
# 1. Crear estructura
mkdir -p G:\Proyectos\AMD.AI\dashboard\{static,templates/partials,utils,data/blog_drafts}

# 2. requirements.txt
cat > G:\Proyectos\AMD.AI\dashboard\requirements.txt << 'EOF'
fastapi==0.115.0
uvicorn[standard]==0.32.0
httpx==0.27.0
jinja2==3.1.4
pyyaml==6.0.1
ulid==2.0.1
python-multipart==0.0.12
websockets==12.0
EOF

# 3. Instalar
cd G:\Proyectos\AMD.AI\dashboard
pip install -r requirements.txt

# 4. Verificar scripts existentes accesibles
python -c "import sys; sys.path.append(r'G:\Proyectos\AMD.AI\skills\local-ai-use\scripts'); import detect_local, bench_local, tune_local, analyze_local; print('OK')"
```

---

## Como Usar Este Roadmap en Proxima Sesion

1. Leer este archivo -> Conocer estado exacto
2. Verificar parches aplicados (2026-09-06): WS cleanup, schema unificado, rotación, setup_files eliminado
3. Marcar completados -> Actualizar checkboxes `[x]`
4. Actualizar "Ultima actualizacion" -> Fecha actual
5. Anadir notas -> Problemas, decisiones, hallazgos
6. Hardening pendiente: P1-#1 (paths -> config.py), P1-#4 (ZIP validation), P1-#5 (CORS/API key)

---

## Notas para el Agente IA (Proxima Sesion)

> **LEE ESTO AL INICIAR:**
> 1. Lee `AGENTS.md` (instrucciones proyecto)
> 2. Lee `ROADMAP-IA-DASHBOARD.md` (este archivo)
> 3. Verifica estado actual en checkboxes arriba
> 4. Continua desde Paso 1: Setup Base (primer `[ ]` sin marcar)
> 5. Ejecuta comandos de "Proximos Comandos a Ejecutar"
> 6. Actualiza este archivo tras cada paso completado

---

## Decisiones Tecnicas Clave (Ya Tomadas)

| Decision | Opcion Elegida | Razon |
|----------|----------------|-------|
| Frontend | HTMX + Alpine + Tailwind CDN | Sin build step, server-side rendering, ligero |
| Puerto | 9090 | No interfiere con servidores web comunes |
| Host | 0.0.0.0 | LAN ready desde dia 1 |
| Event Store | JSONL append-only | Simple, versionable, streaming-friendly |
| Blog Format | Markdown + YAML Frontmatter | Compatible Astro Content Collections |
| Auth LAN | Basic Auth (env vars) | Simple, suficiente para red local |
| Background Jobs | asyncio + polling/WS | Nativo Python, sin Redis/Celery |

---

## Historial de Cambios

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-09-05 | Creacion roadmap inicial + Fases 0-3 definidas | IA |
| 2026-09-05 | Skill `local-ai-use` completado y validado | IA |
| 2026-09-06 | Auditoria completa: 14+ problemas identificados (5 crit., 6 diseno, 3 codigo) | IA |
| 2026-09-06 | Parche P2-#13: Eliminar `setup_files.py` (obsoleto) | IA |
| 2026-09-06 | Parche P2-#15: Limpieza WS connections + exception handler | IA |
| 2026-09-06 | Parche P0-#3: Unificar schema eventos (blog_generator lee `data`/`event_type`) | IA |
| 2026-09-06 | Parche P2-#8: Rotación events.jsonl (max 5000 lineas) | IA |
| 2026-09-06 | Parche P1-#1: Extraer hardcoded paths a config.py + env vars (10+ rutas) | IA |
| 2026-09-06 | Parche P1-#5: CORS restringido a localhost + red local + API key desde env var | IA |
| 2026-09-06 | Parche P1-#4: ZIP extraction validation (PurePosixPath, sanitizacion, bloqueo parent/absolutas) | IA |
| 2026-09-06 | Parche P2-#6: Split main.py en routers modulares (benchmark, tuning, launch, llama, events, blog) | IA |
| 2026-09-06 | Backup completo: `G:\Proyectos\AMD.AI.backup.20260906` | IA |

---

**PROXIMO PASO:** P4 (CORS/Auth/api-key/firewall) + repo Astro en blog-cloudflare-astro/

## Nota modelos 2026-09-06
- `models/` usa una carpeta por modelo con complementarios: `gemma-4-12B-it-qat-UD-Q4_K_XL.gguf` + `mmproj-BF16.gguf` (vision) + `mtp-gemma-4-12B-it.gguf` (drafter MTP).
- El scanner agrupa por carpeta y el .bat anade `--mmproj` + `--model-draft ... --spec-type draft-mtp --spec-draft-n-max 4`.
- `scripts/` (raiz) queda como legacy: usar `skills/local-ai-use/scripts/`.

---

*Este roadmap se actualiza automaticamente en cada sesion. Ultima sync: 2026-09-05*