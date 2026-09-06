# Local AI Use — Complete CLI Reference

---

## detect_local.py

### Synopsis
```bash
python detect_local.py [OPTIONS]
```

### Description
Detects AMD GPU environment, validates llama.cpp backends, and generates model compatibility matrix.

### Options

| Option | Description |
|--------|-------------|
| `--validate-backends` | Test llama-bench on all detected Vulkan/HIP builds |
| `--compatibility` | Scan GGUF models, check VRAM fit, recommend backend |
| `--json-only` | Output only JSON (for CI/CD) |
| `--output, -o FILE` | Save JSON report to file |

### Examples
```bash
# Full detection + validation + compatibility
python detect_local.py --validate-backends --compatibility

# CI/CD mode (JSON only)
python detect_local.py --validate-backends --compatibility --json-only -o detect_report.json

# Just check backends
python detect_local.py --validate-backends
```

### Output (JSON)
```json
{
  "timestamp": "2026-09-05T10:30:00",
  "gpu": {
    "device_name": "AMD Radeon RX 9070",
    "gfx_version": "gfx1103",
    "architecture": "RDNA 4",
    "vram_gb": 16
  },
  "hip": {
    "available": true,
    "hip_version": "7.2.0-8017ffed34",
    "clang_version": "AMD clang 23.0.0git"
  },
  "backends": [
    {"backend": "vulkan", "available": true, "path": "...", "llama_bench_works": true},
    {"backend": "hip", "available": true, "path": "...", "llama_bench_works": true}
  ],
  "models": [
    {"model_name": "Qwen3.5-9B", "size_gb": 5.56, "vulkan_compatible": true, "hip_compatible": true, "recommended_backend": "vulkan (primary) / hip (experimental)", "max_context_vulkan": 5120, "max_context_hip": 4096}
  ],
  "recommendations": [...]
}
```

---

## bench_local.py

### Synopsis
```bash
python bench_local.py [OPTIONS]
```

### Description
Runs benchmark matrix across models, backends, and configurations. Outputs CSV and JSON.

### Options

| Option | Description |
|--------|-------------|
| `--model PATTERN` | Filter models by substring (e.g., `Qwen3.5-9B`) |
| `--backend {vulkan,hip,both}` | Backend to test (default: both) |
| `--quick` | Reduced matrix (2 ngl × 2 prompt × 2 gen × 2 batch × 1 FA × 1 cache = 32 combos) |
| `--repetitions N` | Benchmark repetitions per combo (default: 3 full, 2 quick) |
| `--output, -o FILE` | CSV output file |
| `--json-output FILE` | JSON output file |
| `--list-models` | List detected models and exit |
| `--yes, -y` | Auto-confirm (non-interactive) |

### Benchmark Matrix (Full)
| Parameter | Values |
|-----------|--------|
| `n_gpu_layers` | -1, 0, 20, 40, 999 |
| `prompt_size` | 512, 1024, 2048, 4096 |
| `gen_size` | 128, 256, 512 |
| `batch_size` | 512, 1024, 2048 |
| `flash_attn` | auto, on, off |
| `cache_type` | q4_0, q8_0, f16 |
| **Total combos** | **5 × 4 × 3 × 3 × 3 × 3 = 1,620 per model per backend** |

### Benchmark Matrix (Quick)
| Parameter | Values |
|-----------|--------|
| `n_gpu_layers` | -1, 0 |
| `prompt_size` | 512, 2048 |
| `gen_size` | 128, 256 |
| `batch_size` | 1024, 2048 |
| `flash_attn` | auto |
| `cache_type` | q4_0 |
| **Total combos** | **2 × 2 × 2 × 2 × 1 × 1 = 32 per model per backend** |

### Examples
```bash
# Quick benchmark HIP
python bench_local.py --model Qwen3.5-9B --backend hip --quick --yes -o bench_hip.csv

# Full benchmark both backends
python bench_local.py --model Qwen3.5-9B --backend both --repetitions 3 -o bench_full.csv --json-output bench_full.json

# List models
python bench_local.py --list-models
```

### Output (CSV Columns)
```
timestamp,hostname,backend,build_path,model_name,model_path,model_size_gb,quantization,
n_gpu_layers,prompt_size,gen_size,batch_size,flash_attn,cache_type_k,cache_type_v,
prefill_tok_s,decode_tok_s,prefill_ms,decode_ms,repetitions,success,error
```

---

## tune_local.py

### Synopsis
```bash
python tune_local.py [OPTIONS]
```

### Description
Auto-tunes llama.cpp configuration using grid search across parameter space with 5 optimization profiles.

### Options

| Option | Description |
|--------|-------------|
| `--model PATTERN` | Model to tune (required) |
| `--backend {vulkan,hip,both}` | Backend (default: both) |
| `--profile {throughput,latency,balanced,max_context,memory_efficient}` | Optimization profile (default: balanced) |
| `--quick` | Reduced search space (8 configs vs 40) |
| `--repetitions N` | Reps per config (default: 2) |
| `--max-combos N` | Limit total combinations |
| `--save-presets` | Save best configs to `presets.ini` |
| `--output FILE` | Full results JSON |
| `--list-profiles` | List profiles and exit |
| `--yes, -y` | Non-interactive |

### Profiles

| Profile | Objective | Weights | Constraints | Use Case |
|---------|-----------|---------|-------------|----------|
| `throughput` | Maximize decode tok/s | decode=1.0, prefill=0.1, vram=-0.001 | min_decode=100, max_vram=14GB | API server, batch |
| `latency` | Minimize prefill ms | prefill_ms=-1.0, decode=0.2, vram=-0.001 | max_prefill=500ms, max_vram=14GB | Interactive chat |
| `balanced` | Balance decode/prefill | decode=0.6, prefill=0.4, vram=-0.001 | min_decode=50, max_prefill=1000ms | General (default) |
| `max_context` | Maximize context tokens | ctx=1.0, decode=0.1, prefill=0.1 | min_decode=20, min_prefill=50 | RAG, long docs |
| `memory_efficient` | Minimize VRAM | vram=-1.0, decode=0.3 | max_vram=8GB, min_decode=30 | Multi-model, large |

### Search Spaces

**Full (40 configs):**
```
n_gpu_layers: -1, 0, 10, 20, 30, 40, 50, 60, 70, 80, 999
prompt_size:  512, 1024, 2048, 4096
gen_size:     128, 256, 512
batch_size:   512, 1024, 2048
flash_attn:   auto, on, off
cache_type:   q4_0, q8_0, f16
Total: 11 × 4 × 3 × 3 × 3 × 3 = 3,564 (filtered to 40 via smart sampling)
```

**Quick (8 configs):**
```
n_gpu_layers: -1, 0
prompt_size:  512, 2048
gen_size:     128, 256
batch_size:   1024, 2048
flash_attn:   auto
cache_type:   q4_0
Total: 2 × 2 × 2 × 2 × 1 × 1 = 32
```

### Score Calculation
```python
score = Σ (metric_value × weight)
# For negative weights (minimize): score += (1/(value+1)) × |weight| × 1000
```

### Constraints Checking
Configs violating constraints get score = -1 (rejected).

### Examples
```bash
# List profiles
python tune_local.py --list-profiles

# Quick throughput tuning
python tune_local.py --model Qwen3.5-9B --backend hip --profile throughput --quick --yes --repetitions 1

# Full balanced tuning with presets
python tune_local.py --model Qwen3.5-9B --backend hip --profile balanced --repetitions 2 --save-presets -o tune_results.json

# Memory efficient for large model
python tune_local.py --model Qwen3.8-27B --backend hip --profile memory_efficient --max-combos 12 --yes
```

### Output: presets.ini
```ini
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

## analyze_local.py

### Synopsis
```bash
python analyze_local.py [OPTIONS]
```

### Description
Performance analysis: scaling sweeps, config comparisons, Chrome Trace generation, Prometheus metrics, baseline comparison.

### Options

| Option | Description |
|--------|-------------|
| `--model PATTERN` | Model to analyze (required) |
| `--backend {vulkan,hip,both}` | Backend (default: both) |
| `--config {default,large_context,cpu_only}` | Base config (default: default) |
| `--scaling-analysis` | Enable scaling sweep |
| `--variable {n_gpu_layers,prompt_size,gen_size,batch_size,flash_attn,cache_type}` | Variable to sweep |
| `--values "v1,v2,v3"` | Comma-separated values for sweep |
| `--compare-configs` | Compare two configs |
| `--config-a @file.json` | Config A (JSON or @file) |
| `--config-b @file.json` | Config B (JSON or @file) |
| `--trace-chrome` | Generate Chrome Trace (`.chrome_trace.json`) |
| `--prometheus` | Generate Prometheus metrics |
| `--save-baseline NAME` | Save as baseline for regression |
| `--compare-baseline FILE` | Compare against baseline |
| `--output FILE` | Full results JSON |
| `--yes, -y` | Non-interactive |

### Base Configs

| Config | ngl | prompt | gen | batch | FA | cache |
|--------|-----|--------|-----|-------|-----|-------|
| `default` | -1 | 512 | 256 | 2048 | auto | q4_0 |
| `large_context` | -1 | 2048 | 256 | 1024 | auto | q4_0 |
| `cpu_only` | 0 | 512 | 256 | 2048 | off | f16 |

### Scaling Variables

| Variable | Typical Values | Scaling Type |
|----------|----------------|--------------|
| `batch_size` | 512,1024,2048,4096 | Batch scaling |
| `n_gpu_layers` | -1,0,10,20,30,40 | Strong/weak scaling |
| `prompt_size` | 512,1024,2048,4096,8192 | Context scaling |
| `gen_size` | 128,256,512 | Generation scaling |
| `flash_attn` | auto,on,off | Feature toggle |
| `cache_type` | q4_0,q8_0,f16 | Quantization scaling |

### Metrics Computed

| Metric | Formula |
|--------|---------|
| `speedup` | throughput[i] / throughput[0] |
| `efficiency` | speedup / (resource_ratio) |
| `bottlenecks` | Saturation detection, efficiency < 70% |
| `recommendations` | Auto-generated from patterns |

### Examples

```bash
# Batch scaling
python analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable batch_size --values "512,1024,2048,4096" --yes

# GPU layer offloading
python analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable n_gpu_layers --values "-1,0,10,20,30,40" --yes

# Prompt scaling
python analyze_local.py --model Qwen3.5-9B --backend hip --scaling-analysis --variable prompt_size --values "512,1024,2048,4096,8192" --yes

# Compare GPU vs CPU
python analyze_local.py --model Qwen3.5-9B --backend hip --compare-configs --config-a @config_gpu.json --config-b @config_cpu.json --yes

# Full analysis with traces
python analyze_local.py --model Qwen3.5-9B --backend both --scaling-analysis --variable batch_size --values "512,1024,2048,4096" --trace-chrome --prometheus --yes -o analysis.json

# Save baseline
python analyze_local.py --model Qwen3.5-9B --backend hip --trace-chrome --prometheus --save-baseline qwen35_9b_hip_v1 --yes

# Compare against baseline
python analyze_local.py --model Qwen3.5-9B --backend hip --compare-baseline baselines/qwen35_9b_hip_v1.json --yes
```

### Chrome Trace Format
```json
{
  "traceEvents": [
    {"name": "Prefill", "ph": "X", "ts": 0, "dur": 1293800, "pid": 1, "tid": 1, "args": {"prompt_tokens": 512, "tok_s": 395.7}},
    {"name": "Decode", "ph": "X", "ts": 1293800, "dur": 75500, "pid": 1, "tid": 1, "args": {"gen_tokens": 256, "tok_s": 3391.7}}
  ],
  "displayTimeUnit": "us",
  "metadata": {"model": "Qwen3.5-9B", "backend": "hip", "config": {...}}
}
```
Open: `chrome://tracing` → Load

### Prometheus Metrics Format
```prometheus
# HELP llama_decode_tokens_per_second Decode throughput
# TYPE llama_decode_tokens_per_second gauge
llama_decode_tokens_per_second{model="Qwen3.5-9B",backend="hip",n_gpu_layers="-1",prompt_size="512",gen_size="256",batch_size="2048",flash_attn="auto",cache_type="q4_0"} 3391.7
```

### Baseline Comparison Output
```json
{
  "decode_change_pct": +5.2,
  "prefill_change_pct": -2.1,
  "memory_change_pct": +1.3,
  "regressions": [],
  "improvements": ["Decode throughput improved 5.2%"]
}
```

---

## llama-server Optimized Flags

### Recommended by Profile

| Profile | Command |
|---------|---------|
| **Balanced (default)** | `llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0 -c 65536` |
| **Throughput** | `llama-server -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0` |
| **Latency** | `llama-server -ngl -1 -p 2048 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0` |
| **Max Context** | `llama-server -ngl -1 -p 4096 -n 512 -b 1024 -fa auto -ctk q4_0 -ctv q4_0 -c 131072` |
| **Memory Efficient** | `llama-server -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0` |
| **CPU Only (Zen 4)** | `llama-server -ngl 0 -p 512 -n 256 -b 2048 -fa off -ctk q4_0 -ctv q4_0` |
| **Hybrid (Large Model)** | `llama-server -ngl 20 -p 512 -n 256 -b 1024 -fa auto -ctk q4_0 -ctv q4_0` |

### Flag Reference

| Flag | Description | Values |
|------|-------------|--------|
| `-ngl, --n-gpu-layers` | GPU layers to offload | -1=all, 0=cpu, N=count |
| `-p, --n-prompt` | Prompt tokens (prefill) | 512-8192 |
| `-n, --n-gen` | Generation tokens (decode) | 128-2048 |
| `-b, --batch-size` | Batch size | 512-4096 |
| `-fa, --flash-attn` | Flash Attention | auto, on, off |
| `-ctk, --cache-type-k` | K-cache quantization | q4_0, q8_0, f16 |
| `-ctv, --cache-type-v` | V-cache quantization | q4_0, q8_0, f16 |
| `-c, --ctx-size` | Context window | 4096-131072 |
| `-t, --threads` | CPU threads | auto, N |
| `--mlock` | Lock memory | flag |
| `--no-mmap` | Disable mmap | flag |

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `HF_TOKEN` | Hugging Face token for gated models | `hf_xxx` |
| `GGML_METRICS` | Enable GGML metrics | `1` |
| `GGML_METRICS_VERBOSE` | Verbose metrics | `1` |
| `HIP_VISIBLE_DEVICES` | HIP device selection | `0` |
| `VK_ICD_FILENAMES` | Vulkan ICD override | `/path/to/icd.json` |

---

## Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `-1073741515` | HIP DLL not found | Add ROCm SDK to PATH |
| `invalid parameter: -c` | Wrong ctx flag | Use `-p`/`-n` not `-c` |
| `OOM` | Out of memory | Reduce ngl, batch, or cache type |
| `Flash Attention not supported` | FA unavailable | Use `-fa off` or `-fa auto` |
| `Model not found` | GGUF path wrong | Check path, use absolute |

---

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Detect Environment
  run: python detect_local.py --validate-backends --compatibility --json-only -o detect.json

- name: Benchmark
  run: python bench_local.py --model ${{ matrix.model }} --backend both --quick --yes -o bench.csv

- name: Regression Check
  run: python analyze_local.py --model ${{ matrix.model }} --backend hip --compare-baseline baselines/baseline.json --yes
```

---

*Reference v1.0 — Complete CLI documentation for local-ai-use skill*