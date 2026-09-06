# AMD.AI 🚀

**Catálogo oficial AMD para ejecutar, optimizar y gestionar LLMs locales en hardware AMD.**

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![AMD](https://img.shields.io/badge/Hardware-AMD%20Radeon%20RX%209070-red.svg)](https://www.amd.com/)
[![ROCm](https://img.shields.io/badge/ROCm-7.2.0-orange.svg)](https://rocm.docs.amd.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Propósito

Proyecto dual enfocado en:

1. **Skill `local-ai-use`** — Catálogo de herramientas para ejecutar/optimizar LLMs locales en GPU AMD (HIP/Vulkan) y CPU Zen
2. **Dashboard IA** — Interfaz web para gestionar modelos, benchmarks, auto-tuning y generación de scripts optimizados

---

## 🖥️ Hardware Objetivo

- **GPU:** AMD Radeon RX 9070 16GB (RDNA 4 / gfx1103 Vulkan, gfx1201 HIP)
- **CPU:** AMD Ryzen 7 7800X3D 8-Core (Zen 4)
- **ROCm:** 7.2.0

---

## 📁 Estructura

```
AMD.AI/
├── skills/local-ai-use/     # ✅ Skill completo (detect, bench, tune, analyze)
├── dashboard/               # 🟢 Dashboard MVP (FastAPI + HTMX)
│   ├── routers/             # Routers modulares (benchmark, tuning, launch, llama, events, blog)
│   ├── utils/               # Model scanner, event logger, blog generator
│   └── templates/           # 6 tabs HTMX (models, benchmark, tuning, launch, blog, updates)
├── docs/                    # Documentación técnica y resultados
├── ROADMAP-IA-DASHBOARD.md  # Plan de desarrollo
└── INFORME DETALLADO.md     # Informe completo con hallazgos técnicos
```

---

## 🚀 Instalación Rápida

### 1. Clonar repositorio
```bash
git clone https://github.com/albertgracia/AMD.AI.git
cd AMD.AI
```

### 2. Instalar dependencias
```bash
cd dashboard
pip install -r requirements.txt
```

### 3. Configurar ROCm en PATH
```powershell
$env:PATH += ";C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin"
```

### 4. Ejecutar Dashboard
```bash
python run_dashboard.py
# Acceso: http://localhost:9090
```

---

## 📊 Skill `local-ai-use`

Herramientas CLI para ejecutar LLMs locales en hardware AMD:

| Script | Función |
|--------|---------|
| `detect_local.py` | Detección GPU, validación backends, matriz compatibilidad |
| `bench_local.py` | Benchmarking parametrizable (hasta 1,620 combos) |
| `tune_local.py` | Auto-tuning con 5 perfiles de optimización |
| `analyze_local.py` | Escalabilidad, traces Chrome, Prometheus |

### Perfiles de Optimización
- `throughput` — Máximo decode tok/s (API server, batch)
- `latency` — Mínimo TTFT (chat interactivo)
- `balanced` — Equilibrio general (default)
- `max_context` — Máximo contexto (RAG, documentos largos)
- `memory_efficient` — Mínima VRAM (multi-modelo)

---

## 📈 Hallazgos Clave

> **CPU Zen 4 supera a GPU RX 9070 en 2.7-9x para modelos ≤8GB Q4_K**. La GPU no está bien aprovechada por kernels actuales.
>
> HIP > Vulkan en GPU: +20% decode, +55% prefill.

Ver [INFORME DETALLADO.md](INFORME%20DETALLADO-Proyecto%20AMD.md) para análisis completo.

---

## 🗺️ Roadmap

- ✅ **FASE 0:** Skill `local-ai-use` completo
- ✅ **FASE 1:** Dashboard MVP funcional (95%)
- 🟡 **FASE 2:** Blog pipeline + Astro integration
- ⏳ **FASE 3:** Dashboard avanzado (visualización, CI/CD, auth)

Ver [ROADMAP-IA-DASHBOARD.md](ROADMAP-IA-DASHBOARD.md) para detalles.

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crear branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'feat: añadir nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT — ver [LICENSE](LICENSE) para detalles.

---

## 🔗 Integración

El skill `local-ai-use` se integra con:
- [serving-llms-on-instinct](https://github.com) — MI300X/MI325X datacenter
- [serving-llms-on-epyc](https://github.com) — EPYC CPU inference
- [lemonade-router-builder](https://github.com) — Multi-model routing
- [hyperloom-workload-optimizer](https://github.com) — Cluster optimization

---

**Desarrollado para AMD Ryzen 7 7800X3D + Radeon RX 9070 16GB** 🎮
