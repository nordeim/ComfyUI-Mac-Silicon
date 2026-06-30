---
name: comfyui-workflow-scaffold
description: >
  Create valid ComfyUI workflow JSON templates for Apple Silicon image generation.
  Use when: (1) Building a new ComfyUI workflow from scratch, (2) Converting a
  prompt-API format workflow to saved-graph format, (3) Adding Mac-compatible
  model loading nodes (Z-Image, FLUX.1/2, Krea 2, Ideogram 4, Qwen-Image,
  FIBO, ERNIE-Image), (4) Scaffolding LoRA/ControlNet/VAE nodes correctly,
  (5) Validating a workflow will run on Mac MPS/MLX backend, (6) User asks
  "create a workflow", "scaffold a ComfyUI template", "workflow JSON",
  "ComfyUI node graph", or "image generation workflow". Triggers on keywords:
  comfyui, workflow, node graph, json template, scaffold, image pipeline.
---

# ComfyUI Workflow Scaffold

Create production-grade ComfyUI workflow JSON templates tailored for Apple Silicon
(M-series) image generation. Every workflow must be valid ComfyUI format AND
compatible with the Mac MLX/MPS constraints documented in the workspace.

## Architecture

A ComfyUI workflow is a JSON file with these required keys:

```
{
  "id": "<uuid>",
  "revision": 0,
  "last_node_id": <int>,
  "last_link_id": <int>,
  "nodes": [...],
  "links": [...],
  "groups": [...],
  "config": {},
  "version": 0.4
}
```

Two output formats exist:

| Format | Structure | Use Case |
|--------|-----------|----------|
| **Saved Graph** (native) | `nodes` (array) + `links` (array) | Direct save to `user/default/workflows/` |
| **Prompt API** (agent-friendly) | `{"1": {...}, "2": {...}}` with `"model": ["1", 0]` references | LLM/agent generation, ComfyUI API submission |

Always produce **Saved Graph** format as the final deliverable. Use Prompt API as
intermediate representation when scaffolding programmatically.

## Node Object Schema (Saved Graph)

```json
{
  "id": 1,
  "type": "UNETLoader",
  "pos": [0, 0],
  "size": [300, 100],
  "flags": {},
  "order": 0,
  "mode": 0,
  "inputs": [
    { "name": "unet_name", "type": "MODEL", "link": null }
  ],
  "outputs": [
    { "name": "MODEL", "type": "MODEL", "links": [] }
  ],
  "properties": { "Node name for S&R": "UNETLoader" },
  "widgets_values": ["z_image_turbo_bf16.safetensors"]
}
```

## Link Object Schema (Saved Graph)

```json
[link_id, source_node_id, source_slot_index, target_node_id, target_slot_index, type]
```

Example: `[1, 1, 0, 3, 0, "MODEL"]` — link from node 1 output 0 (MODEL) to node 3 input 0 (MODEL).

## Canonical 11-Node Scaffold (PyTorch MPS — Image)

For Z-Image Turbo, FLUX.1-dev, Krea 2 Turbo on the PyTorch MPS backend:

```
UNETLoader → ModelSamplingAuraFlow → KSampler (model input)
CLIPLoader → CLIPTextEncode (positive) → FluxGuidance → KSampler
CLIPTextEncode (negative) → KSampler
VAELoader → VAEDecode → SaveImage
EmptySD3LatentImage → KSampler (latent)
KSampler → VAEDecode (samples)
```

### Node-by-node template

```json
[
  { "id": 1, "type": "UNETLoader", "inputs": [], "outputs": [{"name":"MODEL","type":"MODEL","links":[7]}], "widgets_values": ["z_image_turbo_bf16.safetensors"] },
  { "id": 2, "type": "CLIPLoader", "inputs": [], "outputs": [{"name":"CLIP","type":"CLIP","links":[3]}], "widgets_values": ["qwen_3_4b.safetensors", "lumina2"] },
  { "id": 3, "type": "VAELoader", "inputs": [], "outputs": [{"name":"VAE","type":"VAE","links":[9]}], "widgets_values": ["ae.safetensors"] },
  { "id": 4, "type": "CLIPTextEncode", "inputs": [{"name":"text","type":"STRING","link":null},{"name":"clip","type":"CLIP","link":3}], "outputs": [{"name":"CONDITIONING","type":"CONDITIONING","links":[8]}], "widgets_values": ["A beautiful sunset over the ocean"] },
  { "id": 5, "type": "CLIPTextEncode", "inputs": [{"name":"text","type":"STRING","link":null},{"name":"clip","type":"CLIP","link":3}], "outputs": [{"name":"CONDITIONING","type":"CONDITIONING","links":null}], "widgets_values": ["ugly, blurry, low quality"] },
  { "id": 6, "type": "EmptySD3LatentImage", "inputs": [], "outputs": [{"name":"LATENT","type":"LATENT","links":[10]}], "widgets_values": [1024, 1024, 1] },
  { "id": 7, "type": "ModelSamplingAuraFlow", "inputs": [{"name":"shift","type":"FLOAT","link":null},{"name":"model","type":"MODEL","link":1}], "outputs": [{"name":"MODEL","type":"MODEL","links":[11]}], "widgets_values": [3.0] },
  { "id": 8, "type": "FluxGuidance", "inputs": [{"name":"guidance","type":"FLOAT","link":null},{"name":"conditioning","type":"CONDITIONING","link":4}], "outputs": [{"name":"CONDITIONING","type":"CONDITIONING","links":[12]}], "widgets_values": [1.0] },
  { "id": 9, "type": "KSampler", "inputs": [{"name":"seed","type":"INT","link":null},{"name":"steps","type":"INT","link":null},{"name":"cfg","type":"FLOAT","link":null},{"name":"sampler_name","type":"sampler","link":null},{"name":"scheduler","type":"scheduler","link":null},{"name":"denoise","type":"FLOAT","link":null},{"name":"model","type":"MODEL","link":7},{"name":"positive","type":"CONDITIONING","link":8},{"name":"negative","type":"CONDITIONING","link":5},{"name":"latent_image","type":"LATENT","link":6}], "outputs": [{"name":"LATENT","type":"LATENT","links":[13]}], "widgets_values": [42, 8, 1.0, "res_multistep", "simple", 1.0] },
  { "id": 10, "type": "VAEDecode", "inputs": [{"name":"samples","type":"LATENT","link":9},{"name":"vae","type":"VAE","link":3}], "outputs": [{"name":"IMAGE","type":"IMAGE","links":[14]}], "widgets_values": [] },
  { "id": 11, "type": "SaveImage", "inputs": [{"name":"filename_prefix","type":"STRING","link":null},{"name":"images","type":"IMAGE","link":10}], "outputs": [], "widgets_values": ["mac_test"] }
]
```

> **Note:** The above is a simplified structural sketch. For production use, always
> wire complete `links` arrays and unique `id`/`link_id` values. See the full
> reference at `comfyui-set-mac-SKILL.md` §7.1 for the canonical 11-node
> PyTorch-MPS workflow with complete link arrays.

## 3-Node Scaffold (Mflux-ComfyUI — MLX Backend)

For workflows using the `Mflux-ComfyUI` custom node (MLX backend, recommended):

```json
{
  "1": {
    "class_type": "MfluxLoader",
    "inputs": { "model": "mlx-community/FLUX.1-dev", "quantize": 8 }
  },
  "2": {
    "class_type": "MfluxSampler",
    "inputs": {
      "prompt": "cinematic mountain landscape at golden hour",
      "seed": 42, "steps": 20, "width": 1024, "height": 1024,
      "model": ["1", 0]
    }
  },
  "3": {
    "class_type": "SaveImage",
    "inputs": { "filename_prefix": "mflux_out", "images": ["2", 0] }
  }
}
```

## Model-Specific Parameters

### Z-Image Turbo (recommended default)

| Parameter | Value | Notes |
|-----------|-------|-------|
| sampler | `res_multistep` | AuraFlow sampling |
| scheduler | `simple` | |
| steps | 8 | Range: 6-12 |
| cfg | 1.0 | Low CFG by design |
| resolution | 1024×1024 | Native |
| unet | `z_image_turbo_bf16.safetensors` | 11 GB, fits 16 GB Mac |
| clip | `qwen_3_4b.safetensors` | Type: `lumina2` |
| vae | `ae.safetensors` | ~320 MB |

### FLUX.1-dev (legacy, broader ecosystem)

| Parameter | Value | Notes |
|-----------|-------|-------|
| sampler | `euler` | |
| scheduler | `simple` or `beta57` | |
| steps | 20 | |
| cfg | 7.0 | Standard CFG |
| resolution | 1024×1024 | |
| unet | `flux1-dev.safetensors` | 22 GB, needs 24+ GB Mac |

### FLUX.2 [klein] 4B (Apache 2.0, commercial-safe)

| Parameter | Value | Notes |
|-----------|-------|-------|
| sampler | `euler` | |
| scheduler | `beta57` | |
| steps | 4-12 | Distilled model |
| cfg | 7.0 | |
| model | `mlx-community/FLUX.2-klein-4B-distilled-8bit` | ~5 GB |

### Krea 2 Turbo (CFG-FREE — critical)

| Parameter | Value | Notes |
|-----------|-------|-------|
| sampler | `euler_ancestral` | |
| steps | 8 | |
| **guidance** | **0.0** | **MUST be 0 — DESTROYS quality otherwise** |
| resolution | 1024×1024 | |
| unet | `krea2_turbo_bf16.safetensors` | 24 GB |

### Ideogram 4 (typography, JSON prompts)

| Parameter | Value | Notes |
|-----------|-------|-------|
| resolution | 1024×1024 | |
| model | `MLXBits/ideogram-4-mlx-q4` | 15 GB (16 GB Macs) or q8 (48 GB Macs) |
| **Requires** | `ideogram-mlx-forge-loader` branch | See `comfyui-set-mac-SKILL.md` Pitfall 17 |

### Qwen-Image-2512 (Apache 2.0, multilingual)

| Parameter | Value | Notes |
|-----------|-------|-------|
| steps | 20 | |
| model | `mlx-community/Qwen-Image-2512-4bit` | 25.9 GB, **requires 48 GB Mac** |

## LoRA Node Pattern

LoRAs are **model-specific** — applying a FLUX LoRA to Z-Image will crash.

```
PowerLoRALoader (rgthree) → MLXSampler
  lora_name: <model_matching_lora>.safetensors
  strength: 0.4-0.7
```

Known LoRA compatibility:

| LoRA | Compatible Model | Incompatible |
|------|-----------------|--------------|
| `ideogram4_turbotime_v1.safetensors` | Ideogram 4 ONLY | Z-Image, FLUX, Krea |
| FLUX style LoRAs | FLUX.1/2 | Z-Image, Krea |

## Group Organization Pattern

Organize nodes into conceptual stages using ComfyUI groups:

```json
{
  "groups": [
    { "id": 1, "title": "Step 1 - Load Model", "bounding": [x, y, w, h], "color": "#3f789e", "font_size": 24 },
    { "id": 2, "title": "Step 2 - Conditioning", "bounding": [x, y, w, h], "color": "#3f789e", "font_size": 24 },
    { "id": 3, "title": "Step 3 - LoRA", "bounding": [x, y, w, h], "color": "#3f789e", "font_size": 24 },
    { "id": 4, "title": "Step 4 - Sampler", "bounding": [x, y, w, h], "color": "#3f789e", "font_size": 24 },
    { "id": 5, "title": "Step 5 - Save", "bounding": [x, y, w, h], "color": "#3f789e", "font_size": 24 }
  ]
}
```

## MarkdownNote Documentation Pattern

Every shipped workflow MUST include a MarkdownNote node with model links and
install instructions:

```json
{
  "type": "MarkdownNote",
  "widgets_values": [
    "## Model Links\n\n"
    "**Model Name**\n\n"
    "- [model_file.safetensors](https://huggingface.co/org/repo/resolve/main/model_file.safetensors)\n\n"
    "Place in: `~/ComfyUI/models/diffusion_models/`\n\n"
    "## Usage Notes\n\n"
    "- Mac-compatible format (bf16 or MLX-quantized)\n"
    "- Requires X GB VRAM minimum"
  ]
}
```

## Mac-Specific Validation Checklist

Before delivering a workflow, verify:

- [ ] **No fp8 models** — only bf16 or MLX-quantized (int4/int8)
- [ ] **Krea 2 Turbo**: guidance = 0.0 (not 7.0)
- [ ] **LoRA architecture match** — LoRA targets correct model family
- [ ] **Memory fit** — model + encoder + VAE fits in Mac's unified memory
  - 16 GB Mac: Z-Image Turbo bf16 (12 GB) or FLUX.2 klein 4B (6 GB)
  - 24 GB Mac: FLUX.1-dev (22 GB) or Ideogram 4 int4 (15 GB)
  - 48 GB Mac: Qwen-Image-2512 4-bit (26 GB) or Ideogram 4 int8 (27 GB)
- [ ] **Ideogram 4 MLX**: requires `ideogram-mlx-forge-loader` branch noted in docs
- [ ] **ComfyUI launch**: `nohup` + log redirect (avoids BrokenPipeError)
- [ ] **All node `type` strings** match ComfyUI registered node names exactly
- [ ] **Link references** use valid node IDs and slot indices
- [ ] **No DiffusionKit or thoddnn/ComfyUI-MLX** references (archived)

## Workflow Generation Process

### Step 1: Identify Model Family

Determine which model the workflow targets. This dictates:
- UNETLoader `unet_name` and `weight_dtype`
- CLIPLoader `clip_name` and `type`
- Required memory budget
- Compatible sampler settings

### Step 2: Choose Backend

| Backend | Node Pattern | Performance | Complexity |
|---------|-------------|-------------|------------|
| PyTorch MPS | 11-node (UNETLoader→KSampler→VAEDecode) | Good (2-3× slower than MLX) | Higher |
| Mflux-ComfyUI | 3-node (MfluxLoader→MfluxSampler→SaveImage) | Best (native MLX) | Lowest |

### Step 3: Scaffold Nodes

Generate the node array using the canonical scaffold for the chosen backend.
Assign sequential IDs starting from 1. Calculate `last_node_id` and
`last_link_id` as the maximum values + 1.

### Step 4: Wire Links

Create the link array. Each link connects one output slot to one input slot.
Format: `[link_id, src_node_id, src_slot, dst_node_id, dst_slot, type]`.

### Step 5: Add Groups and Documentation

Wrap node sets into logical groups. Add a MarkdownNote with model download
URLs and Mac-specific install notes.

### Step 6: Validate

Run the Mac-specific validation checklist above. Verify JSON parses correctly.

## Reference Files

- `references/workflow-schema.md` — Full JSON schema with all field types
- `references/node-catalog.md` — Complete node type reference for image workflows
- `references/link-patterns.md` — Common connection patterns by model family

## Companion Workspace Files

| File | Relationship |
|------|-------------|
| `comfyui-set-mac-SKILL.md` | Full install guide (2,917 lines) — canonical node patterns in §7 |
| `MLX-Image-Gen-Mac-Implementation-Guide.md` | Condensed reference — §12 has workflow templates |
| `sample_workflows_as_examples/` | 6 LTX-2 video workflows demonstrating structure |
| `research/scripts/` | 10 Python scripts for programmatic generation |

## Output Convention

Save completed workflows to:
```
~/ComfyUI/user/default/workflows/<model_name>_<backend>.json
```

Examples:
- `z_image_turbo_pytorch_mps.json`
- `flux2_klein_mflux_mlx.json`
- `krea2_turbo_native_mlx.json`
