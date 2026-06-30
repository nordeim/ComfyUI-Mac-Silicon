# ComfyUI Node Catalog — Image Generation on Apple Silicon

## Core Nodes (PyTorch MPS Backend)

### UNETLoader
Loads the diffusion model checkpoint.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `unet_name` | string | Filename in `models/diffusion_models/` |
| `weight_dtype` | select | `"default"`, `"fp8_e4m3fn"`, `"fp8_e5m2"` |

### CLIPLoader
Loads text encoder.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `clip_name` | string | Filename in `models/text_encoders/` |
| `type` | select | `"lumina2"` (Z-Image), `"flux"` (FLUX), `"lumina2"` (Krea) |

### VAELoader
Loads VAE decoder.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `vae_name` | string | Filename in `models/vae/` |

### CLIPTextEncode
Encodes prompt text into conditioning.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `text` | string | Prompt text (multiline supported) |
| `clip` | link | Connect to CLIPLoader output |

### EmptySD3LatentImage
Creates blank latent tensor.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `width` | int | Must be divisible by 64 |
| `height` | int | Must be divisible by 64 |
| `batch_size` | int | Usually 1 |

### ModelSamplingAuraFlow
Configures AuraFlow sampling (for Z-Image).

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `shift` | float | Default: 3.0 |
| `model` | link | Connect to UNETLoader |

### FluxGuidance
Applies guidance scaling to conditioning.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `guidance` | float | 1.0 for Z-Image, 7.0 for FLUX, **0.0 for Krea 2** |
| `conditioning` | link | Connect to CLIPTextEncode (positive) |

### KSampler
The core diffusion sampling node.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `seed` | int | Reproducibility seed |
| `steps` | int | Denoising steps |
| `cfg` | float | Classifier-free guidance scale |
| `sampler_name` | select | `"res_multistep"`, `"euler"`, `"euler_ancestral"` |
| `scheduler` | select | `"simple"`, `"beta57"` |
| `denoise` | float | 1.0 for txt2img, 0.3-0.7 for img2img |
| `model` | link | Connect to model output |
| `positive` | link | Positive conditioning |
| `negative` | link | Negative conditioning |
| `latent_image` | link | Latent input |

### VAEDecode
Decodes latent to pixel image.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `samples` | link | Connect to KSampler output |
| `vae` | link | Connect to VAELoader |

### SaveImage
Saves output image.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `filename_prefix` | string | Output filename prefix |
| `images` | link | Connect to VAEDecode |

## Mflux-ComfyUI Nodes (MLX Backend)

### MfluxLoader
Loads MLX-native model.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `model` | select | HuggingFace repo ID or local path |
| `quantize` | int | 4, 8, or 0 (no quantization) |

### MfluxSampler
Runs MLX sampling.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `prompt` | string | Generation prompt |
| `seed` | int | |
| `steps` | int | |
| `width` | int | |
| `height` | int | |
| `model` | link | Connect to MfluxLoader |

## Utility Nodes

### PowerLoRALoader (rgthree)
Loads and applies LoRA.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `lora_name` | string | Filename in `models/loras/` |
| `model` | link | Connect to model |
| `strength` | float | 0.0-1.0, typical: 0.4-0.7 |

### MarkdownNote
Documentation overlay node.

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `text` | string | Markdown content |

### PreviewImage
Shows intermediate image (no file save).

| Parameter | Widget | Notes |
|-----------|--------|-------|
| `images` | link | |

### ImageScaleBy / ImageUpscaleWithModel
Upscaling nodes for post-processing.

## Node Type String Reference

Use these exact strings in the `type` field:

```
UNETLoader
CLIPLoader
VAELoader
CLIPTextEncode
EmptySD3LatentImage
EmptyLatentImage
ModelSamplingAuraFlow
FluxGuidance
KSampler
VAEDecode
SaveImage
PreviewImage
PowerLoRALoader
MarkdownNote
MfluxLoader
MfluxSampler
ImageScaleBy
ImageUpscaleWithModel
ControlNetLoader
ControlNetApply
```
