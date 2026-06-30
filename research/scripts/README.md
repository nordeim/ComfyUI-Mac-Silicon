# MLX Image Generation Companion Scripts

Companion scripts for the research report at `../mlx-image-gen-mac-2026.md`.

## Quick start

Each script is a self-contained `uv run --script` Python file with inline
dependencies. No virtualenv setup required — just `uv` (which ships with
recent Python installs).

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Run any script
uv run 01_z_image_turbo_basic.py
```

The first run downloads the model from HuggingFace (10–60 GB depending on
model) and may take several minutes. Subsequent runs use the cached weights.

## Script index

| # | Script | Section | Purpose |
|---|---|---|---|
| 01 | `01_z_image_turbo_basic.py` | §5.1 | Minimal mflux Python API — Z-Image Turbo int8 |
| 02 | `02_production_server.py` | §5.2 | FastAPI OpenAI-compatible image server |
| 03 | `03_multi_lora.py` | §5.3 | Multi-LoRA loading with scales |
| 04 | `04_image_to_image.py` | §5.4 | Image-to-image editing |
| 05 | `05_controlnet_depth.py` | §5.5 | ControlNet Canny + Depth Pro pipeline |
| 06 | `06_live_preview.py` | §5.6 | Live preview with mlx-taef TAE decoder |
| 07 | `07_teacache_speedup.py` | §5.7 | TeaCache step-skipping (30-50% speedup) |
| 08 | `08_metadata_reproducibility.py` | §5.8 | Metadata export + reproduce workflow |
| 09 | `09_benchmark_harness.py` | §8.3 | Benchmark harness for measuring your hardware |
| 10 | `10_commercial_safe_pipeline.py` | §7.3 | Commercial-safe pipeline (Apache 2.0) |

## Requirements

- **Hardware**: Apple Silicon M-series (M1 minimum, M4 Pro 24 GB+ recommended)
- **OS**: macOS 14+ (macOS 26.2+ required for M5 Neural Accelerator support)
- **Python**: 3.10+ (3.12 recommended)
- **uv**: latest
- **Disk**: 50+ GB free for model weights

## Test environment

These scripts were authored against:
- mflux 0.18.0 (Jun 7, 2026)
- MLX 0.31.2
- Python 3.12

API signatures (e.g., `ZImageTurbo(quantize=8)`) match the mflux README as
of 30 Jun 2026. If you hit a `TypeError` on model construction, check the
mflux changelog for API changes — the library is actively developed.

## License

These scripts are MIT-licensed. The models they invoke have their own
licenses — see Section 7.3 of the report for the strict license audit.

## See also

- Research report: `../mlx-image-gen-mac-2026.md`
- Existing SKILL.md (baseline): `/home/z/my-project/upload/comfyui-set-mac-SKILL.md`
- mflux project: https://github.com/filipstrand/mflux
