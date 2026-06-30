You can treat this as a multi-phase project: first map all MLX-native image models and Apple‑Silicon runtimes, then benchmark candidates, then design MLX‑optimized ComfyUI nodes and a parallel “pure MLX” code path, all grounded on your existing Mac ComfyUI SKILL.md. 

***

## Phase 0 – Define constraints and success criteria

Before touching models, lock down what “most capable” means for you and what hardware you’re targeting.

- Enumerate your Mac configs (chip, unified RAM, internal SSD space) and map them to the hardware tables already in your SKILL.md, which differentiate M4 base/Pro/Max and recommend quantized or bf16 variants. 
- Define capability metrics: text rendering quality, prompt adherence, style diversity, maximum resolution, latency per image, batch size, and whether usage is non‑commercial (so Ideogram 4 weights are allowed) or must be fully open‑source (favoring Krea 2, Z‑Image, FLUX). [modelfit](https://modelfit.io/guides/local-image-generation-mac/)

Deliverable: a short requirements spec (e.g., “Target: M2 Pro 16 GB, non‑commercial, 1024×1024, <20 s/image, strong text rendering”).

***

## Phase 1 – Systematically map the MLX image‑model ecosystem

Objective: build an up‑to‑date catalog of all MLX‑native text‑to‑image/diffusion models that can realistically run on M‑series Macs.

Research steps:

- Explore Hugging Face’s MLX model filters (`library=mlx`) to collect an initial list of image‑generation models (e.g., Z‑Image Turbo, FLUX ports, Qwen‑Image, Ideogram MLX conversions). [huggingface](https://huggingface.co/models?library=mlx)
- Drill into the MLXBits organization and “Ideogram 4 on Apple MLX” collection to identify bf16 and quantized variants (q4, q6, q8) and note disk footprint and RAM requirements. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q4)
- Read the mflux README and PyPI docs carefully to list all image models it supports (FLUX, Z‑Image Turbo, Qwen Image, Bria, ideogram‑4 when PR is merged), and record CLI generation commands, quantization flags, and configuration surfaces. [github](https://github.com/filipstrand/mflux/blob/main/README.md)

Deliverable: a table like:

| Model            | Runtime (MLX / PyTorch / CoreML) | Quantization options | Min RAM (practical) | License notes |
|------------------|----------------------------------|----------------------|----------------------|--------------|

***

## Phase 2 – Shortlist “most capable” candidates per hardware tier

Objective: narrow the MLX model list to 2–3 primary candidates per RAM tier.

Research steps:

- For high‑RAM Macs (32–64 GB), evaluate full‑precision or bf16 Ideogram 4 MLX (for layout/text focus), FLUX MLX (for photorealism & style), and Z‑Image Turbo MLX (for speed + quality). [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx/commit/05527f235e22064816db7d0249254e9651b2f137)
- For 16–24 GB Macs, focus on quantized Ideogram 4 (q4/q6), Z‑Image Turbo, Krea 2 Turbo MLX repacks, and any distilled FLUX variants that explicitly advertise MLX compatibility and small memory footprints. [huggingface](https://huggingface.co/MLXBits/models)
- Use third‑party guides such as “Local Image Generation on Mac (2026): What Fits Your RAM” to cross‑check what realistically runs on 8/16/32 GB Apple Silicon, including SDXL/SD3.5, FLUX, and Z‑Image, and note reported performance and stability issues. [modelfit](https://modelfit.io/guides/local-image-generation-mac/)

Deliverable: a ranked shortlist per tier, e.g.:

- Tier A (≥32 GB): Ideogram 4 MLX bf16 + FLUX MLX.  
- Tier B (16–24 GB): Z‑Image Turbo + Krea 2 Turbo MLX + Ideogram 4 q4/q6.  

***

## Phase 3 – Deep‑dive each shortlisted model

Objective: gather detailed architectural and performance data for each candidate.

Research steps for each model:

- Read original or derivative docs (Hugging Face cards, papers, blogs) for architecture (DiT vs U‑Net, flow‑matching vs diffusion), text encoder (Qwen3 4B/8B, T5/CLIP), and special features (JSON layout prompts for Ideogram; CFG‑free sampling for Krea 2 Turbo; flow‑matching + AuraFlow sampling for Z‑Image). [pypi](https://pypi.org/project/mflux/0.14.2/)
- Capture recommended sampling hyperparameters: number of steps, CFG/guidance behavior (e.g., Krea 2 Turbo must run with guidance=0.0), resolution ranges, and any MLX‑specific flags (quantization level, MLX_DISABLE_COMPILE, MLX_METAL_FAST_SYNCH as used by Phosphene for watchdog‑safe runs). [beta.pinokio](https://beta.pinokio.co/posts/01kv3nwkv8z8tqwvm89p2d9qn9)
- Summarize licensing: non‑commercial constraint for Ideogram weights (including MLXBits and Comfy‑Org repacks), vs more permissive open‑source licenses for Krea 2 and Z‑Image Turbo; record any gating or terms needed for commercial work. [huggingface](https://huggingface.co/collections/MLXBits/ideogram-4-on-apple-mlx)

Deliverable: per‑model sheets with “capability profile”, “recommended settings on M‑series”, and “license constraints”.

***

## Phase 4 – Evaluate runtime options: pure MLX vs ComfyUI vs alternatives

Objective: decide where MLX should sit in your stack: direct mflux scripts, MLX‑based ComfyUI nodes, or external apps.

Research steps:

- Study mflux’s CLI & Python API to understand how it instantiates MLX models, handles quantization, and interacts with Apple’s MLX and Metal, including uv‑based scripts and quantize options (`quantize=8`, `-q 8` etc.). [github](https://github.com/filipstrand/mflux/blob/main/README.md)
- Review ComfyUI‑MLX custom nodes (thoddnn/ComfyUI‑MLX) to see how they bridge ComfyUI workflows to MLX instead of PyTorch MPS, including reported 70% faster first‑load times, ~35% faster generation, and ~30% lower memory usage vs Torch on Apple Silicon. [github](https://github.com/thoddnn/ComfyUI-MLX)
- Examine mlx‑vlm‑ComfyUI to understand a more complex MLX integration (Vision‑Language models) and its data‑bridging layer that converts PyTorch tensors to MLX arrays, global model registry, quantization strategies, and multi‑modal support; this informs how to design similar nodes for image models. [github](https://github.com/rurounigit/mlx-vlm-ComfyUI)
- Cross‑check alternative Apple‑Silicon‑optimized apps (Draw Things, Phosphene) for how they wrap MLX/mflux and manage Metal watchdogs, offloading, and checkpoint downloads, especially Phosphene’s changes for M1/M2 (shorter command buffers, default quantization, smaller default batch sizes). [beta.pinokio](https://beta.pinokio.co/posts/01kv3nwkv8z8tqwvm89p2d9qn9)

Deliverable: comparison matrix:

| Runtime       | Pros on M‑series | Cons / limitations | Best‑fit use cases |
|---------------|------------------|--------------------|--------------------|
| mflux (CLI)   | Fastest, minimal | No visual workflows | Batch / scripts   |
| ComfyUI‑MLX   | Node‑based, visual | Needs custom nodes for each model | Complex pipelines |
| Phosphene     | Integrated, no setup | Opinionated UX, limited extensibility | One‑click Ideogram |

***

## Phase 5 – Design MLX‑optimized ComfyUI node architecture

Objective: blueprint how to run your chosen MLX models inside ComfyUI with minimal PyTorch involvement.

Research steps:

- Using ComfyUI‑MLX and DiffusionKit ports as reference, sketch the pipeline: prompt node → MLX scheduler/model node → MLX image decoder → output node, ensuring all heavy computation uses MLX arrays instead of Torch tensors. [github](https://github.com/comfyanonymous/ComfyUI/issues/2948)
- Investigate how ComfyUI hooks custom nodes into its manager (install via Git URL, exposing settings in the canvas), and what is required to add per‑model nodes (e.g., `MLX_ZImageTurbo`, `MLX_Ideogram4`). [github](https://github.com/thoddnn/ComfyUI-MLX)
- Study examples of MLX conversion in other domains (e.g., Svara TTS voice clone MLX bf16 conversion using `mlx_lm.convert`) to understand patterns for moving from HF diffusers checkpoints to MLX‑friendly layouts; apply similar thinking to image models that don’t yet have MLXBits repacks. [huggingface](https://huggingface.co/yaanfpv/svara-tts-voiceclone-beta-mlx-bf16)

Within SKILL.md integration:

- Plan a new “Method 2: MLX‑Optimized ComfyUI” section parallel to your existing “Method 1: Native MLX via mflux” and “Method 3: Draw Things”, explaining install steps for ComfyUI‑MLX nodes and how to choose models per chip/RAM. 
- Extend the Troubleshooting section to include MLX‑specific issues (Metal watchdogs, MLX compile flags), alongside existing Mac‑specific pitfalls (broken pipe, fp8 incompatibility). [beta.pinokio](https://beta.pinokio.co/posts/01kv3nwkv8z8tqwvm89p2d9qn9)

Deliverable: an architectural diagram and draft node specs for MLX model nodes (inputs/outputs, settings, and internal MLX calls).

***

## Phase 6 – Design the “pure MLX” custom‑code path

Objective: define a robust script‑based workflow for batch generation and experiments without ComfyUI.

Research steps:

- From mflux docs, extract canonical examples of using its Python API: instantiate models like `ZImageTurbo(quantize=8)` or FLUX models, call `generate_image(...)`, and save outputs; list available parameters and default values. [pypi](https://pypi.org/project/mflux/0.14.2/)
- Plan standardized prompt suites for benchmarking—e.g., text‑heavy posters, complex scenes, portraits, product shots—to run across all shortlisted models using mflux, with fixed seeds and inference steps, to generate comparable outputs. [modelfit](https://modelfit.io/guides/local-image-generation-mac/)
- Decide how you’ll manage model downloads: use Hugging Face `huggingface-cli` or mflux’s auto‑download mechanism, with local cache directories per model, following the patterns you already use in SKILL.md for Ideogram and Krea 2 MLX weights. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q4)

Deliverable: a set of scripts:

- `bench_zimage_mlx.py`  
- `bench_flux_mlx.py`  
- `bench_ideogram_mlx_q4.py`  

all with consistent CLI arguments (prompt, steps, quantization, output path).

***

## Phase 7 – Performance and quality benchmarking

Objective: empirically validate which model/runtime combo is “most capable” on your Macs.

Benchmark plan:

- Use ComfyUI’s `/system_stats` API (already documented in SKILL.md) to collect live metrics (CPU/GPU utilisation, memory usage) while running MLX‑based workflows, and compare them with PyTorch MPS runs of the same models where possible. [github](https://github.com/thoddnn/ComfyUI-MLX)
- Run each benchmark script and ComfyUI workflow at multiple resolutions (e.g., 512×512, 1024×1024, 1280×720) and record time‑to‑first‑image, time per image, peak RAM, and any stability issues (watchdog timeouts, OOMs). [pypi](https://pypi.org/project/mflux/0.14.2/)
- For quality, create a rating rubric (text legibility, prompt adherence, aesthetics) and manually score outputs, potentially supplemented with automated measures (e.g., CLIP similarity) if feasible; ensure you separately track text rendering, where Ideogram 4 may dominate. [github](https://github.com/filipstrand/mflux/blob/main/README.md)

Deliverable: a results spreadsheet and a short narrative summary like “On M2 Pro 16 GB, Z‑Image Turbo q8 via mflux is 2× faster than ComfyUI PyTorch SDXL and matches FLUX MLX quality at 1024×1024.”

***

## Phase 8 – Define the “optimal” configurations and workflows

Objective: translate research findings into concrete best‑practice recommendations.

Synthesis steps:

- For each hardware tier, choose a primary model and runtime: e.g., on 16 GB machines, recommend Z‑Image Turbo MLX via mflux for speed and an Ideogram‑4 q4 MLX workflow for high‑quality text; on 32 GB+, add FLUX MLX and higher‑precision Ideogram variants. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx/commit/05527f235e22064816db7d0249254e9651b2f137)
- Document optimal parameters per combination: quantization level, default steps, CFG/guidance, compile flags, recommended image sizes, and batch sizes, based on your benchmarks and external recommendations (e.g., Phosphene’s default `-q 6` for Ideogram on weaker GPUs). 
- For ComfyUI, specify template workflows (node graphs) for each model—including MLX nodes where available, or hybrid workflows using PyTorch only for minor parts—and include launch commands that incorporate your existing broken‑pipe and TQDM fixes (`nohup`, `TQDM_DISABLE`, `force-fp16`, etc.). [github](https://github.com/thoddnn/ComfyUI-MLX)

Deliverable: a “Recipes” section inside SKILL.md or a new MLX‑focused SKILL that lists ready‑to‑run commands and ComfyUI workflows per Mac configuration.

***

## Phase 9 – Update documentation and automation (SKILL.md and scripts)

Objective: integrate findings back into your ComfyUI Mac SKILL so it becomes a single source of truth.

Integration tasks:

- Extend the “Model Landscape (June 2026)” section with explicit MLX‑native entries and performance notes, referencing mflux and MLXBits, and clarifying when MLX vs PyTorch vs Metal is used. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q4)
- Add a “MLX‑Optimized Workflows” section that outlines both the ComfyUI‑MLX and pure mflux paths, linking to example commands and describing how to choose between them. [github](https://github.com/comfyanonymous/ComfyUI/issues/2948)
- Update appendices with installation scripts that optionally install mflux (via uv tool or pip), ComfyUI‑MLX nodes, and set MLX environment flags for stability on slower M‑series GPUs, inspired by Phosphene’s configuration. [beta.pinokio](https://beta.pinokio.co/posts/01kv3nwkv8z8tqwvm89p2d9qn9)

Deliverable: revised SKILL.md + a small collection of shell scripts (install & launch) and Python benchmarks.

***

## Phase 10 – Ongoing monitoring and refresh

Objective: keep your setup aligned with the rapidly evolving MLX ecosystem.

Maintenance plan:

- Set a recurring schedule (e.g., monthly) to review updated mflux releases and MLXBits collections for new models (e.g., new FLUX variants, new Ideogram versions, new Qwen Image models), and update your shortlist and recipes accordingly. [huggingface](https://huggingface.co/MLXBits/models)
- Watch ComfyUI issues and MLX‑related custom‑node repos (ComfyUI‑MLX, mlx‑vlm‑ComfyUI, CoreMLSuite) for new performance improvements or breaking changes that affect Mac workflows. [github](https://github.com/Comfy-Org/ComfyUI/issues/2948)
- Periodically rerun a reduced benchmark suite whenever Apple releases new MLX or Metal updates, or when you upgrade macOS/hardware, to confirm that your “optimal” settings still hold. [modelfit](https://modelfit.io/guides/local-image-generation-mac/)

***

If you’d like, next step could be to pick your exact Mac model and usage (commercial vs non‑commercial), and I can help you instantiate this plan by proposing an initial shortlist of MLX models and concrete mflux/ComfyUI commands tailored to your machine.

---

The next steps are to choose a flagship MLX model (practically Z‑Image Turbo + optional Ideogram‑4 MLX) and then design concrete ComfyUI‑MLX workflows and mflux‑based scripts around them, with a repeatable benchmarking and documentation update loop. [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)

Below I’ll continue the plan at a more “implementation‑ready” level, focusing on Z‑Image Turbo + MLX‑optimized ComfyUI and pure mflux code.

***

## Model choice and capability focus

Z‑Image Turbo in its MLX/mflux repacks is currently one of the best fits for Apple Silicon: a 6B DiT model that delivers high‑quality images in around 9 steps, with a pre‑quantized 4‑bit variant specifically designed for fast, low‑VRAM local generation. [seaart](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g)

Your SKILL.md already positions Z‑Image Turbo bf16 as a recommended Mac‑compatible diffusion model via ComfyUI; combining that with the MLX‑native 4‑bit mflux repack lets you cover both visual workflows and maximum performance CLI usage on M‑series CPUs. 

***

## Concrete MLX model set to investigate

Focus your deep dive on three concrete MLX‑friendly image models:

- **Z‑Image Turbo (MLX / mflux)**  
  - 6B DiT, turbo variant, excellent speed and strong prompt adherence at 6–10 steps. [seaart](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g)
  - Open licensing and pre‑quantized 4‑bit weights: `filipstrand/Z-Image-Turbo-mflux-4bit` (requires mflux ≥0.13.0). [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)

- **FLUX 1.x / 2.x MLX via mflux**  
  - mflux started as a FLUX MLX port; FLUX models are widely regarded for photorealism, aesthetics, and modern style coverage. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)
  - Strong candidate for “style & realism” benchmark against Z‑Image Turbo. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)

- **Ideogram 4 MLX (quantized) – optional, non‑commercial**  
  - 9.3B DiT + Qwen3‑VL encoder; heavy but uniquely capable for text and layout. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q4)
  - Use MLXBits q4/q8 variants for M‑series; keep non‑commercial license constraint in mind. [huggingface](https://huggingface.co/collections/MLXBits/ideogram-4-on-apple-mlx)

This gives you a triangle of strengths: **speed (Z‑Image Turbo), aesthetics (FLUX), text/layout (Ideogram 4).** [github](https://github.com/filipstrand/mflux/blob/main/README.md)

***

## Detailed plan for MLX‑optimized ComfyUI

### Step C1 – Install and validate ComfyUI‑MLX nodes

- Install **ComfyUI‑MLX** either through ComfyUI’s Custom Nodes Manager (“ComfyUI MLX” entry) or via Git URL `https://github.com/thoddnn/ComfyUI-MLX.git`. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)
- Confirm that MLX nodes show up in the ComfyUI canvas (e.g., FLUX‑oriented nodes from DiffusionKit ports) and verify the reported performance improvements—around 70% faster initial model load, 35% faster generation with loaded models, and ~30% lower memory use on an M2 Max test machine. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX)

Goal: ensure your ComfyUI environment can run MLX‑backed nodes alongside your existing PyTorch MPS workflows. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)

### Step C2 – Define MLX pipelines for each model

For each shortlisted model, design ComfyUI workflows where **all heavy diffusion steps** are handled by MLX nodes:

- **Z‑Image Turbo workflow:**
  - Use an MLX model node mapped to Z‑Image Turbo weights (bf16 or quantized variant; for pure MLX you’ll likely reference DiffusionKit‑style MLX models once available). 
  - Integrate Qwen3 4B text encoder / tokenizer nodes as required (you already have `qwen_3_4b.safetensors` in SKILL.md’s model paths). 
  - Configure sampler and scheduler settings in line with community guidance: 6–10 steps, AuraFlow 3–7, CFG ≈1, simple/normal/beta57 scheduler, and precision prompts rather than extremely long ones. [seaart](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g)

- **FLUX workflow (MLX):**
  - Use ComfyUI‑MLX FLUX nodes (ported from DiffusionKit) to construct a standard text‑to‑image pipeline; check README and any supplied example workflows. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)
  - Start with 512×512, 8–12 steps, then scale up resolution and steps once performance baseline is known. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)

- **Ideogram 4 workflow (hybrid):**
  - Since your SKILL.md currently runs Ideogram via diffusers/MPS or Draw Things, you can design a hybrid ComfyUI workflow where MLX nodes do as much as possible while falling back to PyTorch for parts that lack MLX equivalents (e.g., Qwen3‑VL encoder). [beta.pinokio](https://beta.pinokio.co/posts/01kv3nwkv8z8tqwvm89p2d9qn9)
  - Keep JSON caption and layout control as a separate node input to Ideogram, following SKILL.md’s structured prompt patterns. 

Goal: end up with **one MLXified ComfyUI graph per model**, each tuned for Mac, and ready to compare to existing PyTorch workflows on the same canvas. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX)

### Step C3 – Integrate SKILL‑level configuration and launch patterns

Your SKILL.md already addresses Mac quirks (broken pipe, TQDM issues, fp8 incompatibility); extend that to cover ComfyUI‑MLX:

- Add an “MLX Nodes” subsection under ComfyUI installation that instructs users to install ComfyUI‑MLX via Manager or Git URL, referencing its MIT license and Apple‑Silicon focus. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/pyproject.toml)
- Incorporate MLX workflows into your launch instructions, still using `nohup`, `TQDM_DISABLE`, `DISABLE_TQDM`, and `--force-fp16` as appropriate to avoid broken pipe errors and ensure Mac‑friendly execution. 
- Document which workflows require MLX and which are PyTorch; explicitly warn that fp8 weights (e.g., certain Z‑Image Turbo FP8 packs) remain incompatible with MPS and that MLX‑native or bf16/quantized weights should be preferred. [youtube](https://www.youtube.com/watch?v=7KH8vAYzIqI)

Goal: a unified SKILL that tells a Mac user exactly how to get **ComfyUI + MLX nodes + MLX‑friendly models** running with minimal friction. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)

***

## Detailed plan for pure MLX / mflux custom code

### Step M1 – Install mflux and fetch MLX models

Standardize on mflux for MLX‑native scripts:

- Install mflux via `uv tool install --upgrade mflux` (recommended in Z‑Image Turbo MLX card) or pip, depending on your environment preferences. [pypi](https://pypi.org/project/mflux/0.14.2/)
- Download pre‑quantized Z‑Image Turbo MLX weights (4‑bit model):  
  - `filipstrand/Z-Image-Turbo-mflux-4bit`, which uses 4‑bit quantization and is tuned for fast local generation. [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)
- Optionally fetch MLX FLUX models and any MLXBits Ideogram conversions once mflux supports them natively or via example scripts. [github](https://github.com/filipstrand/mflux/blob/main/README.md)

Goal: have a dedicated `mlx-models/` directory (or Hugging Face cache) with all MLX‑ready models pinned and documented. [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)

### Step M2 – Design per‑model mflux CLI recipes

For each model, capture canonical mflux CLI forms:

- **Z‑Image Turbo (4‑bit) recipe (from HF card):**  
  - Use `mflux-generate-z-image-turbo` with `--model filipstrand/Z-Image-Turbo-mflux-4bit`, 1280×720 resolution, 9 steps, and optional LoRA paths/scales. [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)
  - Example flags from card: `--width 1280 --height 720 --seed 456 --steps 9 --lora-paths renderartist/Technically-Color-Z-Image-Turbo --lora-scales 0.5`. [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)

- **FLUX recipe:**  
  - Use `mflux-generate` or FLUX‑specific commands based on README/common models docs (`src/mflux/models/common/README.md`), with steps, resolution, and quantization tuned for your Mac. [github](https://github.com/filipstrand/mflux/blob/main/README.md)

- **Ideogram 4 MLX recipe:**  
  - Use future `mflux-generate-ideogram4` or equivalent once MLXBits Ideogram repos integrate with mflux; follow similar CLI style to your existing SKILL.md Ideogram MLX examples but with mflux instead of custom Python. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx/commit/05527f235e22064816db7d0249254e9651b2f137)

Goal: a set of **shell one‑liners** that you can invoke from scripts or terminals for repeatable experiments, plus equivalent Python snippets for more flexible code. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)

### Step M3 – Build Python benchmarking harness

Beyond CLI, design a Python harness:

- Wrap mflux model calls in a `BenchmarkRunner` that:
  - Loads each model once (Z‑Image Turbo, FLUX, Ideogram 4 when available). [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)
  - Exposes a `run(prompt, steps, cfg, resolution)` interface. [pypi](https://pypi.org/project/mflux/0.14.2/)
- Integrate timing (per‑image latency, throughput), peak memory measurement (using `psutil` or `mlx` telemetry if available), and seed control. [pypi](https://pypi.org/project/mflux/0.14.2/)
- Run your curated prompt suite (short vs mid‑length prompts, text‑heavy prompts, style prompts) across models and record results in CSVs. [seaart](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g)

Goal: have robust scripts that let you compare MLX model performance and quality independent of ComfyUI. [pypi](https://pypi.org/project/mflux/0.14.2/)

***

## Tightening the quality and settings guidance

Using current Z‑Image Turbo guidance and community experiments:

- Favor **short to mid‑length precise prompts** over extremely long prompts for Z‑Image Turbo; community testing shows better prompt adherence with concise, tag‑like prompting. [seaart](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g)
- Use **AuraFlow 3–7**, samplers like Euler or DPM++ SDE, and simple/normal/beta57 schedulers, with 6–10 steps and CFG around 1 (negative prompts have little effect because CFG is low). [seaart](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g)
- Note Z‑Image Turbo’s strengths (speed, real‑life characters, good text but not as strong as image quality) and weaker areas (very complex atmospheric effects). This helps you decide where Ideogram 4 or FLUX should be used instead. [seaart](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g)

Goal: embed these “best settings” into your recipes and SKILL, so users don’t have to rediscover them. 

***

## Refining benchmarking and “most capable” decision

To move from theory to a defensible “most capable model for M‑series” conclusion:

- Run **head‑to‑head comparisons**: for each prompt type (e.g., text‑heavy posters, portraits, dynamic action), generate images with Z‑Image Turbo, FLUX MLX, and (if licensing allows) Ideogram 4 MLX. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)
- Track:
  - Latency per image at fixed resolution and steps. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)
  - Peak RAM / stability (watchdog timeouts, OOMs) across 16, 24, 32+ GB configs. [modelfit](https://modelfit.io/guides/local-image-generation-mac/)
  - Subjective quality: text legibility, prompt adherence, aesthetics. [seaart](https://www.seaart.ai/articleDetail/d4kpg4te878c73bme33g)
- Use these results to formulate a **tiered recommendation**, such as:
  - Z‑Image Turbo via mflux: best default for most Apple Silicon users, particularly 16–24 GB RAM (speed/quality trade‑off). [modelfit](https://modelfit.io/guides/local-image-generation-mac/)
  - FLUX MLX via mflux or ComfyUI‑MLX: preferred for high‑resolution photorealism and stylistic diversity on higher‑RAM machines. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)
  - Ideogram 4 MLX (quantized): specialist for non‑commercial text‑heavy layout work where JSON captioning and bounding boxes matter more than raw speed. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q4)

This step turns your plan into actual evidence‑backed choices. [modelfit](https://modelfit.io/guides/local-image-generation-mac/)

***

## Documentation and SKILL evolution

As you implement:

- Create a **new section** in your SKILL.md (or a separate MLX‑focused SKILL) titled, e.g., “MLX‑Optimized Image Generation on Apple Silicon”, summarizing:
  - Recommended MLX models (Z‑Image Turbo, FLUX MLX, optional Ideogram 4 MLX). [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)
  - How to install mflux and ComfyUI‑MLX nodes. [pypi](https://pypi.org/project/mflux/0.14.2/)
  - Recipes: CLI commands, Python benchmark scripts, and ComfyUI workflows, including model paths and environment variables. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)
- Keep the **Troubleshooting** section up‑to‑date with MLX‑specific issues (Metal watchdog, quantization requirements) alongside your existing Mac‑specific fixes (broken pipe, fp8 unsupported on MPS). [youtube](https://www.youtube.com/watch?v=7KH8vAYzIqI)

That way your SKILL becomes a living, Mac‑centric manual for “latest MLX image models + optimal Apple Silicon runtimes”, not just ComfyUI setup. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)

***

If you tell me your exact Mac model/RAM and whether you need commercial usage, I can next propose specific Z‑Image Turbo + FLUX configurations (steps, CFG, resolution) and concrete ComfyUI graphs and mflux commands tailored to your machine.

---

With an M4 mini Pro and 128 GB unified memory, you’re in the “no‑compromise” tier—you can comfortably run the heaviest MLX image models (Ideogram 4 MLX, Z‑Image Turbo, FLUX MLX) at high resolution, large batch sizes, and high precision, with MLX/mflux as your primary runtime and ComfyUI‑MLX for visual workflows. [note](https://note.com/mikai_daichi/n/n31fdfdefc21d?hl=en)

Below is how I’d tailor the plan specifically to your machine.

***

## What your hardware enables

Even Apple’s documented M4 Pro mini configs (up to 64 GB unified memory) are marketed as tiny powerhouses for AI workflows, with a 12‑core CPU, 16‑core GPU, and a 16‑core Neural Engine designed to “fly through AI‑based pro workflows.” [apple](https://www.apple.com/shop/buy-mac/mac-mini)

Your 128 GB unified memory and 2 TB SSD go well beyond the memory recommendations in your SKILL.md (which already treats 24–36 GB as “excellent headroom”); this means you can:  

- Keep **multiple large models resident at once** (e.g., Z‑Image Turbo + FLUX MLX + Ideogram 4 MLX q8) without aggressive offloading. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q8)
- Use **higher‑precision variants** (q8 or bf16 where available) and render **2K–4K images** or larger batches while remaining stable. 
***

## Recommended model set for your M4 Pro

Given your hardware, I’d focus on this core trio:

- **Z‑Image Turbo (MLX/mflux, 4‑bit + bf16)**  
  - Pre‑quantized 4‑bit MLX variant is available as `filipstrand/Z-Image-Turbo-mflux-4bit`, explicitly designed for fast local generation on Mac. [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)
  - Community guides show it works exceptionally well on Apple Silicon with 6–10 steps, AuraFlow 3–7, CFG ≈1, and short, precise prompts. [zimage](https://zimage.run/de/blog/zi-030-z-image-apple-silicon-mac-en-20260509)

- **FLUX 2 Klein 4B (MLX/mflux)**  
  - The “MFlux Skill for OpenClaw” highlights FLUX.2 Klein 4B as a fast, Apache‑2.0 model for local MLX image generation on Mac, positioned as the “fast” counterpart to Z‑Image Turbo’s “quality.” [clawhub](https://clawhub.ai/pjain/mflux)
  - Perfect for high‑volume generation and photorealistic styles on your hardware. [clawhub](https://clawhub.ai/pjain/mflux)

- **Ideogram 4 MLX q8 (non‑commercial, MLXBits)**  
  - MLXBits provides `ideogram-4-mlx-q8`, evaluated across third‑party arenas and internal benchmarks, offering strong text and layout capabilities at 8‑bit quantization. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q4)
  - Your SKILL.md warns that Ideogram 4 weights (including MLXBits and Comfy‑Org repacks) are under a **Non‑Commercial** agreement, so you should only use them for non‑revenue activities unless you have an enterprise license. [huggingface](https://huggingface.co/collections/MLXBits/ideogram-4-on-apple-mlx)

With 128 GB RAM, you can treat Z‑Image Turbo + FLUX MLX as your **always‑on general models**, and load Ideogram 4 q8 for specialized text/layout tasks without worrying about OOM. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q8)

***

## Optimal MLX + mflux workflow for you

### mflux setup

For your machine, make mflux your primary runtime:

- Install mflux (either via `uv tool install --upgrade mflux` or pip) following the mflux PyPI and documentation guidance. [pypi](https://pypi.org/project/mflux/0.14.2/)
- Download MLX models with Hugging Face CLI or mflux’s built‑in support:
  - `filipstrand/Z-Image-Turbo-mflux-4bit` (fast, 4‑bit). [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)
  - FLUX.2 Klein 4B MLX models referenced in the MFlux skill. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)
  - MLXBits Ideogram 4 q8 if/when mflux provides a ready integration. [huggingface](https://huggingface.co/collections/MLXBits/ideogram-4-on-apple-mlx)

Store them on your 2 TB SSD under a dedicated directory (e.g., `~/mlx-models/`) to keep paths organized and aligned with how your SKILL.md handles model directories. 
### Example generation recipes (CLI level)

Use the HF/mflux examples, tuned up for your hardware:

- **Z‑Image Turbo 4‑bit via mflux CLI:**  
  - HF card suggests: `--width 1280 --height 720 --seed 456 --steps 9` plus optional LoRA paths/scales. [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)
  - On your machine you can safely increase resolution (e.g., 1920×1080, 2048×2048) and maintain 9–12 steps without major slowdowns. [note](https://note.com/mikai_daichi/n/n31fdfdefc21d?hl=en)

- **FLUX.2 Klein 4B via mflux:**  
  - Use the FLUX‑oriented commands from the mflux README and common models docs (`src/mflux/models/common/README.md`); the MFlux Skill indicates this is the “fast” image model built for local MLX use. [github](https://github.com/filipstrand/mflux/blob/main/README.md)

- **Ideogram 4 MLX q8 via mflux (when available):**  
  - Mirror your existing SKILL.md CLI patterns for Ideogram 4, but point them at MLXBits q8 weights and mflux‑powered commands, respecting the Non‑Commercial license. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q8)

Your hardware allows you to benchmark these at **fixed seeds and settings** across resolutions to produce a solid latency/quality profile. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)

***

## Optimal ComfyUI + MLX setup on your M4 Pro

### Install ComfyUI‑MLX nodes

Extend your existing ComfyUI install (already tailored for Mac in SKILL.md) with MLX nodes:

- Install **ComfyUI‑MLX** via the Custom Nodes Manager or directly from `https://github.com/thoddnn/ComfyUI-MLX.git`, as described in its README and in third‑party guides like RunComfy’s MLX node overview. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)
- These nodes are specifically designed to “enhance workflow efficiency for ComfyUI users on Mac with Apple Silicon, optimizing performance and speed,” and user reports mention substantial speed and memory improvements versus pure PyTorch MPS. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX)

Continue to use your SKILL’s Mac‑safe launch pattern (virtualenv, `nohup`, `TQDM_DISABLE`, `DISABLE_TQDM`, `--force-fp16`) to avoid broken pipe errors and keep long‑running MLX workflows stable. 
### Model and workflow mapping inside ComfyUI

On your 128 GB machine:

- Map **Z‑Image Turbo bf16** (from Comfy‑Org) into ComfyUI as you already do (`z_image_turbo_bf16.safetensors` in `diffusion_models/`) and pair it with an MLX‑backed sampler node where possible; use Qwen3 text encoder and Z‑Image VAE paths from SKILL.md. [zimage](https://zimage.run/blog/zi-103-z-image-turbo-apple-silicon-comfyui-en-20260617)
- Add MLX‑backed FLUX nodes (ported via ComfyUI‑MLX) for a second workflow focused on photorealism and styles. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)
- Keep Ideogram 4 primarily in **Draw Things or CLI** for now (as in SKILL.md), and only weave it into ComfyUI if MLX nodes mature for that model; you’ll still benefit from your Mac‑specific guidance on JSON prompts and layout control. [beta.pinokio](https://beta.pinokio.co/posts/01kv3nwkv8z8tqwvm89p2d9qn9)

Then use ComfyUI’s `/system_stats` API to measure real‑time CPU/GPU/memory usage for MLX vs PyTorch workflows—your large RAM will clearly show MLX’s more efficient memory usage while letting you push resolution and batch size much higher than typical setups. [zimage](https://zimage.run/de/blog/zi-030-z-image-apple-silicon-mac-en-20260509)

***

## Practical implication for your research

Because your machine is over‑provisioned relative to most Mac configs, you can:

- Treat **Z‑Image Turbo + FLUX MLX via mflux** as your default, high‑speed local stack for nearly all image work. [clawhub](https://clawhub.ai/pjain/mflux)
- Reserve **Ideogram 4 MLX q8** for non‑commercial text‑heavy and layout‑driven tasks, where its architecture and training give it a unique edge. [huggingface](https://huggingface.co/MLXBits/ideogram-4-mlx-q4)
- Use **ComfyUI‑MLX** as a visual orchestration layer, building complex multi‑step workflows (control nets, upscalers, LoRAs) while keeping the core diffusion work in MLX for maximum throughput on your M4 Pro. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX)

If you’d like, I can next propose very concrete command lines (mflux) plus ComfyUI node graphs for “default Z‑Image Turbo workflow” and “default FLUX workflow” tuned to your M4 Pro, including suggested steps, CFG, and resolutions for fast but high‑quality generation.

---

Here’s the comprehensive how‑to guide as a standalone markdown report, including concrete mflux commands and ComfyUI workflow templates tuned to your M4 Pro. It’s saved as an artifact you can read and reuse in your automation.  

At a high level, it covers:  

- Recommended models on your M4 Pro: Z‑Image Turbo (4‑bit MLX via mflux + bf16 in ComfyUI) and FLUX2 Klein 4B MLX for speed/quality balance, with Ideogram 4 MLX as an optional non‑commercial text/layout specialist. [support.apple](https://support.apple.com/en-us/121555)
- Concrete **mflux CLI commands** for Z‑Image Turbo and FLUX, with suggested resolutions, steps, and CFG tuned to fast but high‑quality generation on Apple Silicon. [everymac](https://everymac.com/systems/apple/mac_mini/specs/mac-mini-m4-pro-12-core-cpu-16-core-gpu-2024-specs.html)
- Detailed **ComfyUI setup** steps for Z‑Image Turbo on Apple Silicon (model paths, bf16 checkpoints, text encoder, VAE) and recommended default settings: 1024×1024, ~8 steps, CFG≈1.0. [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)
- Structural **templates for ComfyUI graphs** (what nodes to include and how they connect) for both Z‑Image Turbo and FLUX workflows, plus guidance on integrating ComfyUI‑MLX nodes to move the heavy diffusion work onto MLX. [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4)

You can open the report, copy the example commands and workflow structures, and then:  

- Paste the mflux commands into your shell to test Z‑Image Turbo and FLUX at 1024×1024 or higher resolutions. [support.apple](https://support.apple.com/en-us/121555)
- Build JSON workflows in ComfyUI matching the node templates (prompt → encoder → model → sampler → VAE → output), and save them as loadable templates for your M4 Pro. [huggingface](https://huggingface.co/filipstrand/Z-Image-Turbo-mflux-4bit)

---

Below are draft schemas for `image_zimage_m4pro.json` and `image_flux_m4pro.json` that you can adapt directly into ComfyUI. They follow standard ComfyUI JSON structure, reference your SKILL.md model paths, and use default steps/CFG/resolution tuned for fast but high‑quality generation on your M4 Pro. [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)

***

## Design principles for both templates

These schemas are based on the official Z‑Image Turbo template (`image_z_image_turbo.json`) and community FLUX2 Klein workflows, but rewritten as generic ComfyUI graphs so they avoid copying specific copyrighted templates while preserving structure. [comfy](https://www.comfy.org/fr/workflows/image_flux2_klein_text_to_image-814fd547d86e/)

They assume your models are placed as in SKILL.md:  

- Z‑Image Turbo:  
  - `ComfyUI/models/diffusion_models/z_image_turbo_bf16.safetensors`  
  - `ComfyUI/models/text_encoders/qwen_3_4b.safetensors`  
  - `ComfyUI/models/vae/ae.safetensors` [docs.comfy](https://docs.comfy.org/zh-CN/tutorials/image/z-image/z-image-turbo)
- FLUX:  
  - FLUX2 Klein UNet in `models/diffusion_models/flux2_klein_4b.safetensors` (or whatever filename you use). [comfy](https://www.comfy.org/workflows/image_flux2_klein_text_to_image/)

You can import each JSON by:  

1. Saving the text to a `.json` file.  
2. Dragging it into the ComfyUI canvas or using “Load” in the UI. [comfyui](https://comfyui.org/en/z-image-turbo-in-comfyui-realism)

***

## Z‑Image Turbo workflow schema (`image_zimage_m4pro.json`)

### Goals and default settings

This schema implements a single‑prompt, single‑image Z‑Image Turbo text‑to‑image workflow:  

- Resolution: 1024×1024 (native Z‑Image Turbo resolution; good balance of speed and quality). [comfyanonymous.github](https://comfyanonymous.github.io/ComfyUI_examples/z_image/)
- Steps: 8 (sweet spot; can adjust 6–12). [huggingface](https://huggingface.co/SeeSee21/Z-Image-Turbo-AIO/blob/main/README.md)
- CFG: 1.0 (Z‑Image Turbo is trained to work best with low CFG). [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4)

The graph uses standard ComfyUI core nodes plus explicit “DiffusionModelLoader”, “CLIPTextEncode”, “VAELoader”, “KSampler”, “VAEDecode”, and “SaveImage” nodes. [note](https://note.com/rikunarita/n/n46723d6e9255?hl=en)

### JSON skeleton (adaptable)

This is a **conceptual schema**; feel free to change node `type` strings to match the exact names shown in your ComfyUI installation (they’re case‑sensitive). [fossies](https://fossies.org/linux/ComfyUI/blueprints/Text%20to%20Image%20(Z-Image-Turbo).json)

```json
{
  "version": 0.4,
  "revision": 0,
  "last_node_id": 8,
  "last_link_id": 7,
  "nodes": [
    {
      "id": 1,
      "type": "PrimitiveStringMultiline",          // Prompt input
      "title": "Prompt",
      "pos": [50, 50],
      "size": [300, 120],
      "widgets_values": [
        "cinematic portrait, soft natural light, 35mm film look"
      ],
      "outputs": [
        {
          "name": "text",
          "type": "STRING",
          "links":  [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)
        }
      ]
    },
    {
      "id": 2,
      "type": "PrimitiveInt",                      // Seed
      "title": "Seed",
      "pos": [50, 190],
      "size": [150, 60],
      "widgets_values": [1234],
      "outputs": [
        {
          "name": "value",
          "type": "INT",
          "links":  [comfy](https://www.comfy.org/fr/workflows/image_flux2_klein_text_to_image-814fd547d86e/)
        }
      ]
    },
    {
      "id": 3,
      "type": "PrimitiveInt",                      // Width
      "title": "Width",
      "pos": [50, 260],
      "size": [150, 60],
      "widgets_values": [1024],
      "outputs": [
        {
          "name": "value",
          "type": "INT",
          "links":  [comfy](https://www.comfy.org/workflows/image_flux2_klein_text_to_image/)
        }
      ]
    },
    {
      "id": 4,
      "type": "PrimitiveInt",                      // Height
      "title": "Height",
      "pos": [50, 330],
      "size": [150, 60],
      "widgets_values": [1024],
      "outputs": [
        {
          "name": "value",
          "type": "INT",
          "links":  
        }
      ]
    },
    {
      "id": 5,
      "type": "PrimitiveInt",                      // Steps
      "title": "Steps",
      "pos": [50, 400],
      "size": [150, 60],
      "widgets_values":  [comfyanonymous.github](https://comfyanonymous.github.io/ComfyUI_examples/z_image/),
      "outputs": [
        {
          "name": "value",
          "type": "INT",
          "links":  [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4)
        }
      ]
    },
    {
      "id": 6,
      "type": "PrimitiveFloat",                    // CFG
      "title": "CFG",
      "pos": [50, 470],
      "size": [150, 60],
      "widgets_values": [1.0],
      "outputs": [
        {
          "name": "value",
          "type": "FLOAT",
          "links":  [github](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_z_image_turbo.json)
        }
      ]
    },
    {
      "id": 7,
      "type": "CLIPTextEncode",                    // Uses qwen_3_4b
      "title": "CLIP Text Encode (Prompt)",
      "pos": [400, 80],
      "size": [310, 160],
      "inputs": [
        {
          "name": "text",
          "type": "STRING",
          "link": 1
        }
      ],
      "widgets_values": [
        "qwen_3_4b"                                // clip_name combo
      ],
      "outputs": [
        {
          "name": "CONDITIONING",
          "type": "CONDITIONING",
          "links":  [docs.comfy](https://docs.comfy.org/zh-CN/tutorials/image/z-image/z-image-turbo)
        }
      ]
    },
    {
      "id": 8,
      "type": "DiffusionModelLoader",              // Z-Image Turbo UNet
      "title": "Load Z-Image Turbo Model",
      "pos": [400, 260],
      "size": [310, 140],
      "widgets_values": [
        "z_image_turbo_bf16"                       // unet_name combo
      ],
      "outputs": [
        {
          "name": "MODEL",
          "type": "MODEL",
          "links":  [comfyanonymous.github](https://comfyanonymous.github.io/ComfyUI_examples/z_image/)
        }
      ]
    },
    {
      "id": 9,
      "type": "VAELoader",                         // Z-Image Turbo VAE
      "title": "Load VAE (ae)",
      "pos": [400, 420],
      "size": [260, 120],
      "widgets_values": [
        "ae"                                       // vae_name combo
      ],
      "outputs": [
        {
          "name": "VAE",
          "type": "VAE",
          "links":  [comfyui](https://comfyui.org/en/z-image-turbo-in-comfyui-realism)
        }
      ]
    },
    {
      "id": 10,
      "type": "EmptyLatentImage",                  // Latent with width/height
      "title": "Empty Latent (Resolution)",
      "pos": [400, 560],
      "size": [260, 120],
      "inputs": [
        {
          "name": "width",
          "type": "INT",
          "link": 3
        },
        {
          "name": "height",
          "type": "INT",
          "link": 4
        }
      ],
      "outputs": [
        {
          "name": "LATENT",
          "type": "LATENT",
          "links":  [huggingface](https://huggingface.co/SeeSee21/Z-Image-Turbo-AIO/blob/main/README.md)
        }
      ]
    },
    {
      "id": 11,
      "type": "KSampler",
      "title": "KSampler (Z-Image Turbo)",
      "pos": [780, 260],
      "size": [390, 220],
      "inputs": [
        { "name": "model", "type": "MODEL", "link": 8 },
        { "name": "seed", "type": "INT", "link": 2 },
        { "name": "steps", "type": "INT", "link": 5 },
        { "name": "cfg", "type": "FLOAT", "link": 6 },
        { "name": "positive", "type": "CONDITIONING", "link": 7 },
        { "name": "latent_image", "type": "LATENT", "link": 10 }
      ],
      "widgets_values": [
        "euler_ancestral",                         // sampler_name
        "simple"                                   // scheduler_name
      ],
      "outputs": [
        {
          "name": "LATENT",
          "type": "LATENT",
          "links":  [note](https://note.com/rikunarita/n/n46723d6e9255?hl=en)
        }
      ]
    },
    {
      "id": 12,
      "type": "VAEDecode",
      "title": "VAE Decode",
      "pos": [780, 520],
      "size": [260, 150],
      "inputs": [
        { "name": "vae", "type": "VAE", "link": 9 },
        { "name": "latent", "type": "LATENT", "link": 11 }
      ],
      "outputs": [
        {
          "name": "IMAGE",
          "type": "IMAGE",
          "links":  [fossies](https://fossies.org/linux/ComfyUI/blueprints/Text%20to%20Image%20(Z-Image-Turbo).json)
        }
      ]
    },
    {
      "id": 13,
      "type": "SaveImage",
      "title": "Save Image",
      "pos": [1100, 520],
      "size": [260, 140],
      "inputs": [
        { "name": "images", "type": "IMAGE", "link": 12 }
      ],
      "widgets_values": [
        "zimage_outputs",                          // output folder
        "zimage_m4pro"                             // base filename
      ]
    }
  ],
  "links": [
    { "id": 1, "from_node": 1, "from_output": 0, "to_node": 7, "to_input": 0 },
    { "id": 2, "from_node": 2, "from_output": 0, "to_node": 11, "to_input": 1 },
    { "id": 3, "from_node": 3, "from_output": 0, "to_node": 10, "to_input": 0 },
    { "id": 4, "from_node": 4, "from_output": 0, "to_node": 10, "to_input": 1 },
    { "id": 5, "from_node": 5, "from_output": 0, "to_node": 11, "to_input": 2 },
    { "id": 6, "from_node": 6, "from_output": 0, "to_node": 11, "to_input": 3 },
    { "id": 7, "from_node": 7, "from_output": 0, "to_node": 11, "to_input": 4 },
    { "id": 8, "from_node": 8, "from_output": 0, "to_node": 11, "to_input": 0 },
    { "id": 9, "from_node": 9, "from_output": 0, "to_node": 12, "to_input": 0 },
    { "id": 10, "from_node": 10, "from_output": 0, "to_node": 11, "to_input": 5 },
    { "id": 11, "from_node": 11, "from_output": 0, "to_node": 12, "to_input": 1 },
    { "id": 12, "from_node": 12, "from_output": 0, "to_node": 13, "to_input": 0 }
  ]
}
```

**How to adapt to your SKILL:**  

- Ensure `qwen_3_4b`, `z_image_turbo_bf16`, and `ae` match the actual names in your ComfyUI model combos; SKILL.md uses those filenames and paths. 
- If you install **ComfyUI‑MLX**, replace `KSampler` with the MLX sampler node type and set MLX‑friendly samplers/schedulers (e.g., `res_multistep` + `beta`). [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)
- You can raise resolution (width/height) and slightly increase `steps` on your 128 GB M4 Pro; the rest of the graph remains valid. [ominix-ai-ominix-mlx.mintlify](https://ominix-ai-ominix-mlx.mintlify.app/image/zimage)

***

## FLUX workflow schema (`image_flux_m4pro.json`)

### Goals and default settings

This schema implements a FLUX2 Klein 4B text‑to‑image workflow:  

- Resolution: 1024×1024 (good default; can be scaled up). [comfy](https://www.comfy.org/fr/workflows/image_flux2_klein_text_to_image-814fd547d86e/)
- Steps: 12 (typical for FLUX; can go 10–16). [note](https://note.com/old_pgmrs_will/n/n4a161ab7ef45?hl=en-US)
- CFG: 7.0 (typical CFG for diffusion models like FLUX). [clawhub](https://clawhub.ai/pjain/mflux)

It mirrors the Z‑Image layout but uses a FLUX UNet and, if needed, a separate FLUX VAE, along with standard text encoding and sampling nodes. [comfy](https://www.comfy.org/workflows/image_flux2_klein_text_to_image/)

### JSON skeleton (adaptable)

Again, treat this as a template; adjust node `type` strings and model names to the exact ones in your installation. [comfy](https://www.comfy.org/fr/workflows/image_flux2_klein_text_to_image-814fd547d86e/)

```json
{
  "version": 0.4,
  "revision": 0,
  "last_node_id": 9,
  "last_link_id": 8,
  "nodes": [
    {
      "id": 1,
      "type": "PrimitiveStringMultiline",
      "title": "Prompt",
      "pos": [50, 50],
      "size": [300, 120],
      "widgets_values": [
        "highly detailed studio portrait, softbox lighting, 85mm lens"
      ],
      "outputs": [
        { "name": "text", "type": "STRING", "links":  [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo) }
      ]
    },
    {
      "id": 2,
      "type": "PrimitiveInt",
      "title": "Seed",
      "pos": [50, 190],
      "size": [150, 60],
      "widgets_values": [42],
      "outputs": [
        { "name": "value", "type": "INT", "links":  [comfy](https://www.comfy.org/fr/workflows/image_flux2_klein_text_to_image-814fd547d86e/) }
      ]
    },
    {
      "id": 3,
      "type": "PrimitiveInt",
      "title": "Width",
      "pos": [50, 260],
      "size": [150, 60],
      "widgets_values": [1024],
      "outputs": [
        { "name": "value", "type": "INT", "links":  [comfy](https://www.comfy.org/workflows/image_flux2_klein_text_to_image/) }
      ]
    },
    {
      "id": 4,
      "type": "PrimitiveInt",
      "title": "Height",
      "pos": [50, 330],
      "size": [150, 60],
      "widgets_values": [1024],
      "outputs": [
        { "name": "value", "type": "INT", "links":  
      ]
    },
    {
      "id": 5,
      "type": "PrimitiveInt",
      "title": "Steps",
      "pos": [50, 400],
      "size": [150, 60],
      "widgets_values":  [fossies](https://fossies.org/linux/ComfyUI/blueprints/Text%20to%20Image%20(Z-Image-Turbo).json),
      "outputs": [
        { "name": "value", "type": "INT", "links":  [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4) }
      ]
    },
    {
      "id": 6,
      "type": "PrimitiveFloat",
      "title": "CFG",
      "pos": [50, 470],
      "size": [150, 60],
      "widgets_values": [7.0],
      "outputs": [
        { "name": "value", "type": "FLOAT", "links":  [github](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_z_image_turbo.json) }
      ]
    },
    {
      "id": 7,
      "type": "CLIPTextEncode",
      "title": "CLIP Text Encode (Prompt)",
      "pos": [400, 80],
      "size": [310, 160],
      "inputs": [
        { "name": "text", "type": "STRING", "link": 1 }
      ],
      "widgets_values": [
        "flux_text_encoder"                        // adjust to actual encoder
      ],
      "outputs": [
        { "name": "CONDITIONING", "type": "CONDITIONING", "links":  [docs.comfy](https://docs.comfy.org/zh-CN/tutorials/image/z-image/z-image-turbo) }
      ]
    },
    {
      "id": 8,
      "type": "DiffusionModelLoader",
      "title": "Load FLUX2 Klein 4B Model",
      "pos": [400, 260],
      "size": [310, 140],
      "widgets_values": [
        "flux2_klein_4b"                           // UNet checkpoint name
      ],
      "outputs": [
        { "name": "MODEL", "type": "MODEL", "links":  [comfyanonymous.github](https://comfyanonymous.github.io/ComfyUI_examples/z_image/) }
      ]
    },
    {
      "id": 9,
      "type": "VAELoader",
      "title": "Load FLUX VAE",
      "pos": [400, 420],
      "size": [260, 120],
      "widgets_values": [
        "flux_vae"                                 // adjust to actual VAE
      ],
      "outputs": [
        { "name": "VAE", "type": "VAE", "links":  [comfyui](https://comfyui.org/en/z-image-turbo-in-comfyui-realism) }
      ]
    },
    {
      "id": 10,
      "type": "EmptyLatentImage",
      "title": "Empty Latent (Resolution)",
      "pos": [400, 560],
      "size": [260, 120],
      "inputs": [
        { "name": "width", "type": "INT", "link": 3 },
        { "name": "height", "type": "INT", "link": 4 }
      ],
      "outputs": [
        { "name": "LATENT", "type": "LATENT", "links":  [huggingface](https://huggingface.co/SeeSee21/Z-Image-Turbo-AIO/blob/main/README.md) }
      ]
    },
    {
      "id": 11,
      "type": "KSampler",
      "title": "KSampler (FLUX)",
      "pos": [780, 260],
      "size": [390, 220],
      "inputs": [
        { "name": "model", "type": "MODEL", "link": 8 },
        { "name": "seed", "type": "INT", "link": 2 },
        { "name": "steps", "type": "INT", "link": 5 },
        { "name": "cfg", "type": "FLOAT", "link": 6 },
        { "name": "positive", "type": "CONDITIONING", "link": 7 },
        { "name": "latent_image", "type": "LATENT", "link": 10 }
      ],
      "widgets_values": [
        "euler",                                   // sampler_name
        "beta"                                     // scheduler_name
      ],
      "outputs": [
        { "name": "LATENT", "type": "LATENT", "links":  [note](https://note.com/rikunarita/n/n46723d6e9255?hl=en) }
      ]
    },
    {
      "id": 12,
      "type": "VAEDecode",
      "title": "VAE Decode",
      "pos": [780, 520],
      "size": [260, 150],
      "inputs": [
        { "name": "vae", "type": "VAE", "link": 9 },
        { "name": "latent", "type": "LATENT", "link": 11 }
      ],
      "outputs": [
        { "name": "IMAGE", "type": "IMAGE", "links":  [fossies](https://fossies.org/linux/ComfyUI/blueprints/Text%20to%20Image%20(Z-Image-Turbo).json) }
      ]
    },
    {
      "id": 13,
      "type": "SaveImage",
      "title": "Save Image",
      "pos": [1100, 520],
      "size": [260, 140],
      "inputs": [
        { "name": "images", "type": "IMAGE", "link": 12 }
      ],
      "widgets_values": [
        "flux_outputs",
        "flux_m4pro"
      ]
    }
  ],
  "links": [
    { "id": 1, "from_node": 1, "from_output": 0, "to_node": 7, "to_input": 0 },
    { "id": 2, "from_node": 2, "from_output": 0, "to_node": 11, "to_input": 1 },
    { "id": 3, "from_node": 3, "from_output": 0, "to_node": 10, "to_input": 0 },
    { "id": 4, "from_node": 4, "from_output": 0, "to_node": 10, "to_input": 1 },
    { "id": 5, "from_node": 5, "from_output": 0, "to_node": 11, "to_input": 2 },
    { "id": 6, "from_node": 6, "from_output": 0, "to_node": 11, "to_input": 3 },
    { "id": 7, "from_node": 7, "from_output": 0, "to_node": 11, "to_input": 4 },
    { "id": 8, "from_node": 8, "from_output": 0, "to_node": 11, "to_input": 0 },
    { "id": 9, "from_node": 9, "from_output": 0, "to_node": 12, "to_input": 0 },
    { "id": 10, "from_node": 10, "from_output": 0, "to_node": 11, "to_input": 5 },
    { "id": 11, "from_node": 11, "from_output": 0, "to_node": 12, "to_input": 1 },
    { "id": 12, "from_node": 12, "from_output": 0, "to_node": 13, "to_input": 0 }
  ]
}
```

**How to adapt to your SKILL:**  

- Replace `flux2_klein_4b`, `flux_text_encoder`, and `flux_vae` with the actual model names you use; the MFlux Skill and FLUX workflows list specific model identifiers and encoders. [github](https://github.com/filipstrand/mflux/blob/main/src/mflux/models/common/README.md)
- If you install **ComfyUI‑MLX**, use MLX FLUX nodes (e.g., MLX FLUX model loader and sampler) instead of the generic `DiffusionModelLoader`/`KSampler`. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX)
- On your M4 Pro 128 GB, you can increase resolution and steps modestly for more detail while keeping CFG around 7.0, as suggested by FLUX workflow guides. [note](https://note.com/mikai_daichi/n/n31fdfdefc21d?hl=en)

***

## How this aligns with your Mac launch script and SKILL

Your SKILL.md already has:  

- A Mac‑safe ComfyUI launch command using `nohup`, virtualenv, `TQDM_DISABLE`, and `--force-fp16`, which should continue to be used when running these workflows to avoid broken pipe and TQDM issues. 
- Clear model directories and a “Mac‑compatible models” table that lists Z‑Image Turbo bf16, Krea2 Turbo bf16, and Flux1‑dev as supported diffusion models on Mac. 

These JSON templates simply add **ready‑wired graphs** that match those paths and model names, so you can:  

1. Save them as `image_zimage_m4pro.json` and `image_flux_m4pro.json`.  
2. Load them in ComfyUI.  
3. Edit prompt, seed, steps, CFG per run, while leaving the model wiring identical.  

If you’d like, next step I can help you:  

- Add MLX‑specific variants of these graphs (using ComfyUI‑MLX node types instead of generic KSampler/model loader), or  
- Design a combined “Z‑Image Turbo + FLUX” workflow that lets you select the model via a combo box and run both from a single template.

---

The next step is to (1) refactor your existing Z‑Image and FLUX graphs to use MLX‑backed nodes, and (2) design a combined template with a simple model selector so one workflow can drive both Z‑Image Turbo and FLUX2 Klein on your M4 Pro. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX/mlx-sampler)

Below is a detailed plan plus example schemas you can adapt.

***

## Overall strategy

- Keep the **graph topology** you already have (prompt → encoder → model → sampler → VAE → output), but swap generic loaders/samplers with MLX‑specific ones where the ComfyUI‑MLX pack provides them. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX)
- For the **combined workflow**, centralize inputs (prompt, seed, steps, CFG, resolution) and add a **model selection widget** that drives either Z‑Image Turbo or FLUX blocks, so you can switch models without changing the graph. [comfy](https://www.comfy.org/workflows/model/flux-2-klein/)

This keeps your SKILL consistent while letting you choose between MLX and PyTorch backends and between Z‑Image vs FLUX from one template.

***

## 1. MLX‑specific variants of the existing graphs

### 1.1 MLX building blocks to target

From ComfyUI‑MLX and node references:  

- **MLXSampler**: an MLX‑specific sampler node intended to replace standard KSampler for diffusion models, offering high‑quality sampling with MLX’s performance on Apple Silicon. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX/mlx-sampler)
- **MLX model loader nodes**: ComfyUI‑MLX and related packs expose MLX‑backed model loader nodes (naming varies by pack, e.g. `MLXModelLoader` / `UNETLoaderMLX` in FLUX‑oriented suites). These are used to load MLX UNet checkpoints instead of PyTorch ones. [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md)

Your goal:  

- For Z‑Image Turbo: use a MLX UNet loader plus MLXSampler, while still reusing CLIP/Qwen text encoders and VAE nodes (which may remain PyTorch or MLX depending on availability). [comfyanonymous.github](https://comfyanonymous.github.io/ComfyUI_examples/z_image/)
- For FLUX2 Klein: use MLX FLUX model loader + MLXSampler tuned to FLUX distilled settings (steps/CFG) per ComfyUI FLUX guides. [comfyui.nomadoor](https://comfyui.nomadoor.net/ja/basic-workflows/flux-2-klein/)

### 1.2 MLX Z‑Image Turbo graph (conceptual schema)

Start from your previous `image_zimage_m4pro.json` and change three core pieces:

- Replace `DiffusionModelLoader` → `MLXModelLoader` (or equivalent from ComfyUI‑MLX) and point it at a **MLX‑compatible Z‑Image UNet** (e.g., a future MLX repack or a GGUF‑to‑MLX pipeline). [huggingface](https://huggingface.co/jayn7/Z-Image-Turbo-GGUF/blob/main/example_workflow.json)
- Replace `KSampler` → `MLXSampler`, feeding the same inputs (model, seed, steps, CFG, conditioning, latent). [docs.comfy](https://docs.comfy.org/built-in-nodes/SamplerCustom)
- Optionally, use an MLX‑optimized VAE loader (`MLXVAEModelLoader`) when available; otherwise keep the existing VAE loader. [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX)

Minimal conceptual update (showing just the changed nodes):

```json
{
  "nodes": [
    {
      "id": 8,
      "type": "MLXModelLoader",                 // MLX-backed UNet loader
      "title": "Load Z-Image Turbo MLX Model",
      "widgets_values": [
        "z_image_turbo_mlx"                     // MLX UNet checkpoint name
      ],
      "outputs": [
        { "name": "MODEL", "type": "MODEL", "links":  [github](https://github.com/capitan01R/ComfyUI-Flux2Klein-Enhancer) }
      ]
    },
    {
      "id": 11,
      "type": "MLXSampler",                     // MLX sampler instead of KSampler
      "title": "MLXSampler (Z-Image Turbo)",
      "inputs": [
        { "name": "model", "type": "MODEL", "link": 8 },
        { "name": "seed", "type": "INT", "link": 2 },
        { "name": "steps", "type": "INT", "link": 5 },
        { "name": "cfg", "type": "FLOAT", "link": 6 },
        { "name": "conditioning", "type": "CONDITIONING", "link": 7 },
        { "name": "latent_image", "type": "LATENT", "link": 10 }
      ],
      "widgets_values": [
        "euler_ancestral",                      // sampler
        "simple"                                // scheduler
      ],
      "outputs": [
        { "name": "LATENT", "type": "LATENT", "links":  [huggingface](https://huggingface.co/jayn7/Z-Image-Turbo-GGUF/blob/main/example_workflow.json) }
      ]
    }
  ]
}
```

Default settings stay the same for your M4 Pro:  

- Resolution 1024×1024. [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4)
- Steps 8 (6–12 range). [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)
- CFG 1.0. [huggingface](https://huggingface.co/SeeSee21/Z-Image-Turbo-AIO/blob/main/README.md)

You only need to adjust `widgets_values` to match the MLX UNet name once you have that checkpoint in `models/diffusion_models/`. [ominix-ai-ominix-mlx.mintlify](https://ominix-ai-ominix-mlx.mintlify.app/image/zimage)

### 1.3 MLX FLUX2 Klein graph (conceptual schema)

For FLUX, ComfyUI FLUX guides and enhancer packs show that FLUX‑specific workflows typically use dedicated loaders like `UNETLoader`/`CLIPLoader` plus a tuned sampler/scheduler combination (often Beta‑style schedulers for distilled models). [facebook](https://www.facebook.com/groups/comfyui/posts/950399787732722/)

Your MLX variant would:

- Replace generic `DiffusionModelLoader` with an MLX FLUX UNet loader (e.g. `MLXFluxModelLoader` or similar from ComfyUI‑MLX or Flux2Klein‑Enhancer). [github](https://github.com/capitan01R/ComfyUI-Flux2Klein-Enhancer)
- Replace `KSampler` with `MLXSampler`, tuned to FLUX2 Klein 4B settings (e.g., 12–16 steps, CFG≈7, Beta 57 scheduler if your node pack exposes it). [youtube](https://www.youtube.com/watch?v=kNap0VWP1xs)

Conceptual changes:

```json
{
  "nodes": [
    {
      "id": 8,
      "type": "MLXFluxModelLoader",             // MLX FLUX loader
      "title": "Load FLUX2 Klein 4B MLX Model",
      "widgets_values": [
        "flux2_klein_4b_mlx"                    // MLX UNet checkpoint name
      ],
      "outputs": [
        { "name": "MODEL", "type": "MODEL", "links":  [github](https://github.com/capitan01R/ComfyUI-Flux2Klein-Enhancer) }
      ]
    },
    {
      "id": 11,
      "type": "MLXSampler",
      "title": "MLXSampler (FLUX2 Klein 4B)",
      "inputs": [
        { "name": "model", "type": "MODEL", "link": 8 },
        { "name": "seed", "type": "INT", "link": 2 },
        { "name": "steps", "type": "INT", "link": 5 },
        { "name": "cfg", "type": "FLOAT", "link": 6 },
        { "name": "conditioning", "type": "CONDITIONING", "link": 7 },
        { "name": "latent_image", "type": "LATENT", "link": 10 }
      ],
      "widgets_values": [
        "euler",                                // sampler tuned for FLUX
        "beta57"                                // scheduler, via RES4LYF pack if installed
      ],
      "outputs": [
        { "name": "LATENT", "type": "LATENT", "links":  [huggingface](https://huggingface.co/jayn7/Z-Image-Turbo-GGUF/blob/main/example_workflow.json) }
      ]
    }
  ]
}
```

Recommended defaults based on FLUX guides:  

- Steps: 12–16 for 1024×1024. [youtube](https://www.youtube.com/watch?v=GYJYud-E2I0)
- CFG: ≈7.0. [youtube](https://www.youtube.com/watch?v=jV7SNCMEKMw)

You can keep the rest of the graph identical to your non‑MLX FLUX template, just swapping loader/sampler for MLX versions.

***

## 2. Combined “Z‑Image Turbo + FLUX” workflow with model selector

The goal here is a **single template** that:  

- Has one set of inputs: prompt, seed, steps, CFG, width, height.  
- Lets you choose **“Z‑Image Turbo” or “FLUX2 Klein 4B”** from a dropdown.  
- Routes that choice into the appropriate model loader, sampler, and VAE nodes.  

You can implement this in ComfyUI using:  

- A `PrimitiveCombo` or `String` widget for `model_choice` (values: `"zimage"`, `"flux"`). [docs.comfy](https://docs.comfy.org/built-in-nodes/SamplerCustom)
- A custom “ModelSwitch” node (from node packs like `rgthree` or a small custom node) that outputs different MODEL/VAE pairs based on the selected string. [facebook](https://www.facebook.com/groups/comfyui/posts/950399787732722/)

### 2.1 Conceptual node layout

High‑level structure:

- Node 1: Prompt input.  
- Node 2–6: Seed, steps, CFG, width, height.  
- Node 7: Text encoder (Qwen or FLUX encoder; you can even use Qwen for both). [huggingface](https://huggingface.co/SeeSee21/Z-Image-Turbo-AIO/blob/main/README.md)
- Node 8: `PrimitiveCombo` for model choice (`\"zimage\"`/`\"flux\"`).  
- Node 9: `ModelSwitch` node that takes `model_choice` and outputs `MODEL` + `VAE`.  
- Node 10: Latent image initializer.  
- Node 11: MLXSampler (shared sampler).  
- Node 12: VAEDecode (uses VAE from ModelSwitch).  
- Node 13: SaveImage.  

This keeps the overall flow identical; only the underlying model/vae change depending on model_choice.

### 2.2 Combined workflow schema (conceptual JSON)

Below is a **conceptual JSON** you can adapt; replace `ModelSwitch` with the specific node name from your node pack (or implement it yourself as a custom node that chooses between two branches). [github](https://github.com/capitan01R/ComfyUI-Flux2Klein-Enhancer)

```json
{
  "version": 0.4,
  "revision": 0,
  "nodes": [
    {
      "id": 1,
      "type": "PrimitiveStringMultiline",
      "title": "Prompt",
      "widgets_values": [
        "cinematic portrait, soft natural light"
      ],
      "outputs": [{ "name": "text", "type": "STRING", "links":  [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX/mlx-sampler) }]
    },
    {
      "id": 2,
      "type": "PrimitiveInt",
      "title": "Seed",
      "widgets_values": [1234],
      "outputs": [{ "name": "value", "type": "INT", "links":  [runcomfy](https://www.runcomfy.com/comfyui-nodes/ComfyUI-MLX) }]
    },
    {
      "id": 3,
      "type": "PrimitiveInt",
      "title": "Width",
      "widgets_values": [1024],
      "outputs": [{ "name": "value", "type": "INT", "links":  [docs.comfy](https://docs.comfy.org/tutorials/flux/flux-2-klein) }]
    },
    {
      "id": 4,
      "type": "PrimitiveInt",
      "title": "Height",
      "widgets_values": [1024],
      "outputs": [{ "name": "value", "type": "INT", "links":  [comfy](https://www.comfy.org/workflows/model/flux-2-klein/) }]
    },
    {
      "id": 5,
      "type": "PrimitiveInt",
      "title": "Steps",
      "widgets_values":  [github](https://github.com/capitan01R/ComfyUI-Flux2Klein-Enhancer),         // default for Z-Image; you can override per model in ModelSwitch
      "outputs": [{ "name": "value", "type": "INT", "links":  [comfy](https://www.comfy.org/fr/workflows/image_flux2_klein_text_to_image-814fd547d86e/) }]
    },
    {
      "id": 6,
      "type": "PrimitiveFloat",
      "title": "CFG",
      "widgets_values": [1.0],       // default; FLUX branch can use internal override
      "outputs": [{ "name": "value", "type": "FLOAT", "links":  [github](https://github.com/thoddnn/ComfyUI-MLX/blob/main/README.md) }]
    },
    {
      "id": 7,
      "type": "CLIPTextEncode",
      "title": "CLIP Text Encode (Prompt)",
      "inputs": [{ "name": "text", "type": "STRING", "link": 1 }],
      "widgets_values": [
        "qwen_3_4b"                  // shared encoder (works for Z-Image; FLUX may use own if desired)
      ],
      "outputs": [{ "name": "CONDITIONING", "type": "CONDITIONING", "links":  [facebook](https://www.facebook.com/groups/comfyui/posts/950399787732722/) }]
    },
    {
      "id": 8,
      "type": "PrimitiveCombo",
      "title": "Model Choice",
      "widgets_values": [
        "zimage",                    // default, options: zimage / flux
        "zimage",
        ["zimage", "flux"]
      ],
      "outputs": [{ "name": "value", "type": "STRING", "links":  [github](https://github.com/capitan01R/ComfyUI-Flux2Klein-Enhancer) }]
    },
    {
      "id": 9,
      "type": "ModelSwitch",        // custom node: choose MODEL/VAE based on model_choice
      "title": "Switch Between Z-Image and FLUX",
      "inputs": [
        { "name": "choice", "type": "STRING", "link": 8 }
      ],
      "widgets_values": [
        "z_image_turbo_mlx",         // zimage_model
        "ae",                        // zimage_vae
        "flux2_klein_4b_mlx",        // flux_model
        "flux_vae"                   // flux_vae
      ],
      "outputs": [
        { "name": "MODEL", "type": "MODEL", "links":  [github](https://github.com/capitan01R/ComfyUI-Flux2Klein-Enhancer) },
        { "name": "VAE", "type": "VAE", "links":  [comfyanonymous.github](https://comfyanonymous.github.io/ComfyUI_examples/z_image/) }
      ]
    },
    {
      "id": 10,
      "type": "EmptyLatentImage",
      "title": "Empty Latent (Resolution)",
      "inputs": [
        { "name": "width", "type": "INT", "link": 3 },
        { "name": "height", "type": "INT", "link": 4 }
      ],
      "outputs": [{ "name": "LATENT", "type": "LATENT", "links":  [comfyui.nomadoor](https://comfyui.nomadoor.net/ja/basic-workflows/flux-2-klein/) }]
    },
    {
      "id": 11,
      "type": "MLXSampler",
      "title": "MLXSampler (Shared)",
      "inputs": [
        { "name": "model", "type": "MODEL", "link": 8 },
        { "name": "seed", "type": "INT", "link": 2 },
        { "name": "steps", "type": "INT", "link": 5 },
        { "name": "cfg", "type": "FLOAT", "link": 6 },
        { "name": "conditioning", "type": "CONDITIONING", "link": 7 },
        { "name": "latent_image", "type": "LATENT", "link": 10 }
      ],
      "widgets_values": [
        "euler_ancestral",          // good for Z-Image; FLUX may prefer euler/beta57
        "simple"
      ],
      "outputs": [{ "name": "LATENT", "type": "LATENT", "links":  [huggingface](https://huggingface.co/jayn7/Z-Image-Turbo-GGUF/blob/main/example_workflow.json) }]
    },
    {
      "id": 12,
      "type": "VAEDecode",
      "title": "VAE Decode",
      "inputs": [
        { "name": "vae", "type": "VAE", "link": 9 },
        { "name": "latent", "type": "LATENT", "link": 11 }
      ],
      "outputs": [{ "name": "IMAGE", "type": "IMAGE", "links":  [ominix-ai-ominix-mlx.mintlify](https://ominix-ai-ominix-mlx.mintlify.app/image/zimage) }]
    },
    {
      "id": 13,
      "type": "SaveImage",
      "title": "Save Image",
      "inputs": [
        { "name": "images", "type": "IMAGE", "link": 12 }
      ],
      "widgets_values": [
        "combined_outputs",
        "mlx_zimage_flux_m4pro"
      ]
    }
  ],
  "links": [
    { "id": 1, "from_node": 1, "from_output": 0, "to_node": 7, "to_input": 0 },
    { "id": 2, "from_node": 2, "from_output": 0, "to_node": 11, "to_input": 1 },
    { "id": 3, "from_node": 3, "from_output": 0, "to_node": 10, "to_input": 0 },
    { "id": 4, "from_node": 4, "from_output": 0, "to_node": 10, "to_input": 1 },
    { "id": 5, "from_node": 5, "from_output": 0, "to_node": 11, "to_input": 2 },
    { "id": 6, "from_node": 6, "from_output": 0, "to_node": 11, "to_input": 3 },
    { "id": 7, "from_node": 7, "from_output": 0, "to_node": 11, "to_input": 4 },
    { "id": 8, "from_node": 8, "from_output": 0, "to_node": 9, "to_input": 0 },
    { "id": 9, "from_node": 9, "from_output": 0, "to_node": 11, "to_input": 0 },
    { "id": 10, "from_node": 10, "from_output": 0, "to_node": 11, "to_input": 5 },
    { "id": 11, "from_node": 11, "from_output": 0, "to_node": 12, "to_input": 1 },
    { "id": 12, "from_node": 12, "from_output": 0, "to_node": 13, "to_input": 0 }
  ]
}
```

**Tuning recommendations for the combined template on your M4 Pro:**  

- Use **steps=8, CFG=1.0** when `model_choice = "zimage"`; use **steps≈12, CFG≈7.0** when `model_choice = "flux"`—you can implement this by adding internal overrides in `ModelSwitch` or by exposing a second steps/CFG widget for the FLUX branch. [docs.comfy](https://docs.comfy.org/tutorials/flux/flux-2-klein)
- Start with **1024×1024**, but you can safely push both branches to higher resolutions thanks to your 128 GB unified memory; FLUX workflows show good behavior at 1536×1536 with the right scheduler. [youtube](https://www.youtube.com/watch?v=tplPGT9Otd8)

***

If you want, next I can help you translate one of these conceptual schemas into an exact ComfyUI JSON matching the node type names in your current installation (e.g., after you tell me the exact `type` strings for your ComfyUI‑MLX nodes), or add ControlNet/LoRA subgraphs on top for Z‑Image and FLUX within this combined template.

---

To add ControlNet and LoRA subgraphs on top of your combined Z‑Image + FLUX template, treat them as optional “branches” that plug into the same core text‑to‑image graph: prompt → encoder → model → sampler → VAE → output. [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)

Below is a meticulous design plan you can follow when editing your JSON.

***

## Design goals

- Keep one **combined template** with `model_choice` (`"zimage"` / `"flux"`).  
- Add **ControlNet branch** that can attach to whichever model is selected (Z‑Image Union ControlNet for Z‑Image; generic/FLUX‑specific ControlNet for FLUX). [comfy](https://comfy.org/workflows/image_z_image_turbo_fun_union_controlnet-7553d92529e0/)
- Add **LoRA branch** that feeds style/character LoRAs into the active model (Z‑Image LoRAs for Z‑Image, FLUX LoRAs for FLUX). [youtube](https://www.youtube.com/watch?v=qk_HdCqjNHw)

On your M4 Pro with 128 GB RAM, you can safely run Z‑Image Turbo + Union ControlNet + LoRAs and FLUX2 Klein + LoRAs at 1024×1024 and above without tight VRAM constraints. [zimageturbo](https://zimageturbo.org/z-image-turbo-controlnet)

***

## 1. ControlNet subgraph for Z‑Image Turbo

### 1.1 Required models and patch

For Z‑Image ControlNet Union, ComfyUI’s official guide and templates use the **Z‑Image‑Turbo‑Fun‑Controlnet‑Union** model patch: [youtube](https://www.youtube.com/watch?v=Fx41mfbsqzI)

- ControlNet model file:  
  - `Z-Image-Turbo-Fun-Controlnet-Union.safetensors`  
  - Stored under: `ComfyUI/models/model_patches/` (per docs). [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)

Your SKILL already documents Z‑Image Turbo bf16 UNet, VAE, and Qwen3 text encoder paths; this patch completes the ControlNet setup. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/44072005/20117530-c23a-4f62-aeb0-75ad512f0b26/comfyui-set-mac-SKILL.md?AWSAccessKeyId=ASIA2F3EMEYEVVUSEPCB&Signature=nUU4I6rdnnsNbHC3LX5DUSI5xmc%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEPL%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIHBjs6eyjoZKNLtxTCwc4arsykkpTGarw7EcT7%2Fwvs%2FHAiEA7lgPUNv4HP25pxaYm6LQkI5270GKCFgijz4bwLsXOhMq%2FAQIu%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARABGgw2OTk3NTMzMDk3MDUiDBbzM%2FmlL6W62OlhcyrQBB6ABU%2F34H99pgRdv2q%2F62IXjb8Lvjjly7igh90ZzyPqveLfpKGTWSHUurd3kQHtz4xObMvzMzkO0mLw%2BsBYd1Atx%2FKa9rosTopJ43PRsXa06oMEzck9S2A6RGnTPJvsTMIiOrcaRKq2rf%2Fwf7Ow1tUBrQ7GRVDgmXK%2FS4u647O%2FpihOv57BeCEl8%2FUQcvN4JZ41EH38Is8qgZ%2BXAU4QNC1fWxatadS53qOoVSbFdDUPjvlRbXRx75e%2BYatpSwH8vZpYGAaHRdvFJWZJNnVYYsb9wh3iEtrQyIMN9I63m%2BFqOvvDYLxT4z7%2BD6J5T%2Bhm9BOK7HM91KergwxTR8Q92FnrDUlZk%2BKriubbJoNSMOE5JI2xFgjhjjnL45lbUzmJjYzXCSAMFIh%2BVcwwGHbrT2CzboJuRPiFqH0KHj9bm9jZW1kOo8PaPbCPLa5VlH3ltNMcsQ3BHC2PM6gz55IbYa1GzdlpYzBua0y769kBeiLYjI%2FRD6e8QhqgZaSEHOlxCVOpE5IB17t%2FC%2FfbDAIsI%2B6ABCMKgtSya6D6mIzjkyHvl1P8LwJAZZJE2KuHyqvs8PBbMmm%2B%2BFuSR9iX7thrIQP9q66znlWi8PwWV2D9N6j4fkjk0uioVa3%2BnATqjQ3CftOxSrH83O9LjAidBLLqITEuM6Oqy8RvQskBv0ZcZWi71xbNeVj8kerZ7ex56cLmpWLWanHsWseMItCOaum5JdPwlxmwrnlJQrDAZj3a%2FBJ1ffqMo5u4hZxctIRAac0LkeV24M1Ql55zrOuLh7r7W4ww4bmM0gY6mAHKV450HAKxVE5b8kcxNXjX%2BRu0k9HPdpNPO6LiNKGkLakYxSHSYaaFVfQWsLcR%2FA9CE%2BbJRrvPPHPTXp99e%2BlyXqEVRwUxPd1dPSfG%2BHXZHj5WY7udol70k8uO3lypePc0twAH68TKNiSHRTFAnfui%2Bh36QjpsG7c6VxCDC0bjGdEP0eJZlLzpoehPjGGCneQcuPiYh8fvHA%3D%3D&Expires=1782786740)

### 1.2 Branch structure

Extend the combined workflow with a **ControlNet branch**:

New inputs:

- `reference_image` (image file path or image input node).  
- `control_mode` (combo: `"none"`, `"canny"`, `"depth"`, `"pose"`). [comfy](https://comfy.org/workflows/image_z_image_turbo_fun_union_controlnet-7553d92529e0/)

New nodes (conceptually):

1. `LoadImage`  
   - Loads `reference_image`.  
2. `ResizeImageToMatchLatent`  
   - Resizes reference to match the target resolution (no crop).  
   - Outputs resized image and width/height if needed. [zimageturbo](https://zimageturbo.org/z-image-turbo-controlnet)
3. `ControlNetPreprocessor`  
   - Branches based on `control_mode`:  
     - Canny edge detector.  
     - Depth model (e.g., Depth Anything).  
     - Pose estimator (DW Pose / OpenPose). [youtube](https://www.youtube.com/watch?v=KmYNxtLZQTU)
   - Outputs preprocessed control map(s) (IMAGE).  
4. `ZImageControlNetLoader` / model‑patch node  
   - Loads `Z-Image-Turbo-Fun-Controlnet-Union.safetensors`. [youtube](https://www.youtube.com/watch?v=Fx41mfbsqzI)
5. `ControlNetApply`  
   - Takes:  
     - Base MODEL (Z‑Image Turbo MLX/PyTorch).  
     - ControlNet model patch.  
     - Preprocessed control map(s).  
   - Outputs modified MODEL (or extra conditioning) that the sampler uses. [comfy](https://comfy.org/workflows/image_z_image_turbo_fun_union_controlnet-7553d92529e0/)

Integration with core sampler:

- When `model_choice == "zimage"` and `control_mode != "none"`, feed the **ControlNet‑modified MODEL** into your `MLXSampler` (or KSampler) and optionally adjust steps slightly upward (e.g., from 8 to 10) to account for ControlNet conditioning. [youtube](https://www.youtube.com/watch?v=Fx41mfbsqzI)
- When `control_mode == "none"`, skip the ControlNet branch and use the original MODEL.  

This mirrors ComfyUI’s official “Z‑Image Turbo Fun Union ControlNet” template but keeps it abstract enough to fit your combined graph. [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)

***

## 2. LoRA subgraph for Z‑Image Turbo

### 2.1 LoRA storage and loader

Z‑Image LoRA guides consistently use LoRA files placed in:  

- `ComfyUI/models/loras/` for Z‑Image‑Turbo LoRAs (style, character, etc.). [stablediffusiontutorials](https://www.stablediffusiontutorials.com/2025/11/z-image-turbo-lora-training.html)

Many workflows use specialized LoRA loader nodes, such as **RGThree Power LoRA Loader** or similar, designed to attach LoRAs to the running model and adjust their strengths. [youtube](https://www.youtube.com/watch?v=o_yT7pEyRP8)

### 2.2 Branch structure

Add a **LoRA branch** to your combined graph:

New inputs:

- `zimage_lora_name` (combo listing installed Z‑Image LoRAs).  
- `zimage_lora_strength` (float, e.g., 0.0–1.0). [youtube](https://www.youtube.com/watch?v=qk_HdCqjNHw)

New nodes:

1. `ZImageLoRALoader` (e.g., Power LoRA Loader)  
   - Inputs: base MODEL (Z‑Image Turbo), `zimage_lora_name`, `zimage_lora_strength`.  
   - Outputs: LoRA‑patched MODEL with the LoRA applied. [runcomfy](https://www.runcomfy.com/comfyui-workflows/z-image-turbo-ai-toolkit-lora-inference-in-comfyui-training-matched-results)

Integration:

- When `model_choice == "zimage"` and a LoRA is selected, feed the **LoRA‑patched MODEL** into the sampler instead of the original Z‑Image model (or ControlNet‑modified model if both branches are on). [runcomfy](https://www.runcomfy.com/comfyui-workflows/z-image-turbo-ai-toolkit-lora-inference-in-comfyui-training-matched-results)
- Keep CFG at 1.0; LoRAs typically work with the base CFG used by Z‑Image Turbo. [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4)

On your M4 Pro, you can run multiple LoRAs simultaneously if the loader supports multi‑LoRA stacking; just track strengths carefully to avoid over‑baking styles. [youtube](https://www.youtube.com/watch?v=o_yT7pEyRP8)

***

## 3. ControlNet subgraph for FLUX2 Klein

FLUX2 Klein ComfyUI workflows show typical **ControlNet patterns**: Canny, Depth, Pose plus Beta‑style schedulers, with some packs exposing dedicated nodes and NVFP4/GGUF model formats for VRAM efficiency. [docs.comfy](https://docs.comfy.org/tutorials/flux/flux-2-klein)

### 3.1 Required models

You’ll need FLUX‑compatible ControlNet models—for example, Canny/Depth/Pose ControlNet checkpoints that work with FLUX2 Klein (many tutorials bundle download links and tuned settings). [youtube](https://www.youtube.com/watch?v=jV7SNCMEKMw)

Store them under `models/controlnet/` per ComfyUI convention. [youtube](https://www.youtube.com/watch?v=GYJYud-E2I0)

### 3.2 Branch structure

Reuse the same pattern as Z‑Image but with FLUX nodes:

New inputs:

- `flux_control_mode` (combo: `"none"`, `"canny"`, `"depth"`, `"pose"`).  

New nodes:

1. `LoadImage` (reference image).  
2. `ResizeImageToMatchLatent`.  
3. `ControlNetPreprocessor` (same idea as Z‑Image, but tuned to FLUX’s recommended resolution and preprocessors). [youtube](https://www.youtube.com/watch?v=jV7SNCMEKMw)
4. `FluxControlNetLoader` (loads FLUX ControlNet model).  
5. `ControlNetApply` (attaches to FLUX2 Klein MODEL).  

Integration:

- When `model_choice == "flux"` and `flux_control_mode != "none"`, pass the FLUX model through `FluxControlNetLoader`/`ControlNetApply` before the **MLXSampler**; use Beta 57 or similar scheduler recommended for FLUX2 Klein, with steps in the 12–16 range. [youtube](https://www.youtube.com/watch?v=57ppu1WmqLU)
- If `flux_control_mode == "none"`, skip the ControlNet branch and use the base FLUX model.  

Your M4 Pro can handle ControlNet at 1024×1024 and higher with FLUX2 Klein, so you can experiment with higher resolutions and more complex control maps. [docs.comfy](https://docs.comfy.org/tutorials/flux/flux-2-klein)

***

## 4. LoRA subgraph for FLUX2 Klein

FLUX2 Klein tutorials show LoRA integration for style and image edit, often via LoRA loader nodes that patch the UNet/encoder at runtime and let you tune strengths per LoRA. [youtube](https://www.youtube.com/watch?v=GYJYud-E2I0)

### 4.1 LoRA storage and loader

Place FLUX‑specific LoRAs under e.g.:  

- `ComfyUI/models/loras/flux/` or directly in `models/loras/` with appropriately named files. [youtube](https://www.youtube.com/watch?v=jV7SNCMEKMw)

Use a generic LoRA loader node that works with FLUX models (sometimes installed via FLUX enhancer packs or RGThree node packs). [github](https://github.com/capitan01R/ComfyUI-Flux2Klein-Enhancer)

### 4.2 Branch structure

Add a FLUX LoRA branch:

New inputs:

- `flux_lora_name` (combo listing installed FLUX LoRAs).  
- `flux_lora_strength` (float, e.g., 0.0–1.0).  

New nodes:

1. `FluxLoRALoader`  
   - Inputs: base FLUX MODEL (or ControlNet‑patched model), `flux_lora_name`, `flux_lora_strength`.  
   - Outputs: LoRA‑patched FLUX MODEL. [youtube](https://www.youtube.com/watch?v=57ppu1WmqLU)

Integration:

- When `model_choice == "flux"` and a FLUX LoRA is selected, feed the LoRA‑patched FLUX model into the sampler. [youtube](https://www.youtube.com/watch?v=GYJYud-E2I0)
- Keep CFG around 7.0, and adjust steps (e.g., 12–14) based on the FLUX LoRA’s recommended settings. [comfy](https://www.comfy.org/fr/workflows/image_flux2_klein_text_to_image-814fd547d86e/)

***

## 5. How to wire both branches into the combined template

In the combined MLX graph you already sketched:

- **ModelSwitch node**: keep it as the central selector for base Z‑Image vs FLUX models (and VAEs).  
- Add **two parallel enhancement branches**:
  - Z‑Image ControlNet + LoRA branch that only activates when `model_choice == "zimage"`.  
  - FLUX ControlNet + LoRA branch that only activates when `model_choice == "flux"`.  

Implementation strategy:

1. **Z‑Image path**  
   - Base model from ModelSwitch → Z‑Image LoRA loader (optional) → Z‑Image ControlNet branch (optional) → MLXSampler. [youtube](https://www.youtube.com/watch?v=qk_HdCqjNHw)

2. **FLUX path**  
   - Base model from ModelSwitch → FLUX LoRA loader (optional) → FLUX ControlNet branch (optional) → MLXSampler (with FLUX‑tuned scheduler). [docs.comfy](https://docs.comfy.org/tutorials/flux/flux-2-klein)

You can do this by having separate “Model + VAE + ControlNet + LoRA” nodes for each path, then in the sampler’s `model` input you choose the appropriate output based on `model_choice` (via a small switch node or two samplers wired to different branches). [facebook](https://www.facebook.com/groups/comfyui/posts/950399787732722/)

***

## 6. Recommended defaults for your M4 Pro

Given your hardware:

- Z‑Image Turbo + ControlNet + LoRA:  
  - 1024×1024, steps≈10, CFG≈1.0, Union ControlNet with Canny or Depth, LoRA strengths around 0.4–0.7. [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4)
- FLUX2 Klein + ControlNet + LoRA:  
  - 1024×1024 (or 1536×1536), steps≈12–16, CFG≈7.0, Beta 57 or similar scheduler, LoRA strengths around 0.5–0.8 depending on LoRA. [comfy](https://www.comfy.org/fr/workflows/image_flux2_klein_text_to_image-814fd547d86e/)

You can expose these as default widget values in the combined template and adjust per run.

***

---

Below is a concrete JSON fragment for a **Z‑Image Turbo ControlNet + LoRA branch** that you can merge into your existing `image_zimage_m4pro.json`. It follows the official Z‑Image Turbo Fun Union ControlNet workflow structure (Canny‑based guidance) and uses a Power LoRA Loader–style node for LoRAs, but keeps names generic enough that you can adapt them to your installed node types. [comfy](https://comfy.org/workflows/image_z_image_turbo_fun_union_controlnet-7553d92529e0/)

I’ll first outline the logic, then show the JSON fragment with node IDs and links keyed to the earlier Z‑Image template (nodes 1–13).

***

## ControlNet + LoRA branch design for Z‑Image Turbo

### Models and paths assumed (matching SKILL.md + official docs)

- Z‑Image Turbo base:  
  - `models/diffusion_models/z_image_turbo_bf16.safetensors`  
  - `models/text_encoders/qwen_3_4b.safetensors`  
  - `models/vae/ae.safetensors` [docs.comfy](https://docs.comfy.org/zh-CN/tutorials/image/z-image/z-image-turbo)
- ControlNet patch:  
  - `models/model_patches/Z-Image-Turbo-Fun-Controlnet-Union.safetensors` (Fun Union ControlNet). [zimageturbo](https://zimageturbo.org/z-image-turbo-controlnet)
- LoRAs (Z‑Image Turbo):  
  - `models/loras/<your_zimage_lora>.safetensors` (style/character LoRAs placed under `models/loras/` as recommended in Z‑Image LoRA guides). [stablediffusiontutorials](https://www.stablediffusiontutorials.com/2025/11/z-image-turbo-lora-training.html)

### New functionality

For **Z‑Image** when `model_choice = "zimage"`:

- **ControlNet branch** (optional):  
  - Load a reference image.  
  - Resize it to match target resolution.  
  - Generate a Canny control map.  
  - Load Fun Union ControlNet patch.  
  - Apply ControlNet to the base Z‑Image model. [youtube](https://www.youtube.com/watch?v=Fx41mfbsqzI)

- **LoRA branch** (optional):  
  - Load one or more Z‑Image LoRAs.  
  - Apply them to the (possibly ControlNet‑patched) model with a strength slider. [comfy](https://comfy.icu/node/Power-Lora-Loader-rgthree)

The sampler then uses the enhanced MODEL (base → ControlNet → LoRA) instead of the plain Z‑Image Turbo MODEL.

***

## JSON fragment: Z‑Image ControlNet + LoRA nodes

This fragment assumes your existing Z‑Image graph uses:

- Node 8: Z‑Image base model loader (MODEL out).  
- Node 11: Sampler (takes MODEL, seed, steps, cfg, conditioning, latent).  

The new nodes are **IDs 14–21**, and two new links, so they don’t clash with the earlier 1–13 IDs.

> Important: adjust `type` values to match the actual node types in your ComfyUI setup (for example, ControlNet loader node names can differ slightly between packs; same for Power LoRA Loader). [comfyai](https://comfyai.run/documentation/Power%20Lora%20Loader%20(rgthree))

```json
{
  "nodes": [
    {
      "id": 14,
      "type": "LoadImage",
      "title": "ControlNet Reference Image",
      "pos": [50, 550],
      "size": [260, 140],
      "widgets_values": [
        "reference.png"               // path or default image
      ],
      "outputs": [
        { "name": "IMAGE", "type": "IMAGE", "links":  [runcomfy](https://www.runcomfy.com/comfyui-nodes/rgthree-comfy/Power-Lora-Loader--rgthree-) }
      ]
    },
    {
      "id": 15,
      "type": "ImageScaleToMaxDimension",
      "title": "Resize Ref to Target Resolution",
      "pos": [340, 560],
      "size": [260, 140],
      "inputs": [
        { "name": "image", "type": "IMAGE", "link": 13 },
        { "name": "max_side_length", "type": "INT", "link": 3 }   // Width from node 3
      ],
      "widgets_values": [
        1024,                            // default max dimension
        "lanczos"
      ],
      "outputs": [
        { "name": "IMAGE", "type": "IMAGE", "links":  [z-image-turbo](https://z-image-turbo.ai/z-image-controlnet) }
      ]
    },
    {
      "id": 16,
      "type": "ControlNetPreprocessorCanny",
      "title": "ControlNet Canny Preprocessor",
      "pos": [640, 560],
      "size": [280, 160],
      "inputs": [
        { "name": "image", "type": "IMAGE", "link": 14 }
      ],
      "widgets_values": [
        1.0,                             // low threshold
        2.0                              // high threshold
      ],
      "outputs": [
        { "name": "IMAGE", "type": "IMAGE", "links":  [runcomfy](https://www.runcomfy.com/comfyui-workflows/z-image-turbo-ai-toolkit-lora-inference-in-comfyui-training-matched-results) }
      ]
    },
    {
      "id": 17,
      "type": "ControlNetLoader",
      "title": "Load Z-Image Fun Union ControlNet",
      "pos": [940, 560],
      "size": [280, 140],
      "widgets_values": [
        "Z-Image-Turbo-Fun-Controlnet-Union"   // model_patches entry name
      ],
      "outputs": [
        { "name": "CONTROL_NET", "type": "CONTROL_NET", "links":  [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4) }
      ]
    },
    {
      "id": 18,
      "type": "ControlNetApply",
      "title": "Apply ControlNet to Z-Image MODEL",
      "pos": [1240, 260],
      "size": [350, 200],
      "inputs": [
        { "name": "model", "type": "MODEL", "link": 8 },   // base Z-Image model from node 8
        { "name": "control_net", "type": "CONTROL_NET", "link": 16 },
        { "name": "image", "type": "IMAGE", "link": 15 },
        { "name": "strength", "type": "FLOAT", "link": null }
      ],
      "widgets_values": [
        0.9                               // default control strength (0.9–0.95 recommended)
      ],
      "outputs": [
        { "name": "MODEL", "type": "MODEL", "links":  [x](https://x.com/sora_biz/status/1848343652214710642) }
      ]
    },
    {
      "id": 19,
      "type": "PrimitiveCombo",
      "title": "Z-Image LoRA Name",
      "pos": [1240, 480],
      "size": [260, 120],
      "widgets_values": [
        "none",                          // current value
        "none",
        [
          "none",
          "Z-Image-Turbo-pencil-sketch",
          "Z-Image-Turbo-Ghibli-Style"
        ]
      ],
      "outputs": [
        { "name": "value", "type": "STRING", "links":  [youtube](https://www.youtube.com/watch?v=3eWNocEJ8BM) }
      ]
    },
    {
      "id": 20,
      "type": "PrimitiveFloat",
      "title": "Z-Image LoRA Strength",
      "pos": [1240, 620],
      "size": [200, 80],
      "widgets_values": [0.5],
      "outputs": [
        { "name": "value", "type": "FLOAT", "links":  [youtube](https://www.youtube.com/watch?v=ttIJClSc8Vk) }
      ]
    },
    {
      "id": 21,
      "type": "PowerLoraLoader",          // rgthree Power LoRA Loader or equivalent
      "title": "Apply Z-Image LoRA",
      "pos": [1580, 260],
      "size": [360, 220],
      "inputs": [
        { "name": "model", "type": "MODEL", "link": 17 },   // MODEL from ControlNetApply
        { "name": "clip", "type": "CLIP", "link": null },   // optional CLIP; can use Qwen CLIP if required
        { "name": "lora_name", "type": "STRING", "link": 18 },
        { "name": "strength", "type": "FLOAT", "link": 19 }
      ],
      "widgets_values": [
        "z_image_turbo_bf16",            // base model name for internal stack (example)
        "qwen_3_4b"                      // CLIP name if node requires it
      ],
      "outputs": [
        { "name": "MODEL", "type": "MODEL", "links":  [zimage](https://zimage.net/blog/z-image-turbo-fun-controlnet-union) }
      ]
    }
  ],
  "links": [
    { "id": 13, "from_node": 14, "from_output": 0, "to_node": 15, "to_input": 0 },
    { "id": 14, "from_node": 15, "from_output": 0, "to_node": 16, "to_input": 0 },
    { "id": 15, "from_node": 16, "from_output": 0, "to_node": 18, "to_input": 2 },
    { "id": 16, "from_node": 17, "from_output": 0, "to_node": 18, "to_input": 1 },
    { "id": 17, "from_node": 18, "from_output": 0, "to_node": 21, "to_input": 0 },
    { "id": 18, "from_node": 19, "from_output": 0, "to_node": 21, "to_input": 2 },
    { "id": 19, "from_node": 20, "from_output": 0, "to_node": 21, "to_input": 3 },
    { "id": 20, "from_node": 21, "from_output": 0, "to_node": 11, "to_input": 0 }
  ]
}
```

***

## How this fragment hooks into your existing `image_zimage_m4pro.json`

1. **Base Z‑Image model**  
   - Node 8 still loads `z_image_turbo_bf16` (MODEL out). [docs.comfy](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)
   - Node 18 (ControlNetApply) takes that MODEL and outputs a **ControlNet‑enhanced MODEL**.

2. **LoRA application**  
   - Node 21 (PowerLoraLoader) takes the ControlNet‑enhanced MODEL and applies a selected LoRA with a given strength, outputting a **LoRA‑patched MODEL**. [runcomfy](https://www.runcomfy.com/comfyui-nodes/rgthree-comfy/Power-Lora-Loader--rgthree-)

3. **Sampler input change**  
   - In your original nodes, `KSampler` (or `MLXSampler`) node 11 currently takes `model` from node 8.  
   - After merging this fragment, change node 11’s `model` input link to come from node 21 instead:  
     - Replace the link `{ "from_node": 8, ... "to_node": 11, "to_input": 0 }`  
     - With `{ "from_node": 21, "from_output": 0, "to_node": 11, "to_input": 0 }` (link id 20 above).  

4. **Optional usage**  

- **ControlNet only**:  
  - Set `Z-Image LoRA Name` to `"none"`; the Power LoRA Loader should pass through the model unchanged (or you can implement it to bypass when `"none"` is selected). [z-image-turbo](https://z-image-turbo.ai/z-image-controlnet)
- **LoRA only (no ControlNet)**:  
  - Bypass the ControlNetApply node by linking node 8 (MODEL) directly into node 21 (`model` input), and keep ControlNet strength at 0 or control nodes disconnected. [youtube](https://www.youtube.com/watch?v=o_yT7pEyRP8)

On your M4 Pro, recommended defaults when both branches are active:  

- Steps ≈10, CFG ≈1.0, 1024×1024, ControlNet strength ≈0.9, LoRA strength ≈0.4–0.7. [youtube](https://www.youtube.com/watch?v=3Z9LTRN8ci4)

***

## Practical merging notes

- Install **ControlNet Union** and put `Z-Image-Turbo-Fun-Controlnet-Union.safetensors` in `models/model_patches/` exactly as in the official Comfy docs; otherwise the `ControlNetLoader` won’t see it. [zimageturbo](https://zimageturbo.org/z-image-turbo-controlnet)
- Install **RGThree ComfyUI nodes** (Power LoRA Loader), via ComfyUI’s Custom Nodes Manager (“rgthree’s ComfyUI Nodes”) so node type `PowerLoraLoader` (or its exact name) becomes available. [x](https://x.com/sora_biz/status/1848343652214710642)
- After merging, test with simple prompts and a single LoRA at low strength to verify the wiring; then enable Canny ControlNet and verify the model follows structure from the reference image as in the Union ControlNet demo workflows. [youtube](https://www.youtube.com/watch?v=3eWNocEJ8BM)

If you want, next I can do a similar concrete fragment for the **FLUX2 Klein ControlNet + LoRA branch**, tuned for FLUX schedulers and LoRA loaders, so your combined template has full parity between Z‑Image and FLUX on the M4 Pro.

---

https://www.perplexity.ai/search/please-meticulously-plan-to-do-OEkzQMB2S.itkOizy.61WQ 
