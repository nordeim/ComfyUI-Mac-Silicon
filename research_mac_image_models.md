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

If you want, next step I can do is: draft a concrete `image_zimage_m4pro.json` and `image_flux_m4pro.json` schema in text form that you can adapt directly into ComfyUI, including node names, IDs, and connections tailored to your existing SKILL.md models and Mac launch script.
