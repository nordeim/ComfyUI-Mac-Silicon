#!/bin/bash
# Run WS-A (Model Landscape) and WS-B (MLX Runtime Survey) searches in parallel.
# Each search writes to /home/z/my-project/research/raw/<key>.json

set -u
mkdir -p /home/z/my-project/research/raw
cd /home/z/my-project/research/raw

# Helper: run a search in the background and save to <key>.json
run_search() {
  local key="$1"
  local query="$2"
  local num="${3:-10}"
  z-ai function -n web_search -a "{\"query\": \"$query\", \"num\": $num}" -o "${key}.json" 2>"${key}.err" &
}

# ---------- WS-A: Model Landscape (Jan-Jun 2026) ----------
run_search ws_a_01 "latest open weight text-to-image diffusion model 2026"
run_search ws_a_02 "Flux 2 Black Forest Labs release 2026"
run_search ws_a_03 "Qwen-Image MLX Apple Silicon 2026"
run_search ws_a_04 "Nano Banana image model MLX"
run_search ws_a_05 "Ideogram 4 alternative open weight model 2026"
run_search ws_a_06 "Stable Diffusion 4 Stability AI 2026"
run_search ws_a_07 "Krea 2 vs Ideogram 4 vs Z-Image benchmark 2026"
run_search ws_a_08 "HuggingFace trending diffusion models 2026"
run_search ws_a_09 "Gemini image open weights release 2026"
run_search ws_a_10 "Apple MLX image generation 2026 new models"

# ---------- WS-B: MLX Runtime Survey ----------
run_search ws_b_01 "mflux GitHub Apple Silicon MLX image generation"
run_search ws_b_02 "ComfyUI MLX custom node backend 2026"
run_search ws_b_03 "apple/mlx-examples stable diffusion flux"
run_search ws_b_04 "Draw Things MLX backend native metal 2026"
run_search ws_b_05 "ComfyUI Apple Silicon MPS vs MLX performance 2026"
run_search ws_b_06 "ml-explore mlx flux image generation"
run_search ws_b_07 "comfyui-mlx github repository 2026"
run_search ws_b_08 "MLX diffusion transformer runtime 2026"
run_search ws_b_09 "Apple Silicon native metal image generation framework"
run_search ws_b_10 "Diffusers MLX backend Apple 2026"

# Wait for all parallel searches to complete
wait
echo "=== All WS-A and WS-B searches complete ==="
ls -lh /home/z/my-project/research/raw/
