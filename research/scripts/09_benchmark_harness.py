#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mflux", "psutil"]
# ///
"""
Benchmark harness for running all models with consistent metrics

Section reference: Report §8.3 — Suggested follow-up research
Expected runtime on M4 Pro 24 GB: ~10-15 minutes total for 3 models x 3 runs each
Tested against: mflux 0.18.0, MLX 0.31.2, Python 3.12

Source: /home/z/my-project/download/research/mlx-image-gen-mac-2026.md
"""

"""Benchmark harness for mflux models.

Runs each model 3 times, reports mean/min/max wall-clock time and
peak RSS. Adjust MODEL_CONFIGS to benchmark different models.
"""
import gc
import statistics
import time
from dataclasses import dataclass
from typing import Callable

import psutil


@dataclass
class ModelConfig:
    name: str
    loader: Callable
    prompt: str
    steps: int
    width: int = 1024
    height: int = 1024


def bench(model_cfg: ModelConfig, runs: int = 3) -> dict:
    """Run a model `runs` times and return timing/memory stats."""
    # Warmup run (not counted) — model loads weights on first call
    print(f"  Warming up {model_cfg.name}...")
    model = model_cfg.loader()
    _ = model.generate_image(
        prompt=model_cfg.prompt, seed=42,
        num_inference_steps=model_cfg.steps,
        width=model_cfg.width, height=model_cfg.height,
    )

    timings = []
    peak_rss = []
    for i in range(runs):
        print(f"  Run {i+1}/{runs}...")
        proc = psutil.Process()
        rss_before = proc.memory_info().rss
        t0 = time.perf_counter()
        _ = model.generate_image(
            prompt=model_cfg.prompt, seed=42+i,
            num_inference_steps=model_cfg.steps,
            width=model_cfg.width, height=model_cfg.height,
        )
        elapsed = time.perf_counter() - t0
        rss_after = proc.memory_info().rss
        timings.append(elapsed)
        peak_rss.append(rss_after / 1e9)  # GB
        print(f"    {elapsed:.2f}s, RSS={rss_after/1e9:.2f} GB")

    # Cleanup
    del model
    gc.collect()

    return {
        "model": model_cfg.name,
        "runs": runs,
        "mean_time_s": statistics.mean(timings),
        "min_time_s": min(timings),
        "max_time_s": max(timings),
        "stdev_time_s": statistics.stdev(timings) if len(timings) > 1 else 0,
        "mean_rss_gb": statistics.mean(peak_rss),
        "max_rss_gb": max(peak_rss),
    }


def main() -> None:
    # Adjust these to match what you have downloaded locally
    from mflux.models.z_image import ZImageTurbo
    # from mflux.models.flux1 import Flux1
    # from mflux.models.flux2 import Flux2Klein4B

    configs = [
        ModelConfig(
            name="z-image-turbo-int8",
            loader=lambda: ZImageTurbo(quantize=8),
            prompt="cinematic mountain landscape, golden hour",
            steps=9,
        ),
        # Add more configs as you download models:
        # ModelConfig(
        #     name="flux1-dev-int8",
        #     loader=lambda: Flux1(variant="dev", quantize=8),
        #     prompt="cinematic mountain landscape, golden hour",
        #     steps=20,
        # ),
        # ModelConfig(
        #     name="flux2-klein-4b-int8",
        #     loader=lambda: Flux2Klein4B(variant="distilled", quantize=8),
        #     prompt="cinematic mountain landscape, golden hour",
        #     steps=4,
        # ),
    ]

    results = []
    for cfg in configs:
        print(f"\nBenchmarking: {cfg.name}")
        try:
            results.append(bench(cfg, runs=3))
        except Exception as e:
            print(f"  FAILED: {e}")
            results.append({"model": cfg.name, "error": str(e)})

    print("\n=== Results ===")
    for r in results:
        if "error" in r:
            print(f"{r['model']}: ERROR {r['error']}")
        else:
            print(
                f"{r['model']}: "
                f"mean={r['mean_time_s']:.2f}s "
                f"(min={r['min_time_s']:.2f}, max={r['max_time_s']:.2f}, "
                f"stdev={r['stdev_time_s']:.2f}), "
                f"peak RSS={r['max_rss_gb']:.2f} GB"
            )


if __name__ == "__main__":
    main()
