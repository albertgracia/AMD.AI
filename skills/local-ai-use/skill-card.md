# Local AI Use on AMD Hardware

**Run, optimize, and benchmark local LLMs on AMD hardware using llama.cpp**

---

## 🎯 What It Does

| Capability | Description |
|------------|-------------|
| **Environment Detection** | Auto-detects AMD GPU, Vulkan/HIP/ROCm, validates llama.cpp builds |
| **Model Compatibility** | Scans GGUF models, checks VRAM fit, recommends backend per model |
| **Benchmarking** | Matrix: model × backend × ngl × batch × ctx × cache × FA |
| **Auto-Tuning** | 5 profiles: throughput, latency, balanced, max_context, memory_efficient |
| **Profiling** | Scaling analysis, bottleneck detection, Chrome Trace, Prometheus metrics |
| **Regression Testing** | Baseline comparison, CI/CD integration |

---

## 🖥️ Supported Hardware

| Hardware | Backend | Status |
|----------|---------|--------|
| Radeon RX 9000 (RDNA 4) | Vulkan ✅ HIP ⚠️ | **HIP recommended** |
| Radeon RX 7000 (RDNA 3) | Vulkan ✅ HIP ✅ | Both |
| Radeon RX 6000 (RDNA 2) | Vulkan ✅ HIP ✅ | Both |
| Ryzen AI (Phoenix/Hawk Point) | Vulkan ✅ HIP ❌ | Vulkan |
| Instinct MI300X/MI325X | HIP ✅ | **Use `serving-llms-on-instinct`** |
| Instinct MI200 | HIP ✅ | Use `serving-llms-on-instinct` |
| EPYC (Genoa/Bergamo) | CPU ✅ | **Use `serving-llms-on-epyc`** |

---

## ⚡ Quick Start

```bash
# 1. Detect environment & models
python scripts/detect_local.py --validate-backends --compatibility

# 2. Quick benchmark
python scripts/bench_local.py --model Qwen3.5-9B --backend hip --quick --yes

# 3. Auto-tune for your use case
python scripts/tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --quick --yes

# 4. Run optimized server
llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0 -c 65536
```

---

## 📊 Benchmark Results (RX 9070 16GB + Ryzen 7 7800X3D)

### Qwen3.5-9B-Q4_K (5.56 GB)

| Backend | GPU Decode | CPU Decode | Speedup |
|---------|------------|------------|---------|
| **HIP** | 3,461 tok/s | **27,454 tok/s** | **CPU +693%** |
| **Vulkan** | 2,887 tok/s | **27,122 tok/s** | **CPU +839%** |

> **Key Finding**: For models ≤8GB Q4_K, **CPU (Zen 4) is 2.7-9x faster than GPU** on RX 9070.
> HIP outperforms Vulkan on GPU by +20% decode / +55% prefill.

### Optimal Configs (HIP)

| Profile | Config | Decode | Prefill | VRAM |
|---------|--------|--------|---------|------|
| **Throughput** | `ngl=-1, p=512, g=256, b=2048` | 3,617 | 811 | 6.6 GB |
| **Latency** | `ngl=-1, p=2048, g=256, b=1024` | 3,438 | 1,502 | 6.2 GB |
| **Balanced** | `ngl=-1, p=2048, g=256, b=2048` | 3,405 | 1,556 | 6.7 GB |
| **Max Context** | `ngl=-1, p=2048, g=256, b=2048` | 3,410 | 1,449 | 6.7 GB |
| **Memory Efficient** | `ngl=-1, p=512, g=256, b=2048` | 3,543 | 753 | 6.6 GB |

### Scaling Characteristics

| Variable | Optimal Range | Efficiency Drop |
|----------|---------------|-----------------|
| **Batch Size** | 1024-2048 | <20% at 4096 |
| **GPU Layers** | -1 (all) or 10-20 (hybrid) | ngl>30 = CPU faster |
| **Prompt Size** | Linear scaling up to 8192 | Perfect linear |

---

## 🛠️ CLI Commands

```bash
# Detect environment
python detect_local.py --validate-backends --compatibility --output report.json

# Benchmark
python bench_local.py --model Qwen3.5-9B --backend both --quick --yes -o results.csv

# Auto-tune
python tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --quick --yes --save-presets

# Analyze scaling
python analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable batch_size --values "512,1024,2048,4096"

# Compare configs
python analyze_local.py --model Qwen3.5-9B --backend hip --compare-configs --config-a @gpu.json --config-b @cpu.json

# Generate traces
python analyze_local.py --model Qwen3.5-9B --backend hip --trace-chrome --prometheus
```

---

## 📁 Outputs

| Output | Format | Use |
|--------|--------|-----|
| Detection report | JSON | CI/CD, automation |
| Benchmark results | CSV + JSON | Analysis, plotting |
| Tuning presets | `presets.ini` | llama-server args |
| Scaling analysis | JSON + table | Bottleneck detection |
| Chrome Trace | `.chrome_trace.json` | `chrome://tracing` |
| Prometheus metrics | `.prometheus.metrics` | Monitoring |
| Regression baseline | JSON | CI/CD comparison |

---

## 🔧 Requirements

| Component | Windows | Linux |
|-----------|---------|-------|
| **Vulkan** | Driver 2.0+ (Adrenalin) | Mesa 23+ / AMDGPU-PRO |
| **HIP/ROCm** | `_rocm_sdk_devel` in PATH | ROCm 6.0+ native |
| **llama.cpp** | `GGML_VULKAN=ON`, `GGML_HIP=ON` | Same |
| **Models** | GGUF format | GGUF format |
| **Python** | 3.10+ | 3.10+ |

---

## 🔗 Related Skills

| Skill | Purpose |
|-------|---------|
| `serving-llms-on-instinct` | MI300X/MI325X datacenter serving |
| `serving-llms-on-epyc` | EPYC CPU inference |
| `lemonade-router-builder` | Multi-model intelligent routing |
| `hyperloom-workload-optimizer` | Cluster workload optimization |
| `tracelens-analysis-orchestrator` | Performance trace analysis |

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-09-05 | Initial release: detect, bench, tune, analyze |

---

## 📄 License

MIT — Part of AMD Skills Catalog

---

*Skill Card v1.0 — Generated 2026-09-05*