#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux"]
# ///
"""
Image-to-image editing with denoise control

Section reference: Report §5.4 — Image-to-image and editing
Expected runtime on M4 Pro 24 GB: ~30-60 seconds for 1024x1024 at 20 steps
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

"""Image-to-image editing.

Requires an input image at ./input_photo.png.
"""
from pathlib import Path

from mflux.models.flux1 import Flux1


def main() -> None:
    input_path = Path("./input_photo.png")
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input image not found: {input_path}. Place your image there."
        )

    model = Flux1(variant="dev", quantize=8)
    image = model.generate_image(
        prompt="transform this photo into a watercolor painting, soft brush strokes",
        seed=42,
        num_inference_steps=20,
        width=1024,
        height=1024,
        image_path=str(input_path),
        denoise=0.6,  # 0.0 = identity, 1.0 = full regeneration
    )
    image.save("watercolor.png")
    print("Saved: watercolor.png")


if __name__ == "__main__":
    main()
