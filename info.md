# Running Ideogram 4.0 & Krea 2 on Apple M4 MacBooks: The Complete Guide (June 2026)

This guide provides a meticulously researched, up-to-date workflow for running the latest state-of-the-art image models on Apple Silicon M4 MacBooks. It verifies recent ecosystem developments, corrects previous assumptions regarding model availability, and provides exact commands for native MLX inference.

## 1. Executive Summary & Model Landscape
The local AI image generation landscape shifted dramatically in June 2026 with the open-weight release of two major foundation models:

* **Ideogram 4.0:** Released on June 3, 2026, this is Ideogram's first open-weight text-to-image model. It features a 9.3B parameter single-stream DiT architecture. Unlike older models that rely on CLIP or T5, Ideogram 4 uses the Qwen3-VL-8B-Instruct vision-language model as its text encoder. The model was trained on structured JSON captions rather than free text, unlocking precise bounding-box layout control.
* **Krea 2:** This is an open-source foundation model family designed for high aesthetic quality and stylistic diversity. It ships as two distinct models: Krea 2 RAW for full-step sampling, and Krea 2 Turbo for fast inference. Krea 2 Turbo is an 8-step distilled checkpoint that operates completely CFG-free with a guidance scale of 0.

Both models can be run locally on Apple M4 MacBooks using the MLX framework or native GUIs like ComfyUI and Draw Things.

---

## 2. Hardware Considerations for Apple M4
Running 9B+ parameter models with large vision-language encoders requires careful memory management. Apple's Unified Memory Architecture (UMA) allows the GPU to access system RAM, but you must stay within physical limits to avoid SSD swap thrashing.

| Mac Chip | Unified Memory | Recommended Model Variant | Expected Performance |
| :--- | :--- | :--- | :--- |
| **M4 (Base)** | 16 GB | `MLXBits/ideogram-4-mlx-q4` (4-bit) | Fits in RAM (~15GB footprint). Good for 1024x1024. |
| **M4 Pro** | 24 GB+ | `MLXBits/ideogram-4-mlx-q8` (8-bit) or Krea 2 Turbo | Excellent headroom. Allows larger batches or 2K generation. |
| **M4 Max** | 36 GB+ | FP8 variants or Full Precision | Desktop-class performance; minimal offloading required. |

---

## 3. Method 1: Native MLX via `mflux` (Recommended)
The `mflux` library provides a line-by-line MLX port of state-of-the-art generative image models. It is the most efficient way to run these models on Apple Silicon.

### Step 1: Install Dependencies
Ensure you have Python 3.10+ and install `mflux` via pip:
```bash
pip install mflux huggingface_hub
```

### Step 2: Download the MLX Weights
The community organization MLXBits maintains an "Ideogram 4 on Apple MLX" collection on Hugging Face. The `MLXBits/ideogram-4-mlx-q4` repository is quantized to approximately 15 GB on disk, making it the smallest Ideogram 4 build available. It requires an Apple Silicon Mac with at least 16 GB of unified memory. For Krea 2, the `SceneWorks/krea-2-turbo-mlx` repository provides an on-device, Apple-MLX-ready repack of the Turbo checkpoint.

```bash
# Download Ideogram 4 (4-bit for 16GB Macs)
hf download MLXBits/ideogram-4-mlx-q4 --local-dir ./ideogram-4-mlx-q4

# Download Krea 2 Turbo (MLX)
hf download SceneWorks/krea-2-turbo-mlx --local-dir ./krea-2-turbo-mlx
```

### Step 3: Generate Images
You can download the weights and point the `mflux-generate-ideogram4` command at the local directory. The `mflux` tool auto-detects the precision directly from the `split_model.json` file without needing manual quantization flags.

**For Ideogram 4:**
```bash
mflux-generate-ideogram4 \
 --model-path ./ideogram-4-mlx-q4 \
 --prompt "A cinematic shot of a cyberpunk cityscape" \
 --steps 20 --width 1024 --height 1024 \
 --output ideogram_out.png
```

**For Krea 2 Turbo:**
Note that Krea 2 Turbo is CFG-free, so you must set guidance to 0 and use roughly 8 steps.
```bash
mflux-generate \
 --model-path ./krea-2-turbo-mlx \
 --prompt "Aesthetic film photography, grainy, neon lights" \
 --steps 8 --guidance 0.0 --width 1024 --height 1024 \
 --output krea_out.png
```

---

## 4. Method 2: Visual Node Editing with ComfyUI
ComfyUI introduced day-0 native support for Ideogram 4.0 right at launch. The official ComfyUI organization provides repackaged model files at the `Comfy-Org/Ideogram-4` repository for easy downloading.

1. **Update ComfyUI:** Ensure you are on the latest version to access the native Ideogram V4 nodes.
2. **Download Models:** Follow the notes in the official workflow to download the Qwen3-VL encoder and the DiT weights into your `ComfyUI/models/` directories.
3. **JSON Prompting:** The Ideogram V4 node already contains a default structured JSON prompt which you can modify or replace with plain text.
4. **Krea 2 Workflows:** ComfyUI also features dedicated workflows for Krea 2, allowing you to train LoRAs on the RAW base model and run inference on the Turbo distilled variant.

---

## 5. Method 3: Draw Things App (Easiest GUI)
For users who prefer a standalone macOS application, Draw Things offers native support. The Draw Things app supports Ideogram 4 by importing the `ideogram-ai/ideogram-4-nf4-diffusers` pipeline.

1. Download **Draw Things** from the Mac App Store.
2. Open the Model Manager and search for "Ideogram 4".
3. The app will handle the Metal Performance Shaders (MPS) optimization and memory offloading automatically.
4. Paste your JSON prompt into the text field and hit generate.

---

## 6. The JSON Prompt Workflow (Ideogram 4 Specific)
Because Ideogram 4 was trained on structured JSON captions, using plain text will yield inferior layout control. To unlock bounding-box placement and color palette conditioning, use the following schema:

```json
{
 "high_level_description": "A futuristic workspace with a glowing monitor.",
 "style_description": {
 "aesthetics": "Cyberpunk, neon-lit, high contrast.",
 "lighting": "Volumetric blue and magenta rim lighting.",
 "color_palette": ["#00FFFF", "#FF00FF", "#1A1A1A"]
 },
 "compositional_deconstruction": {
 "background": "Dark server room with blinking LEDs.",
 "elements": [
 {
 "type": "obj",
 "bbox": [200, 300, 800, 700],
 "desc": "A sleek curved monitor displaying code."
 },
 {
 "type": "text",
 "bbox": [250, 400, 750, 500],
 "text": "SYSTEM ONLINE",
 "desc": "Bright green terminal font."
 }
 ]
 }
}
```
You can generate these JSON structures automatically using the Ideogram API's "Magic Prompt" endpoint or by prompting a local LLM like Qwen2.5-7B to output this exact schema.

---

## 7. Troubleshooting & Optimization

* **Out of Memory (OOM) on 16GB Macs:** The combination of the 9.3B DiT and the 8B Qwen3-VL encoder is heavy. If you experience OOM errors with the 8-bit MLX models, you must use the `MLXBits/ideogram-4-mlx-q4` variant.
* **Krea 2 Turbo Quality Issues:** If your Krea 2 Turbo images look noisy or burnt, ensure your CFG (Classifier-Free Guidance) is set exactly to `0.0` and your steps are around `8`. Using standard CFG values (like 7.0) with Turbo models will destroy the image.
* **MPS vs. MLX:** While PyTorch's MPS backend can run these models via `diffusers`, it is significantly slower and lacks the native quantization support of Apple's MLX framework. Always prefer `mflux` or native app integrations for M-series chips.
* **Thermal Throttling:** The base M4 MacBook Air is fanless. Extended generation sessions (especially at 2K resolutions) may cause the chip to throttle. The M4 Pro and Max MacBook Pros with active cooling will sustain peak generation speeds indefinitely.

---

## Validation

This guide was audited on 2026-07-01 by Z.ai as part of the ComfyUI-Mac-Silicon workspace audit. The full per-claim validation report — with live evidence URLs replacing the previous anonymous `[[N]]` citations — is at [`ComfyUI-Mac-Silicon-Validation-Report.md`](ComfyUI-Mac-Silicon-Validation-Report.md). The remediation plan and post-remediation re-audit are at [`ComfyUI-Mac-Silicon-Remediation-Plan.md`](ComfyUI-Mac-Silicon-Remediation-Plan.md) and [`ComfyUI-Mac-Silicon-Post-Remediation-Report.md`](ComfyUI-Mac-Silicon-Post-Remediation-Report.md).

> The previous "validation report" section that used anonymous `[[N]]` citations has been removed. Those citations did not resolve to any URL or bibliography in the workspace and were structurally indistinguishable from hallucinated validation. The underlying content of this guide (sections 1–7 above) is accurate on its own merits — see the validation report for the live evidence.

