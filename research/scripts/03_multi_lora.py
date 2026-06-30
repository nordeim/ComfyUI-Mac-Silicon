#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux"]
# ///
"""
Multi-LoRA loading with scales (FLUX.1 dev example)

Section reference: Report §5.3 — Multi-LoRA loading
Expected runtime on M4 Pro 24 GB: ~30-60 seconds for 1024x1024 at 20 steps with FLUX.1 dev int8
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

"""Multi-LoRA demonstration.

Requires two LoRA files at ./loras/style_v01.safetensors and
./loras/detail_v02.safetensors. Adjust paths and scales as needed.
"""
from pathlib import Path

from mflux.models.flux1 import Flux1


def main() -> None:
    lora_dir = Path("./loras")
    lora_paths = [
        str(lora_dir / "style_v01.safetensors"),
        str(lora_dir / "detail_v02.safetensors"),
    ]
    for p in lora_paths:
        if not Path(p).exists():
            raise FileNotFoundError(
                f"LoRA file not found: {p}. Place your LoRAs in ./loras/"
            )

    # 8-bit quantization — ~13 GB on disk
    model = Flux1(variant="dev", quantize=8)
    image = model.generate_image(
        prompt="cyberpunk samurai, neon rain, cinematic, highly detailed",
        seed=42,
        num_inference_steps=20,
        width=1024,
        height=1024,
        lora_paths=lora_paths,
        lora_scales=[0.7, 0.4],  # style dominant, detail subtle
    )
    image.save("cyber_samurai.png")
    print("Saved: cyber_samurai.png")


if __name__ == "__main__":
    main()
