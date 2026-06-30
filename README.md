# ComfyUI Mac Silicon — Workspace Snapshot

**Snapshot version:** v1.5
**Snapshot date:** 2026-06-30
**Target platform for testing:** Apple Silicon Mac (M1/M2/M3/M4/M5), macOS Tahoe 26.x (26.2+ for M5 Neural Accelerator)

This workspace contains the complete v1.5 deliverables for running ComfyUI and MLX-optimized image generation on Apple Silicon. It is a portable snapshot — extract on a Mac and follow the instructions below.

---

## What's in this workspace

```
my-project/
├── README.md                         ← you are here
├── MANIFEST.txt                      ← exact file list with sizes (verify after extraction)
├── .gitignore
│
├── scripts/                          ← working scripts used to build this snapshot
│   ├── deep_read.sh                    (deep-reads primary sources via page_reader)
│   ├── extract_notes.py                (extracts clean text from page_reader JSON)
│   ├── generate_companion_scripts.py   (generates the 10 companion scripts in download/research/scripts/)
│   ├── run_searches_throttled.sh       (throttled parallel web search — recommended)
│   ├── run_searches_ws_ab.sh           (WS-A + WS-B parallel searches)
│   ├── run_searches_ws_cde.sh          (WS-C + WS-D + WS-E parallel searches)
│   └── run_searches_ws_f.sh            (WS-F gap-filling searches)
│
├── download/                         ← FINAL DELIVERABLES (start here)
│   ├── README.md                        (overview of download/ folder)
│   ├── comfyui-set-mac-SKILL.md         (v1.5 SKILL.md — the main install guide, 14k words)
│   └── research/
│       ├── mlx-image-gen-mac-2026.md    (research report — 11.5k words, 49 cited sources)
│       └── scripts/                     (10 production-ready Python scripts)
│           ├── README.md                  (scripts overview + quick start)
│           ├── 01_z_image_turbo_basic.py
│           ├── 02_production_server.py
│           ├── 03_multi_lora.py
│           ├── 04_image_to_image.py
│           ├── 05_controlnet_depth.py
│           ├── 06_live_preview.py
│           ├── 07_teacache_speedup.py
│           ├── 08_metadata_reproducibility.py
│           ├── 09_benchmark_harness.py
│           └── 10_commercial_safe_pipeline.py
│
├── upload/                           ← reference (v1.4 baseline, preserved unchanged)
│   └── comfyui-set-mac-SKILL.md         (v1.4 SKILL.md — for diff comparison with v1.5)
│
└── research/                         ← research audit trail (intermediate artifacts)
    └── notes/                          (14 clean-text extracts of primary sources)
        ├── apple_mlx_m5.txt
        ├── bfl_flux2.txt
        ├── comfyui_mlx_nodes.txt
        ├── diffusionkit.txt
        ├── draw_things_metal_fa.txt
        ├── fibo_mlx.txt
        ├── flux2_repo.txt
        ├── flux2_swift_mlx.txt
        ├── ideogram4_mlx_q4.txt
        ├── m4pro_benchmark.txt
        ├── mflux_pypi.txt
        ├── mflux_readme.txt
        ├── qwen_image_mlx.txt
        └── zimage_mlx_reddit.txt
```

**Excluded from this snapshot** (for size and privacy):
- `.git/` — version control history (internal)
- `.env` — credentials (must never be shipped)
- `skills/` — internal skill files (61 MB, not relevant to Mac testing)
- `tool-results/` — internal tool output captures
- `research/raw/` — 56 raw JSON search results (332 KB, intermediate)
- `research/pages/` — 14 raw HTML page reads (3.4 MB, intermediate)

---

## Mac prerequisites (verify before running anything)

```bash
# 1. Verify Apple Silicon
uname -m
# Expected: arm64

# 2. Verify macOS version (Tahoe 26.x or later; 26.2+ for M5 Neural Accelerator)
sw_vers

# 3. Install Homebrew if missing
which brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 4. Install Python 3.12 (recommended)
brew install python@3.12

# 5. Install uv (required for the companion scripts — they use inline uv dependencies)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 6. Verify uv
uv --version
```

---

## Quick start on Mac (5 minutes to first image)

```bash
# 1. Extract the snapshot
cd ~
tar -xzf /path/to/comfyui-mac-workspace-snapshot-2026-06-30.tar.gz
cd my-project

# 2. Read the v1.5 SKILL.md (the main install guide)
less download/comfyui-set-mac-SKILL.md

# 3. Run the first companion script (downloads Z-Image Turbo, ~11 GB, then generates one image)
uv run download/research/scripts/01_z_image_turbo_basic.py
# Output: puffin.png in current directory

# 4. Run the commercial-safe pipeline (Apache 2.0 license, ~5 GB FLUX.2 klein 4B)
uv run download/research/scripts/10_commercial_safe_pipeline.py
# Output: commercial_mug.png

# 5. Benchmark your hardware
uv run download/research/scripts/09_benchmark_harness.py
# Output: timing + RSS table for each model
```

The first run of any script will download model weights from HuggingFace (10–60 GB depending on model) and may take several minutes. Subsequent runs use the cached weights.

---

## Recommended testing order

For comprehensive validation of the v1.5 stack on your Mac:

1. **Read** `download/comfyui-set-mac-SKILL.md` — start with the "Critical v1.5 Update Notices" section
2. **Run** `01_z_image_turbo_basic.py` — verifies mflux install + Python API
3. **Run** `10_commercial_safe_pipeline.py` — verifies FLUX.2 klein 4B (Apache 2.0, safest)
4. **Run** `09_benchmark_harness.py` — captures your hardware's baseline numbers
5. **Run** `02_production_server.py` — verifies FastAPI server pattern
6. **Run** `07_teacache_speedup.py` — verifies TeaCache step-skipping (30-50% speedup)
7. **Read** `download/research/mlx-image-gen-mac-2026.md` — full 11.5k word research report with 49 cited sources

---

## Companion scripts license

All 10 companion scripts in `download/research/scripts/` are **MIT-licensed** — free for any use.

The models they invoke have their own licenses. See **Section 12** of the v1.5 SKILL.md (`download/comfyui-set-mac-SKILL.md`) for the strict Apache 2.0 vs Non-Commercial audit.

---

## Workspace provenance

- **Built:** 2026-06-30 (Singapore timezone)
- **Research methodology:** 56 web searches across 6 workstreams + 14 deep page reads of primary sources
- **Source baseline:** `upload/comfyui-set-mac-SKILL.md` (v1.4, 1,442 lines)
- **Updated to:** `download/comfyui-set-mac-SKILL.md` (v1.5, 2,917 lines, 14,033 words)
- **Research report:** `download/research/mlx-image-gen-mac-2026.md` (11,570 words, 49 cited sources)

---

## Verify the snapshot after extraction

```bash
cd my-project

# Verify file count (should match MANIFEST.txt)
find . -type f | wc -l

# Verify no .env or .git leaked in
ls -la .env .git 2>&1 | head
# Expected: "No such file or directory" for both

# Verify the v1.5 SKILL.md is intact (should be 2,917 lines)
wc -l download/comfyui-set-mac-SKILL.md

# Verify all 10 companion scripts are present
ls download/research/scripts/0*.py download/research/scripts/10_*.py | wc -l
# Expected: 10

# Compare with MANIFEST.txt
diff <(find . -type f | sort) <(grep -oE 'my-project/.*' MANIFEST.txt | sed 's|^my-project/||' | sort) || true
```

If any verification fails, the snapshot is corrupt — re-download from the source.

---

## Need help?

- **Install issues:** See `download/comfyui-set-mac-SKILL.md` Section 9 (Troubleshooting & Pitfalls) — 20 pitfalls with solutions
- **License questions:** See `download/comfyui-set-mac-SKILL.md` Section 12 (License Audit)
- **Model selection:** See `download/comfyui-set-mac-SKILL.md` Model Landscape section
- **Production deployment:** See `download/comfyui-set-mac-SKILL.md` Section 11 (Production Deployment Patterns)
- **Deep research context:** See `download/research/mlx-image-gen-mac-2026.md` (11.5k words, 49 sources)

---

*Workspace snapshot v1.5 — built 2026-06-30. Validated against Comfy-Org, MLXBits, SceneWorks, filipstrand/mflux, black-forest-labs/flux2, MLX community, briaai, and Apple ML Research sources.*
