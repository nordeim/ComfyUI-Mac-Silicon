# Link Patterns by Model Family

## Z-Image Turbo (PyTorch MPS)

```
UNETLoader.MODEL → ModelSamplingAuraFlow.MODEL
ModelSamplingAuraFlow.MODEL → KSampler.MODEL
CLIPLoader.CLIP → CLIPTextEncode.CLIP (positive)
CLIPLoader.CLIP → CLIPTextEncode.CLIP (negative)
CLIPTextEncode.CONDITIONING (positive) → FluxGuidance.CONDITIONING
FluxGuidance.CONDITIONING → KSampler.POSITIVE
CLIPTextEncode.CONDITIONING (negative) → KSampler.NEGATIVE
EmptySD3LatentImage.LATENT → KSampler.LATENT_IMAGE
VAELoader.VAE → VAEDecode.VAE
KSampler.LATENT → VAEDecode.SAMPLES
VAEDecode.IMAGE → SaveImage.IMAGES
```

## Z-Image Turbo with LoRA

```
UNETLoader.MODEL → PowerLoRALoader.MODEL
PowerLoRALoader.MODEL → ModelSamplingAuraFlow.MODEL
PowerLoRALoader.STRENGTH → (widget: 0.6)
```

## FLUX.1-dev (PyTorch MPS)

```
UNETLoader.MODEL → KSampler.MODEL
CLIPLoader.CLIP → CLIPTextEncode.CLIP (positive)
CLIPLoader.CLIP → CLIPTextEncode.CLIP (negative)
CLIPTextEncode.CONDITIONING (positive) → FluxGuidance.CONDITIONING
FluxGuidance.CONDITIONING → KSampler.POSITIVE
CLIPTextEncode.CONDITIONING (negative) → KSampler.NEGATIVE
EmptyLatentImage.LATENT → KSampler.LATENT_IMAGE
VAELoader.VAE → VAEDecode.VAE
KSampler.LATENT → VAEDecode.SAMPLES
VAEDecode.IMAGE → SaveImage.IMAGES
```

Key difference from Z-Image: **No ModelSamplingAuraFlow** — FLUX connects UNETLoader directly to KSampler.

## FLUX.2 [klein] 4B (Mflux-ComfyUI, MLX)

```
MfluxLoader.MODEL → MfluxSampler.MODEL
MfluxSampler.IMAGE → SaveImage.IMAGES
```

Minimal 3-node flow — no separate CLIP/VAE needed (bundled in MLX).

## Krea 2 Turbo (PyTorch MPS)

```
UNETLoader.MODEL → KSampler.MODEL
CLIPLoader.CLIP → CLIPTextEncode.CLIP (positive)
CLIPLoader.CLIP → CLIPTextEncode.CLIP (negative)
CLIPTextEncode.CONDITIONING (positive) → FluxGuidance.CONDITIONING
FluxGuidance.CONDITIONING → KSampler.POSITIVE
CLIPTextEncode.CONDITIONING (negative) → KSampler.NEGATIVE
EmptySD3LatentImage.LATENT → KSampler.LATENT_IMAGE
VAELoader.VAE → VAEDecode.VAE
KSampler.LATENT → VAEDecode.SAMPLES
VAEDecode.IMAGE → SaveImage.IMAGES
```

**Critical:** FluxGuidance guidance = **0.0** (not 7.0 like FLUX).

## Ideogram 4 (PyTorch MPS or Mflux-ComfyUI)

```
UNETLoader.MODEL → KSampler.MODEL
CLIPLoader.CLIP → CLIPTextEncode.CLIP (positive)  [clip_name: qwen3_vl_8b.safetensors]
CLIPLoader.CLIP → CLIPTextEncode.CLIP (negative)
CLIPTextEncode.CONDITIONING (positive) → KSampler.POSITIVE  [no FluxGuidance]
CLIPTextEncode.CONDITIONING (negative) → KSampler.NEGATIVE
EmptyLatentImage.LATENT → KSampler.LATENT_IMAGE
VAELoader.VAE → VAEDecode.VAE
KSampler.LATENT → VAEDecode.SAMPLES
VAEDecode.IMAGE → SaveImage.IMAGES
```

Key difference: **No FluxGuidance** — Ideogram 4 handles guidance internally.

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| CLIPTextEncode negative connected to positive input | Garbled output | Wire negative to `KSampler.negative` |
| Missing ModelSamplingAuraFlow for Z-Image | Wrong sampling distribution | Add node between UNETLoader and KSampler |
| FluxGuidance on non-FLUX models | Wrong guidance scale | Omit for Ideogram, Krea |
| fp8 model filename in UNETLoader | Won't load on Mac | Use bf16 or MLX-quantized variants |
| LoRA from different architecture | Crash at KSampler | Match LoRA to model family |
| VAELoader output to KSampler | Type mismatch | VAE → VAEDecode, not KSampler |

## Slot Index Reference

### KSampler Input Slots
```
0: seed (INT)
1: steps (INT)
2: cfg (FLOAT)
3: sampler_name (SAMPLER)
4: scheduler (SCHEDULER)
5: denoise (FLOAT)
6: model (MODEL)
7: positive (CONDITIONING)
8: negative (CONDITIONING)
9: latent_image (LATENT)
```

### CLIPTextEncode Input Slots
```
0: text (STRING/multiline)
1: clip (CLIP) — link from CLIPLoader
```

### VAEDecode Input Slots
```
0: samples (LATENT) — link from KSampler
1: vae (VAE) — link from VAELoader
```

### FluxGuidance Input Slots
```
0: guidance (FLOAT)
1: conditioning (CONDITIONING) — link from positive CLIPTextEncode
```
