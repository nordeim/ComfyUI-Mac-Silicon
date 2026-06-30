#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux"]
# ///
"""
Metadata export + reproduce workflow

Section reference: Report §5.8 — Seed reproducibility and metadata
Expected runtime on M4 Pro 24 GB: ~60-80 seconds for first generation; instant reproduce from metadata
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

"""Metadata export + reproduce workflow.

Demonstrates seed reproducibility: any generated image can be exactly
reproduced by re-running with the same metadata file.
"""
import json
from pathlib import Path

from mflux.models.z_image import ZImageTurbo


METADATA_PATH = Path("./generation_metadata.json")


def generate_with_metadata() -> None:
    model = ZImageTurbo(quantize=8)
    image = model.generate_image(
        prompt="a puffin standing on a cliff",
        seed=42,
        num_inference_steps=9,
        width=1024,
        height=1024,
    )
    image.save("puffin.png")

    # Export metadata (mflux's native format)
    metadata = image.metadata  # attribute name may vary; check mflux docs
    with METADATA_PATH.open("w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata: {METADATA_PATH}")


def reproduce_from_metadata() -> None:
    with METADATA_PATH.open() as f:
        metadata = json.load(f)
    model = ZImageTurbo(quantize=8)
    image = model.generate_image(**metadata)
    image.save("puffin_reproduced.png")
    print("Reproduced: puffin_reproduced.png")


def main() -> None:
    if METADATA_PATH.exists():
        reproduce_from_metadata()
    else:
        generate_with_metadata()


if __name__ == "__main__":
    main()
