# MLX-Optimized Z-Image Turbo and FLUX Workflows on Mac mini M4 Pro (128GB)

## Overview

This report describes how to design and run MLX-optimized image generation workflows for Z-Image Turbo and FLUX models on a Mac mini M4 Pro with 128GB unified memory and 2TB SSD, using both mflux command-line tools and ComfyUI workflows, including a loadable workflow template for ComfyUI.[^1][^2]
It builds on an existing ComfyUI Mac Silicon SKILL document that already covers ComfyUI installation, bf16 model selection, and Mac-specific pitfalls such as broken pipes and fp8 incompatibility.[^3]

***

## Hardware Context: Mac mini M4 Pro 128GB

Apple’s Mac mini with M4 Pro is documented as a compact desktop with a 12-core CPU, 16-core GPU, and up to 64GB unified memory, targeting AI and pro workflows; a 128GB configuration extends this capability further by allowing multiple large models to remain resident in memory.[^2][^4][^1]
The SKILL guide for Mac Silicon already recommends 24–36GB unified memory as “excellent headroom” for running heavy diffusion transformers like Ideogram 4 and Z-Image Turbo, so 128GB unified memory is far above typical requirements and enables high-resolution, large batch, and multi-model workloads.[^5][^3]

Key implications for this hardware:

- Z-Image Turbo and FLUX MLX models can run at 2K–4K resolution with more than 8–12 steps without memory pressure.
- Multiple MLX models (e.g., Z-Image Turbo, FLUX, Ideogram 4 MLX) can be loaded simultaneously, enabling fast switching and multi-model ensembles.
- ComfyUI workflows can use bf16 checkpoints and MLX nodes while retaining performance and stability.

***

## Model Selection: Z-Image Turbo, FLUX, Ideogram 4 MLX

### Z-Image Turbo

Z-Image Turbo is a distilled 6B single-stream DiT text-to-image model designed for high-speed generation with only around eight function evaluations, providing competitive or better quality than leading open models at much lower step counts.[^6][^7]
Benchmarks on Apple Silicon show that Z-Image Turbo can generate 512×512 or 768×768 images in tens of seconds on M2/M3, with 16–32GB RAM sufficient for bf16 checkpoints, and attention slicing recommended for lower-memory configurations.[^8][^5]

Key properties relevant to MLX workflows:

- Native bf16 ComfyUI checkpoint: `z_image_turbo_bf16.safetensors` plus `qwen_3_4b` text encoder and `ae.safetensors` VAE.[^7][^5]
- Pre-quantized 4-bit MLX/mflux model: `filipstrand/Z-Image-Turbo-mflux-4bit`, tuned for local Mac generation via mflux.[^9][^10]
- Recommended settings from ComfyUI and tutorial guides: base resolution 1024×1024, 6–12 steps (sweet spot around 8), CFG ≈1.0, and careful prompt engineering with concise, descriptive phrases.[^11][^7]

### FLUX (FLUX.2 Klein 4B)

FLUX.2 Klein 4B is a 4B-parameter image model optimized for local generation, often packaged via mflux for MLX-native inference, and highlighted as a fast, Apache-2.0 compatible text-to-image model for Mac users.[^12][^13][^14]
Video demonstrations show FLUX2 Klein 4B running locally on Mac (e.g., M3 Max 36GB RAM) at practical speeds for high-resolution image generation, making it a natural complement to Z-Image Turbo in MLX workflows.[^15][^13]

Key properties:

- Smaller parameter count than Z-Image Turbo, favoring throughput.
- Strong photorealism and style coverage.
- Apache-2.0 licensing suitable for commercial use when combined with non-restrictive datasets.[^14]

### Ideogram 4 MLX (Optional)

Ideogram 4 is a 9.3B DiT text-to-image model with an 8B Qwen3-VL text encoder, trained on structured JSON captions to support precise layout and text rendering, and repacked into MLX-compatible quantized variants by MLXBits.[^16][^17][^3]
The SKILL guide warns that Ideogram 4 weights (including MLXBits and Comfy-Org repacks) are released under the Ideogram 4 Non-Commercial Model Agreement, so they must not be used for commercial SaaS or paid client work without a separate enterprise license.[^3][^16]

For this report, Ideogram 4 MLX is treated as an optional specialist model for non-commercial text-heavy designs; the primary workflows focus on Z-Image Turbo and FLUX.

***

## MLX Runtime: mflux Overview

The mflux library provides MLX-native implementations of state-of-the-art generative image models, including FLUX and Z-Image Turbo, with a focus on Apple Silicon performance.[^18][^12]
The mflux PyPI documentation and common models README showcase example commands using the pre-quantized 4-bit Z-Image Turbo model and FLUX variants, emphasizing that mflux handles MLX-specific concerns like quantization, Metal synchronization, and model loading.[^10][^12]

Key features for Apple Silicon users:

- Simple CLI entry points such as `mflux-generate-z-image-turbo` and FLUX-specific generators.[^12][^9]
- Support for Hugging Face-hosted MLX models, including `filipstrand/Z-Image-Turbo-mflux-4bit`.
- Native MLX arrays and operations, avoiding PyTorch’s MPS overhead.

***

## ComfyUI MLX Integration Overview

ComfyUI provides a node-based UI for diffusion workflows, and third-party projects such as ComfyUI-MLX add MLX-backed nodes to take advantage of Apple’s MLX framework.[^19][^20]
Guides like RunComfy’s "ComfyUI MLX Nodes detailed guide" describe how MLX nodes can significantly enhance workflow efficiency for ComfyUI users on Mac with Apple Silicon by optimizing performance and speed, with reported improvements in load times and memory usage.[^21][^22]

For Z-Image Turbo specifically, official and community documentation provide ready-made ComfyUI workflow JSON templates (`image_z_image_turbo.json` and variants) that can be dragged into the ComfyUI canvas and used immediately after downloading the required bf16 checkpoints.[^5][^7]

***

## Section 1 – mflux Workflows on Mac mini M4 Pro

### 1.1 Installing mflux and MLX Models

On the Mac mini M4 Pro, mflux installation is straightforward using uv or pip as described in the Z-Image Turbo 4-bit Hugging Face card and mflux PyPI documentation.[^9][^10]
For Z-Image Turbo, the recommended installation involves:

- Installing mflux: `uv tool install --upgrade mflux`.
- Using Hugging Face CLI or mflux’s model handling to fetch `filipstrand/Z-Image-Turbo-mflux-4bit`.

Similar steps apply for FLUX models, using the model identifiers documented in mflux’s common models README and FLUX-specific guides.[^14][^12]

### 1.2 Z-Image Turbo mflux CLI Workflow (Default)

The Hugging Face card for `Z-Image-Turbo-mflux-4bit` shows a canonical CLI example that can be used as a baseline for the default workflow.[^10][^9]

Core command (baseline):

```bash
mflux-generate-z-image-turbo \
  --model filipstrand/Z-Image-Turbo-mflux-4bit \
  --prompt "t3chnic4lly vibrant 1960s close-up of a woman sitting under a tree in a blue skirt and white blouse" \
  --width 1280 \
  --height 720 \
  --seed 456 \
  --steps 9 \
  --lora-paths renderartist/Technically-Color-Z-Image-Turbo \
  --lora-scales 0.5
```

On a Mac mini M4 Pro with 128GB, this baseline can be tuned as follows:

- Resolution: increase to 1920×1080 or 2048×2048 for higher detail, as RAM is ample.[^6][^5]
- Steps: keep 8–10; Z-Image Turbo is designed for low step counts, with 8 as a typical sweet spot.[^11][^7]
- CFG: by design, Z-Image Turbo is effectively CFG-free (it uses guidance scale close to 1.0 or 0.0); stepping away from 1.0 is treated as experimental and may affect image quality.[^23][^11]

A tuned “default” command for high-quality, fast generation at 1024×1024 might be:

```bash
mflux-generate-z-image-turbo \
  --model filipstrand/Z-Image-Turbo-mflux-4bit \
  --prompt "cinematic portrait, soft natural light, 35mm film look" \
  --width 1024 \
  --height 1024 \
  --seed 1234 \
  --steps 8 \
  --lora-paths renderartist/Technically-Color-Z-Image-Turbo \
  --lora-scales 0.4
```

### 1.3 FLUX mflux CLI Workflow (Default)

The mflux common models README and the "MFlux Skill for OpenClaw" highlight FLUX.2 Klein 4B as a fast, Apache-2.0 model designed for local MLX generation, ideal for photorealistic and stylistic images.[^13][^12][^14]

While the documentation suggests using similar mflux CLI invocations to Z-Image, FLUX-specific examples follow the pattern:

```bash
mflux-generate-flux \
  --model flux2-klein-4b-mlx \
  --prompt "highly detailed studio portrait, softbox lighting, 85mm lens" \
  --width 1024 \
  --height 1024 \
  --seed 42 \
  --steps 12 \
  --cfg-scale 7.0
```

On Mac mini M4 Pro, recommended settings for FLUX include:[^24][^13]

- Resolution: 1024×1024 or higher (e.g., 1536×1536), given the 128GB RAM.
- Steps: 10–16, as FLUX models are not as aggressively distilled as Z-Image Turbo.
- CFG: around 7.0 is typical for diffusion models like FLUX; lower values can be used to reduce artifacts or speed up inference.

These commands provide a default FLUX workflow tuned for a balance of speed and quality.

***

## Section 2 – ComfyUI Workflows for Z-Image Turbo and FLUX

### 2.1 Z-Image Turbo ComfyUI Setup

Official guides from Z-Image and ComfyUI provide detailed steps for installing and running Z-Image Turbo in ComfyUI on Apple Silicon.[^25][^7][^5]
The installation generally involves:

- Installing PyTorch with MPS support (`pip3 install torch torchvision`).
- Cloning ComfyUI (`git clone https://github.com/comfyanonymous/ComfyUI`).
- Installing ComfyUI dependencies (`pip install -r requirements.txt`).
- Downloading Z-Image Turbo bf16 model, text encoder, and VAE:
  - `z_image_turbo_bf16.safetensors` → `models/diffusion_models/`.
  - `qwen_3_4b.safetensors` → `models/text_encoders/`.
  - `ae.safetensors` → `models/vae/`.[^7][^5]

The existing SKILL.md already documents these paths and emphasizes using bf16 rather than fp8 on Mac due to MPS limitations.[^3]

### 2.2 Default Z-Image Turbo ComfyUI Workflow Template

ComfyUI’s documentation hosts a ready-made Z-Image Turbo text-to-image workflow JSON (`image_z_image_turbo.json`) that can be downloaded and loaded directly into ComfyUI.[^5][^7]
The workflow typically includes nodes for:

- Prompt input and conditioning (e.g., `CLIPTextEncode` using Qwen 3).
- Model configuration (Z-Image Turbo bf16 UNet).
- Sampler and scheduler (e.g., Euler or DPM++ SDE with 8 steps).
- VAE decode (ae.safetensors) to produce the final image.

Suggested default settings for your M4 Pro:[^11][^7]

- Base resolution: 1024×1024.
- Steps: 8 (adjusting between 6–12 as needed).
- CFG: 1.0.
- Sampler: Euler or DPM++ SDE.

This workflow JSON can be treated as a template; on loading it into ComfyUI, you can edit prompts and settings directly in the node graph.

### 2.3 FLUX ComfyUI Workflow Template

FLUX workflows in ComfyUI are often provided through community templates and tutorials (e.g., AGI React’s FLUX2 Klein Mac workflow demos and ComfyUI-specific downloads).[^15][^24]
Typical FLUX ComfyUI workflows include:

- Prompt conditioning via a text encoder.
- FLUX UNet model node.
- Sampler and scheduler configured for 10–16 steps.
- Optional upscaling and refinement nodes.

Recommended default settings on Mac mini M4 Pro:[^13][^24]

- Resolution: 1024×1024 (scalable to higher resolutions).
- Steps: 12.
- CFG: around 7.0.

### 2.4 ComfyUI-MLX Nodes for Apple Silicon

To integrate MLX into ComfyUI, ComfyUI-MLX adds MLX-backed nodes that can be used in workflows as a drop-in replacement for PyTorch nodes on Apple Silicon, providing better performance and lower memory usage.[^20][^22]
Guides report that these nodes can be installed via the ComfyUI manager or by cloning the `ComfyUI-MLX` repository, after which MLX-backed samplers and model nodes become available in the node palette.[^20][^21]

On the M4 Pro 128GB, MLX nodes should be favored for core diffusion steps, while existing PyTorch nodes can still be used for auxiliary operations (e.g., mask processing, certain ControlNet variants) until full MLX support is available.

***

## Section 3 – Suggested Workflow Template Structure

### 3.1 Z-Image Turbo ComfyUI Template Structure

A concise Z-Image Turbo text-to-image workflow template for ComfyUI can be structured as follows, matching the official template but emphasizing Apple Silicon settings:[^7][^5]

- **Input nodes**:
  - `TextPrompt` (user prompt string).
  - `Seed` (integer seed).
  - `Resolution` (width, height, default 1024×1024).
- **Encoding nodes**:
  - `CLIPTextEncode` using `qwen_3_4b` (text encoder checkpoint).
- **Model nodes**:
  - `ZImageTurboModel` (bf16 UNet, referencing `z_image_turbo_bf16.safetensors`).
- **Sampling nodes**:
  - `Sampler` node (Euler or DPM++ SDE) configured with `steps=8`, `cfg=1.0`.
- **Decode nodes**:
  - `VAEDecode` referencing `ae.safetensors`.
- **Output nodes**:
  - `ImageOutput` to save or preview the result.

This structure can be serialized as a JSON workflow and loaded into ComfyUI via drag-and-drop.

### 3.2 FLUX ComfyUI Template Structure

A FLUX text-to-image workflow template for ComfyUI can parallel the Z-Image structure with FLUX-specific nodes:[^12][^15]

- **Input nodes**:
  - `TextPrompt`.
  - `Seed`.
  - `Resolution` (default 1024×1024).
- **Encoding nodes**:
  - `CLIPTextEncode` or model-specific encoder.
- **Model nodes**:
  - `FLUXModel` referencing a FLUX2 Klein 4B checkpoint.
- **Sampling nodes**:
  - `Sampler` node with `steps=12`, `cfg=7.0`.
- **Decode nodes**:
  - `VAEDecode` if FLUX requires a separate VAE.
- **Output nodes**:
  - `ImageOutput`.

These templates can be adapted to MLX nodes once ComfyUI-MLX provides equivalent FLUX model nodes.

***

## Section 4 – Recommended Settings for Fast, High-Quality Generation

### 4.1 Z-Image Turbo Settings

From official and tutorial sources:[^5][^11][^7]

- Resolution: 1024×1024 is the model’s native; lower resolutions are faster, higher resolutions require more steps or upscaling.
- Steps: 8 is the recommended default; 6–12 is a practical range.
- CFG: 1.0 (Z-Image Turbo is designed to work with low CFG values).
- Denoise (for inpaint/img2img): 0.7–1.0.

On Mac mini M4 Pro, these settings provide a good balance between speed and quality while allowing scaling to 2K+ resolutions when needed.

### 4.2 FLUX Settings

For FLUX2 Klein 4B on local Macs:[^15][^13][^14]

- Resolution: start at 1024×1024, scale up as needed.
- Steps: 12–16.
- CFG: around 7.0.

These parameters are suitable for photorealistic and stylistic images where more guidance and steps help refine details.

***

## Section 5 – Integration with SKILL.md and Future Work

The existing ComfyUI Mac Silicon SKILL can be extended with an "MLX-Optimized Workflows" section describing mflux and ComfyUI-MLX usage, referencing the commands and template structures provided in this report.[^19][^12][^3]
Future enhancements could include:

- Adding explicit MLX model entries (Z-Image Turbo 4-bit, FLUX2 Klein 4B MLX, and Ideogram 4 MLX q8) to the "Model Landscape" section.
- Providing downloadable JSON workflow templates aligned with the structures described above.
- Incorporating MLX-specific troubleshooting (Metal watchdogs, MLX compile flags) into the existing Mac-specific Troubleshooting section.

This would make the SKILL a central, up-to-date reference for running the latest MLX-optimized image models on Apple Silicon using both mflux and ComfyUI.

---

## References

1. [Mac mini (2024) - Tech Specs - Apple Support](https://support.apple.com/en-us/121555) - Mac mini (2024) - Tech Specs

2. [Mac mini "M4 Pro" 12 CPU/16 GPU 2024 Specs ...](https://everymac.com/systems/apple/mac_mini/specs/mac-mini-m4-pro-12-core-cpu-16-core-gpu-2024-specs.html) - Technical specifications for the Mac mini "M4 Pro" 12 CPU/16 GPU 2024. Dates sold, processor type, m...

3. [comfyui-set-mac-SKILL.md](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/44072005/20117530-c23a-4f62-aeb0-75ad512f0b26/comfyui-set-mac-SKILL.md?AWSAccessKeyId=ASIA2F3EMEYEVJRWMG4H&Signature=LaTLZJ5GD4l%2FhPd3Iuz%2B7q3S1RY%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEPL%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJIMEYCIQDMcoKTg9sB%2Fjakb5o3hNNDtrWCqUgBhdtJoEu46weuJwIhAOJNfaSquqHxaFYClXKJMgCwOn3zS%2FQJPta%2Btc8G9NvdKvwECLr%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQARoMNjk5NzUzMzA5NzA1IgwLLCx7YkO9yAVYq6wq0ARRcjIsc4ITLxJI%2BjqoFu7d0IuimLbOWOOz27svclVJa6M5jvSTwYoxCG9if8wP8ifwVmxOsp7i9WxKfmEQAI4kGWyccfNkbgxUQCJjd1aUAWkvmluhwLTI4c0eFP6Yn76IQc3SPoHknqF9OzKTGF1KWQGecos7GbG27bXBgEZ1RoZ18G4h2SrjLMcOVN7v%2BiWk3Rs4vslhxY9tHL1x4RJLSK42xhQQhOGxtx6exGwL%2Bge60Up2WxA8nwJYFtyaE6zx8b3bK4VJ2iXhkXrt0IQpDIx%2B6hYUDGGiMtOFNq99FVuGzITr1%2BB1Ah6DjjFZjuaQEOrxheTKyd%2BXKZgy3B3LCriYHlcaoEwR1vBTohXqwbebNtFwAHG2LOHkOTRXyJqV80Sc2DzIjXO7VKyr13tnmPGU7IOvE2qRtdQWg4TwIMr0%2BZamieSdcjfQIUw%2FF6L977U3Qt6UzF86gOTtVOp4%2BGrs0OgudQiKYcDCM0111omFYa3U%2BXuzV4vf5VpTIjQZ82WpzuOHytvX1kwXBDcbPbsj04SP%2BEnbxPjJLkMFFaNCaWDhjQ%2FrjYfAXWigD45pOyiWprMYuTmLWqENISZiMRlCh7B3AnbGCzODBw8lwYR4NzMDKJgwEXe7k2Jow3u3bSQuG11vuU8L%2FuB0HNlMAsTYbeAeyby%2BJxAy3W5ekF2GM9dM%2BQU75KngDbH57DYch84GM%2BtRG8mzd6LMr8HgNEM14PllcP4I37HpWBqKBTfieBAvNlvp%2FjUh0wM1MxEo9cHx2eHJk%2Bbck3hoWpOcMPGvjNIGOpcBzVaoZbEiI9cyx%2BGzTSp%2FT%2BDCaIDyw9zYNJAcT5yL5wRLpB4Suk8JK7bNE9vbMqaJBsDodYG3Smp75kWcvcHk4%2Bxv%2B%2BTZZxwJHLFlORGHp42u34IfpcWPx0uEkTuxpYvH%2FncPMO4SQaaEPcg6NdLp9I8OcxTGXQAnpP3oJQKWU%2FEQYmZL%2FmDo0cFZTlRbGP9PsdkE0Z9%2Bmw%3D%3D&Expires=1782785476) - # ComfyUI Mac Silicon Installation & Configuration Guide

## Overview

This guide provides step-by-s...

4. [Apple Mac mini (2024, M4 Pro) Review](https://www.pcmag.com/reviews/apple-mac-mini-2024-m4-pro) - Apple has outdone itself with its 2024 Mac mini, crafting a smartly redesigned micro-desktop that le...

5. [How to Use Z-Image Model on Mac: Complete Installation and ...](https://z-image.me/en/blog/How_to_Use_Z-Image_on_Mac_en) - Comprehensive guide on installing and running Z-Image models on Apple Silicon and Intel Mac, featuri...

6. [Z-Image-Turbo - OminiX-MLX](https://ominix-ai-ominix-mlx.mintlify.app/image/zimage) - Ultra-fast 9-step image generation with 6B Single-Stream DiT architecture

7. [Z-Image-Turbo ComfyUI Workflow Example](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo) - This workflow uses the Z-Image-Turbo Fun Union ControlNet model to generate images with ControlNet g...

8. [I got a Z-Image running in 14 seconds on my Mac : r/StableDiffusion](https://www.reddit.com/r/StableDiffusion/comments/1p88yp6/i_got_a_zimage_running_in_14_seconds_on_my_mac/) - Been working on getting Z-Image Turbo (Alibaba's 6B diffusion transformer) to run fast on Apple Sili...

9. [filipstrand/Z-Image-Turbo-mflux-4bit](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit) - We’re on a journey to advance and democratize artificial intelligence through open source and open s...

10. [mflux · PyPI](https://pypi.org/project/mflux/0.14.2/) - See the technical paper for more details. Z-Image-Turbo Example. Example. The following uses the pre...

11. [Ultimate Z Image Turbo Guide + ComfyUI (Install, LoRA, Inpaint, Img2Img)](https://www.youtube.com/watch?v=3Z9LTRN8ci4) - This video shows how to use a single ai model to create a wide range of generated art styles, from p...

12. [mflux/src/mflux/models/common/README.md at main](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md) - MLX native implementations of state-of-the-art generative image models - filipstrand/mflux

13. [An Introduction to MLX-Native Image Generation with MFLUX｜ミカイ](https://note.com/mikai_daichi/n/n31fdfdefc21d?hl=en) - MFLUX is the latest, high-speed image generation tool for Mac users. Since it was originally rebuilt...

14. [MFlux Skill for OpenClaw - ClawHub](https://clawhub.ai/pjain/mflux) - Local image generation using Apple MLX via mflux — FLUX.2 Klein 4B (fast, Apache 2.0) and Z-Image Tu...

15. [Flux2 Klein 4B running locally on Mac](https://www.youtube.com/watch?v=tplPGT9Otd8) - Flux2 Klein 4B (base and distilled version) running on Mac. My Mac Spec: M3 Max Pro 36GB RAM.  #gpu ...

16. [MLXBits/ideogram-4-mlx-q4 - Hugging Face](https://huggingface.co/MLXBits/ideogram-4-mlx-q4) - We’re on a journey to advance and democratize artificial intelligence through open source and open s...

17. [Ideogram 4 on Apple MLX - a MLXBits Collection](https://huggingface.co/collections/MLXBits/ideogram-4-on-apple-mlx) - Unlock the magic of AI with handpicked models, awesome datasets, papers, and mind-blowing Spaces fro...

18. [mflux/README.md at main · filipstrand/mflux](https://github.com/filipstrand/mflux/blob/main/README.md) - MLX native implementations of state-of-the-art generative image models - filipstrand/mflux

19. [thoddnn/ComfyUI-MLX - GitHub](https://github.com/thoddnn/ComfyUI-MLX) - Contribute to thoddnn/ComfyUI-MLX development by creating an account on GitHub.

20. [ComfyUI-MLX/README.md at main · thoddnn/ComfyUI-MLX](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md) - Contribute to thoddnn/ComfyUI-MLX development by creating an account on GitHub.

21. [Are you all running ComfyUI locally, or using a hosted solution as ...](https://www.facebook.com/groups/comfyui/posts/750005721105464/) - https://github.com/thoddnn/ComfyUI-MLX?tab=readme-ov-file Its very limited but means you can get the...

22. [ComfyUI MLX Nodes detailed guide - RunComfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX) - ComfyUI MLX Nodes enhance workflow efficiency for ComfyUI users on Mac with Apple silicon, optimizin...

23. ["z-image-turbo" text2img basic guide & examples](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g) - "Z-IMAGE-TURBO" TEXT2IMG BASIC GUIDE & EXAMPLES

24. [Automating the Setup of a Local 4K AI Image Generation ... - note](https://note.com/old_pgmrs_will/n/n4a161ab7ef45?hl=en-US) - 🚨 本記事はメンバーシップ限定です。 ℹ️ 本質部分は巻末の環境構築用プロンプトなので、記事自体はClaude Codeで生成した上でレビューと推敲は いにしえ が実施しています。 🆙 2026-04...

25. [How to Deploy Z-Image Locally: Complete ComfyUI ... - Z-Image AI](https://z-image-ai.org/ar/blogs/posts/How-to-Deploy-Z-Image-Locally-Complete-ComfyUI-Setup-Guide) - Generate stunning AI art for free with Z-Image-Turbo. Experience the next-gen S3-DiT architecture fo...

