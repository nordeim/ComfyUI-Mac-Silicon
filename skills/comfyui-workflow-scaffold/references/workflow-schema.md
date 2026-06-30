# ComfyUI Workflow JSON Schema (v0.4)

## Top-Level Structure

```json
{
  "id": "394ed254-7306-42a2-9ae6-aa880ce4456d",
  "revision": 0,
  "last_node_id": 11,
  "last_link_id": 14,
  "nodes": [...],
  "links": [...],
  "groups": [...],
  "config": {},
  "version": 0.4
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | UUID v4, uniquely identifies this workflow |
| `revision` | int | Increment on edit (default: 0) |
| `last_node_id` | int | Highest node ID + 1 (auto-computed by ComfyUI) |
| `last_link_id` | int | Highest link ID + 1 (auto-computed by ComfyUI) |
| `nodes` | array | Node objects (see below) |
| `links` | array | Link objects (see below) |
| `groups` | array | Group objects (see below) |
| `config` | object | Always `{}` |
| `version` | float | Always `0.4` |

## Node Object

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
    {
      "name": "unet_name",
      "type": "MODEL",
      "link": null
    }
  ],
  "outputs": [
    {
      "name": "MODEL",
      "type": "MODEL",
      "links": [7]
    }
  ],
  "properties": {
    "Node name for S&R": "UNETLoader"
  },
  "widgets_values": ["z_image_turbo_bf16.safetensors"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique within workflow |
| `type` | string | ComfyUI registered node type name |
| `pos` | [float, float] | Canvas position [x, y] |
| `size` | [float, float] | Node dimensions [w, h] |
| `flags` | object | Usually `{}` |
| `order` | int | Execution order (topological sort) |
| `mode` | int | 0 = normal, 2 = collapsed, 4 = muted |
| `inputs` | array | Input socket definitions |
| `outputs` | array | Output socket definitions |
| `properties` | object | Node-specific metadata |
| `widgets_values` | array | Widget display values |

## Input/Output Socket

```json
{
  "name": "model",
  "type": "MODEL",
  "link": 7
}
```

For outputs:
```json
{
  "name": "MODEL",
  "type": "MODEL",
  "links": [7, 8]
}
```

Common socket types: `MODEL`, `CLIP`, `VAE`, `CONDITIONING`, `LATENT`, `IMAGE`, `STRING`, `INT`, `FLOAT`, `SAMPLER`, `SIGMAS`, `GUIDER`, `NOISE`.

## Link Object

```json
[link_id, source_node_id, source_slot_index, target_node_id, target_slot_index, type]
```

Example:
```json
[7, 1, 0, 9, 0, "MODEL"]
```

This means: "Link #7 connects output 0 of node 1 (MODEL) to input 0 of node 9 (MODEL)."

## Group Object

```json
{
  "id": 1,
  "title": "Step 1 - Load Model",
  "bounding": [x, y, width, height],
  "color": "#3f789e",
  "font_size": 24,
  "flags": {}
}
```

## Prompt API Format (Alternative)

For agent generation or ComfyUI API submission, use the prompt API format:

```json
{
  "1": {
    "class_type": "UNETLoader",
    "inputs": {
      "unet_name": "z_image_turbo_bf16.safetensors",
      "weight_dtype": "default"
    }
  },
  "9": {
    "class_type": "KSampler",
    "inputs": {
      "model": ["1", 0],
      "positive": ["8", 0],
      "negative": ["5", 0],
      "latent_image": ["6", 0],
      "seed": 42,
      "steps": 8,
      "cfg": 1.0,
      "sampler_name": "res_multistep",
      "scheduler": "simple",
      "denoise": 1.0
    }
  }
}
```

References like `"model": ["1", 0]` mean "node 1, output slot 0".
