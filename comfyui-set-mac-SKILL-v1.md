# ComfyUI Mac Silicon Installation & Configuration Guide

## Overview

This guide provides step-by-step instructions for installing ComfyUI on a Mac with Apple Silicon (M1/M2/M3/M4), including Python environment setup, model downloads, and configuration for optimal performance.

**Target System:** Mac with Apple Silicon, 16GB+ RAM (recommended 32GB+)
**ComfyUI Version:** 0.26.0
**Python Version:** 3.12.x (recommended), 3.13.x (bleeding edge, some custom nodes may fail)

### ⚠️ Critical Mac-Specific Issues

This guide addresses two critical issues for Mac users:

1. **Broken Pipe Error:** ComfyUI crashes with `[Errno 32] Broken pipe` when it is backgrounded with stdout/stderr still attached to a shell pipe that later closes. **Fix:** launch with `nohup` and redirect stdout/stderr to `comfyui-runtime.log`.

2. **fp8 Model Incompatibility:** Ideogram 4 fp8 models use Float8_e4m3fn format which is NOT supported on Apple Silicon MPS backend. **Fix:** Use bf16 models instead (z_image_turbo_bf16, krea2_turbo_bf16).

For detailed solutions, see [Troubleshooting & Pitfalls](#9-troubleshooting--pitfalls).

### 📦 Model Management

For the complete workflow of researching, downloading, installing, and creating workflows for new models, see the **ComfyUI Model Manager** skill:

```bash
~/.pi/agent/skills/comfyui-model-manager/SKILL.md
```

This covers: model discovery (HuggingFace/CivitAI), LFS/gated repo handling, compatibility checking, workflow generation for SDXL/Flux/Krea2/Z-Image/Pony, and validation.

---

## Model Landscape (June 2026)

This guide covers three flagship models available for local Apple Silicon inference:

### Ideogram 4.0
- **Released:** June 3, 2026 — Ideogram's first open-weight text-to-image model
- **Architecture:** 9.3B parameter single-stream DiT (Diffusion Transformer)
- **Text Encoder:** Qwen3-VL-8B-Instruct (vision-language model, replaces CLIP/T5)
- **Key Feature:** Trained on structured JSON captions → enables precise bounding-box layout control
- **License:** Code is Apache-2.0; **model weights are Non-Commercial** (Ideogram 4 Non-Commercial Model Agreement). Do NOT use for commercial SaaS or paid work without an enterprise license.

### Krea 2
- **Variants:** Two distinct models:
  - **Krea 2 RAW** — Full-step base checkpoint, suitable for fine-tuning and LoRA training
  - **Krea 2 Turbo** — 8-step distilled checkpoint, optimized for fast inference
- **Key Feature:** Krea 2 Turbo operates **completely CFG-free** (guidance scale = 0)
- **License:** Open-source foundation model

### Z-Image Turbo
- **Architecture:** Flow matching with AuraFlow sampling
- **Text Encoder:** Qwen3 4B
- **Key Feature:** 8-step generation with CFG = 1, excellent for Mac due to bf16 availability

### ⚠️ Licensing Warning
> While Ideogram 4's **code** is Apache-2.0, the **model weights** (including community repacks like `MLXBits/ideogram-4-mlx-q4` and `Comfy-Org/Ideogram-4`) are released under the **Ideogram 4 Non-Commercial Model Agreement**. Do NOT use these weights for commercial SaaS products, paid client work, or any revenue-generating activity without a separate enterprise license from Ideogram. Krea 2 and Z-Image have more permissive licenses — verify individually.

### Hardware Recommendations by Chip

| Mac Chip | Unified Memory | Recommended Model Variant | Expected Performance |
| :--- | :--- | :--- | :--- |
| **M4 (Base)** | 16 GB | `MLXBits/ideogram-4-mlx-q4` (4-bit) or `z_image_turbo_bf16` | Fits in RAM (~15GB footprint). Good for 1024×1024. |
| **M4 Pro** | 24 GB+ | `MLXBits/ideogram-4-mlx-q8` (8-bit) or Krea 2 Turbo | Excellent headroom. Allows larger batches or 2K generation. |
| **M4 Max** | 36 GB+ | FP8 variants or full precision | Desktop-class performance; minimal offloading required. |

> **Note:** The combination of a 9.3B DiT + 8B Qwen3-VL encoder is extremely heavy. On 16GB Macs, you MUST use quantized (4-bit) variants to avoid OOM.

---

## Three Methods for Running on Apple Silicon

Depending on your workflow preference, choose one of three methods:

| Method | Best For | Performance | Ease of Use |
| :--- | :--- | :--- | :--- |
| **MLX via `mflux`** | CLI enthusiasts, batch processing | ⭐⭐⭐⭐⭐ Fastest (native MLX quantization) | Terminal commands |
| **ComfyUI** | Visual node editing, complex workflows | ⭐⭐⭐⭐ Good (PyTorch MPS) | Visual canvas |
| **Draw Things** | Casual users, quick generation | ⭐⭐⭐⭐ Good (native Metal) | Easiest GUI |

**Performance Note:** While PyTorch's MPS backend can run these models via `diffusers`, it is **significantly slower** than Apple's MLX framework and lacks native quantization support. Always prefer `mflux` or native app integrations for M-series chips.

---

## Method 1: Native MLX via `mflux` (Recommended for Speed)

The `mflux` library provides a line-by-line MLX port of state-of-the-art generative image models. It is the most efficient way to run Ideogram 4 and Krea 2 on Apple Silicon.

### Step M1.1: Install Dependencies
```bash
pip install mflux huggingface_hub
```

### Step M1.2: Download the MLX Weights

The community organization **MLXBits** maintains an "Ideogram 4 on Apple MLX" collection on Hugging Face. The `MLXBits/ideogram-4-mlx-q4` repository is quantized to approximately 15 GB on disk — the smallest Ideogram 4 build available.

```bash
# Download Ideogram 4 (4-bit for 16GB Macs)
huggingface-cli download MLXBits/ideogram-4-mlx-q4 --local-dir ./ideogram-4-mlx-q4

# Download Ideogram 4 (8-bit for 24GB+ Macs)
huggingface-cli download MLXBits/ideogram-4-mlx-q8 --local-dir ./ideogram-4-mlx-q8

# Download Krea 2 Turbo (MLX-ready repack)
huggingface-cli download SceneWorks/krea-2-turbo-mlx --local-dir ./krea-2-turbo-mlx
```

### Step M1.3: Generate Images

**For Ideogram 4:**
```bash
mflux-generate-ideogram4 \
  --model-path ./ideogram-4-mlx-q4 \
  --prompt "A cinematic shot of a cyberpunk cityscape" \
  --steps 20 --width 1024 --height 1024 \
  --output ideogram_out.png
```

> `mflux` auto-detects precision from the `split_model.json` file — no manual quantization flags needed.

**For Krea 2 Turbo:**
```bash
mflux-generate \
  --model-path ./krea-2-turbo-mlx \
  --prompt "Aesthetic film photography, grainy, neon lights" \
  --steps 8 --guidance 0.0 --width 1024 --height 1024 \
  --output krea_out.png
```

> ⚠️ **Critical:** Krea 2 Turbo is CFG-free. You **MUST** set `--guidance 0.0`. Using standard CFG values (like 7.0) will destroy image quality.

---

## Method 3: Draw Things App (Easiest GUI)

For users who prefer a standalone macOS application, Draw Things offers native support:

1. Download **Draw Things** from the Mac App Store
2. Open the Model Manager and search for "Ideogram 4"
3. The app imports the `ideogram-ai/ideogram-4-nf4-diffusers` pipeline
4. MPS optimization and memory offloading are handled automatically
5. Paste your JSON prompt into the text field and generate

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Python Environment Setup](#2-python-environment-setup)
3. [ComfyUI Installation](#3-comfyui-installation)
4. [Dependency Installation](#4-dependency-installation)
5. [Model Downloads (Ideogram 4)](#5-model-downloads-ideogram-4)
6. [Launching ComfyUI](#6-launching-comfyui)
7. [Loading Workflows](#7-loading-workflows)
8. [LoRA Compatibility Warning](#8-⚠️-lora-compatibility-warning)
9. [Troubleshooting & Pitfalls](#9-troubleshooting--pitfalls)
10. [Quick Reference](#10-quick-reference)

---

## New in This Version

- **Model Landscape** — Ideogram 4.0, Krea 2 (RAW/Turbo), Z-Image Turbo explained
- **Hardware Table** — Chip-specific recommendations (M4 Base/Pro/Max)
- **Three Methods** — MLX/mflux, ComfyUI, Draw Things
- **Method 1: MLX** — Native `mflux` CLI for fastest inference
- **Method 3: Draw Things** — Easiest GUI app
- **JSON Prompting** — Ideogram 4 structured caption workflow
- **Licensing** — Ideogram 4 Non-Commercial warning
- **Thermal** — M4 Air throttling guidance
- **CFG-Free** — Krea 2 Turbo guidance=0 requirement

---

## 1. Prerequisites

### System Requirements
- **OS:** macOS Tahoe 26.x (or newer)
- **Architecture:** Apple Silicon (M1/M2/M3/M4)
- **RAM:** 16GB minimum, 32GB+ recommended
- **Disk:** 50GB+ free space for models
- **Python:** 3.10+ (3.12 recommended, 3.13 bleeding edge)

### Required Software
```bash
# Check if Homebrew is installed
brew --version

# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12 (recommended for stability; 3.13 is bleeding edge)
brew install python@3.12

# Install wget (optional but useful)
brew install wget
```

---

## 2. Python Environment Setup

### Step 2.1: Create Virtual Environment

```bash
# Create venv directory
mkdir -p ~/.venv

# Create Python 3.12 virtual environment
/opt/homebrew/bin/python3.12 -m venv ~/.venv

# Verify installation
source ~/.venv/bin/activate
python --version
# Should output: Python 3.13.x

# Upgrade pip
pip install --upgrade pip
```

### Step 2.2: Add to Shell Configuration

Add the venv activation to your shell config files:

```bash
# For zsh (default on Mac)
echo 'source ~/.venv/bin/activate' >> ~/.zshrc

# For bash
echo 'source ~/.venv/bin/activate' >> ~/.bashrc

# For immediate effect in current session
source ~/.venv/bin/activate
```

### Step 2.3: Verify PATH Setup

```bash
# Check that python points to the venv
which python
# Should output: /Users/<username>/.venv/bin/python

python --version
# Should output: Python 3.13.x
```

---

## 3. ComfyUI Installation

### Step 3.1: Clone or Download ComfyUI

```bash
# Option A: Clone from GitHub
cd ~
git clone https://github.com/comfyanonymous/ComfyUI.git

# Option B: If you have an existing installation
# Just use the existing directory
ls ~/ComfyUI  # or wherever your installation is
```

### Step 3.2: Navigate to ComfyUI Directory

```bash
cd ~/ComfyUI  # or your ComfyUI directory
```

### Step 3.3: Verify ComfyUI Structure

```bash
# Check that main.py exists
ls -la main.py

# Check models directory
ls -la models/
# Should contain: diffusion_models, text_encoders, vae, loras, etc.
```

---

## 4. Dependency Installation

### Step 4.1: Install PyTorch for Mac

```bash
# Make sure venv is activated
source ~/.venv/bin/activate

# Install PyTorch with MPS (Metal Performance Shaders) support
pip install torch torchvision torchaudio

# Verify MPS support
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

### Step 4.2: Install ComfyUI Requirements

```bash
cd ~/ComfyUI

# Install all requirements
pip install -r requirements.txt

# This installs: numpy, pillow, transformers, safetensors, etc.
```

### Step 4.3: Install Additional Dependencies

```bash
# Install SQLAlchemy (required for newer versions)
pip install sqlalchemy alembic

# Install other common dependencies
pip install aiohttp aiohappyeyeballs
```

---

## 5. Model Downloads

### ⚠️ Important: Mac Compatibility

**Do NOT use fp8 models on Mac!** The fp8 (Float8_e4m3fn) format is NOT supported on Apple Silicon MPS backend. Use bf16 models instead.

### Available Models (Mac Compatible)

| Model | Format | Size | Notes |
|-------|--------|------|-------|
| `z_image_turbo_bf16.safetensors` | bf16 | 11 GB | ✅ Recommended for Mac (lightest) |
| `krea2_turbo_bf16.safetensors` | bf16 | 24 GB | ✅ Works on Mac (RAW for training, Turbo for inference) |
| `flux1-dev.safetensors` | bf16 | 22 GB | ✅ Works on Mac |
| `ideogram4_fp8_scaled.safetensors` | fp8 | 8.6 GB | ❌ **NOT Mac compatible** |
| `ideogram4_unconditional_fp8_scaled.safetensors` | fp8 | 8.6 GB | ❌ **NOT Mac compatible** |

### Krea 2 Model Variants

Krea 2 ships as two distinct models:
- **Krea 2 RAW** — Full-step base checkpoint, suitable for fine-tuning and LoRA training
- **Krea 2 Turbo** — 8-step distilled checkpoint for fast inference (CFG-free, guidance = 0)

For ComfyUI, use the **Turbo** variant. The RAW variant is only needed if you plan to train LoRAs.

### Ideogram 4 on ComfyUI — Important Notes

ComfyUI introduced **day-0 native support** for Ideogram 4.0 with dedicated Ideogram V4 nodes. When using Ideogram 4 (once bf16 weights become available or via MLX):
- Use the **Ideogram V4 Loader** node (not the generic UNETLoader)
- The Qwen3-VL-8B-Instruct text encoder is required (different from Qwen3 4B used by Z-Image)
- Structured JSON prompts unlock bounding-box layout control (see [JSON Prompting](#json-prompting-ideogram-4-specific))

### Step 5.1: Download Mac-Compatible Models

```bash
cd ~/ComfyUI/models

# Download z_image_turbo_bf16 (recommended for Mac, ~11 GB)
curl -L -o diffusion_models/z_image_turbo_bf16.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/diffusion_models/z_image_turbo_bf16.safetensors"

# Alternative: Download krea2_turbo_bf16 (~24 GB)
curl -L -o diffusion_models/krea2_turbo_bf16.safetensors \
  "https://huggingface.co/Comfy-Org/krea2/resolve/main/diffusion_models/krea2_turbo_bf16.safetensors"
```

### Step 5.2: Download Text Encoder

**For Z-Image / Krea 2 (Qwen3 4B):**
```bash
curl -L -o text_encoders/qwen_3_4b.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/text_encoders/qwen_3_4b.safetensors"
```

**For Ideogram 4 (Qwen3-VL-8B — different encoder!):**
```bash
# Ideogram 4 uses Qwen3-VL-8B-Instruct, NOT the same as Z-Image's encoder
curl -L -o text_encoders/qwen3_vl_8b.safetensors \
  "https://huggingface.co/Comfy-Org/Ideogram-4/resolve/main/text_encoders/qwen3_vl_8b.safetensors"
```

### Step 5.3: Download VAE

```bash
# Download Z Image VAE (~320 MB)
curl -L -o vae/ae.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors"
```

### Step 5.4: Download LoRA (Optional, Architecture-Specific)

```bash
# Download TurboTime LoRA for faster generation (~386 MB)
# ⚠️ WARNING: This LoRA is for Ideogram 4 ONLY.
# Do NOT use with Z-Image or Krea2 models (different architecture = crash).
# If you're using z_image_turbo_bf16, skip this step.
curl -L -o loras/ideogram4_turbotime_v1.safetensors \
  "https://huggingface.co/ostris/ideogram_4_turbotime_lora/resolve/main/ideogram_4_turbotime_v1.safetensors"

# Note: This LoRA may have file integrity issues. If validation fails, use without LoRA.
```

### Step 5.5: Verify Downloads

```bash
echo "=== Installed Models ==="
echo ""
echo "Diffusion Models:"
ls -lh diffusion_models/*.safetensors
echo ""
echo "Text Encoders:"
ls -lh text_encoders/*.safetensors
echo ""
echo "VAE:"
ls -lh vae/*.safetensors
echo ""
echo "LoRAs:"
ls -lh loras/*.safetensors
```

### Expected File Sizes

| File | Size | Location |
|------|------|----------|
| `z_image_turbo_bf16.safetensors` | ~11 GB | `diffusion_models/` |
| `krea2_turbo_bf16.safetensors` | ~24 GB | `diffusion_models/` |
| `qwen_3_4b.safetensors` | ~1.2 GB | `text_encoders/` |
| `ae.safetensors` | ~320 MB | `vae/` |
| `ideogram4_turbotime_v1.safetensors` | ~386 MB | `loras/` (optional) |

---

## 6. Launching ComfyUI

### ⚠️ Critical: Fix Broken Pipe Error

If ComfyUI is launched in the background from a non-interactive shell, do **not** leave stdout/stderr attached to that shell. When the shell exits, ComfyUI can later write logs/progress to a dead pipe and crash with `[Errno 32] Broken pipe`.

Use a detached launch with stdout/stderr redirected to a real log file. `TQDM_DISABLE=1` is helpful, but the key fix is stable log redirection:

```bash
export TQDM_DISABLE=1
cd ~/ComfyUI
source ~/.venv/bin/activate
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &
```

### Step 6.1: Start ComfyUI

```bash
# Navigate to ComfyUI directory
cd ~/ComfyUI

# Make sure venv is activated
source ~/.venv/bin/activate

# Start ComfyUI with broken pipe fix
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &
```

### Step 6.2: Verify ComfyUI is Running

```bash
# Check if ComfyUI is running
curl -s http://127.0.0.1:8188/system_stats | python3 -m json.tool

# Open in browser
open http://127.0.0.1:8188
```

### Step 6.3: Common Launch Options

```bash
# Standard launch (with broken pipe fix)
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &

# With split attention (if memory issues)
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 --use-split-cross-attention \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &

# Different port (if 8188 is in use)
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8189 \
  > ~/ComfyUI/comfyui-runtime-8189.log 2>&1 < /dev/null &

# Verbose logging
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 --verbose \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &
```

---

## 7. Loading Workflows

### ⚠️ Important: Use Mac-Compatible Workflows

**Do NOT use workflows designed for fp8 models!** They will fail on Mac MPS backend.

### Step 7.1: Create Mac-Compatible Workflow

Since there's no official Mac-compatible workflow, create a simple test workflow:

```bash
# Create a simple workflow directory
mkdir -p ~/ComfyUI/user/default/workflows

# Create a Mac-compatible test workflow
cat > ~/ComfyUI/user/default/workflows/mac_test_workflow.json << 'EOF'
{
  "1": {
    "class_type": "UNETLoader",
    "inputs": {
      "unet_name": "z_image_turbo_bf16.safetensors",
      "weight_dtype": "default"
    }
  },
  "2": {
    "class_type": "CLIPLoader",
    "inputs": {
      "clip_name": "qwen_3_4b.safetensors",
      "type": "lumina2"
    }
  },
  "3": {
    "class_type": "VAELoader",
    "inputs": {
      "vae_name": "ae.safetensors"
    }
  },
  "4": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "A beautiful sunset over the ocean with vibrant colors in the sky",
      "clip": ["2", 0]
    }
  },
  "5": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "ugly, blurry, low quality",
      "clip": ["2", 0]
    }
  },
  "6": {
    "class_type": "EmptySD3LatentImage",
    "inputs": {
      "width": 1024,
      "height": 1024,
      "batch_size": 1
    }
  },
  "7": {
    "class_type": "ModelSamplingAuraFlow",
    "inputs": {
      "shift": 3.0,
      "model": ["1", 0]
    }
  },
  "8": {
    "class_type": "FluxGuidance",
    "inputs": {
      "guidance": 1.0,
      "conditioning": ["4", 0]
    }
  },
  "9": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 42,
      "steps": 8,
      "cfg": 1.0,
      "sampler_name": "res_multistep",
      "scheduler": "simple",
      "denoise": 1.0,
      "model": ["7", 0],
      "positive": ["8", 0],
      "negative": ["5", 0],
      "latent_image": ["6", 0]
    }
  },
  "10": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["9", 0],
      "vae": ["3", 0]
    }
  },
  "11": {
    "class_type": "SaveImage",
    "inputs": {
      "filename_prefix": "mac_test",
      "images": ["10", 0]
    }
  }
}
EOF
```

### Step 7.2: Load Workflow in ComfyUI

1. Open ComfyUI in browser: `http://127.0.0.1:8188`
2. Click **"Workflows"** in the left sidebar
3. Click **"Refresh"** to reload workflow list
4. Click on **"mac_test_workflow"** to load the workflow

### Step 7.3: Configure Model Selection

In the workflow, ensure these nodes are configured:

| Node | Setting | Value |
|------|---------|-------|
| Load Diffusion Model | `unet_name` | `z_image_turbo_bf16.safetensors` |
| Load CLIP | `clip_name` | `qwen_3_4b.safetensors` |
| Load CLIP | `type` | `lumina2` |
| Load VAE | `vae_name` | `ae.safetensors` |

### Step 7.4: Generate via API (Recommended)

For testing, using the API is more reliable than the UI:

```bash
# Queue the workflow
cat ~/ComfyUI/user/default/workflows/mac_test_workflow.json | python3 -c "
import sys, json
workflow = json.load(sys.stdin)
prompt = {'prompt': workflow}
print(json.dumps(prompt))
" | curl -s -X POST http://127.0.0.1:8188/prompt \
  -H "Content-Type: application/json" \
  -d @-

# Wait and check for results
sleep 60
curl -s http://127.0.0.1:8188/history | python3 -c "
import sys, json
data = json.load(sys.stdin)
for prompt_id, info in data.items():
    outputs = info.get('outputs', {})
    for node_id, output in outputs.items():
        if 'images' in output:
            for img in output['images']:
                print(f'✅ Image: {img.get("filename")}')
"
```

---

## JSON Prompting (Ideogram 4 Specific)

Ideogram 4 was trained on **structured JSON captions** rather than free text. Using plain text will yield inferior layout control. To unlock bounding-box placement and color palette conditioning, use the following schema:

```json
{
  "high_level_description": "A futuristic workspace with a glowing monitor.",
  "style_description": {
    "aesthetics": "Cyberpunk, neon-lit, high contrast.",
    "lighting": "Volumetric blue and magenta rim lighting.",
    "color_palette": ["#00FFFF", "#FF00FF", "#1A1A1A"]
  },
  "compositional_deconstruction": {
    "background": "Dark server room with blinking LEDs.",
    "elements": [
      {
        "type": "obj",
        "bbox": [200, 300, 800, 700],
        "desc": "A sleek curved monitor displaying code."
      },
      {
        "type": "text",
        "bbox": [250, 400, 750, 500],
        "text": "SYSTEM ONLINE",
        "desc": "Bright green terminal font."
      }
    ]
  }
}
```

### JSON Prompt Rules
- `high_level_description`: Overall scene summary
- `style_description.aesthetics`: Visual style keywords
- `style_description.lighting`: Lighting description
- `style_description.color_palette`: Array of hex color codes
- `compositional_deconstruction.background`: Background description
- `compositional_deconstruction.elements`: Array of objects/text with `bbox` [x1, y1, x2, y2]
- Each element needs `type` ("obj" or "text"), `bbox`, and `desc`
- Text elements additionally need `text` field

### Generating JSON Prompts
You can generate these JSON structures automatically by:
1. Using the Ideogram API's "Magic Prompt" endpoint
2. Prompting a local LLM (e.g., Qwen2.5-7B) to output this exact schema
3. Using the ComfyUI Ideogram V4 node's built-in JSON prompt field

---

## 8. ⚠️ LoRA Compatibility Warning

### CRITICAL: Architecture Mismatch

**Do NOT use Ideogram 4 LoRAs with Z-Image or Krea2 models.**

LoRAs are architecture-specific. Z-Image (Tencent) and Ideogram 4 (Ideogram AI) have completely different underlying DiT/UNet architectures and tensor dimensions. Applying an Ideogram 4 LoRA (`ideogram4_turbotime_v1.safetensors`) to a Z-Image model will result in a **tensor size mismatch error** or silent failure.

| Model | Compatible LoRA | Incompatible LoRA |
|-------|----------------|-------------------|
| `z_image_turbo_bf16` | Z-Image specific (if available) | ❌ Ideogram 4 TurboTime |
| `krea2_turbo_bf16` | Krea2 specific (if available) | ❌ Ideogram 4 TurboTime |
| `ideogram4_bf16` (when available) | ✅ Ideogram 4 TurboTime | — |

### If You Must Use a LoRA

1. **Only use LoRAs specifically trained for your model's architecture**
2. Verify the LoRA was trained for the exact model (e.g., Z-Image LoRA for Z-Image model)
3. If no architecture-specific LoRA exists, run without one — the base models work well

### Step 8.1: Add LoRA Loader Node (When Compatible)

1. **Right-click** on an empty area of the canvas
2. Select **"Add Node"** → **"Loaders"** → **"Load LoRA"**
3. Set `lora_name`, `strength_model`, and `strength_clip`

### Step 8.2: Connect LoRA Node

**Connection Diagram:**
```
[UNET Loader (model)] → [Load LoRA (model in)] → [Load LoRA (model out)] → [Next Node]
[CLIP Loader (clip)] → [Load LoRA (clip in)] → [Load LoRA (clip out)] → [CLIP Text Encode]
```

### Step 8.3: Generation Settings With Compatible LoRA

| Parameter | Standard | With Compatible LoRA |
|-----------|----------|----------------------|
| **Steps** | 8 | 2-8 (model-dependent) |
| **CFG** | 1 | 1 |
| **Sampler** | res_multistep | euler (LoRA-dependent) |
| **Scheduler** | simple | normal (LoRA-dependent) |

---

## 9. Troubleshooting & Pitfalls

### 🔴 CRITICAL: Broken Pipe Error (Detached Logging Issue)

**Error:**
```
[Errno 32] Broken pipe
BrokenPipeError: [Errno 32] Broken pipe
```

**Cause:** ComfyUI was launched in the background from a non-interactive shell while stdout/stderr still pointed at that shell's pipe. After the shell/tool exits, ComfyUI keeps running, but any later log/progress write can hit a dead pipe and crash. This is a launch/logging issue, NOT a model issue.

**Fix:** Kill the old listener and restart ComfyUI detached with stdout/stderr redirected to a real log file:
```bash
# Kill the exact process listening on 8188
LISTENER=$(lsof -tiTCP:8188 -sTCP:LISTEN || true)
[ -n "$LISTENER" ] && kill -9 $LISTENER
sleep 3

# Start detached with stable logging
cd ~/ComfyUI
source ~/.venv/bin/activate
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &
```

**Traceback location:** Check the persistent runtime log:
```bash
tail -200 ~/ComfyUI/comfyui-runtime.log
```

---

### 🔴 CRITICAL: Ideogram 4 fp8 Models Incompatible with MPS

**Error:**
```
RuntimeError: MPS backend does not support Float8_e4m3fn dtype
```

**Cause:** The `ideogram4_fp8_scaled.safetensors` models use Float8_e4m3fn format, which is NOT supported on Apple Silicon MPS backend.

**Solution:** Use bf16 models instead. Available alternatives:
- `z_image_turbo_bf16.safetensors` (11 GB) - Recommended for Mac
- `krea2_turbo_bf16.safetensors` (24 GB) - Also works
- `flux1-dev.safetensors` (22 GB) - Flux model

```bash
# Check available models
ls -lh ~/ComfyUI/models/diffusion_models/

# Use z_image_turbo_bf16 instead of ideogram4_fp8
# In workflow, set unet_name to: z_image_turbo_bf16.safetensors
```

**Note:** There is NO bf16 variant of Ideogram 4 available from Comfy-Org. The fp8 models are designed for NVIDIA GPUs only.

---

### Pitfall 1: Python Version Error

**Error:**
```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

**Cause:** Python 3.9 or lower doesn't support `str | None` syntax

**Solution:**
```bash
# Install Python 3.12 (recommended for stability)
brew install python@3.12

# Create new venv with Python 3.12
rm -rf ~/.venv
/opt/homebrew/bin/python3.12 -m venv ~/.venv

# Activate and verify
source ~/.venv/bin/activate
python --version  # Should show Python 3.13.x
```

---

### Pitfall 2: Missing SQLAlchemy Module

**Error:**
```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**Solution:**
```bash
source ~/.venv/bin/activate
pip install sqlalchemy alembic
```

---

### Pitfall 3: Port Already in Use

**Error:**
```
Port 8188 is already in use on address 127.0.0.1
```

**Solution:**
```bash
# Find and kill the process using port 8188
lsof -ti:8188 | xargs kill -9

# Or use a different port
python main.py --force-fp16 --listen 127.0.0.1 --port 8189
```

---

### Pitfall 4: Database Lock Error

**Error:**
```
Could not acquire lock on database 'comfyui.db'
```

**Solution:**
```bash
# Kill all ComfyUI processes
pkill -9 -f "python main.py"

# Wait a moment
sleep 3

# Delete the lock file
rm -f ~/ComfyUI/user/comfyui.db-journal

# Restart ComfyUI
python main.py --force-fp16 --listen 127.0.0.1 --port 8188
```

---

### Pitfall 5: ComfyUI-Manager Missing Dependencies

**Error:**
```
[ERROR] [ComfyUI-Manager] Neither `python -m pip` nor `uv` are available
ModuleNotFoundError: No module named 'git'
```

**Solution:**
```bash
source ~/.venv/bin/activate

# Fix pip first
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

# Install git module
pip install gitpython

# Or install ComfyUI-Manager requirements
cd ~/ComfyUI/custom_nodes/ComfyUI-Manager
pip install -r requirements.txt
```

---

### Pitfall 6: Impact Pack Missing OpenCV

**Error:**
```
ModuleNotFoundError: No module named 'cv2'
```

**Solution:**
```bash
source ~/.venv/bin/activate
pip install opencv-python
```

---

### Pitfall 7: Download Interrupted/Incomplete Files

**Symptom:** File size doesn't match expected size

**Solution:**
```bash
# Check file size
ls -lh models/diffusion_models/ideogram4_fp8_scaled.safetensors

# If incomplete, re-download with resume support
curl -L -C - -o models/diffusion_models/ideogram4_fp8_scaled.safetensors \
  "https://huggingface.co/Comfy-Org/Ideogram-4/resolve/main/diffusion_models/ideogram4_fp8_scaled.safetensors"

# Or delete and re-download
rm models/diffusion_models/ideogram4_fp8_scaled.safetensors
curl -L -o models/diffusion_models/ideogram4_fp8_scaled.safetensors \
  "https://huggingface.co/Comfy-Org/Ideogram-4/resolve/main/diffusion_models/ideogram4_fp8_scaled.safetensors"
```

---

### Pitfall 8: MPS Out of Memory

**Error:**
```
MPS backend out of memory
```

**Solution:**
```bash
# Use split attention to reduce memory usage
python main.py --force-fp16 --listen 127.0.0.1 --port 8188 --use-split-cross-attention

# Or use lower precision
python main.py --force-fp16 --listen 127.0.0.1 --port 8188

# Allow MPS to use more unified memory (may cause system instability)
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

# Check available memory
memory_pressure 2>/dev/null || echo "Memory pressure tool not available"
```

---

### Pitfall 9: LoRA Not Loading

**Symptom:** LoRA node shows "model not found"

**Solution:**
```bash
# Verify LoRA file exists and is not empty
ls -lh models/loras/ideogram4_turbotime_v1.safetensors

# Check file size (should be ~386 MB)
# If 0 bytes or very small, re-download:
rm models/loras/ideogram4_turbotime_v1.safetensors
curl -L -o models/loras/ideogram4_turbotime_v1.safetensors \
  "https://huggingface.co/ostris/ideogram_4_turbotime_lora/resolve/main/ideogram_4_turbotime_v1.safetensors"
```

**Known Issue:** The ideogram4_turbotime_v1.safetensors file may fail safetensors validation even after re-download. This appears to be a file integrity issue. Consider using the model without LoRA if this occurs.

---

### Pitfall 10: Workflow Not Appearing

**Symptom:** New workflow doesn't show in the Workflows panel

**Solution:**
```bash
# Ensure workflow is in the correct directory
ls -la ~/ComfyUI/user/default/workflows/

# Click "Refresh" in the Workflows panel in ComfyUI
# If still not showing, restart ComfyUI
```

---

### Pitfall 11: Tensor Size Mismatch

**Error:**
```
The size of tensor a (4) must match the size of tensor b (128) at non-singleton dimension 1
```

**Cause:** Mixing incompatible model nodes, VAE dimensions, or applying LoRAs trained for a different architecture (e.g., using an Ideogram 4 LoRA on a Z-Image model)

**Solution:**
- Don't mix SD3, AuraFlow, Flux, and Z Image nodes randomly
- Use the correct VAE for your model. For `z_image_turbo_bf16.safetensors`, use `ae.safetensors`.
- Use the correct latent node. For z-image, use `EmptySD3LatentImage`, not `EmptyLatentImage`.
- For z-image, known-good sampler settings are `res_multistep` + `simple`, `steps=8`, `cfg=1.0`.
- **Do NOT use Ideogram 4 LoRAs with Z-Image or Krea2 models** — they have different architectures and will cause tensor mismatch errors.

---

### Pitfall 12: Python 3.13 Compatibility Issues

**Symptom:** Various package installation failures or strange errors

**Note:** Python 3.13 is newer and may cause issues with some packages. If you encounter persistent problems:

```bash
# Consider downgrading to Python 3.11
brew install python@3.11

# Recreate venv with Python 3.11
rm -rf ~/.venv
/opt/homebrew/bin/python3.11 -m venv ~/.venv

# Reactivate and reinstall dependencies
source ~/.venv/bin/activate
pip install --upgrade pip
pip install -r ~/ComfyUI/requirements.txt
```

---

### Pitfall 13: Krea 2 Turbo CFG Must Be 0

**Symptom:** Images look noisy, burnt, or completely corrupted when using Krea 2 Turbo

**Cause:** Krea 2 Turbo is a distilled checkpoint that operates **completely CFG-free**. Using standard CFG values (like 4.0, 7.0, or any value other than 0) will destroy image quality.

**Solution:**
- In ComfyUI KSampler node: set `cfg` to **0.0** (not 1.0, not 7.0)
- In `mflux`: use `--guidance 0.0`
- Steps should be around **8** (not 25+)
- Do NOT use negative prompt with Turbo models

---

### Pitfall 14: M4 Air Thermal Throttling

**Symptom:** First generation is fast, then subsequent generations become progressively slower

**Cause:** The base M4 MacBook Air is **fanless**. Running the 9.3B DiT + 8B Qwen3-VL encoder (or even the 4B encoder + 11GB model) generates significant heat. After 3–5 consecutive generations, the chip hits thermal limits and throttles.

**Solution:**
- Allow cooling time between generations (30–60 seconds)
- Use `--lowvram` or aggressive offloading flags
- Consider MLX via `mflux` for better thermal management (more efficient than PyTorch MPS)
- M4 Pro and Max MacBook Pros have active cooling and sustain peak speeds indefinitely

---

### Pitfall 15: MPS vs MLX Performance

**Symptom:** Generation is slower than expected on Apple Silicon

**Cause:** PyTorch's MPS backend via `diffusers` is **significantly slower** than Apple's native MLX framework. MPS lacks native quantization support and has higher overhead per operation.

**Solution:**
- For CLI/batch work: use `mflux` (MLX-native) — see [Method 1: MLX via mflux](#method-1-native-mlx-via-mflux-recommended-for-speed)
- For GUI work: ComfyUI with MPS is acceptable but expect ~2-3× slower than MLX
- Draw Things app uses native Metal and performs well for a GUI

---

## 10. Quick Reference

### Essential Commands

```bash
# Activate environment
source ~/.venv/bin/activate

# Kill the exact listener if port 8188 is stuck
LISTENER=$(lsof -tiTCP:8188 -sTCP:LISTEN || true)
[ -n "$LISTENER" ] && kill -9 $LISTENER

# Start ComfyUI with stable detached logging (fixes BrokenPipeError)
cd ~/ComfyUI
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &

# Check if running
curl -s http://127.0.0.1:8188/system_stats | python3 -m json.tool

# Check logs
tail -200 ~/ComfyUI/comfyui-runtime.log

# Fix broken pip
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

# Install missing dependencies
pip install gitpython opencv-python sqlalchemy alembic toml scikit-image

# --- MLX via mflux (alternative method) ---
# Download MLX weights
huggingface-cli download MLXBits/ideogram-4-mlx-q4 --local-dir ./ideogram-4-mlx-q4
huggingface-cli download SceneWorks/krea-2-turbo-mlx --local-dir ./krea-2-turbo-mlx

# Generate with Ideogram 4 (MLX)
mflux-generate-ideogram4 --model-path ./ideogram-4-mlx-q4 \
  --prompt "A cinematic shot" --steps 20 --width 1024 --height 1024 --output out.png

# Generate with Krea 2 Turbo (MLX) — CFG MUST be 0!
mflux-generate --model-path ./krea-2-turbo-mlx \
  --prompt "Aesthetic film photography" --steps 8 --guidance 0.0 --width 1024 --height 1024 --output out.png
```

### Model Paths

| Model Type | Path |
|------------|------|
| Diffusion Models | `~/ComfyUI/models/diffusion_models/` |
| Text Encoders | `~/ComfyUI/models/text_encoders/` |
| VAE | `~/ComfyUI/models/vae/` |
| LoRAs | `~/ComfyUI/models/loras/` |
| Checkpoints | `~/ComfyUI/models/checkpoints/` |

### Mac-Compatible Models

| Model | Path | Notes |
|-------|------|-------|
| `z_image_turbo_bf16.safetensors` | `diffusion_models/` | ✅ Recommended |
| `krea2_turbo_bf16.safetensors` | `diffusion_models/` | ✅ Works |
| `flux1-dev.safetensors` | `diffusion_models/` | ✅ Works |
| `qwen_3_4b.safetensors` | `text_encoders/` | ✅ Required |
| `ae.safetensors` | `vae/` | ✅ Required for z-image |

### Browser Access

- **ComfyUI Interface:** http://127.0.0.1:8188
- **System Stats API:** http://127.0.0.1:8188/system_stats

### Installed Versions

| Component | Version |
|-----------|---------|
| ComfyUI | 0.26.0 |
| Python | 3.12.x (recommended) |
| PyTorch | 2.12.x |
| Device | MPS (Apple Silicon) |
| TQDM Fix | `TQDM_DISABLE=1` (required) |

---

## Appendix A: Full Installation Script

```bash
#!/bin/bash
# ComfyUI Mac Silicon Installation Script
# Includes fixes for broken pipe error and missing dependencies

set -e

echo "=== ComfyUI Mac Silicon Installation ==="

# 1. Install Homebrew if needed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. Install Python 3.12 (recommended for stability)
echo "Installing Python 3.12..."
brew install python@3.12

# 3. Create virtual environment
echo "Creating Python virtual environment..."
mkdir -p ~/.venv
/opt/homebrew/bin/python3.12 -m venv ~/.venv

# 4. Activate venv
source ~/.venv/bin/activate

# 5. Upgrade pip and fix broken pip installation
python -m ensurepip --upgrade
pip install --upgrade pip setuptools wheel

# 6. Clone ComfyUI
echo "Cloning ComfyUI..."
cd ~
COMFYUI_DIR="$HOME/ComfyUI"
if [ ! -d "$COMFYUI_DIR" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
fi
cd "$COMFYUI_DIR"

# 7. Install PyTorch
echo "Installing PyTorch..."
pip install torch torchvision torchaudio

# 8. Install requirements
echo "Installing ComfyUI requirements..."
pip install -r requirements.txt

# 9. Install additional dependencies (fixes ComfyUI-Manager and Impact Pack errors)
pip install sqlalchemy alembic opencv-python gitpython toml scikit-image

# 10. Download models - NOTE: Use bf16 models for Mac, NOT fp8
# fp8 models use Float8_e4m3fn which is NOT supported on MPS backend
echo "Downloading models (bf16 for Mac compatibility)..."
mkdir -p models/diffusion_models models/text_encoders models/vae models/loras

# z_image_turbo_bf16 - Works on Mac (recommended)
curl -L -o models/diffusion_models/z_image_turbo_bf16.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/diffusion_models/z_image_turbo_bf16.safetensors" &

# Alternative: krea2_turbo_bf16 - Also works on Mac
curl -L -o models/diffusion_models/krea2_turbo_bf16.safetensors \
  "https://huggingface.co/Comfy-Org/krea2/resolve/main/diffusion_models/krea2_turbo_bf16.safetensors" &

# Text encoder
curl -L -o models/text_encoders/qwen_3_4b.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/text_encoders/qwen_3_4b.safetensors" &

# Z Image VAE
curl -L -o models/vae/ae.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors" &

# Wait for downloads
wait

# 11. Add venv and TQDM fix to shell config (fixes broken pipe error)
echo "Adding venv and TQDM fix to shell configuration..."
echo 'source ~/.venv/bin/activate' >> ~/.zshrc
echo 'export TQDM_DISABLE=1' >> ~/.zshrc
echo 'source ~/.venv/bin/activate' >> ~/.bashrc
echo 'export TQDM_DISABLE=1' >> ~/.bashrc

# Apply to current session
export TQDM_DISABLE=1

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start ComfyUI (with broken pipe fix):"
echo "  source ~/.venv/bin/activate"
echo "  cd $COMFYUI_DIR"
echo "  nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 > $COMFYUI_DIR/comfyui-runtime.log 2>&1 < /dev/null &"
echo ""
echo "Then open: http://127.0.0.1:8188"
echo ""
echo "IMPORTANT: Use bf16 models (z_image_turbo_bf16, krea2_turbo_bf16)"
echo "Do NOT use fp8 models (ideogram4_fp8) - they don't work on Mac MPS"
```

---

## Appendix B: Workflow Connection Diagram (Mac Compatible)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    z_image_turbo_bf16 (Mac Compatible)                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ UNET Loader      │
│ - z_image_turbo  │
│   _bf16          │──── model ──────────────────────────────┐
│ (NOT fp8!)       │                                         │
└──────────────────┘                                         │
                                                             │
┌──────────────────┐                                         │
│ CLIP Loader      │                                         │
│ - qwen_3_4b      │──── clip ────────────────────┐         │
│ - type: lumina2  │                              │         │
└──────────────────┘                              │         │
                                                  │         │
                                                  ▼         ▼
                                        ┌─────────────────────┐
                                        │ Load LoRA (Optional) │
                                        │ ⚠️ Must be arch-    │
                                        │ compatible with     │
                                        │ your model!         │
                                        └─────────────────────┘
                                            │           │
                                            │           │
                              model out     │           │     clip out
                                            ▼           ▼
┌──────────────────┐         ┌──────────────────┐    ┌──────────────────┐
│ ModelSampling    │◄────────│                  │    │ CLIP Text Encode │
│ AuraFlow         │         │                  │◄───│ (Positive)       │
│ - shift: 3.0     │         │                  │    │                  │
└──────────────────┘         │                  │    └──────────────────┘
                             │                  │
                             │                  │    ┌──────────────────┐
                             │                  │    │ CLIP Text Encode │
                             │                  │◄───│ (Negative)       │
                             │                  │    │                  │
                             │                  │    └──────────────────┘
                             └──────────────────┘
                                     │
                                     ▼
                             ┌──────────────────┐
                             │ KSampler         │
                             │ - steps: 8       │
                             │ - cfg: 1         │
                             │ - sampler: res_multistep │
                             │ - scheduler: simple│
                             └──────────────────┘
                                     │
                                     ▼
                             ┌──────────────────┐
                             │ VAE Decode       │
                             │ - ae.safetensors │
                             └──────────────────┘
                                     │
                                     ▼
                             ┌──────────────────┐
                             │ Save Image       │
                             └──────────────────┘
```

### Node Configuration (Mac Compatible)

| Node | Parameter | Value |
|------|-----------|-------|
| UNETLoader | unet_name | `z_image_turbo_bf16.safetensors` |
| CLIPLoader | clip_name | `qwen_3_4b.safetensors` |
| CLIPLoader | type | `lumina2` |
| VAELoader | vae_name | `ae.safetensors` |
| EmptySD3LatentImage | width/height | `1024` / `1024` |
| ModelSamplingAuraFlow | shift | `3.0` |
| FluxGuidance | guidance | `1.0` |
| KSampler | steps | `8` |
| KSampler | cfg | `1.0` |
| KSampler | sampler_name | `res_multistep` |
| KSampler | scheduler | `simple` |

---

## Appendix C: Verification Checklist

Before running generation, verify:

### Environment
- [ ] Python version is 3.12+ (or 3.11 for better compatibility)
- [ ] Virtual environment is activated
- [ ] PyTorch with MPS support is installed
- [ ] ComfyUI is launched detached with stdout/stderr redirected to `comfyui-runtime.log` (fixes broken pipe error)
- [ ] `TQDM_DISABLE=1` is set
- [ ] Missing dependencies installed: `pip install gitpython opencv-python sqlalchemy alembic toml scikit-image`

### Models (Mac Compatible)
- [ ] At least one bf16 diffusion model downloaded:
  - [ ] `z_image_turbo_bf16.safetensors` (~11 GB) ✅ Recommended
  - [ ] OR `krea2_turbo_bf16.safetensors` (~24 GB)
  - [ ] OR `flux1-dev.safetensors` (~22 GB)
- [ ] Text encoder downloaded:
  - [ ] `qwen_3_4b.safetensors` (~1.2 GB)
- [ ] VAE downloaded:
  - [ ] `ae.safetensors` (~320 MB)
- [ ] **NOT using fp8 models** (ideogram4_fp8 is not Mac compatible)

### ComfyUI
- [ ] ComfyUI starts without errors
- [ ] No "Broken pipe" errors in logs
- [ ] Workflow loads in browser
- [ ] Model selections match installed files

### Quick Test
```bash
# Check installed models
ls -lh ~/ComfyUI/models/diffusion_models/z_image_turbo_bf16.safetensors
ls -lh ~/ComfyUI/models/text_encoders/qwen_3_4b.safetensors
ls -lh ~/ComfyUI/models/vae/ae.safetensors

# Start ComfyUI with stable detached logging
cd ~/ComfyUI
source ~/.venv/bin/activate
nohup env TQDM_DISABLE=1 DISABLE_TQDM=1 PYTHONUNBUFFERED=1 \
  ~/.venv/bin/python main.py --force-fp16 --listen 127.0.0.1 --port 8188 \
  > ~/ComfyUI/comfyui-runtime.log 2>&1 < /dev/null &

# Check logs
tail -200 ~/ComfyUI/comfyui-runtime.log
```

---

## Document Information

- **Author:** ComfyUI Setup Agent
- **Created:** 2026-06-29
- **Last Updated:** 2026-06-30
- **Tested on:** macOS Tahoe 26.x, Apple Silicon (128 GB RAM)
- **ComfyUI Version:** 0.26.0
- **Python Version:** 3.12.x
- **PyTorch Version:** 2.12.1
- **Status:** Production Ready (v1.4 — expanded with MLX/mflux, Draw Things, JSON prompting, Krea 2 variants, licensing)

### Covered Models
- **Ideogram 4.0** (9.3B DiT, Qwen3-VL-8B, JSON prompting, non-commercial license)
- **Krea 2** (RAW + Turbo variants, CFG-free Turbo)
- **Z-Image Turbo** (bf16, AuraFlow, 8-step)
- **Flux** (bf16 fallback)

### Covered Methods
- **ComfyUI** (visual node editing, PyTorch MPS)
- **MLX via mflux** (CLI, fastest on Apple Silicon)
- **Draw Things** (GUI app, easiest)

### Changelog

- **2026-06-30 (v1.4):** Major expansion. Added Model Landscape section (Ideogram 4.0, Krea 2 RAW/Turbo, Z-Image). Added hardware table for M4 Base/Pro/Max. Added three methods (MLX/mflux, ComfyUI, Draw Things). Added JSON prompting schema for Ideogram 4. Added licensing warning (Ideogram 4 non-commercial). Added Krea 2 CFG=0 pitfall, M4 Air thermal throttling, MPS vs MLX performance comparison. Added MLX model repositories (MLXBits, SceneWorks).
- **2026-06-30 (v1.3):** Critical fix: LoRA architecture mismatch warning added. Fixed macOS version (Sequoia→Tahoe). Unified directory paths. Changed Python recommendation from 3.13 to 3.12.
- **2026-06-29 (v1.2):** Corrected z-image workflow from recovered PNG metadata. Corrected BrokenPipeError fix.
- **2026-06-29 (v1.1):** Added initial broken pipe mitigation, documented MPS fp8 incompatibility.
- **2026-06-29 (v1.0):** Initial release with complete installation guide and 10 pitfalls.

---

*This guide was created by documenting real installation experience including all pitfalls encountered and solutions applied. Validated against official Comfy-Org, MLXBits, and SceneWorks repositories.*
