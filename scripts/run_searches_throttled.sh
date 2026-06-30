#!/bin/bash
# Throttled parallel searches - max 2 concurrent, 1s delay between launches
# Avoids 429 rate limit errors

set -u
mkdir -p /home/z/my-project/research/raw
cd /home/z/my-project/research/raw

run_search() {
  local key="$1"
  local query="$2"
  local num="${3:-10}"
  if [ -f "${key}.json" ] && [ -s "${key}.json" ]; then
    echo "SKIP (exists): $key"
    return 0
  fi
  z-ai function -n web_search -a "{\"query\": \"$query\", \"num\": $num}" -o "${key}.json" 2>"${key}.err"
  local rc=$?
  if [ $rc -eq 0 ] && [ -s "${key}.json" ]; then
    echo "OK: $key"
  else
    echo "FAIL: $key (rc=$rc)"
  fi
}

# Process pairs sequentially with small wait between pairs
PAIRS=(
  "ws_a_01|latest open weight text-to-image diffusion model 2026"
  "ws_a_02|Flux 2 Black Forest Labs release 2026"
  "ws_a_03|Qwen-Image MLX Apple Silicon 2026"
  "ws_a_04|Nano Banana image model MLX"
  "ws_a_05|Ideogram 4 alternative open weight model 2026"
  "ws_a_06|Stable Diffusion 4 Stability AI 2026"
  "ws_a_07|Krea 2 vs Ideogram 4 vs Z-Image benchmark 2026"
  "ws_a_08|HuggingFace trending diffusion models 2026"
  "ws_a_09|Gemini image open weights release 2026"
  "ws_a_10|Apple MLX image generation 2026 new models"
  "ws_b_01|mflux GitHub Apple Silicon MLX image generation"
  "ws_b_02|ComfyUI MLX custom node backend 2026"
  "ws_b_03|apple/mlx-examples stable diffusion flux"
  "ws_b_04|Draw Things MLX backend native metal 2026"
  "ws_b_05|ComfyUI Apple Silicon MPS vs MLX performance 2026"
  "ws_b_06|ml-explore mlx flux image generation"
  "ws_b_07|comfyui-mlx github repository 2026"
  "ws_b_08|MLX diffusion transformer runtime 2026"
  "ws_b_09|Apple Silicon native metal image generation framework"
  "ws_b_10|Diffusers MLX backend Apple 2026"
)

# Run pairs (2 concurrent), wait, then next pair
for ((i=0; i<${#PAIRS[@]}; i+=2)); do
  pair1="${PAIRS[$i]}"
  key1="${pair1%%|*}"
  query1="${pair1#*|}"
  run_search "$key1" "$query1" &
  
  if [ $((i+1)) -lt ${#PAIRS[@]} ]; then
    pair2="${PAIRS[$((i+1))]}"
    key2="${pair2%%|*}"
    query2="${pair2#*|}"
    run_search "$key2" "$query2" &
  fi
  
  wait
  sleep 1
done

echo ""
echo "=== Final results ==="
ls -lh /home/z/my-project/research/raw/*.json | awk '{print $5, $9}'
