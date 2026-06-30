#!/bin/bash
# Gap-filling searches: FLUX.2 variants, FIBO, Chroma, M5 chip, MLX 0.31+

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

PAIRS=(
  "ws_f_01|FLUX.2 klein dev pro variants model size parameters"
  "ws_f_02|FLUX.2 MLX port mflux Apple Silicon 2026"
  "ws_f_03|FIBO image model mflux what is"
  "ws_f_04|Chroma image generation model 2026"
  "ws_f_05|Apple M5 chip release date MLX Neural Accelerator"
  "ws_f_06|MLX 0.31 0.32 release notes 2026 image generation"
  "ws_f_07|GLM-Image MLX Apple Silicon port 2026"
  "ws_f_08|Qwen-Image-2512 architecture parameters text encoder"
  "ws_f_09|Ideogram 4 MLX bf16 support Apple Silicon"
  "ws_f_10|FluxForge Studio macOS app FLUX.2 MLX"
  "ws_f_11|comfyui-mlx thoddnn supported models features"
  "ws_f_12|mflux Python API programmatic image generation code"
)

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
echo "=== Gap-filling searches complete ==="
ls -lh /home/z/my-project/research/raw/ws_f_*.json | awk '{print $5, $9}'
