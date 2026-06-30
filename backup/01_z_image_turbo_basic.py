#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux"]
# ///
"""
Minimal mflux Python API usage — Z-Image Turbo int8, single image

Section reference: Report §5.1 — Bare mflux Python API
Expected runtime on M4 Pro 24 GB: ~60-80 seconds for 1024x1024 at 9 steps
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

from mflux.models.z_image import ZImageTurbo

def main() -> None:
    # 8-bit group quantization — ~11 GB on disk, ~12 GB RSS
    model = ZImageTurbo(quantize=8)
    image = model.generate_image(
        prompt="A puffin standing on a cliff at golden hour, cinematic",
        seed=42,
        num_inference_steps=9,
        width=1280,
        height=500,
    )
    image.save("puffin.png")
    print("Saved: puffin.png")

if __name__ == "__main__":
    main()
