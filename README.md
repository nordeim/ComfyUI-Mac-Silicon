# Transparent Proxy — MLX Image Generation Research Workspace

> The definitive blueprint for running state-of-the-art, MLX-optimized generative image models locally on Apple Silicon — from bare-metal install to production workloads, with every pitfall documented and every command copy-paste ready.

**Workspace date:** 2026-06-30
**Platform:** Apple Silicon Mac (M1/M2/M3/M4/M5), macOS Tahoe 26.x (26.2+ for M5 Neural Accelerator)

This workspace is a self-contained research and delivery package for running state-of-the-art, MLX-optimized image generation on Apple Silicon. It contains the definitive v1.5 ComfyUI + MLX installation guide, an 11.5k-word deep technical research report, 10 production-ready Python companion scripts, and all intermediate research artifacts and session notes.

---

## Quick orientation

| Path | What it is | When to open it |
|---|---|---|
| `MLX-Image-Gen-Mac-Implementation-Guide.md` | **Condensed implementation guide (21 KB)** — distilled for an agent: install, downloads, CLI/API/ComfyUI commands, benchmark expected numbers, 20-pitfall table, per-model settings, verification checklist | **Start here for setup/testing continuation** |
| `comfyui-set-mac-SKILL.md` | **The main install & config guide (v1.5)** — 2,917 lines covering 7 runtime methods, 8 model families + editing tools, 20 pitfalls, production deployment patterns, and license audit | Definitive step-by-step reference |
| `mlx-image-gen-mac-2026.md` | **Deep technical research report** — 11,570 words, 56 web searches, 49 cited sources, architecture deep-dives, quantization theory, kernel-level benchmarks | When you need the "why" behind recommendations |
| `MLX-Optimized_Z-Image_Turbo_and_FLUX_Workflows.md` | **Mac mini M4 Pro 128GB targeted report** — concrete mflux CLI commands and ComfyUI workflow schemas tuned for high-RAM Macs | If you have an M4 Pro Max / 128GB Mac |
| `research_mac_image_models.md` | **Original research plan & phased methodology** — 10-phase deep research blueprint for mapping the MLX ecosystem (predecessor to the final report) | For understanding the research methodology |
| `research/scripts/*.py` | **10 production-ready companion scripts** — bare mflux Python API, FastAPI server, multi-LoRA, ControlNet, TeaCache, benchmark harness, and more | For running or adapting any mflux pattern |
| `info.md` | **Condensed Mac setup guide** — shorter standalone reference for Ideogram 4.0 + Krea 2 on M4 MacBooks with JSON prompt schema | Quick standalone Ideogram 4 + Krea 2 setup |
| `zai_session_1.md` | **Complete Z.ai research session transcript** — full record of the 56-search, 14-deep-read research execution that produced the v1.5 deliverables | For audit trail / understanding research provenance |
| `scripts/` | **Working research scripts** — web search orchestrators, deep reader, companion script generator | For re-running or extending the research |
| `research/notes/` | **14 clean-text primary source extracts** — MLX M5 benchmarks, FLUX.2, DiffusionKit, mflux, Draw Things, etc. | For verifying cited sources |
| `skills/comfyui-workflow-scaffold/SKILL.md` | **ComfyUI Workflow Scaffold skill** — agent-readable guide for creating valid ComfyUI workflow JSON templates for Apple Silicon image generation, with model-specific node catalogs and Mac validation checklists | For scaffolding new workflows or validating existing ones |

---

## File details (by modification date, newest first)

### `comfyui-set-mac-SKILL.md` (114 KB, most current)
**ComfyUI Mac Silicon Installation & Configuration Guide v1.5** — the primary deliverable. Fully rewritten from v1.4 (49 KB) to incorporate H1–H2 2026 research findings. Covers:

- **4 critical update notices**: DiffusionKit archived (Mar 2026), mflux 0.18.0 Python API, M5 Neural Accelerator requires macOS 26.2+, Ideogram 4 MLX requires mflux ≥ 0.18.0 (or `mlx-forge` standalone)
- **8 model families + editing tools**: Ideogram 4, Z-Image Turbo, FLUX.2 (klein 4B/9B/KV, dev 32B), Qwen-Image-2512, FIBO, ERNIE-Image, FLUX.1 (8 base families) + Kontext, ControlNet, SeedVR2, In-Context LoRA, CatVTON, IC-Edit, Flux Tools, Depth Pro (editing tools). Krea 2 Turbo support was WIP in mflux 0.18.0 (PR [#468](https://github.com/filipstrand/mflux/actions/runs/28061152328)); check the mflux release notes for the version that finalized it.
- **7 runtime methods**: mflux CLI, mflux Python API, ComfyUI+PyTorch MPS, Draw Things, ComfyUI+Mflux-ComfyUI, Native Swift (FluxForge), Production API Servers
- **Hardware matrix**: M4 Base/Pro/Max/Ultra + M5/Pro/Max with memory bandwidth, Neural Accelerator notes
- **20 pitfalls**: broken pipe fix, fp8 incompatibility, Krea 2 CFG=0, LoRA architecture mismatch, DiffusionKit archival, quantization-is-memory-not-speed, etc.
- **Production deployment**: 10 patterns with companion script references
- **License audit**: strict Apache 2.0 vs Non-Commercial table
- **Appendices**: installation script, workflow diagrams, verification checklist, companion scripts manifest, migration guide v1.4→v1.5

### `mlx-image-gen-mac-2026.md` (84 KB, most current)
**Deep technical research report** — the exhaustive foundation for v1.5. Methodology: 56 web searches across 6 workstreams + 14 deep page reads. Sections:

- Model landscape (8 base families + editing tools, with architecture, quantization, licensing)
- MLX runtime ecosystem (mflux, DiffusionKit archival, Mflux-ComfyUI, Draw Things, FluxForge, production servers)
- Quantization deep dive (group quantization, mixed-precision, GGUF comparison, memory budgeting)
- Hardware benchmarks (Apple Silicon bandwidth tiers, M5 vs M4 MLX 3.8× speedup, cited M4 pro timings)
- Custom code patterns (bare mflux Python API, FastAPI server, LoRA, ControlNet, TeaCache)
- Production deployment patterns
- License audit
- 49 cited primary sources

### `MLX-Optimized_Z-Image_Turbo_and_FLUX_Workflows.md` (22 KB, most current)
**Mac mini M4 Pro 128GB targeted report** — specific recommendations for high-RAM Mac setups. Includes concrete mflux CLI commands and ComfyUI workflow JSON schemas for Z-Image Turbo and FLUX.2 Klein 4B, plus template structures for `image_zimage_m4pro.json` and `image_flux_m4pro.json`.

### `MLX-Image-Gen-Mac-Implementation-Guide.md` (21 KB, most current)
**Condensed implementation guide for the next agent** — distilled from the 210 KB+ research corpus (`research_mac_image_models.md` + `mlx-image-gen-mac-2026.md`):
- **§1–§2 Ecosystem state:** critical changes, model matrix, hardware tiers
- **§3–§4 Setup:** mflux + ComfyUI + Mflux-ComfyUI bridge + all model download commands
- **§5 Running:** CLI / Python API / ComfyUI / FastAPI with copy-paste code
- **§7 Benchmarking:** expected performance per model/hardware
- **§8 Per-model settings:** Z-Image, FLUX.2, Krea 2, Ideogram 4
- **§9 Pitfalls:** all 20 known issues in scannable table form
- **§10 Production:** decision matrix + explicit "never use" list
- **§13 Verification:** 13-item checklist to confirm install
- **§14 File reference:** quick map to SKILL.md / research report / scripts / notes

Purpose: every line is actionable — no duplicate JSON skeletons, no verbose methodology, no agent-specific narrative. Exactly what's needed to continue setup, troubleshooting, and testing.

### `comfyui-set-mac-SKILL-new.md` (113 KB)
Near-final draft of the v1.5 SKILL.md. Content is essentially identical to `comfyui-set-mac-SKILL.md` (the most current version should be considered authoritative).

### `zai_session_1.md` (40 KB)
Full research session transcript from Z.ai — documents the ANALYZE→PLAN→VALIDATE→IMPLEMENT→VERIFY→DELIVER workflow execution including all search queries, analysis, and intermediate deliverables.

### `research_mac_image_models.md` (101 KB)
Original 10-phase research plan and methodology document. Maps out the workstreams that were later executed to produce `mlx-image-gen-mac-2026.md`. Useful for understanding the research architecture.

### `info.md` (13 KB)
**Running Ideogram 4.0 & Krea 2 on Apple M4 MacBooks** — a concise standalone guide covering:
- Model specifications (Ideogram 4 9.3B DiT + Qwen3-VL-8B, Krea 2 RAW + Turbo)
- Hardware considerations by chip tier
- Three methods: mflux CLI, ComfyUI, Draw Things
- JSON prompt workflow for Ideogram 4
- Troubleshooting and licensing warnings

### `mlx-image-gen-scripts_readme.md` (2.5 KB, most current)
Quick-start README for the companion scripts directory — installation, script index table, requirements.

### `research/mlx-image-gen-mac-2026.md` (84 KB)
Copy of the research report in the research/ subfolder — same content as the root-level `mlx-image-gen-mac-2026.md`.

### `research/scripts/` (10 Python scripts)
Production-ready mflux companion scripts, each self-contained with `uv run --script` inline dependencies:

| # | Script | Purpose |
|---|---|---|
| 01 | `01_z_image_turbo_basic.py` | Minimal mflux Python API — Z-Image Turbo int8 |
| 02 | `02_production_server.py` | FastAPI OpenAI-compatible image server |
| 03 | `03_multi_lora.py` | Multi-LoRA loading with scales |
| 04 | `04_image_to_image.py` | Image-to-image editing |
| 05 | `05_controlnet_depth.py` | ControlNet Canny + Depth Pro pipeline |
| 06 | `06_live_preview.py` | Live preview with mlx-taef TAE decoder |
| 07 | `07_teacache_speedup.py` | TeaCache step-skipping (30–50% speedup) |
| 08 | `08_metadata_reproducibility.py` | Metadata export + reproduce workflow |
| 09 | `09_benchmark_harness.py` | Benchmark harness for measuring your hardware |
| 10 | `10_commercial_safe_pipeline.py` | Commercial-safe pipeline (Apache 2.0) |

All scripts: MIT-licensed. Models invoked have their own licenses (see SKILL.md Section 12).

### `research/notes/` (14 text files)
Clean-text extracts of primary sources, used as citation audit trail:
- `apple_mlx_m5.txt` — Apple's M5 + MLX research benchmarks
- `bfl_flux2.txt` — Black Forest Labs FLUX.2 blog
- `comfyui_mlx_nodes.txt` — ComfyUI-MLX node details
- `diffusionkit.txt` — DiffusionKit archival notice
- `draw_things_metal_fa.txt` — Draw Things Metal FlashAttention 2.0
- `fibo_mlx.txt` — FIBO Bria AI MLX card
- `flux2_repo.txt` — FLUX.2 GitHub repo
- `flux2_swift_mlx.txt` — FluxForge Swift MLX
- `ideogram4_mlx_q4.txt` — Ideogram 4 MLXBits model card
- `m4pro_benchmark.txt` — M4 Pro hands-on benchmark
- `mflux_pypi.txt` — mflux PyPI metadata
- `mflux_readme.txt` — mflux README model matrix
- `qwen_image_mlx.txt` — Qwen-Image-2512 MLX card
- `zimage_mlux_reddit.txt` — Z-Image Turbo MLX community notes

### `scripts/` (7 working scripts)
Research and generation utilities:
- `deep_read.sh` — deep-reads primary sources via page_reader
- `extract_notes.py` — extracts clean text from page_reader JSON
- `generate_companion_scripts.py` — generates the 10 research/scripts/ companion scripts
- `run_searches_throttled.sh` — throttled parallel web search (recommended)
- `run_searches_ws_ab.sh` — WS-A + WS-B parallel searches (Model Landscape + MLX Runtimes)
- `run_searches_ws_cde.sh` — WS-C + WS-D + WS-E searches (Quantization + Benchmarks + Code)
- `run_searches_ws_f.sh` — WS-F gap-filling searches

### Legacy files (preserved for reference)

| File | Size | Description |
|---|---|---|
| `comfyui-set-mac-SKILL-v1.md` | 49 KB | v1.4 baseline — earlier SKILL before v1.5 rewrite |
| `comfyui-set-mac-skill-updates.md` | 52 KB | v1.4→v1.5 delta notes documenting planned changes |
| `comfyui-set-mac-updates.md` | 23 KB | Incremental update notes from v1.3→v1.4 |
| `comfyui-set-mac-validation.md` | 13 KB | Validation checklist and source verification |
| `list_local_skills.txt` | 2 KB | Inventory of available agent skills (69 entries) |
| `.gitignore` | 30 B | Excludes `backup/`, `skills/`, `node_modules/` |

---

## Usage workflows

### 1. Set up ComfyUI + MLX on your Mac
```bash
# Read the v1.5 guide
less comfyui-set-mac-SKILL.md

# Start with Method 2 (mflux Python API) for fastest results
uv run research/scripts/01_z_image_turbo_basic.py
```

### 2. Run the research report independently
```bash
less mlx-image-gen-mac-2026.md
```

### 3. Benchmark your specific hardware
```bash
uv run research/scripts/09_benchmark_harness.py
```

### 4. Compare v1.4 → v1.5 changes
```bash
diff comfyui-set-mac-SKILL-v1.md comfyui-set-mac-SKILL.md
```

### 5. Validate the research sources
```bash
# Each cited source has a clean-text extract in research/notes/
ls research/notes/
```

---

## Key findings summary

1. **DiffusionKit is archived (Mar 21, 2026)** — the `thoddnn/ComfyUI-MLX` path is stale. Use `Mflux-ComfyUI` by `@raysers` for ComfyUI↔MLX bridging.
2. **mflux 0.18.0** has a first-class Python API supporting 8 model families + a suite of editing tools (Kontext, ControlNet, SeedVR2, In-Context LoRA, CatVTON, IC-Edit, Flux Tools, Depth Pro) — no longer CLI-only.
3. **M5 Neural Accelerator** delivers 3.8× M5/M4 speedup for FLUX-dev-4bit via MLX (requires macOS 26.2+).
4. **Quantization is a memory tool, not a speed tool** for MLX diffusion — prefer int8 unless memory-constrained.
5. **Commercial-safe models**: Only FLUX.2 [klein] 4B distilled and Qwen-Image-2512 are Apache 2.0 in the flagship tier.
6. **Draw Things** uses proprietary Metal FlashAttention 2.0 — up to 25% faster per iteration than mflux on identical workloads.

---

Created: skills/comfyui-workflow-scaffold/SKILL.md
 
Location: `skills/comfyui-workflow-scaffold/` 
 
### Structure 
 
``` 
  comfyui-workflow-scaffold/ 
  ├── SKILL.md                          (333 lines) 
  └── references/ 
      ├── workflow-schema.md            (155 lines) 
      ├── node-catalog.md               (168 lines) 
      └── link-patterns.md              (129 lines) 
``` 
 
### What This Skill Does 
 
This skill enables the agent to create valid ComfyUI workflow JSON templates for Apple Silicon image generation. It synthesizes patterns from: 
 
1. 6 sample workflows in sample_workflows_as_examples/ — structural patterns (groups, MarkdownNote docs, node/link schema) 
2. MLX-Image-Gen-Mac-Implementation-Guide.md — Mac-specific constraints (no fp8, Krea 2 cfg=0, hardware limits) 
3. comfyui-set-mac-SKILL.md — canonical 11-node PyTorch MPS scaffold and 3-node Mflux-ComfyUI scaffold 
 
### Key Capabilities 
 
| Feature | Detail | 
|---|---| 
| Two output formats | Saved Graph (native) + Prompt API (agent-friendly) | 
| Model-specific templates | Z-Image Turbo, FLUX.1/2, Krea 2, Ideogram 4, Qwen-Image, FIBO | 
| Backend selection | PyTorch MPS (11-node) vs Mflux-ComfyUI MLX (3-node) | 
| Mac validation checklist | fp8 detection, memory fit, LoRA architecture match, Krea cfg=0 | 
| Reference files | Full JSON schema, node catalog with slot indices, link patterns per model | 
 
### Trigger Phrases 
 
The skill activates on: "create a workflow", "scaffold a ComfyUI template", "workflow JSON", "ComfyUI node graph", "image generation workflow", or keywords: comfyui, workflow, node graph, json template, scaffold, image pipeline.

---

## Snapshot metadata

- **Built:** 2026-06-30
- **Research methodology:** 56 web searches across 6 workstreams + 14 deep page reads
- **Source:** 49 cited primary sources (HuggingFace, GitHub, Apple ML Research, vendor blogs, community threads)
- **Excluded from workspace:** `backup/` (older versions), `.git/` (history), `skills/` (61 MB internal)
- **License:** All original content (scripts, guides, reports) MIT-licensed. Models have separate licenses.

---

## Validation

This workspace was audited on 2026-07-01 by Z.ai. The full per-claim validation report — with live evidence URLs replacing the previous anonymous `[[N]]` citations — is at [`ComfyUI-Mac-Silicon-Validation-Report.md`](ComfyUI-Mac-Silicon-Validation-Report.md). The remediation plan and post-remediation re-audit are at [`ComfyUI-Mac-Silicon-Remediation-Plan.md`](ComfyUI-Mac-Silicon-Remediation-Plan.md) and [`ComfyUI-Mac-Silicon-Post-Remediation-Report.md`](ComfyUI-Mac-Silicon-Post-Remediation-Report.md).

> The previous "validation report" section that used anonymous `[[N]]` citations has been removed. Those citations did not resolve to any URL or bibliography in the workspace and were structurally indistinguishable from hallucinated validation. The workspace's underlying content is accurate on its own merits — see the validation report for the live evidence.
