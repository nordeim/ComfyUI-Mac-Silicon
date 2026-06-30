#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux"]
# ///
"""
ControlNet Canny + Depth Pro pipeline

Section reference: Report §5.5 — ControlNet and depth conditioning
Expected runtime on M4 Pro 24 GB: ~5 seconds (depth extraction) + ~30-60 seconds (generation)
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

"""ControlNet Canny + Depth Pro pipeline.

Step 1: Extract depth map from input image using Apple's Depth Pro.
Step 2: Use depth as conditioning for FLUX.1 dev generation.

Requires input image at ./input.png.
"""
from pathlib import Path

from mflux.models.depth_pro import DepthPro
from mflux.models.flux1 import Flux1


def main() -> None:
    input_path = Path("./input.png")
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    # Step 1: Extract depth map (~5 seconds on M4 Pro)
    print("Step 1: Extracting depth map...")
    depth_model = DepthPro()
    depth_image = depth_model.generate_depth_map(image_path=str(input_path))
    depth_image.save("depth_map.png")
    print("Saved: depth_map.png")

    # Step 2: Use depth as conditioning
    print("Step 2: Generating with depth conditioning...")
    model = Flux1(variant="dev", quantize=8)
    image = model.generate_image(
        prompt="a portrait of a woman with dramatic lighting, cinematic, 50mm lens",
        seed=42,
        num_inference_steps=20,
        width=1024,
        height=1024,
        depth_path="depth_map.png",
        controlnet_strength=0.8,
    )
    image.save("portrait.png")
    print("Saved: portrait.png")


if __name__ == "__main__":
    main()
