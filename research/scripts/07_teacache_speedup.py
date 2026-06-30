#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux", "mlx-teacache"]
# ///
"""
TeaCache step-skipping for 30-50% speedup

Section reference: Report §5.7 — TeaCache step-skipping with mlx-teacache
Expected runtime on M4 Pro 24 GB: ~20-40 seconds (vs 30-60 without TeaCache) — 30-50% speedup
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

"""TeaCache step-skipping for FLUX generation.

TeaCache reuses computation from previous steps when the residual is
small, giving 30-50% speedup with minimal quality loss. Tune the
threshold: 0.10 = conservative (high quality), 0.20 = aggressive
(max speed).
"""
from mlx_teacache import TeaCacheWrapper
from mflux.models.flux1 import Flux1


def main() -> None:
    model = Flux1(variant="dev", quantize=8)
    model = TeaCacheWrapper(model, threshold=0.20)

    image = model.generate_image(
        prompt="cinematic mountain landscape, golden hour, dramatic clouds",
        seed=42,
        num_inference_steps=20,  # effective steps ~12-14 with TeaCache
        width=1024,
        height=1024,
    )
    image.save("mountain_teacache.png")
    print("Saved: mountain_teacache.png")


if __name__ == "__main__":
    main()
