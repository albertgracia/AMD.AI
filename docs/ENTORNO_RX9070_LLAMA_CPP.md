# Documentación del Entorno: AMD Radeon RX 9070 16GB + llama.cpp

**Fecha:** 2026-09-05  
**Proyecto:** AMD.AI - Skill `local-ai-use`  
**Workspace:** `G:\Proyectos\AMD.AI`  
**Hardware:** AMD Radeon RX 9070 (16 GB VRAM, RDNA 4 / gfx1103)  
**SO:** Windows 11

---

## 1. Resumen Ejecutivo

| Componente | Estado | Versión/Detalle |
|------------|--------|-----------------|
| **Vulkan** | ✅ Funcionando | Instance 1.4.357, Driver AMD 2.0.395 |
| **ROCm / HIP** | ✅ Instalado (vía Python SDK) | HIP 7.2.0, AMD clang 23.0.0git, rocclr |
| **llama.cpp Vulkan** | ✅ Múltiples builds | `G:\llama.cpp\bin\llama-b*-bin-win-vulkan-x64\` |
| **llama.cpp HIP/ROCm** | ✅ Build funcional | `G:\llama.cpp-src\build-hip\bin\` (ggml-hip.dll 70MB) |
| **amd-smi / rocminfo** | ❌ No disponibles | Solo vía `_rocm_sdk_devel` Python package |

---

## 2. Detalle de Vulkan

### 2.1 Información del Dispositivo
```text
GPU0:
  apiVersion         = 1.4.349
  driverVersion      = 2.0.395
  vendorID           = 0x1002 (AMD)
  deviceID           = 0x7550
  deviceType         = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU
  deviceName         = AMD Radeon RX 9070
  driverID           = DRIVER_ID_AMD_PROPRIETARY
  driverName         = AMD proprietary driver
```

### 2.2 Capas Vulkan Activas (12)
| Capa | Versión | Propósito |
|------|---------|-----------|
| VK_LAYER_AMD_switchable_graphics | 1.4.349 | Gráficos conmutables AMD |
| VK_LAYER_KHRONOS_profiles | 1.4.357 | Perfiles Khronos |
| VK_LAYER_KHRONOS_shader_object | 1.4.357 | Shader objects |
| VK_LAYER_KHRONOS_synchronization2 | 1.4.357 | Synchronization2 |
| VK_LAYER_KHRONOS_validation | 1.4.357 | Validación (debug) |
| VK_LAYER_LUNARG_api_dump | 1.4.357 | API dump |
| VK_LAYER_LUNARG_crash_diagnostic | 1.4.357 | Diagnóstico crashes |
| VK_LAYER_LUNARG_gfxreconstruct | 1.4.357 | Captura GFXReconstruct |
| VK_LAYER_LUNARG_monitor | 1.4.357 | Monitoreo ejecución |
| VK_LAYER_LUNARG_screenshot | 1.4.357 | Captura pantalla |
| VK_LAYER_VALVE_steam_fossilize | 1.4.303 | Pipeline caching Steam |
| VK_LAYER_VALVE_steam_overlay | 1.3.207 | Overlay Steam |

### 2.3 Extensiones de Instancia (14)
- `VK_EXT_debug_report`, `VK_EXT_debug_utils`, `VK_EXT_swapchain_colorspace`
- `VK_KHR_device_group_creation`, `VK_KHR_external_fence_capabilities`
- `VK_KHR_external_memory_capabilities`, `VK_KHR_external_semaphore_capabilities`
- `VK_KHR_get_physical_device_properties2`, `VK_KHR_get_surface_capabilities2`
- `VK_KHR_portability_enumeration`, `VK_KHR_surface`, `VK_KHR_surface_maintenance1`
- `VK_KHR_win32_surface`, `VK_LUNARG_direct_driver_loading`

### 2.4 Formatos de Superficie Soportados (VK_KHR_win32_surface)
- `R8G8B8A8_UNORM` (sRGB)
- `B8G8R8A8_UNORM` (sRGB)
- `R16G16B16A16_SFLOAT` (Extended sRGB Linear / Display Native AMD)
- `A2B10G10R10_UNORM_PACK32` (sRGB / HDR10 ST2084 / BT2020 Linear)

---

## 3. Detalle de ROCm / HIP (vía `_rocm_sdk_devel`)

### 3.1 Información de hipconfig
```text
HIP version: 7.2.0-8017ffed34

==hipconfig
HIP_PATH           : C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel
ROCM_PATH          : C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel
HIP_COMPILER       : clang
HIP_PLATFORM       : amd
HIP_RUNTIME        : rocclr
CPP_CONFIG         : /

==hip-clang
HIP_CLANG_PATH     : C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\lib\llvm\bin
AMD clang version 23.0.0git (https://github.com/ROCm/llvm-project.git 43215c73116c407735c85a180d174f718798c328+PATCHED:c48937daab16e97c0dd600b011d9065b3962b1ca)
Target: x86_64-pc-windows-msvc
Thread model: posix
InstalledDir: C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\lib\llvm\bin
hip-clang-cxxflags : -O3
hip-clang-ldflags  : --driver-mode=g++ -O3 -fuse-ld=lld --ld-path="...\lld-link.exe" --hip-link
```

### 3.2 Variables de Entorno Relevantes (PATH)
- `_rocm_sdk_devel` en `C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin`
- CMake, Ninja, Python 3.13, Git, Go, Node.js, .NET, Rust/Cargo disponibles

### 3.3 Drivers de Pantalla Windows
```
Advanced Micro Devices, Inc.
C:\WINDOWS\System32\DriverStore\FileRepository\u0203304.inf_amd64_a6e5a337568ce3f0\B026373\
  atidx9loader64.dll, amdxx64.dll, amdxc64.dll
AMD Radeon RX 9070
```

---

## 4. Estructura de llama.cpp

### 4.1 `G:\llama.cpp` (Directorio de trabajo / builds precompilados)
```
G:\llama.cpp\
├── bin\
│   ├── llama-b10712-bin-win-rocm-7.14-x64\      # Build ROCm 7.14 (antiguo)
│   ├── llama-b10712-bin-win-vulkan-x64\         # Build Vulkan principal
│   ├── llama-b10796-bin-win-vulkan-x64\         # Build Vulkan reciente
│   ├── llama-b96806d-bin-win-vulkan-x64\        # Build Vulkan anterior
│   ├── ggml-vulkan.dll          (55 MB)         # Backend Vulkan
│   ├── ggml-hip.dll             (NO en este dir)
│   ├── llama-server.exe
│   ├── llama-cli.exe
│   └── llama-bench.exe
├── gguf\                          # Modelos GGUF
├── bat\                           # Scripts .bat de lanzamiento
├── mcp-servers.json               # Config MCP servers
├── presets.ini                    # Presets de configuración
└── *.bat                          # Scripts de lanzamiento modelos
```

### 4.2 `G:\llama.cpp-src` (Código fuente + build HIP)
```
G:\llama.cpp-src\
├── build-hip\                     # Build HIP/ROCm funcional
│   └── bin\
│       ├── ggml-hip.dll           (70 MB)         # Backend HIP
│       ├── llama-server.exe
│       ├── llama-cli.exe
│       └── llama-bench.exe
├── CMakePresets.json              # Presets: vulkan, hip, sycl, msvc, clang
├── CMakeLists.txt
└── ... (fuente completa llama.cpp)
```

### 4.3 CMakePresets.json - Presets Relevantes
```json
{
  "configurePresets": [
    { "name": "vulkan", "cacheVariables": { "GGML_VULKAN": "ON" } },
    { "name": "x64-windows-vulkan-debug",   "inherits": ["base", "vulkan", "debug"] },
    { "name": "x64-windows-vulkan-release", "inherits": ["base", "vulkan", "release"] }
  ]
}
```
*Nota: No hay preset explícito para HIP en CMakePresets.json; el build-hip se configuró manualmente.*

### 4.4 Build HIP - CMakeCache.txt (extracto)
```cmake
GGML_HIP:BOOL=ON
GGML_HIP_GRAPHS:BOOL=ON
GGML_HIP_MMQ_MFMA:BOOL=ON
GGML_HIP_NO_VMM:BOOL=ON
HIP_PLATFORM:STRING=amd
HIP_PATH:UNINITIALIZED=C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel
CMAKE_HIP_COMPILER:UNINITIALIZED=...\clang.exe
hip_HIPCC_EXECUTABLE:FILEPATH=...\hipcc.exe
hip_HIPCONFIG_EXECUTABLE:FILEPATH=...\hipconfig.exe
```

---

## 5. Configuración Actual de Lanzamiento (Vulkan)

### 5.1 Script Principal: `run-qwen3.5-9b-server-opencode.bat`
```bat
.\bin\llama-b10712-bin-win-vulkan-x64\llama-server.exe ^
  --host 0.0.0.0 ^
  --port 8080 ^
  --api-key "anything" ^
  --model "gguf\Qwen3.5-9B\Qwen3.5-9B-UD-Q4_K_XL.gguf" ^
  --n-gpu-layers all ^
  --flash-attn on ^
  --fit off ^
  --ctx-size 65536 ^
  --jinja ^
  --reasoning on ^
  --cache-type-k q4_0 ^
  --cache-type-v q4_0 ^
  --temp 0.6 ^
  --top-p 0.95 ^
  --top-k 20 ^
  --min-p 0.0 ^
  --tools all ^
  --mcp-servers-config "G:\llama.cpp\mcp-servers.json" ^
  --cors-origins "*" ^
  --presence-penalty 0.0 ^
  --repeat-penalty 1.0 ^
  --parallel 1 ^
  --log-verbosity 4 ^
  --cache-idle-slots ^
  --alias Qwen3.5-9B
```

### 5.2 Parámetros Clave Explicados
| Parámetro | Valor | Propósito |
|-----------|-------|-----------|
| `--n-gpu-layers all` | all | Offload completo a GPU |
| `--flash-attn on` | on | Flash Attention (si soportado) |
| `--ctx-size` | 65536 | Contexto 64K tokens |
| `--cache-type-k/v` | q4_0 | KV cache cuantizado 4-bit |
| `--temp` | 0.6 | Temperatura sampling |
| `--top-p` | 0.95 | Nucleus sampling |
| `--top-k` | 20 | Top-k sampling |
| `--min-p` | 0.0 | Min-p sampling |
| `--reasoning on` | on | Modo reasoning (Qwen3) |
| `--jinja` | - | Template Jinja para chat |
| `--tools all` | all | Habilitar todas las tools MCP |
| `--cache-idle-slots` | - | Liberar slots KV cache inactivos |

---

## 6. Modelos Disponibles (GGUF en `G:\llama.cpp\gguf\`)

| Modelo | Archivo | Cuantización | Tamaño aprox. |
|--------|---------|--------------|---------------|
| Qwen3.5-9B | Qwen3.5-9B-UD-Q4_K_XL.gguf | Q4_K_XL (UD) | ~5.5 GB |
| Qwen3.8-27B | Qwen3.8-27B-GSQ-RCO-MTP*.gguf | GSQ-RCO-MTP | ~15-17 GB |
| Qwen3.8-9B Distill | qwen3.8-9b-distill*.gguf | Varios | ~5-6 GB |
| InternVL3-14B | internvl3-14b*.gguf | Varios | ~8-9 GB |
| Llama 3.2 11B Vision | llama32-11b-vision*.gguf | Varios | ~6-7 GB |
| Qwen2.5-VL-7B | qwen25-vl-7b*.gguf | Varios | ~4-5 GB |
| Apertus 1.5-8B | apertus-1.5-8b*.gguf | Varios | ~4-5 GB |

*Nota: La RX 9070 tiene 16 GB VRAM. Modelos >12 GB cuantizados (Q4_K_M/Q5_K_M) caben con offload parcial o KV cache en CPU.*

---

## 7. Limitaciones y Consideraciones Críticas

### 7.1 RX 9070 (RDNA 4 / gfx1103) en Windows
| Aspecto | Situación |
|---------|-----------|
| **ROCm soporte oficial** | Limitado - ROCm 6.x soporta gfx1100 (RDNA 3); gfx1103 en *early enablement* |
| **HIP en Windows** | Funciona vía `_rocm_sdk_devel` (Python), sin herramientas nativas (`amd-smi`, `rocminfo`) |
| **Vulkan** | **Recomendado** - Maduro en Windows, drivers Adrenalin estables |
| **Quantization KV cache** | Funciona en ambos backends (`--cache-type-k/v q4_0`) |
| **Flash Attention** | Vulkan: sí; HIP: verificar (puede caer a SDPA) |
| **MMQ/MFMA kernels** | Habilitados en build HIP (`GGML_HIP_MMQ_MFMA=ON`) |

### 7.2 Diferencias Vulkan vs HIP en llama.cpp
| Característica | Vulkan | HIP/ROCm |
|----------------|--------|----------|
| **Estabilidad Windows** | ✅ Alta | ⚠️ Experimental |
| **Rendimiento RDNA 4** | ✅ Bueno | ⚠️ Kernels genéricos |
| **Tooling/debug** | Validation layers, GFXReconstruct | Limitado (sin rocprof/rocminfo) |
| **Portabilidad Linux** | Requiere recompilar | Nativo (Instinct, EPYC) |
| **Multi-GPU** | Limitado | Mejor soporte (RCCL) |

---

## 8. Referencias de Scripts .bat Existentes

### 8.1 Scripts de Servidor (en `G:\llama.cpp\`)
- `run-qwen3.5-9b-server-opencode.bat` - Principal (Vulkan, 64K ctx, tools MCP)
- `run-qwen3.5-9b-server-opencode-131k.bat` - Contexto 131K
- `run-qwen3.5-9b-server-test.bat` - Testing
- `run-qwen3.8-27b-server-opencode.bat` - Qwen3.8-27B Vulkan
- `run-Qwen3.8-27B-GSQ-RCO-server.bat` - GSQ-RCO Vulkan
- `run-Qwen3.8-27B-GSQ-RCO-server-TUNED.bat` - Tuned GSQ-RCO
- `run-qwen38-hip-lan.bat` - **HIP/ROCm** (build-hip)
- `start-qwen3.5-9b-hip-lan-131k-q8.bat` - **HIP/ROCm** 131K Q8
- `start-qwen38-hip-lan.bat` - **HIP/ROCm** Qwen3.8
- `start-Qwythos-9B-Claude-Mythos-hip-lan.bat` - **HIP/ROCm** Mythos
- `run-llama32-11b-vision-server.bat` - Llama 3.2 Vision
- `run-internvl3-14b-server.bat` - InternVL3
- `run-apertus-1.5-8b-server.bat` - Apertus

### 8.2 Scripts CLI
- `run-qwen3.5-9b-cli.bat`, `run-qwen3.8-27b-cli.bat`, etc.

---

## 9. Próximos Pasos Propuestos para Skill `local-ai-use`

### 9.1 Fase 1: Detección y Validación (Scripts Python)
```python
# G:\Proyectos\AMD.AI\scripts\detect_local.py
- Detectar GPU via vulkaninfo + hipconfig
- Mapear deviceID 0x7550 → gfx1103 (RDNA 4)
- Reportar VRAM real, CUs, WGP, clock speeds
- Validar backends: Vulkan (primario), HIP (fallback)
- Matriz compatibilidad: modelo × backend × cuantización
```

### 9.2 Fase 2: Benchmarking Automatizado
```python
# G:\Proyectos\AMD.AI\scripts\bench_local.py
- llama-bench matrix: modelo × cuantización × backend × ctx-size × n-gpu-layers
- Métricas: tok/s (prefill/decode), VRAM peak, latencia P50/P99
- Output: JSON + CSV + gráficos comparativos Vulkan vs HIP
- Baseline persistente para regression testing
```

### 9.3 Fase 3: Auto-Tuning
```python
# G:\Proyectos\AMD.AI\scripts\tune_local.py
- Grid search: n-gpu-layers, batch-size, flash-attn, cache-type, threads
- Perfiles: "max-throughput", "low-latency", "max-context", "balanced"
- Persistencia en presets.ini por modelo/backend
```

### 9.4 Fase 4: Análisis y Observabilidad
```python
# G:\Proyectos\AMD.AI\scripts\analyze_local.py
- GGML_METRICS + Vulkan validation layers + HIP profiling
- Detección cuellos de botella: memory-bound vs compute-bound
- Export: Chrome Trace, Perfetto, Prometheus
```

### 9.5 Fase 5: Integración Skill AMD
```
skills/local-ai-use/
├── SKILL.md              # Descripción, triggers, prerequisites
├── skill-card.md         # Visual para marketplaces
├── reference.md          # CLI reference completo
├── scripts/
│   ├── detect_local.py
│   ├── bench_local.py
│   ├── tune_local.py
│   └── analyze_local.py
├── data/
│   ├── model_compatibility.json
│   ├── gpu_presets.json
│   └── quantization_guide.json
└── evals/
    ├── benchmark_baselines.json
    └── regression_tests.py
```

---

## 10. Decisiones Pendientes

1. **Backend prioritario:** ¿Vulkan (estable Windows) o HIP (portabilidad Linux/Instinct)?
2. **Modelos objetivo:** Qwen3.5-9B, Qwen3.8-27B, DeepSeek-R1, Gemma-3, otros?
3. **Métricas clave:** Throughput (tok/s), latencia (TTFT/TPOT), VRAM efficiency, power/perf?
4. **Integración:** Solo CLI/scripts, o también API server + MCP + OpenAI-compatible?
5. **Distribución:** Skill standalone en este repo, o contribuir upstream a `amd/skills`?
6. **Testing real:** ¿Disponibilidad de GPUs AMD Instinct / EPYC / Ryzen AI para validación cruzada?

---

## 11. Archivos de Referencia en Workspace

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| Este documento | `G:\Proyectos\AMD.AI\docs\ENTORNO_RX9070_LLAMA_CPP.md` | Documentación completa |
| Vulkan info raw | `vulkaninfo --summary` | Salida completa vulkaninfo |
| HIP config raw | `hipconfig --full` | Salida completa hipconfig |
| CMakePresets | `G:\llama.cpp-src\CMakePresets.json` | Presets CMake llama.cpp |
| CMakeCache HIP | `G:\llama.cpp-src\build-hip\CMakeCache.txt` | Config build HIP |
| Scripts .bat | `G:\llama.cpp\*.bat` | Scripts lanzamiento modelos |
| Modelos GGUF | `G:\llama.cpp\gguf\` | Modelos cuantizados |

---

## 12. Comandos de Verificación Rápida

```powershell
# Verificar Vulkan
vulkaninfo --summary

# Verificar HIP/ROCm
& "C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin\hipconfig.exe" --full

# Test llama.cpp Vulkan
G:\llama.cpp\bin\llama-b10712-bin-win-vulkan-x64\llama-bench.exe -m gguf\Qwen3.5-9B\Qwen3.5-9B-UD-Q4_K_XL.gguf -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0 -r 3 -o json

# Test llama.cpp HIP (requiere ROCm SDK en PATH)
$env:PATH = "C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin;" + $env:PATH
G:\llama.cpp-src\build-hip\bin\llama-bench.exe -m gguf\Qwen3.5-9B\Qwen3.5-9B-UD-Q4_K_XL.gguf -ngl -1 -p 512 -n 256 -b 2048 -fa auto -ctk q4_0 -ctv q4_0 -r 3 -o json
```

---

## 13. Scripts de Automatización Creados

| Script | Descripción | Uso |
|--------|-------------|-----|
| `detect_local.py` | Detección completa entorno + validación backends + matriz compatibilidad | `python detect_local.py --validate-backends --compatibility` |
| `bench_local.py` | Benchmarking automatizado Vulkan vs HIP con matriz parametrizable | `python bench_local.py --model Qwen3.5-9B --backend both --quick --yes` |

### 13.1 detect_local.py - Opciones
```bash
python detect_local.py                          # Detección completa + reporte
python detect_local.py --json-only              # Solo JSON (CI/CD)
python detect_local.py --validate-backends      # Validar backends llama.cpp
python detect_local.py --compatibility          # Matriz modelo×backend×cuantización
python detect_local.py --output report.json     # Guardar JSON
```

### 13.2 bench_local.py - Opciones
```bash
python bench_local.py --list-models             # Listar modelos GGUF detectados
python bench_local.py --model Qwen3.5-9B --backend vulkan --quick --yes --repetitions 1
python bench_local.py --model Qwen3.5-9B --backend hip --quick --yes --repetitions 1
python bench_local.py --model Qwen3.5-9B --backend both --output results.csv --json-output results.json
python bench_local.py --model DeepSeek --backend both --repetitions 3  # Benchmark completo
```

---

## 14. Resultados de Benchmark: Qwen3.5-9B-Q4_K (5.56 GB)

### 14.1 Resumen Comparativo Vulkan vs HIP

| Métrica | **Vulkan (b10712)** | **Vulkan (b10796)** | **HIP/ROCm** | Ganador |
|---------|---------------------|---------------------|--------------|---------|
| **Pre-fill max (ngl=0)** | 3,296 tok/s | 3,213 tok/s | **4,539 tok/s** | 🏆 **HIP** (+38%) |
| **Decode max (ngl=0)** | 28,642 tok/s | 28,452 tok/s | 28,375 tok/s | 🏆 **Vulkan** (+1%) |
| **Pre-fill max (ngl=-1)** | 924 tok/s | 923 tok/s | **1,552 tok/s** | 🏆 **HIP** (+68%) |
| **Decode max (ngl=-1)** | 2,965 tok/s | 2,960 tok/s | **3,501 tok/s** | 🏆 **HIP** (+18%) |

### 14.2 Hallazgos Clave

1. **HIP/ROCm en Windows FUNCIONA** vía `_rocm_sdk_devel` Python package
   - Requiere ROCm SDK en PATH (ya configurado permanentemente en User PATH)
   - Detecta RX 9070 como **gfx1201** (vs gfx1103 en Vulkan)
   - Wave size: 32 (vs 64 en Vulkan)

2. **HIP superior para GPU completa (ngl=-1)**:
   - Prefill: 1.5-1.7x más rápido
   - Decode: 1.18x más rápido
   - Config recomendada: `ngl=-1, prompt=2048, gen=256, batch=1024, fa=auto, cache=q4_0`

3. **Vulkan ligeramente mejor en CPU-only (ngl=0) decode**:
   - Diferencia ~1% (28,642 vs 28,375 tok/s)
   - Build b10712 ≈ b10796 (diferencias <2%)

4. **Ambos backends estables**: 0 fallos en 48 combinaciones testeadas

### 14.3 Archivos de Resultados
```
G:\Proyectos\AMD.AI\docs\
├── BENCHMARK_RESULTS_QWEN3.5-9B.md      # Análisis completo
├── bench_test.csv / .json               # Vulkan (32 combos)
├── bench_hip_test.csv / .json           # HIP (16 combos)
├── detection_report_final.json          # Detección entorno
└── ENTORNO_RX9070_LLAMA_CPP.md          # Este documento
```

---

## 15. Fix Permanente: ROCm SDK en PATH de Usuario

**Problema:** `llama-bench.exe` HIP fallaba con exit code -1073741515 (DLLs ROCm no encontradas)

**Solución:** Añadido permanentemente al PATH de usuario:
```
C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin
```

**Verificación:**
```powershell
$env:PATH -split ';' | Select-String rocm_sdk_devel
# Debe mostrar la ruta del SDK
```

**Nota:** Requiere reiniciar terminal/PowerShell para tomar efecto en nuevas sesiones.

---

## 16. Próximos Pasos para Skill `local-ai-use`

1. **Fase 3 - Auto-tuning (`tune_local.py`)**:
   - Grid search automático: ngl, batch, flash-attn, cache-type
   - Perfiles: "max-throughput", "low-latency", "max-context", "balanced"
   - Persistencia en `presets.ini` por modelo/backend

2. **Fase 4 - Análisis (`analyze_local.py`)**:
   - GGML_METRICS + Vulkan validation layers + HIP profiling
   - Detección cuellos de botella: memory-bound vs compute-bound
   - Export: Chrome Trace, Perfetto, Prometheus

3. **Fase 5 - Integración Skill AMD**:
   - SKILL.md, skill-card.md, reference.md
   - data/: model_compatibility.json, gpu_presets.json, quantization_guide.json
   - evals/: benchmark_baselines.json, regression_tests.py

---

*Documento actualizado tras benchmark 2026-09-05. Para nuevos benchmarks, ejecutar `bench_local.py`.*