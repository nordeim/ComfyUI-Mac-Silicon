#!/bin/bash
# WS-C (Quantization), WS-D (Benchmarks), WS-E (Custom Code) searches
# Throttled: 2 concurrent, 1s delay between pairs

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
  # WS-C: Quantization
  "ws_c_01|MLX 4-bit quantization diffusion model Apple Silicon"
  "ws_c_02|MLX 8-bit quantization Flux image generation"
  "ws_c_03|MLX 2-bit 3-bit quantization image model"
  "ws_c_04|mflux quantization Q4 Q8 command line options"
  "ws_c_05|Apple MX format quantization MLX 2026"
  "ws_c_06|MLX mixed precision diffusion inference"
  "ws_c_07|MLX LoRA multi-LoRA loading image generation"
  "ws_c_08|MLX memory offload Apple Silicon unified memory"
  # WS-D: Benchmarks
  "ws_d_01|mflux benchmark M1 M2 M3 M4 Apple Silicon"
  "ws_d_02|Flux MLX Apple Silicon benchmark steps per second"
  "ws_d_03|Draw Things vs mflux vs ComfyUI benchmark Mac"
  "ws_d_04|Ideogram 4 MLX performance M4 Pro Max"
  "ws_d_05|Apple Silicon diffusion benchmark 2026 throughput"
  "ws_d_06|Z-Image Turbo MLX benchmark Apple Silicon"
  "ws_d_07|Qwen-Image MLX benchmark Apple Silicon speed"
  "ws_d_08|FLUX.2 MLX Apple Silicon benchmark 2026"
  # WS-E: Custom Code
  "ws_e_01|mflux python API programmatic usage example"
  "ws_e_02|MLX diffusion model python code tutorial"
  "ws_e_03|ComfyUI custom node MLX backend tutorial"
  "ws_e_04|MLX image generation production deployment"
  "ws_e_05|Apple MLX server image generation API"
  "ws_e_06|DiffusionKit Apple official repository"
  "ws_e_07|FLUX.2 MLX port mflux support"
  "ws_e_08|MLX FastAttention image generation kernel"
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
echo "=== WS-C, WS-D, WS-E complete ==="
ls -lh /home/z/my-project/research/raw/ws_[cde]_*.json | awk '{print $5, $9}'
