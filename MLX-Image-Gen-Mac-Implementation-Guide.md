# MLX Image Generation on Apple Silicon — Implementation Guide

**Version:** 1.0 | **Date:** 2026-06-30
**Target:** Apple Silicon Macs (M1–M5), macOS Tahoe 26.x (26.2+ for M5 Neural Accelerator)
**Audience:** AI agent continuing the setup, testing, and production deployment of local image generation

---

## 1. What This Guide Is

This is a **condensed, actionable reference** distilled from the full 100 KB+ research plan (`research_mac_image_models.md`) and 84 KB research report (`mlx-image-gen-mac-2026.md`). It contains exactly what you need to:

1. Set up the runtime environment (mflux, ComfyUI, ComfyUI-MLX)
2. Download the correct Mac-compatible models
3. Run image generation via CLI, Python API, or ComfyUI
4. Benchmark and validate the installation
5. Avoid the 20 known pitfalls

**For deep context** (architecture deep-dives, cited benchmarks, quantization theory), see `mlx-image-gen-mac-2026.md`.
**For the full install guide** (step-by-step ComfyUI setup, workflows, troubleshooting), see `comfyui-set-mac-SKILL.md`.

---

## 2. Current State of the Ecosystem (H1 2026)

### 2.1 Critical Changes Since v1.4

| Change | Impact | Action |
|--------|--------|--------|
| **DiffusionKit archived (Mar 21, 2026)** | `thoddnn/ComfyUI-MLX` is stale, no updates since Nov 2025 | Migrate to **Mflux-ComfyUI** by `@raysers` for ComfyUI↔MLX bridging |
| **mflux 0.18.0 (Jun 7, 2026)** | Full Python API now available (not CLI-only) | Use `model = ZImageTurbo(quantize=8); image = model.generate_image(...)` for production |
| **M5 Neural Accelerator** | 3.8× speedup vs M4 on FLUX-dev-4bit via MLX | Requires **macOS 26.2+**; earlier versions run at M4 speed |
| **Ideogram 4 MLX requires special branch** | Stock mflux can't load MLXBits weights (FP8 layout) | Install `ideogram-mlx-forge-loader` branch or standalone `mlx-forge` |
| **Quantization = memory tool, NOT speed** | Int4 doesn't speed up diffusion (compute-bound) | Prefer int8 unless memory-constrained; int4 halves footprint only |

### 2.2 Model Landscape (9 families, mflux 0.18.0)

| Model | Params | Best MLX Quant | Disk Size | RAM Used | License | Strength |
|-------|--------|----------------|-----------|----------|---------|----------|
| **Z-Image Turbo** | 6B | int8 | ~11 GB | ~12 GB | Open-source | Speed + quality |
| **FLUX.2 [klein] 4B** | 4B | int8 | ~5 GB | ~6 GB | **Apache 2.0** | Fastest commercial-safe |
| **FLUX.2 [klein] 9B** | 9B | int4/int8 | ~18 GB | ~18 GB | NC | Quality + editing |
| **FLUX.2 [dev]** | 32B+24B | int4 | ~24 GB | ~24 GB | NC | Max quality open-weight |
| **Ideogram 4** | 9.3B+8B | int4/int8 | 15–27 GB | 15–27 GB | NC | Typography + JSON layout |
| **Qwen-Image-2512** | 20B | 4-bit | 25.9 GB | ~26 GB | **Apache 2.0** | Multilingual commercial |
| **FIBO** | 8B+3B | 4-bit | ~7 GB | ~8 GB | CC-BY-NC | JSON-native, lightest |
| **ERNIE-Image** | 8B | int8 | ~14 GB | ~14 GB | Verify | Vivid, high-contrast |
| **FLUX.1 (legacy)** | 12B | int8 | ~11 GB | ~12 GB | NC (dev) / Apache (schnell) | Legacy with Kontext |

### 2.3 Hardware Recommendations by Chip

| Chip | Bandwidth | RAM | Recommended Model |
|------|-----------|-----|------------------|
| M4 Base | 120 GB/s | 16–32 GB | Z-Image Turbo int8 or FLUX.2 klein 4B |
| M4 Pro | 273 GB/s | 24–48 GB | FLUX.2 klein 4B (24GB) or Ideogram 4 int4 / Qwen-Image 4-bit (48GB) |
| M4 Max | 546 GB/s | 36–128 GB | Any model; FLUX.2 dev int4 or Ideogram 4 int8 |
| M5 Base | 153 GB/s | 16–24 GB | Same as M4 but 3.8× faster (needs macOS 26.2+) |
| M5 Pro/Max | TBD | 24–128 GB | All models with Neural Accelerator speedup |

---

## 3. Installation & Setup

### 3.1 Prerequisites

```bash
# Verify Apple Silicon
uname -m  # → arm64

# Verify macOS version (Tahoe 26.x; 26.2+ for M5)
sw_vers

# Install Homebrew
which brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12
brew install python@3.12

# Install uv (REQUIRED for companion scripts)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3.2 Create Virtual Environment

```bash
mkdir -p ~/.venv
/opt/homebrew/bin/python3.12 -m venv ~/.venv
source ~/.venv/bin/activate
pip install --upgrade pip
```

### 3.3 Install mflux + MLX Companions

```bash
# Recommended: uv (faster, no venv needed for scripts)
uv tool install --upgrade mflux --with hf_transfer

# OR install in venv
pip install mflux huggingface_hub hf_transfer

# Optional companions
uv pip install mlx-taef     # Live preview during generation
uv pip install mlx-teacache # TeaCache step-skipping (30-50% speedup)
```

Verify:
```bash
mflux --version  # → 0.18.0 or later
```

### 3.4 Install ComfyUI + Mflux-ComfyUI Bridge

```bash
# Clone ComfyUI
cd ~
git clone https://github.com/comfyanonymous/ComfyUI.git

# Install dependencies
source ~/.venv/bin/activate
cd ~/ComfyUI
pip install -r requirements.txt
pip install torch torchvision torchaudio
pip install sqlalchemy alembic opencv-python gitpython toml scikit-image

# Install Mflux-ComfyUI custom node (the CURRENT ComfyUI↔MLX bridge)
cd ~/ComfyUI/custom_nodes
git clone https://github.com/raysers/Mflux-ComfyUI.git
cd Mflux-ComfyUI
pip install -r requirements.txt  # if any

# Restart ComfyUI
cd ~/ComfyUI
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &

# Verify
curl -s http://127.0.0.1:8188/system_stats | python3 -m json.tool
```

> CRITICAL: Use `nohup` + redirect to log file to avoid `[Errno 32] Broken pipe` crash when backgrounded.

---

## 4. Model Downloads

### 4.1 Mac-Compatible Models (bf16 or MLX-quantized ONLY)

> WARNING: Do NOT use fp8 models on Mac — Float8_e4m3fn is NOT supported on Apple Silicon MPS backend.

```bash
cd ~/ComfyUI/models
mkdir -p diffusion_models text_encoders vae loras

# === Z-Image Turbo (recommended starter, ~11 GB) ===
curl -L -o diffusion_models/z_image_turbo_bf16.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/diffusion_models/z_image_turbo_bf16.safetensors"

# === Z-Image text encoder ===
curl -L -o text_encoders/qwen_3_4b.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/text_encoders/qwen_3_4b.safetensors"

# === Z-Image VAE ===
curl -L -o vae/ae.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors"

# === FLUX.2 klein 4B (Apache 2.0, commercial-safe, ~5 GB) ===
hf download mlx-community/FLUX.2-klein-4B-distilled-8bit \
  --local-dir diffusion_models/flux2-klein-4b-mlx

# === Qwen-Image-2512 4-bit (Apache 2.0, requires 48GB Mac) ===
hf download mlx-community/Qwen-Image-2512-4bit \
  --local-dir diffusion_models/qwen-image-2512-4bit

# === Ideogram 4 MLX (requires ideogram-mlx-forge-loader branch) ===
hf download MLXBits/ideogram-4-mlx-q4 --local-dir diffusion_models/ideogram-4-mlx-q4
hf download MLXBits/ideogram-4-mlx-q8 --local-dir diffusion_models/ideogram-4-mlx-q8

# === FIBO 4-bit (non-commercial, ~7 GB) ===
hf download briaai/Fibo-mlx-4bit --local-dir diffusion_models/fibo-mlx-4bit

# === Krea 2 Turbo (bf16, ~24 GB) ===
curl -L -o diffusion_models/krea2_turbo_bf16.safetensors \
  "https://huggingface.co/Comfy-Org/krea2/resolve/main/diffusion_models/krea2_turbo_bf16.safetensors"

# === LoRA example (Ideogram 4 TurboTime — architecture-specific!) ===
curl -L -o loras/ideogram4_turbotime_v1.safetensors \
  "https://huggingface.co/ostris/ideogram_4_turbotime_lora/resolve/main/ideogram_4_turbotime_v1.safetensors"
```

> NOTE: LoRAs are model-specific. The TurboTime LoRA works ONLY with Ideogram 4 — applying to FLUX or Z-Image will crash.

---

## 5. Running Image Generation

### 5.1 Method 1: mflux CLI (fastest setup)

```bash
# Z-Image Turbo
mflux-generate-z-image-turbo \
  --prompt "A puffin standing on a cliff" \
  --width 1280 --height 500 \
  --seed 42 --steps 9 -q 8 \
  --output z_image_out.png

# FLUX.2 klein 4B (Apache 2.0)
mflux-generate-flux2 \
  --model ./flux2-klein-4b-mlx \
  --prompt "a product photo of a ceramic mug, soft natural light" \
  --steps 4 --seed 42 --width 1024 --height 1024 \
  --output flux2_out.png

# Ideogram 4 (requires forge-loader branch)
mflux-generate-ideogram4 \
  --model-path ./ideogram-4-mlx-q4 \
  --prompt "a ginger cat wearing a tiny wizard hat reading a spellbook" \
  --preset V4_QUALITY_48 \
  --output ideogram_out.png
```

### 5.2 Method 2: mflux Python API (recommended for production)

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux"]
# ///
from mflux.models.z_image import ZImageTurbo

model = ZImageTurbo(quantize=8)
image = model.generate_image(
    prompt="A puffin standing on a cliff",
    seed=42,
    num_inference_steps=9,
    width=1280,
    height=500,
)
image.save("puffin.png")
```

Full script: `research/scripts/01_z_image_turbo_basic.py`

### 5.3 Method 3: ComfyUI + Mflux-ComfyUI (visual node editor)

After installing the Mflux-ComfyUI custom node (Section 3.4), create a minimal 3-node workflow:

```json
{
  "1": {
    "class_type": "MfluxLoader",
    "inputs": { "model": "mlx-community/FLUX.1-dev", "quantize": 8 }
  },
  "2": {
    "class_type": "MfluxSampler",
    "inputs": {
      "prompt": "cinematic mountain landscape at golden hour",
      "seed": 42, "steps": 20, "width": 1024, "height": 1024,
      "model": ["1", 0]
    }
  },
  "3": {
    "class_type": "SaveImage",
    "inputs": { "filename_prefix": "mflux_out", "images": ["2", 0] }
  }
}
```

### 5.4 Method 4: FastAPI Production Server

```python
from fastapi import FastAPI
from pydantic import BaseModel
from mflux.models.z_image import ZImageTurbo
import base64, io

app = FastAPI()
model = ZImageTurbo(quantize=8)

class GenerateRequest(BaseModel):
    prompt: str
    seed: int = 42
    steps: int = 9
    width: int = 1024
    height: int = 1024

@app.post("/v1/images/generations")
async def generate(req: GenerateRequest):
    image = model.generate_image(
        prompt=req.prompt, seed=req.seed,
        num_inference_steps=req.steps,
        width=req.width, height=req.height,
    )
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return {"data": [{"b64_json": base64.b64encode(buf.getvalue()).decode()}]}
```

Full script: `research/scripts/02_production_server.py`

---

## 6. Companion Scripts Reference

All scripts are in `research/scripts/` and are MIT-licensed. Run with `uv run <script>.py`.

| # | Script | Purpose | Maps To |
|---|--------|---------|---------|
| 01 | `01_z_image_turbo_basic.py` | Minimal mflux Python API | Method 2 (§5.2) |
| 02 | `02_production_server.py` | FastAPI OpenAI-compatible server | Method 4 (§5.4) |
| 03 | `03_multi_lora.py` | Multi-LoRA loading with scales | Production §5.3 |
| 04 | `04_image_to_image.py` | Image-to-image editing | Production §5.4 |
| 05 | `05_controlnet_depth.py` | ControlNet Canny + Depth Pro | Production §5.5 |
| 06 | `06_live_preview.py` | Live preview with mlx-taef | Production §5.6 |
| 07 | `07_teacache_speedup.py` | TeaCache 30-50% speedup | Production §5.7 |
| 08 | `08_metadata_reproducibility.py` | Metadata export/reproduce | Production §5.8 |
| 09 | `09_benchmark_harness.py` | Hardware benchmark suite | Benchmarking (§7) |
| 10 | `10_commercial_safe_pipeline.py` | Apache 2.0 pipeline | Production §5.10 |

---

## 7. Benchmarking & Validation

### 7.1 Quick Validation (5 minutes)

```bash
# 1. Verify mflux installation
mflux --version  # Should show 0.18.0+

# 2. Verify ComfyUI is running
curl -s http://127.0.0.1:8188/system_stats | python3 -m json.tool

# 3. Generate first image
uv run research/scripts/01_z_image_turbo_basic.py
# Expected: puffin.png generated in ~15-60s depending on hardware

# 4. Verify output
ls -lh puffin.png  # Should be non-zero PNG
```

### 7.2 Full Benchmark Suite

```bash
uv run research/scripts/09_benchmark_harness.py
# Expected output: table of mean/min/max wall-clock times + peak RSS per model
```

### 7.3 Expected Performance (cited from primary sources)

| Model | Hardware | Steps | Resolution | Time | RSS |
|-------|----------|-------|------------|------|-----|
| Z-Image Turbo int8 | M4 Pro 24GB | 9 | 1024×1024 | ~15-25s | ~12 GB |
| FLUX.2 klein 4B int8 | M4 Pro 24GB | 4 | 1024×1024 | ~8-15s | ~6 GB |
| FLUX-dev-4bit | M4 (base) | 20 | 1024×1024 | ~50-90s | ~22 GB |
| FLUX-dev-4bit | M5 Max | 20 | 1024×1024 | ~13-24s | ~22 GB |
| Ideogram 4 int4 | M5 Max | 20 | 1024×1024 | ~2:12 | ~17 GB |
| Flux.1 Dev Q6_K | M4 Pro 24GB | 20 | 1024×1024 | ~50-90s | ~10 GB |
| SD 1.5 | M4 Pro 24GB | 20 | 512×512 | ~5-10s | ~3 GB |
| ComfyUI PyTorch MPS | M4 Pro 24GB | 20 | 1024×1024 | ~60-80s | ~14 GB |

---

## 8. Recommended Settings per Model

### 8.1 Z-Image Turbo (best default for Mac)

```yaml
sampler: euler_ancestral or DPM++ SDE
scheduler: simple or beta57
steps: 8 (range: 6-12)
cfg: 1.0  # Low CFG by design
resolution: 1024×1024 (native)
lora_strength: 0.4-0.7
```

### 8.2 FLUX.2 Klein 4B

```yaml
sampler: euler
scheduler: beta57 (or simple)
steps: 4-12 (distilled) or 50 (base)
cfg: 7.0
resolution: 1024×1024
```

### 8.3 Krea 2 Turbo (IMPORTANT)

```yaml
sampler: euler_ancestral
steps: 8
guidance: 0.0  # MUST be 0 — CFG-free by design!
resolution: 1024×1024
```

> CRITICAL: Using standard CFG (e.g., 7.0) with Krea 2 Turbo DESTROYS image quality.

### 8.4 Ideogram 4 (JSON prompt recommended)

```python
import json
prompt = {
    "high_level_description": "A futuristic workspace with a glowing monitor.",
    "style_description": {
        "aesthetics": "Cyberpunk, neon-lit, high contrast.",
        "lighting": "Volumetric blue and magenta rim lighting.",
        "color_palette": ["#00FFFF", "#FF00FF", "#1A1A1A"]
    },
    "compositional_decomposition": {
        "background": "Dark server room with blinking LEDs.",
        "elements": [
            {"type": "obj", "bbox": [200, 300, 800, 700], "desc": "A sleek curved monitor displaying code."},
            {"type": "text", "bbox": [250, 400, 750, 500], "text": "SYSTEM ONLINE", "desc": "Bright green terminal font."}
        ]
    }
}
```

---

## 9. 20 Pitfalls & Solutions

| # | Pitfall | Solution |
|---|---------|----------|
| 1 | `[Errno 32] Broken pipe` crash | Launch ComfyUI with `nohup` + stdout/stderr to log file |
| 2 | fp8 models won't load on Mac | Use bf16 or MLX-quantized (int4/int8) variants |
| 3 | Krea 2 Turbo images look burnt | Set guidance=0.0 exactly (CFG-free model) |
| 4 | LoRA causes crash | LoRAs are model-specific — don't mix architectures |
| 5 | OOM on 16GB Macs | Use int4 quantization for Ideogram 4; avoid int8 (27 GB) |
| 6 | ComfyUI slow vs bare mflux | PyTorch MPS is 2-3× slower; use Mflux-ComfyUI for MLX backend |
| 7 | M5 not faster than M4 | Must be on macOS 26.2+ for Neural Accelerator support |
| 8 | Ideogram 4 MLX won't load in mflux | Requires `ideogram-mlx-forge-loader` branch |
| 9 | Qwen-Image 4-bit OOM on 24GB Mac | Need 48GB Mac or use FLUX.2 klein 4B instead |
| 10 | Quantization doesn't speed up | Expected — quantization saves memory, not compute (diffusion is compute-bound) |
| 11 | thoddnn/ComfyUI-MLX not working | Abandoned — use Mflux-ComfyUI (raysers) instead |
| 12 | DiffusionKit import errors | Archived Mar 2026 — don't use any DiffusionKit-dependent code |
| 13 | Metal watchdog timeout on M1/M2 | Use shorter command buffers, reduce batch size, set `-q 6` |
| 14 | M4 Air thermal throttling | Fanless — limit to 3-5 consecutive generations or use low-res |
| 15 | ComfyUI `library not found` errors | Install with `pip install sqlalchemy alembic opencv-python gitpython toml scikit-image` |
| 16 | Model download hangs | Use `hf download` instead of `curl` for HuggingFace repos (handles LFS) |
| 17 | Gated repo access denied | Run `huggingface-cli login` and accept model card terms |
| 18 | Progress bar corruption (TQDM) | Use `TQDM_DISABLE=1 DISABLE_TQDM=1` env vars |
| 19 | mflux 0.18 API breaks older scripts | Check changelog — `ZImageTurbo(quantize=8)` is new syntax |
| 20 | Notebook/lab not importing mflux | Use `uv run --script` pattern, not bare `pip install` |

---

## 10. Production Deployment Patterns

### 10.1 Decision Matrix

| Use Case | Recommended Runtime | Why |
|----------|---------------------|-----|
| Maximum performance | mflux Python API (bare) | No overhead, direct MLX |
| Visual iteration | Mflux-ComfyUI | Node graph UX on MLX backend |
| Non-technical users | Draw Things (App Store) | Easiest GUI, Metal FlashAttention 2.0 |
| SaaS/API endpoint | FastAPI + mflux | OpenAI-compatible endpoint |
| iOS/macOS app | FluxForge Studio (Swift) | Native Swift MLX pipeline |
| Batch processing | mflux CLI scripts | Simple shell automation |

### 10.2 Critical: Never Use These

| Runtime | Status | Why |
|---------|--------|-----|
| `thoddnn/ComfyUI-MLX` | **DEPRECATED** | Built on archived DiffusionKit (Mar 2026) |
| DiffusionKit directly | **ARCHIVED** | No updates since Mar 21, 2026 |
| fp8 models on MPS | **INCOMPATIBLE** | Float8_e4m3fn not supported on Apple Silicon mflux |
| DiffusionBee | **STALE** | Last update Aug 2024, no FLUX.2 |

---

## 11. Mac Model Path Reference

All models go into `~/ComfyUI/models/` with these subdirectories:

```
~/ComfyUI/models/
├── diffusion_models/     # UNet checkpoints (bf16 safetensors)
│   ├── z_image_turbo_bf16.safetensors
│   ├── krea2_turbo_bf16.safetensors
│   ├── flux2-klein-4b-mlx/          # MLX-quantized (directory)
│   ├── qwen-image-2512-4bit/        # MLX-quantized (directory)
│   ├── ideogram-4-mlx-q4/           # MLX-quantized (directory)
│   └── fibo-mlx-4bit/               # MLX-quantized (directory)
├── text_encoders/        # CLIP/T5/Qwen text encoders
│   ├── qwen_3_4b.safetensors
│   └── qwen3_vl_8b.safetensors      # For Ideogram 4
├── vae/                  # VAE decoders
│   ├── ae.safetensors               # Z-Image/Krea VAE
│   └── flux_vae.safetensors         # FLUX VAE
├── loras/                # LoRA adapters (model-specific!)
│   ├── ideogram4_turbotime_v1.safetensors
│   └── flux_lora_example.safetensors
├── model_patches/        # ControlNet Union patches
│   └── Z-Image-Turbo-Fun-Controlnet-Union.safetensors
└── controlnet/           # ControlNet models
    └── (FLUX-compatible ControlNet)
```

---

## 12. ComfyUI Workflow Templates

### 12.1 Z-Image Turbo (8-node PyTorch MPS)

```
PrimitiveStringMultiline (prompt) → CLIPTextEncode (qwen_3_4b)
PrimitiveInt (seed/width/height/steps/cfg) → KSampler
UNETLoader (z_image_turbo_bf16) → ModelSamplingAuraFlow → FluxGuidance → KSampler
VAELoader (ae.safetensors) → VAEDecode
KSampler → VAEDecode → SaveImage
```

### 12.2 Mflux-ComfyUI (3-node MLX, simpler)

```
MfluxLoader (select model + quantize) → MfluxSampler (prompt/steps/cfg) → SaveImage
```

### 12.3 ControlNet + LoRA Extensions (Z-Image Turbo)

```
LoadImage → ResizeImage → ControlNetPreprocessor (Canny/Depth/Pose)
ControlNetLoader (Fun Union patch) → ControlNetApply
PowerLoRALoader (rgthree) → MLXSampler
```

---

## 13. Verification Checklist

Before declaring the installation complete:

- [ ] `mflux --version` shows 0.18.0+
- [ ] `uv --version` works
- [ ] Python 3.12 active in venv
- [ ] `curl http://127.0.0.1:8188/system_stats` returns JSON (ComfyUI running)
- [ ] `01_z_image_turbo_basic.py` generates puffin.png successfully
- [ ] `10_commercial_safe_pipeline.py` generates image with Apache 2.0 model
- [ ] `09_benchmark_harness.py` completes for at least one model
- [ ] No fp8 models in `diffusion_models/`
- [ ] No DiffusionKit or thoddnn/ComfyUI-MLX in dependencies
- [ ] M5 users: `sw_vers` shows 26.2+
- [ ] Commercial use: license audit completed (only Apache 2.0 models)
- [ ] Mac-safe launch: ComfyUI running with `nohup` + log redirect

---

## 14. File Reference (What's Where)

| File | What It Contains |
|------|------------------|
| `comfyui-set-mac-SKILL.md` | **Full install guide** (2,917 lines, v1.5) |
| `mlx-image-gen-mac-2026.md` | **Deep research report** (11.5k words, 49 citations) |
| `info.md` | Condensed Ideogram 4 + Krea 2 setup guide |
| `MLX-Optimized_Z-Image_Turbo_and_FLUX_Workflows.md` | M4 Pro 128GB targeted workflows |
| `research_mac_image_models.md` | Original 10-phase research plan (predecessor) |
| `research/scripts/*.py` | 10 production-ready Python scripts |
| `research/notes/*.txt` | 14 primary source extracts (citations) |
| `zai_session_1.md` | Full research session transcript |

---

*This guide distills the actionable core from a 200+ KB research corpus. For the "why" behind every recommendation, see `mlx-image-gen-mac-2026.md`. For step-by-step walkthroughs, see `comfyui-set-mac-SKILL.md`.*
