#!/bin/bash
# Deep-read critical primary sources via page_reader
# Throttled: 2 concurrent, 1s delay between pairs

set -u
mkdir -p /home/z/my-project/research/pages
cd /home/z/my-project/research/pages

read_page() {
  local key="$1"
  local url="$2"
  if [ -f "${key}.json" ] && [ -s "${key}.json" ]; then
    echo "SKIP (exists): $key"
    return 0
  fi
  z-ai function -n page_reader -a "{\"url\": \"$url\"}" -o "${key}.json" 2>"${key}.err"
  local rc=$?
  if [ $rc -eq 0 ] && [ -s "${key}.json" ]; then
    echo "OK: $key ($(wc -c < ${key}.json) bytes)"
  else
    echo "FAIL: $key (rc=$rc)"
  fi
}

PAIRS=(
  "apple_mlx_m5|https://machinelearning.apple.com/research/exploring-llms-mlx-m5"
  "mflux_readme|https://github.com/filipstrand/mflux"
  "diffusionkit|https://github.com/argmaxinc/DiffusionKit"
  "bfl_flux2|https://bfl.ai/blog/flux-2"
  "flux2_repo|https://github.com/black-forest-labs/flux2"
  "ideogram4_mlx_q4|https://huggingface.co/MLXBits/ideogram-4-mlx-q4"
  "comfyui_mlx_nodes|https://comfy.icu/extension/thoddnn__ComfyUI-MLX"
  "zimage_mlx_reddit|https://www.reddit.com/r/StableDiffusion/comments/1pkkhn1/converted_zimage_to_mlx_apple_silicon"
  "mflux_pypi|https://pypi.org/project/mflux/0.14.0"
  "qwen_image_mlx|https://huggingface.co/mlx-community/Qwen-Image-2512-4bit"
  "fibo_mlx|https://huggingface.co/briaai/Fibo-mlx-4bit"
  "flux2_swift_mlx|https://github.com/VincentGourbin/flux-2-swift-mlx"
  "draw_things_metal_fa|https://engineering.drawthings.ai/p/metal-flashattention-2-0-pushing-forward-on-device-inference-training-on-apple-silicon-fe8aac1ab23c"
  "m4pro_benchmark|https://www.heyuan110.com/posts/ai/2026-02-15-mac-mini-local-image-generation"
)

for ((i=0; i<${#PAIRS[@]}; i+=2)); do
  pair1="${PAIRS[$i]}"
  key1="${pair1%%|*}"
  url1="${pair1#*|}"
  read_page "$key1" "$url1" &
  
  if [ $((i+1)) -lt ${#PAIRS[@]} ]; then
    pair2="${PAIRS[$((i+1))]}"
    key2="${pair2%%|*}"
    url2="${pair2#*|}"
    read_page "$key2" "$url2" &
  fi
  
  wait
  sleep 1
done

echo ""
echo "=== Deep reads complete ==="
ls -lh /home/z/my-project/research/pages/*.json | awk '{print $5, $9}'
