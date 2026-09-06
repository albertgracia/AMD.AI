# Resultados de Benchmark: Qwen3.5-9B-UD-Q4_K_XL (5.56 GB)

**Fecha:** 2026-09-05  
**Hardware:** AMD Radeon RX 9070 16GB (RDNA 4 / gfx1103 Vulkan, gfx1201 HIP)  
**CPU:** AMD Ryzen 7 7800X3D 8-Core  
**Modelo:** Qwen3.5-9B-UD-Q4_K_XL (Q4_K, 5.56 GB)  
**Backends testeados:** Vulkan (2 builds) + HIP/ROCm  
**Script:** `G:\Proyectos\AMD.AI\scripts\bench_local.py`

---

## 📊 Resumen Comparativo Vulkan vs HIP

| Métrica | **Vulkan (b10712)** | **Vulkan (b10796)** | **HIP/ROCm** | Ganador |
|---------|---------------------|---------------------|--------------|---------|
| **Pre-fill max (ngl=0)** | 3,296 tok/s | 3,213 tok/s | **4,539 tok/s** | 🏆 **HIP** (+38%) |
| **Decode max (ngl=0)** | 28,642 tok/s | 28,452 tok/s | 28,375 tok/s | 🏆 **Vulkan** (+1%) |
| **Pre-fill max (ngl=-1)** | 924 tok/s | 923 tok/s | **1,552 tok/s** | 🏆 **HIP** (+68%) |
| **Decode max (ngl=-1)** | 2,965 tok/s | 2,960 tok/s | **3,501 tok/s** | 🏆 **HIP** (+18%) |
| **Estabilidad** | ✅ 32/32 | ✅ 32/32 | ✅ 16/16 | Empate |
| **Flash Attention** | ✅ auto | ✅ auto | ✅ auto | Empate |

---

## 🔍 Análisis Detallado por Configuración

### ngpu-layers = -1 (GPU completa)

| Prompt | Gen | Batch | **Vulkan b10712** | **Vulkan b10796** | **HIP** |
|--------|-----|-------|-------------------|-------------------|---------|
|        |     |       | Pre / Dec (tok/s) | Pre / Dec (tok/s) | Pre / Dec (tok/s) |
| 512    | 128 | 1024  | 227 / 1,492       | 228 / 1,488       | **1,077 / 1,858** |
| 512    | 128 | 2048  | 231 / 1,488       | 299 / 1,508       | 815 / 1,794 |
| 512    | 256 | 1024  | 228 / 2,957       | 227 / 2,959       | 797 / 3,494 |
| 512    | 256 | 2048  | 231 / 2,959       | 227 / 2,947       | 774 / **3,501** |
| 2048   | 128 | 1024  | 921 / 1,489       | 920 / 1,482       | **1,532 / 1,730** |
| 2048   | 128 | 2048  | 924 / 1,489       | 916 / 1,480       | **1,552 / 1,737** |
| 2048   | 256 | 1024  | 921 / 2,962       | 924 / 2,950       | **1,505 / 3,433** |
| 2048   | 256 | 2048  | 921 / 2,965       | 917 / 2,946       | **1,468 / 3,447** |

**Hallazgo clave:** Con GPU completa (ngl=-1), **HIP supera a Vulkan en prefill 1.5-1.7x y en decode 1.18-1.2x**. Esto sugiere que los kernels HIP para RDNA 4 (gfx1201) están mejor optimizados para carga completa que los kernels Vulkan genéricos.

### ngpu-layers = 0 (CPU only)

| Prompt | Gen | Batch | **Vulkan b10712** | **Vulkan b10796** | **HIP** |
|--------|-----|-------|-------------------|-------------------|---------|
|        |     |       | Pre / Dec (tok/s) | Pre / Dec (tok/s) | Pre / Dec (tok/s) |
| 512    | 128 | 1024  | 1,598 / 13,848    | 1,633 / 14,262    | **2,617 / 13,959** |
| 512    | 128 | 2048  | 1,608 / 13,889    | 1,721 / 14,074    | 2,440 / 14,049 |
| 512    | 256 | 1024  | 1,647 / 27,893    | 1,662 / 28,642    | **2,411 / 28,375** |
| 512    | 256 | 2048  | 1,610 / 28,345    | 1,600 / 28,211    | 2,417 / 28,045 |
| 2048   | 128 | 1024  | 3,206 / 14,462    | 3,197 / 14,196    | **4,495 / 14,053** |
| 2048   | 128 | 2048  | 3,213 / 14,110    | 3,151 / 14,030    | 4,440 / 14,081 |
| 2048   | 256 | 1024  | **3,296 / 28,452** | 3,213 / 28,128    | **4,539 / 27,867** |
| 2048   | 256 | 2048  | 3,158 / 27,877    | 3,168 / 28,134    | 4,332 / 28,072 |

**Hallazgo clave:** En CPU-only (ngl=0), **HIP gana en prefill consistentemente (1.4-1.5x)** pero Vulkan gana ligeramente en decode (1-2%). Esto indica que el backend CPU de llama.cpp (ggml-cpu-zen4.dll) es muy eficiente, y HIP tiene mejor pipeline de prefill.

---

## 🏆 Configuraciones Óptimas

### Para Máximo Throughput (Decode)
| Backend | Config | Decode tok/s |
|---------|--------|--------------|
| **Vulkan** | ngl=-1, prompt=512, gen=256, batch=2048 | **2,965** |
| **HIP** | ngl=-1, prompt=512, gen=256, batch=2048 | **3,501** ← **GANADOR** |

### Para Mínima Latencia (Prefill)
| Backend | Config | Prefill tok/s |
|---------|--------|---------------|
| **Vulkan** | ngl=0, prompt=2048, gen=256, batch=1024 | 3,296 |
| **HIP** | ngl=0, prompt=2048, gen=256, batch=1024 | **4,539** ← **GANADOR** |

### Balanceado (GPU completa + buen prefill)
| Backend | Config | Pre/Dec tok/s |
|---------|--------|---------------|
| **HIP** | ngl=-1, prompt=2048, gen=256, batch=1024 | **1,505 / 3,433** ← **RECOMENDADO** |
| Vulkan | ngl=-1, prompt=2048, gen=256, batch=2048 | 921 / 2,965 |

---

## 📈 Hallazgos Técnicos

### 1. **HIP/ROCm en Windows (via `_rocm_sdk_devel`) FUNCIONA**
- Requiere ROCm SDK en PATH: `C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin`
- Detecta RX 9070 como **gfx1201** (vs gfx1103 en Vulkan)
- VRAM reportada: 16,304 MiB (vs 16 GB en Vulkan)
- Wave size: 32 (vs 64 en Vulkan)

### 2. **Diferencias de Arquitectura**
| Aspecto | Vulkan | HIP/ROCm |
|---------|--------|----------|
| **gfx_version** | gfx1103 (RDNA 4) | gfx1201 (RDNA 4 / Navi 4x) |
| **Wave size** | 64 | 32 |
| **Matrix cores** | KHR_coopmat | MFMA (via GGML_HIP_MMQ_MFMA=ON) |
| **Flash Attention** | ✅ Nativo | ✅ Auto (SDPA fallback) |
| **KV Cache q4_0** | ✅ | ✅ |

### 3. **Builds Vulkan - Diferencias Mínimas**
- b10712 vs b10796: diferencias < 2% en todas las métricas
- Ambos usan ggml-vulkan.dll 53 MB
- b96806d incompleto (falta llama-bench.exe)

### 4. **Escalabilidad con Batch Size**
- **Batch 2048** consistentemente mejor que 1024 en decode (+0.5-1%)
- **Batch 1024** ligeramente mejor en prefill para HIP
- Vulkan menos sensible a batch size

### 5. **Flash Attention Impacto**
- Testado solo `fa=auto` (default)
- En HIP: `fa=auto` usa SDPA fallback en RDNA 4
- En Vulkan: `fa=auto` habilita Flash Attention nativo si disponible

---

## 📁 Archivos Generados

```
G:\Proyectos\AMD.AI\docs\
├── bench_test.csv / .json          # Vulkan (2 builds, 32 combos)
├── bench_hip_test.csv / .json      # HIP (1 build, 16 combos)
├── detection_report_final.json     # Detección completa entorno
└── ENTORNO_RX9070_LLAMA_CPP.md     # Documentación entorno
```

---

## 🎯 Conclusiones y Recomendaciones

### Para Producción (RX 9070 16GB + Qwen3.5-9B-Q4_K):

| Caso de Uso | Backend Recomendado | Configuración |
|-------------|---------------------|---------------|
| **Chat/Server alto throughput** | **HIP** | ngl=-1, prompt=512, gen=256, batch=2048, fa=auto, cache=q4_0 |
| **Baja latencia / Interactive** | **HIP** | ngl=-1, prompt=2048, gen=256, batch=1024, fa=auto, cache=q4_0 |
| **Máximo contexto / CPU offload** | **Vulkan** | ngl=20-40, cache=q4_0, ctx-size=65536 |
| **Portabilidad Linux/Instinct** | **HIP** | Mismo código, recompilar para Linux |

### Próximos Pasos:
1. **Testear más modelos** (Qwen3.8-27B, DeepSeek, Gemma-3)
2. **Benchmark HIP con flash-attn=off** (forzar SDPA)
3. **Probar cuantizaciones más agresivas** (Q3_K, IQ2_XXS) para modelos grandes
4. **Medir VRAM real** con `GGML_METRICS=1` + herramienta de monitoreo
5. **Integrar en skill `local-ai-use`** con presets automáticos

---

## 🔧 Comandos de Referencia

### Vulkan (Build b10712 - Recomendado)
```bash
G:\llama.cpp\bin\llama-b10712-bin-win-vulkan-x64\llama-bench.exe ^
  -m "G:\llama.cpp\gguf\Qwen3.5-9B\Qwen3.5-9B-UD-Q4_K_XL.gguf" ^
  -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0 -r 3 -o json
```

### HIP/ROCm (Requiere ROCm SDK en PATH)
```bash
set PATH=C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin;%PATH%
G:\llama.cpp-src\build-hip\bin\llama-bench.exe ^
  -m "G:\llama.cpp\gguf\Qwen3.5-9B\Qwen3.5-9B-UD-Q4_K_XL.gguf" ^
  -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0 -r 3 -o json
```

### Script Automatizado
```bash
# Vulkan rápido
python G:\Proyectos\AMD.AI\scripts\bench_local.py --model Qwen3.5-9B --backend vulkan --quick --yes

# HIP rápido  
python G:\Proyectos\AMD.AI\scripts\bench_local.py --model Qwen3.5-9B --backend hip --quick --yes

# Completo con CSV
python G:\Proyectos\AMD.AI\scripts\bench_local.py --model Qwen3.5-9B --backend both --output results.csv
```

---

*Generado automáticamente por `bench_local.py` v1.0*