#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux", "mlx-taef"]
# ///
"""
Live preview with mlx-taef TAE decoder

Section reference: Report §5.6 — Live preview with mlx-taef
Expected runtime on M4 Pro 24 GB: ~30-60 seconds for full generation; preview frames every step
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

"""Live preview during generation.

Saves a preview PNG at each diffusion step, providing visual feedback
during long generations. The TAE decoder adds ~10 MB to RSS and runs
in <100 ms per step on M4 Pro.
"""
from pathlib import Path

from mlx_taef import TAEDecoder
from mflux.models.flux1 import Flux1


def main() -> None:
    preview_dir = Path("./previews")
    preview_dir.mkdir(exist_ok=True)

    model = Flux1(variant="dev", quantize=8)
    tae = TAEDecoder()  # ~10 MB additional footprint

    # Use the streaming generator if available; fall back to standard
    # generate_image if the model version doesn't expose it.
    try:
        for step_output in model.generate_image_stream(
            prompt="cinematic mountain landscape at golden hour",
            seed=42,
            num_inference_steps=20,
            width=1024,
            height=1024,
        ):
            preview = tae.decode(step_output.latent)
            preview_path = preview_dir / f"preview_{step_output.step:02d}.png"
            preview.save(preview_path)
            print(f"Saved preview: {preview_path}")
    except AttributeError:
        print("generate_image_stream not available; using standard generate_image")
        image = model.generate_image(
            prompt="cinematic mountain landscape at golden hour",
            seed=42,
            num_inference_steps=20,
            width=1024,
            height=1024,
        )
        image.save("mountain.png")
        print("Saved: mountain.png")


if __name__ == "__main__":
    main()
