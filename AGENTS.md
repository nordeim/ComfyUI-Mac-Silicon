# Repository Guidelines

This workspace documents how to install, benchmark, and run MLX-optimized generative image models on Apple Silicon Macs. It is a research and documentation repository, not a software product under active development.

## Project Structure & Module Organization

```
├── *-SKILL.md, *Guide.md, *Workflows.md   # Deliverable guides (Markdown)
├── mlx-image-gen-mac-2026.md              # Deep research report
├── README.md                              # Workspace overview and file index
├── info.md                                # Compact Ideogram 4 + Krea 2 setup
├── zai_session_1.md                       # Research session transcript
├── scripts/                               # Research tooling (web search, deep-read)
│   ├── run_searches_throttled.sh
│   ├── run_searches_ws_ab.sh
│   ├── run_searches_ws_cde.sh
│   ├── run_searches_ws_f.sh
│   ├── deep_read.sh
│   ├── extract_notes.py
│   └── generate_companion_scripts.py
├── research/
│   ├── notes/                 # 14 clean-text primary-source extracts
│   └── scripts/               # 10 executable Python companion scripts
├── backup/                    # Excluded from Git
└── skills/                    # Excluded from Git
```

The canonical deliverable is `comfyui-set-mac-SKILL.md` (v1.5). Other `comfyui-set-mac-SKILL*` files are drafts or older versions preserved for audit.

## Build, Test, and Development Commands

There is no build system, linter, or CI. The executable artifacts are in `research/scripts/`:

```bash
# Run any companion script (deps auto-install on first run via uv PEP 723)
uv run research/scripts/01_z_image_turbo_basic.py     # Minimal mflux Python API
uv run research/scripts/09_benchmark_harness.py        # Benchmark your hardware
uv run research/scripts/02_production_server.py         # FastAPI image server on :8000

# View a deliverable
less comfyui-set-mac-SKILL.md
less MLX-Image-Gen-Mac-Implementation-Guide.md

# Verify source claims
ls research/notes/
```

## Coding Style & Naming Conventions

- All Python scripts use PEP 723 inline metadata (`# /// script`) — no `requirements.txt` or `setup.py` exists.
- Files are numbered sequentially with descriptive enough names: `01_z_image_turbo_basic.py`.
- Quantization defaults are `int8` throughout; changing them requires explicit justification.
- mflux version and API references are pinned to mflux 0.18.0 as of 2026-06-30.
- mflux benchmark numbers, model settings, and pitfall descriptions must match the cited sources in `research/notes/` — regenerate via `scripts/run_searches_throttled.sh` if you need fresh data.

## Testing Guidelines

There is no test framework. Verification is done by:

1. Running companion scripts against real Apple Silicon hardware.
2. Cross-checking citations against `research/notes/` extracts.
3. Following the 13-item verification checklist in `MLX-Image-Gen-Mac-Implementation-Guide.md` §13.

## Critical Facts to Preserve

When editing or extending this workspace, maintain these invariants:

1. **DiffusionKit is archived** (Mar 21, 2026). `thoddnn/ComfyUI-MLX` is stale. Use Mflux-ComfyUI by `@raysers`.
2. mflux 0.18.0 has a first-class Python API — no longer CLI-only.
3. M5 Neural Accelerator = 3.8× speedup for FLUX-dev-4bit, requires macOS 26.2+.
4. Quantization is a memory tool, not a speed tool, for MLX diffusion — prefer int8 unless memory-constrained.
5. Only FLUX.2 [klein] 4B distilled and Qwen-Image-2512 are Apache 2.0 in the flagship tier.
6. Hardware: M4 Pro/Max/Ultra and M5/Pro/Max all support the stack; M4 Base 16 GB must stick to small models (Z-Image Turbo int8 or FLUX.2 klein 4B).

## Commit & Pull Request Guidelines

- Follow the existing Git log style: lowercase descriptive subject, present tense, no ticket prefixes (`add CLAUDE.md`, `update docs`, `update skills`).
- Keep commits scoped to one logical change.
- Do not commit files inside `backup/`, `skills/`, or `node_modules/` — all are `.gitignore`d.
- Before referencing mflux API signatures or feature claims in commits, verify them against `mlx-image-gen-mac-2026.md` or `research/notes/`.
- Do not rewrite legacy SKILL files (`comfyui-set-mac-SKILL-v1.md`, `*updates.md`, `*new.md`) when their purpose is audit preservation.
