---
name: local-ai-use
description: >
  Run, optimize, and benchmark local LLMs on AMD hardware (Ryzen AI, Radeon, Instinct, EPYC) using llama.cpp.
  Use when the user wants to run a model locally, serve an LLM endpoint, benchmark models, tune performance,
  or analyze bottlenecks on AMD GPUs/CPUs. Supports Vulkan, HIP/ROCm, and CPU backends with automatic
  backend selection, preset optimization profiles, and regression testing.
  Handles: GPU detection, environment validation, model compatibility, benchmarking, auto-tuning, profiling.
  Do not use for NVIDIA GPUs (use CUDA skills), cloud inference APIs, or training/fine-tuning workflows.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
---

# Local AI Use on AMD Hardware

Run and optimize local LLMs on AMD hardware using llama.cpp with Vulkan, HIP/ROCm, and CPU backends.

## Prerequisites

- **AMD GPU**: Radeon RX 6000/7000/9000 series, Ryzen AI NPU, Instinct MI200/MI300, or EPYC with iGPU
- **Drivers**: AMD Adrenalin (Windows) or ROCm 6.0+ (Linux)
- **llama.cpp**: Built with Vulkan (`GGML_VULKAN=ON`) and/or HIP (`GGML_HIP=ON`)
- **ROCm SDK** (for HIP): `_rocm_sdk_devel` Python package or native ROCm install
- **Models**: GGUF format in local path or Hugging Face Hub
- **Windows**: Vulkan 1.3+, HIP via `_rocm_sdk_devel` in PATH
- **Linux**: ROCm 6.0+, Vulkan ICD, `rocminfo`, `amd-smi` available

## Data Files

Read these files directly for configuration:

- **`data/model_compatibility.json`** — Model × backend × quantization compatibility matrix with VRAM estimates and recommended contexts
- **`data/gpu_presets.json`** — GPU-specific presets (RX 9070, RX 7900 XTX, MI300X, Ryzen AI, etc.) with optimal flags
- **`data/quantization_guide.json`** — Quantization recommendations by model size, VRAM, and use case

## Step 1: Detect Environment

```bash
python scripts/detect_local.py --validate-backends --compatibility
```

Returns JSON with:
- GPU info (device_id, name, VRAM, gfx_version, architecture)
- HIP/ROCm availability (version, paths, compiler)
- Backend validation (Vulkan builds, HIP build, llama-bench status)
- Model compatibility matrix (10+ models tested)
- Recommendations (primary backend, optimal config)

## Step 2: Benchmark Models

```bash
# Quick benchmark (32 combos)
python scripts/bench_local.py --model Qwen3.5-9B --backend hip --quick --yes --repetitions 1

# Full benchmark (all configs, both backends)
python scripts/bench_local.py --model Qwen3.5-9B --backend both --repetitions 3 --output results.csv --json-output results.json

# Specific model, custom output
python scripts/bench_local.py --model "DeepSeek" --backend vulkan --output bench_deepseek.csv
```

Outputs: CSV + JSON with prefill/decode tok/s, latency, VRAM estimates per config.

## Step 3: Auto-Tune Configuration

```bash
# List optimization profiles
python scripts/tune_local.py --list-profiles

# Throughput profile (server/batch)
python scripts/tune_local.py --model Qwen3.5-9B --backend hip --profile throughput --quick --yes --repetitions 1

# Latency profile (interactive chat)
python scripts/tune_local.py --model Qwen3.5-9B --backend hip --profile latency --quick --yes --repetitions 1

# Balanced profile (default)
python scripts/tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --quick --yes --repetitions 1

# Memory efficient (large models / multi-model)
python scripts/tune_local.py --model Qwen3.8-27B --backend hip --profile memory_efficient --max-combos 12

# Save presets to presets.ini
python scripts/tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --save-presets
```

Profiles:
| Profile | Objective | Use Case |
|---------|-----------|----------|
| `throughput` | Maximize decode tok/s | API server, batch processing |
| `latency` | Minimize prefill ms (TTFT) | Interactive chat |
| `balanced` | Balance decode/prefill | General purpose (recommended) |
| `max_context` | Maximize context tokens | RAG, long documents |
| `memory_efficient` | Minimize VRAM usage | Multi-model, large models |

## Step 4: Analyze Performance

```bash
# Batch scaling analysis
python scripts/analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable batch_size --values "512,1024,2048,4096"

# GPU layer offloading analysis
python scripts/analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable n_gpu_layers --values "-1,0,10,20,30,40"

# Prompt size scaling
python scripts/analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable prompt_size --values "512,1024,2048,4096,8192"

# Compare two configs (e.g., GPU vs CPU)
python scripts/analyze_local.py --model Qwen3.5-9B --backend hip --compare-configs --config-a @config_gpu.json --config-b @config_cpu.json

# Generate Chrome Trace + Prometheus metrics
python scripts/analyze_local.py --model Qwen3.5-9B --backend hip --trace-chrome --prometheus --config default
```

Outputs:
- Scaling tables with speedup/efficiency
- Bottleneck detection + recommendations
- Chrome Trace (chrome://tracing)
- Prometheus metrics (scrapable)
- Config comparisons with verdicts

## Step 5: Run Optimized Server

```bash
# Balanced preset (recommended default)
llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0 -c 65536

# Maximum throughput (CPU-only on Zen 4)
llama-server -ngl 0 -p 512 -n 256 -b 2048 -fa off -ctk q4_0 -ctv q4_0

# Low latency (interactive)
llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0

# RAG / long context
llama-server -ngl -1 -p 4096 -n 512 -b 1024 -fa auto -ctk q4_0 -ctv q4_0 -c 131072

# Large model with hybrid offload
llama-server -ngl 20 -p 512 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0
```

## Key Findings (RX 9070 16GB, Ryzen 7 7800X3D)

| Backend | GPU Decode | CPU Decode | Winner |
|---------|------------|------------|--------|
| **HIP** | 3,461 tok/s | **27,454 tok/s** | **CPU +693%** |
| **Vulkan** | 2,887 tok/s | **27,122 tok/s** | **CPU +839%** |

- **HIP > Vulkan** on GPU: +20% decode, +55% prefill
- **CPU (Zen 4) dominates** for models ≤8GB (Q4_K)
- **Optimal batch**: 1024-2048 (efficiency drops >4096)
- **Hybrid ngl=10-20**: Sweet spot for larger models
- **Flash Attention**: HIP uses SDPA fallback on RDNA 4; Vulkan native but slower kernels

## Troubleshooting

| Issue | Solution |
|-------|----------|
| HIP `llama-bench` crashes (exit -1073741515) | Add ROCm SDK to PATH: `C:\Users\...\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin` |
| Vulkan `invalid parameter: -c` | Use `-p` (prompt) and `-n` (gen), not `-c` / `--ctx-size` |
| OOM on large models | Reduce `n_gpu_layers`, use `cache_type_k/v q4_0`, smaller batch |
| Flash Attention errors on HIP | Use `-fa off` or `-fa auto` (SDPA fallback) |
| Model not detected | Check GGUF naming matches quantization patterns in `model_compatibility.json` |

## Regression Testing

```bash
# Save baseline
python scripts/analyze_local.py --model Qwen3.5-9B --backend hip --trace-chrome --prometheus --save-baseline qwen35_9b_hip_v1

# Compare against baseline
python scripts/analyze_local.py --model Qwen3.5-9B --backend hip --compare-baseline baselines/qwen35_9b_hip_v1.json
```

Baselines stored in `baselines/` directory with Chrome Trace + Prometheus metrics.

## Integration with AMD Skills Catalog

This skill follows the AMD Skills format and interoperates with:
- `serving-llms-on-instinct` — For MI300X/MI325X datacenter deployment
- `serving-llms-on-epyc` — For EPYC CPU inference
- `lemonade-router-builder` — For multi-model routing
- `hyperloom-workload-optimizer` — For cluster workload optimization

## Files in This Skill

```
local-ai-use/
├── SKILL.md                      # This file
├── skill-card.md                 # Visual card for marketplaces
├── reference.md                  # Complete CLI reference
├── scripts/
│   ├── detect_local.py           # Environment detection + validation
│   ├── bench_local.py            # Benchmarking matrix
│   ├── tune_local.py             # Auto-tuning (5 profiles)
│   └── analyze_local.py          # Scaling analysis, traces, comparison
├── data/
│   ├── model_compatibility.json  # Model × backend matrix
│   ├── gpu_presets.json          # GPU-specific presets
│   └── quantization_guide.json   # Quantization recommendations
└── evals/
    ├── benchmark_baselines.json  # Regression baselines
    └── regression_tests.py       # Automated regression tests
```