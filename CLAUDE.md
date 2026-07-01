# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is a **research and documentation workspace**, not a software product under active development. It contains markdown guides, research reports, and Python companion scripts that document and demonstrate how to install, benchmark, and run MLX-optimized image generation on Apple Silicon Macs.

Most "source code" lives in `research/scripts/` — these are illustrative companion scripts for the reports, not a library or application with a build system.

**Workspace metadata:** Built 2026-06-30 · Apple Silicon (M1–M5) + macOS Tahoe 26.x (26.2+ for M5 Neural Accelerator)

## Authoritative documents (newest-first)

Read in this order when continuing work:

1. **`MLX-Image-Gen-Mac-Implementation-Guide.md`** (21 KB) — Start here. Condensed, actionable agent-facing guide: install commands, model downloads, CLI/API/ComfyUI usage, 20-pitfall table, per-model settings, verification checklist.
2. **`comfyui-set-mac-SKILL.md`** (114 KB, v1.5) — The definitive step-by-step install & config guide. 7 runtime methods × 8 model families + editing tools × 20 pitfalls. **Other `comfyui-set-mac-SKILL*` files are drafts/older versions** — only `comfyui-set-mac-SKILL.md` (without `-new`, `-v1`, `updates`, `validation` suffix) is canonical.
3. **`mlx-image-gen-mac-2026.md`** (84 KB) — Deep technical research report. The "why" behind recommendations. 49 cited primary sources.
4. **`MLX-Optimized_Z-Image_Turbo_and_FLUX_Workflows.md`** (22 KB) — M4 Pro 128 GB-targeted workflows. mflux CLI + ComfyUI JSON schemas for Z-Image Turbo and FLUX.2.
5. **`README.md`** — Workspace overview and file index.
6. **`research/scripts/README.md`** — Script index and requirements.

Legacy files (`comfyui-set-mac-SKILL-v1.md`, `comfyui-set-mac-skill-updates.md`, `comfyui-set-mac-updates.md`, `comfyui-set-mac-validation.md`, `comfyui-set-mac-SKILL-new.md`) are preserved for audit but should not be used as the source of truth.

## Companion scripts (`research/scripts/`)

Ten self-contained Python scripts using PEP 723 inline metadata (`uv run --script`) so dependencies install on first run. All MIT-licensed; models they invoke have their own licenses (see `comfyui-set-mac-SKILL.md` §12 or report §7.3).

| # | File | Section | Purpose |
|---|------|---------|---------|
| 01 | `01_z_image_turbo_basic.py` | §5.1 | Minimal mflux Python API |
| 02 | `02_production_server.py` | §5.2 | FastAPI OpenAI-compatible image server |
| 03 | `03_multi_lora.py` | §5.3 | Multi-LoRA loading with scales |
| 04 | `04_image_to_image.py` | §5.4 | Image-to-image editing |
| 05 | `05_controlnet_depth.py` | §5.5 | ControlNet Canny + Depth Pro |
| 06 | `06_live_preview.py` | §5.6 | Live preview with mlx-taef |
| 07 | `07_teacache_speedup.py` | §5.7 | TeaCache step-skipping (30–50% speedup) |
| 08 | `08_metadata_reproducibility.py` | §5.8 | Metadata export + reproduce workflow |
| 09 | `09_benchmark_harness.py` | §8.3 | Benchmark harness (3×3 runs + RSS) |
| 10 | `10_commercial_safe_pipeline.py` | §7.3 | Apache 2.0 pipeline (FLUX.2 klein 4B) |

### Common commands

```bash
# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run any companion script (deps install on first run; downloads model later)
uv run research/scripts/01_z_image_turbo_basic.py

# Run benchmark harness across loaded models
uv run research/scripts/09_benchmark_harness.py

# Run production server
uv run research/scripts/02_production_server.py   # binds 0.0.0.0:8000
```

Test environment the scripts target: **mflux 0.18.0 · MLX 0.31.2 · Python 3.12**. If a script hits a `TypeError` on model construction, the mflux API changed — check `mlx-image-gen-mac-2026.md` for updated signatures.

## Research tooling (`scripts/`)

Working utilities used to *produce* the research artifacts — not needed by readers of the workspace:

- `run_searches_throttled.sh` — parallel web searches (max 2 concurrent, 1 s spacing) for WS-A through WS-F
- `run_searches_ws_ab.sh` / `run_searches_ws_cde.sh` / `run_searches_ws_f.sh` — per-workstream search variant scripts
- `deep_read.sh` — deep-reads pages into JSON
- `extract_notes.py` — converts page-reader JSON into clean-text notes (HTML strip + whitespace collapse)
- `generate_companion_scripts.py` — generator that produced the 10 research companion scripts

All assume a local path of `/home/z/my-project/research/{raw,pages,notes}` — they will not run cleanly outside that setup and are kept for reproducibility.

## Primary source notes (`research/notes/`)

14 clean-text extracts from cited sources (Apple MLX M5 benchmarks, FLUX.2, DiffusionKit archival, mflux, Draw Things, Ideogram 4, Qwen-Image, etc.). Used as the audit trail for citations in `mlx-image-gen-mac-2026.md`. Read these to verify any specific claim before re-citing it in new material.

## Critical facts to preserve in any work

1. **DiffusionKit is archived** (Mar 21, 2026). The `thoddnn/ComfyUI-MLX` path is stale. Use **Mflux-ComfyUI** by `@raysers` for ComfyUI↔MLX bridging.
2. **mflux 0.18.0** has a first-class Python API — no longer CLI-only.
3. **M5 Neural Accelerator** = 3.8× M5/M4 speedup for FLUX-dev-4bit via MLX. Requires **macOS 26.2+**.
4. **Quantization is a memory tool, not a speed tool** for MLX diffusion — prefer int8 unless memory-constrained.
5. **Only FLUX.2 [klein] 4B distilled and Qwen-Image-2512 are Apache 2.0** in the flagship tier. Verify license per model before commercial use.
6. **Hardware:** M4 Pro/Max/Ultra and M5/Pro/Max all support the stack; M4 Base 16 GB must stick to small models (Z-Image Turbo int8 or FLUX.2 klein 4B).
7. **Draw Things** uses proprietary Metal FlashAttention 2.0 — up to 25% faster per iteration than mflux on identical workloads via a different runtime, not a different model.

## Conventions

- All scripts use PEP 723 inline metadata (`uv run --script`); no `requirements.txt` files exist.
- Quantization defaults in scripts are `int8` — change only with justification (memory vs speed tradeoff is documented in the reports).
- All cited mflux version/code references in committed files are pinned to mflux 0.18.0 as of 2026-06-30.
- `.gitignore` excludes `backup/`, `skills/`, `node_modules/` — these directories either don't appear in the workspace or contain vendored refs not part of the deliverable.

## Things that are NOT in this repo

- No build system, linter, formatter, test framework, or CI configuration. There is nothing to "npm test" or "cargo build" — pick the relevant guide in Markdown and read it.
- No source files outside `research/scripts/` are intended to be executed. Other `.py` and `.sh` files are tooling utilities with hardcoded paths from the original research session.
