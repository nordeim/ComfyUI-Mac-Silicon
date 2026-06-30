# Guide 1 — Wrapping NVIDIA NIM (MiniMax-M3) as a Local Proxy Using LiteLLM

This guide walks you through running the **LiteLLM Proxy** as a local gateway in front of NVIDIA's `integrate.api.nvidia.com` endpoint so that every local application can call a single, key-free local URL and reach the `minimaxai/minimax-m3` model. LiteLLM is the de-facto open-source AI gateway used in production by teams that need a unified OpenAI-compatible surface in front of many providers, and it has first-class support for NVIDIA NIM. Because the NVIDIA NIM endpoint is itself OpenAI-compatible, the OpenAI half of this proxy is essentially zero code, and the Anthropic half — which lets tools like Claude Code speak their native `/v1/messages` protocol — is provided by LiteLLM's built-in Anthropic unified endpoint.

The guide is split into two parallel sections:

- **Section A — OpenAI-compatible local service** (`/v1/chat/completions`, `/v1/models`)
- **Section B — Anthropic-compatible local service** (`/v1/messages`, for Claude Code and the Anthropic SDKs)

Both sections share the same proxy process, the same `config.yaml`, and the same upstream NVIDIA key. You only run one server.

---

## Table of Contents

1. [Architecture overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Obtain a NVIDIA NIM API key](#3-obtain-a-nvidia-nim-api-key)
4. [Install LiteLLM](#4-install-litellm)
5. [Create the `config.yaml`](#5-create-the-configyaml)
6. [Run the proxy](#6-run-the-proxy)
7. [Section A — OpenAI-compatible local service](#7-section-a--openai-compatible-local-service)
8. [Section B — Anthropic-compatible local service (Claude Code)](#8-section-b--anthropic-compatible-local-service-claude-code)
9. [Docker Compose deployment](#9-docker-compose-deployment)
10. [Virtual keys and budget control](#10-virtual-keys-and-budget-control)
11. [Observability: logs, metrics, health](#11-observability-logs-metrics-health)
12. [Troubleshooting](#12-troubleshooting)
13. [Production checklist](#13-production-checklist)

---

## 1. Architecture overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  Local applications                                                  │
│  ─ OpenAI SDK (Python/Node)        ─ Anthropic SDK / Claude Code CLI │
│  ─ LangChain, LlamaIndex           ─ Any client speaking /v1/messages │
│  ─ curl, httpx, fetch              ─ Cursor, Cline, Zed, etc.        │
└───────────────────────────┬──────────────────────────────────────────┘
                            │  http://localhost:4000
                            │  Authorization: Bearer sk-local-proxy-secret
                            ▼
                  ┌──────────────────────────┐
                  │  LiteLLM Proxy (Python)  │
                  │  ─ /v1/chat/completions  │  OpenAI surface (passthrough)
                  │  ─ /v1/models            │
                  │  ─ /v1/messages          │  Anthropic surface (translated)
                  │  ─ /health, /metrics     │
                  └────────────┬─────────────┘
                               │  Authorization: Bearer nvapi-xxxx
                               │  https://integrate.api.nvidia.com/v1
                               ▼
                  ┌──────────────────────────┐
                  │  NVIDIA NIM (MiniMax-M3) │
                  │  1M context, multimodal  │
                  └──────────────────────────┘
```

The proxy performs three jobs: it terminates the client's local auth header and replaces it with the real NVIDIA key, it accepts both OpenAI-shaped and Anthropic-shaped requests on the same port, and it transparently translates the Anthropic `/v1/messages` requests into the OpenAI `/v1/chat/completions` calls that NVIDIA NIM expects. The translation logic — message reshaping, tool-call mapping, stop-reason mapping, and SSE event-type conversion — is maintained by LiteLLM and battle-tested across thousands of deployments, so you do not have to implement it yourself.

The key design property to internalize is that **clients never see NVIDIA**. They see `http://localhost:4000` and a single local secret (`sk-local-proxy-secret` in this guide). The actual `nvapi-...` key lives only inside the proxy's environment. This means you can rotate the NVIDIA key, swap to a different upstream provider, or load-balance across multiple NVIDIA accounts without touching a single line of client code.

---

## 2. Prerequisites

Before you start, make sure your environment satisfies the following requirements. The guide assumes a Unix-like shell (Linux, macOS, or WSL2 on Windows). PowerShell equivalents are noted inline where the syntax differs materially.

- **Python 3.10 or newer.** LiteLLM requires Python 3.10+; Python 3.11 or 3.12 is recommended for the best async performance with `httpx` and `uvicorn`. Check with `python3 --version`.
- **`pip` or `uv`.** Either works. `uv` is substantially faster and is used in the official LiteLLM quickstart. Install it from <https://docs.astral.sh/uv/> if you do not have it.
- **`curl`** for the smoke tests, and optionally `jq` to pretty-print JSON responses.
- **A NVIDIA developer account.** Sign up at <https://build.nvidia.com> — the free tier grants 1,000 inference credits on signup and up to 5,000 total, with a default rate limit of 40 requests per minute. That is plenty for development and small-team use.
- **Approximately 200 MB of disk space** for the LiteLLM package and its dependencies.
- **Port 4000 free on localhost.** This is LiteLLM's default port; if you need a different one, every example below accepts `--port <n>` or a `PORT` env var.
- **Network egress to `integrate.api.nvidia.com` on port 443.** If you are behind a corporate proxy, set `HTTPS_PROXY` before launching LiteLLM so that outbound requests from `httpx` honour it.

No GPU is required anywhere — inference happens entirely on NVIDIA's hosted NIM infrastructure.

---

## 3. Obtain a NVIDIA NIM API key

Navigate to <https://build.nvidia.com/minimaxai/minimax-m3/modelcard> and sign in with your NVIDIA developer account. On the model card page, look for the **"Get API Key"** button in the right-hand sidebar (it may be labelled **"Generate API Key"** on first visit). A key looks like `nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. Copy it immediately — NVIDIA does not let you retrieve the plaintext again after the dialog closes, only rotate it.

Store the key in your environment, not in your code. Add the following line to your `~/.zshrc`, `~/.bashrc`, or a dedicated `~/.config/nvidia/env` file that you source from your shell startup:

```bash
export NVIDIA_NIM_API_KEY="nvapi-xxxxxxxx...xxxx"
```

Reload the shell (`source ~/.zshrc` or open a new terminal) and verify the variable is set:

```bash
echo "${NVIDIA_NIM_API_KEY:0:12}..."   # should print "nvapi-xxxxxx..."
```

You can sanity-check the key directly against NVIDIA before adding the proxy layer:

```bash
curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_NIM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimaxai/minimax-m3",
    "messages": [{"role":"user","content":"Say hello in one short sentence."}],
    "max_tokens": 64,
    "temperature": 0.5
  }'
```

A 200 response with a JSON body containing `choices[0].message.content` confirms the key works and the model name is correct. If you get a 401, the key is wrong or has been rotated; if you get a 404 with a "model not found" message, double-check the exact model ID — NVIDIA is case-sensitive and uses the `vendor/model-name` convention.

---

## 4. Install LiteLLM

The recommended installation method is `uv tool install`, which gives you an isolated, upgradable `litellm` CLI on your PATH without polluting your global Python environment. If you prefer plain `pip`, that works identically.

**Option A — `uv` (recommended):**

```bash
uv tool install 'litellm[proxy]'
```

This installs the `litellm` CLI plus the proxy extras (`uvicorn`, `fastapi`, `gunicorn`, `httpx`, `pydantic`, etc.). It takes about 30 seconds on a warm cache.

**Option B — `pip`:**

```bash
python3 -m venv ~/.venvs/litellm
source ~/.venvs/litellm/bin/activate
pip install 'litellm[proxy]'
```

If you used the `venv` route, remember to `source ~/.venvs/litellm/bin/activate` in every new shell before running `litellm` commands. Adding the line to your `~/.zshrc` is the most common way to make this permanent.

**Verify the install:**

```bash
litellm --version
```

You should see a version number ≥ 1.50. Older versions may lack the Anthropic `/v1/messages` endpoint or the latest NVIDIA NIM routing fixes, so upgrade with `uv tool upgrade litellm` or `pip install -U 'litellm[proxy]'` if you are behind.

---

## 5. Create the `config.yaml`

LiteLLM is configured declaratively through a single YAML file. Create a project directory and write the config there:

```bash
mkdir -p ~/nvidia-proxy && cd ~/nvidia-proxy
```

Now create `~/nvidia-proxy/config.yaml` with the following content. The comments inline explain each field:

```yaml
# ~/nvidia-proxy/config.yaml
# -----------------------------------------------------------------------------
# LiteLLM Proxy configuration for routing local traffic to NVIDIA NIM
# (minimaxai/minimax-m3) under both OpenAI and Anthropic API surfaces.
# -----------------------------------------------------------------------------

model_list:
  # --- Primary alias: what clients type as "model" in their requests ---------
  - model_name: minimax-m3                    # user-facing alias (any string)
    litellm_params:
      model: nvidia_nim/minimaxai/minimax-m3  # actual upstream model id
      api_key: os.environ/NVIDIA_NIM_API_KEY  # read from env, never inline
      # Optional: per-deployment RPM cap to stay under NVIDIA's 40 RPM free tier
      rpm: 35

  # --- Optional convenience aliases (so clients can call "gpt-4o" etc.) -----
  - model_name: gpt-4o
    litellm_params:
      model: nvidia_nim/minimaxai/minimax-m3
      api_key: os.environ/NVIDIA_NIM_API_KEY
      rpm: 35

  - model_name: claude-3-5-sonnet-20241022
    litellm_params:
      model: nvidia_nim/minimaxai/minimax-m3
      api_key: os.environ/NVIDIA_NIM_API_KEY
      rpm: 35

# --- LiteLLM-wide settings --------------------------------------------------
litellm_settings:
  drop_params: true        # silently drop params the upstream doesn't accept
  num_retries: 3           # retry on 429 / 5xx with exponential backoff
  request_timeout: 600     # MiniMax-M3 supports 1M context — be generous
  streaming_timeout: 600

# --- Proxy-wide settings ----------------------------------------------------
general_settings:
  master_key: os.environ/LOCAL_PROXY_KEY    # required for /v1/messages + virtual keys
  # Optional: store virtual keys / spend tracking in a local SQLite DB
  database_url: sqlite:///./litellm.db
  # Optional: enable the admin UI at http://localhost:4000/ui
  disable_admin_ui: false
```

A few important notes about the config:

- **`model_name` is the alias clients see**; `litellm_params.model` is what LiteLLM sends upstream. By aliasing `gpt-4o` and `claude-3-5-sonnet-20241022` to MiniMax-M3, you can drop the proxy into existing apps without changing a single line of model name in their code.
- **`os.environ/VAR_NAME`** is LiteLLM's syntax for reading an environment variable at startup. It avoids hard-coding secrets into the YAML so you can commit the file to version control safely.
- **`drop_params: true`** is critical for the Anthropic surface: Anthropic clients send parameters NVIDIA doesn't understand (e.g. `top_k` at the top level, or `metadata.user_id`); with this flag LiteLLM silently strips them rather than returning 400.
- **`rpm: 35`** is deliberately set 5 below NVIDIA's 40 RPM free-tier ceiling. LiteLLM will return a local 429 with `Retry-After` instead of forwarding a 429 from NVIDIA, which keeps your client-side retry logic simpler.
- **`master_key`** is what your local clients will use as their API key. Set it to a strong random string — `openssl rand -hex 32` is a good generator.

Create the local master key and persist it alongside the NVIDIA key:

```bash
echo "export LOCAL_PROXY_KEY=\"sk-$(openssl rand -hex 24)\"" >> ~/.zshrc
source ~/.zshrc
echo "$LOCAL_PROXY_KEY"   # save this — clients will need it
```

---

## 6. Run the proxy

From the directory containing `config.yaml`:

```bash
cd ~/nvidia-proxy
litellm --config config.yaml --port 4000
```

You should see log output ending with:

```
LiteLLM_Proxy: Uvicorn running on http://0.0.0.0:4000
```

Two URLs are now live on the same process:

| URL                                | Purpose                                  |
|------------------------------------|------------------------------------------|
| `http://localhost:4000/v1/chat/completions` | OpenAI Chat Completions surface  |
| `http://localhost:4000/v1/messages`         | Anthropic Messages surface       |
| `http://localhost:4000/v1/models`           | List of aliases defined in config |
| `http://localhost:4000/health/liveness`     | Liveness probe (always 200)      |
| `http://localhost:4000/health/readiness`    | Readiness probe (checks upstream)|
| `http://localhost:4000/ui`                  | Admin UI (login with master_key) |
| `http://localhost:4000/#/config.yaml`       | Swagger UI for the proxy itself  |

For long-running deployments, run LiteLLM under a process supervisor. The simplest option is `systemd` on Linux or `pm2` on any platform:

```bash
# Example systemd unit at /etc/systemd/system/litellm.service
[Unit]
Description=LiteLLM Proxy
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/nvidia-proxy
EnvironmentFile=/home/ubuntu/nvidia-proxy/.env
ExecStart=/home/ubuntu/.venvs/litellm/bin/litellm --config /home/ubuntu/nvidia-proxy/config.yaml --port 4000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

For local development, just running `litellm --config config.yaml` in a terminal is fine. Use a tool like `tmux` or `screen` if you want it to survive your SSH session disconnecting.

---

## 7. Section A — OpenAI-compatible local service

This section shows how to point OpenAI-compatible clients at your local proxy. The proxy's OpenAI surface is at `http://localhost:4000/v1/...` and accepts the full Chat Completions API surface: messages, system prompts, streaming, tool/function calling, `temperature`, `top_p`, `max_tokens`, `stop`, `response_format` (JSON mode), `n`, `seed`, and `user`. Because NVIDIA NIM is itself OpenAI-compatible, LiteLLM forwards these requests nearly verbatim — the only transformations are injecting the NVIDIA key, applying your `rpm` limit, and rewriting the `model` field from your alias to the real upstream model ID.

### 7.1 Quick smoke test with curl

Run this in a second terminal while the proxy is running in the first:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LOCAL_PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax-m3",
    "messages": [
      {"role": "system", "content": "You are a concise assistant."},
      {"role": "user", "content": "In one sentence, what is the speed of light?"}
    ],
    "max_tokens": 80,
    "temperature": 0.3
  }' | jq .
```

A successful response looks like the OpenAI Chat Completions schema you already know:

```json
{
  "id": "chatcmpl-xxxx",
  "object": "chat.completion",
  "created": 1730000000,
  "model": "minimax-m3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The speed of light in vacuum is approximately 299,792,458 meters per second."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 25, "completion_tokens": 21, "total_tokens": 46}
}
```

If you see `"model": "minimax-m3"` (your alias, not the upstream ID), that confirms LiteLLM is the one answering. If you get a 401, your `Authorization` header does not match `LOCAL_PROXY_KEY`; if you get a 429, you have hit the 35-RPM cap configured in `config.yaml` — wait 60 seconds and retry.

### 7.2 Streaming with Server-Sent Events

Streaming works out of the box. Set `"stream": true` and the proxy will faithfully forward each `data: {...}\n\n` chunk that NVIDIA emits, terminating with `data: [DONE]\n\n`. Because the upstream and downstream are both OpenAI-format SSE, LiteLLM does not need to parse or rewrite the stream — it just pipes bytes through, which gives you the lowest possible latency:

```bash
curl -N http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LOCAL_PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax-m3",
    "stream": true,
    "messages": [{"role":"user","content":"Count from 1 to 5, one per line."}],
    "max_tokens": 100
  }'
```

You will see chunks like `data: {"choices":[{"delta":{"content":"1"}}]}` arriving every few hundred milliseconds. The `-N` flag disables curl's output buffering so you see the chunks in real time.

### 7.3 Multimodal input (images and video)

MiniMax-M3 is a multimodal model — it accepts image and video URLs in the OpenAI `content` array format. LiteLLM passes these through unchanged:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LOCAL_PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax-m3",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Cheetah_Masai_Mara.jpg/640px-Cheetah_Masai_Mara.jpg"}}
      ]
    }],
    "max_tokens": 256
  }' | jq '.choices[0].message.content'
```

For local files, base64-encode them into a data URI:

```python
import base64, requests, os
b64 = base64.b64encode(open("photo.jpg","rb").read()).decode()
r = requests.post(
    "http://localhost:4000/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.environ['LOCAL_PROXY_KEY']}"},
    json={
        "model": "minimax-m3",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in detail."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ]
        }],
        "max_tokens": 512,
    },
)
print(r.json()["choices"][0]["message"]["content"])
```

Video URLs follow the same pattern with `type: "video_url"` — see the original code snippet you provided for the exact shape.

### 7.4 Using the official OpenAI Python SDK

The whole point of an OpenAI-compatible proxy is that you can keep using the official SDK and just change the `base_url` and `api_key`. Install the SDK with `pip install openai` and run:

```python
# client_openai.py
import os
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key=os.environ["LOCAL_PROXY_KEY"],  # the proxy key, NOT the NVIDIA key
)

# Non-streaming
resp = client.chat.completions.create(
    model="minimax-m3",                      # your alias from config.yaml
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function that reverses a linked list."},
    ],
    temperature=0.2,
    max_tokens=1024,
)
print(resp.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="minimax-m3",
    messages=[{"role": "user", "content": "Tell me a story in 3 sentences."}],
    stream=True,
    max_tokens=300,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
print()
```

This script will work identically against OpenAI's real API and against your local proxy — only the `base_url` and `api_key` differ. That is the entire value proposition: client code is portable, the upstream is not.

### 7.5 Using the OpenAI Node SDK

For JavaScript or TypeScript applications, install the official SDK with `npm install openai` and use the same `baseURL` / `apiKey` pattern:

```typescript
// client_openai.ts
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:4000/v1",
  apiKey: process.env.LOCAL_PROXY_KEY!,
});

const resp = await client.chat.completions.create({
  model: "minimax-m3",
  messages: [
    { role: "system", content: "You are a TypeScript expert." },
    { role: "user", content: "Show me a generic debounce function." },
  ],
  temperature: 0.2,
  max_tokens: 600,
});

console.log(resp.choices[0].message.content);
```

### 7.6 Function / tool calling

MiniMax-M3 supports OpenAI-style tool calling. Define tools using the OpenAI schema (`type: "function"` with a `function` sub-object containing `name`, `description`, and `parameters` as a JSON Schema). LiteLLM forwards them verbatim to NVIDIA:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name."},
            },
            "required": ["city"],
        },
    },
}]

resp = client.chat.completions.create(
    model="minimax-m3",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
)
tool_call = resp.choices[0].message.tool_calls[0]
print(tool_call.function.name, tool_call.function.arguments)
# get_weather {"city": "Tokyo"}
```

You then execute the tool locally and feed the result back as a `tool` role message — the standard OpenAI loop, unchanged.

### 7.7 Long context (1M tokens)

MiniMax-M3's 1M-token context window is one of its standout features. To exercise it, simply send a large `messages` array. LiteLLM's `request_timeout: 600` setting from §5 ensures the proxy doesn't time out while NVIDIA processes the long prompt. For very long inputs (>200K tokens), prefer streaming so the client sees progress within seconds rather than waiting minutes for the first byte.

```python
long_text = open("large_document.txt").read()  # up to ~1M tokens
resp = client.chat.completions.create(
    model="minimax-m3",
    messages=[
        {"role": "system", "content": "Summarize the user's document."},
        {"role": "user", "content": long_text + "\n\nPlease summarize in 5 bullets."},
    ],
    max_tokens=2048,
)
```

---

## 8. Section B — Anthropic-compatible local service (Claude Code)

This is the section that justifies using LiteLLM over a hand-rolled proxy. LiteLLM exposes an Anthropic-native `/v1/messages` endpoint on the **same port** as the OpenAI surface. When a client sends an Anthropic-format request, LiteLLM translates it to OpenAI format on the way in, calls NVIDIA NIM, and translates the OpenAI-format response back to Anthropic format on the way out. This translation covers system prompts, content blocks, tool definitions, tool-use/tool-result blocks, stop reasons, and — most importantly — the streaming SSE event taxonomy, which differs substantially between the two APIs (Anthropic uses `message_start` / `content_block_start` / `content_block_delta` / `content_block_stop` / `message_delta` / `message_stop`; OpenAI uses flat `choices[].delta` chunks).

### 8.1 Why an Anthropic surface matters

Many tools and frameworks hard-code the Anthropic API as their only LLM interface. The most prominent example is **Claude Code**, Anthropic's official CLI for agentic coding. Claude Code reads two environment variables — `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` — and refuses to talk to anything that doesn't answer at `/v1/messages` with Anthropic-format SSE. By pointing those variables at your LiteLLM proxy, you can run Claude Code against MiniMax-M3 for free, using NVIDIA's generous free tier instead of paid Anthropic credits. The same trick works for any Anthropic-SDK-based application: Cursor's "Claude API" mode, Cline, Roo Code, Zed's assistant with the Anthropic provider, custom LangChain agents wired to the Anthropic SDK, and so on.

### 8.2 Anthropic API surface exposed by LiteLLM

LiteLLM's Anthropic-compatible endpoints are:

| Path                                  | Method | Purpose                                |
|---------------------------------------|--------|----------------------------------------|
| `/v1/messages`                        | POST   | Create a message (non-streaming or SSE)|
| `/v1/messages/count_tokens`           | POST   | Estimate token count before sending    |
| `/v1/messages` (with `stream: true`)  | POST   | Streaming via Anthropic SSE events     |

Authentication uses Anthropic's standard headers, not the OpenAI `Authorization: Bearer` header:

```
x-api-key: <your LOCAL_PROXY_KEY>
anthropic-version: 2023-06-01
content-type: application/json
```

### 8.3 Quick smoke test with curl (Anthropic format)

```bash
curl http://localhost:4000/v1/messages \
  -H "x-api-key: $LOCAL_PROXY_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "minimax-m3",
    "max_tokens": 200,
    "messages": [
      {"role": "user", "content": "In one sentence, what is the speed of light?"}
    ]
  }' | jq .
```

A successful response looks like a native Anthropic Messages API response:

```json
{
  "id": "msg_xxxx",
  "type": "message",
  "role": "assistant",
  "model": "minimax-m3",
  "content": [
    {
      "type": "text",
      "text": "The speed of light in vacuum is approximately 299,792,458 meters per second."
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 18,
    "output_tokens": 21
  }
}
```

The `stop_reason` value will be one of Anthropic's standard enum values: `end_turn` (natural completion), `max_tokens` (hit the limit), `stop_sequence` (matched a custom stop), or `tool_use` (the model wants to call a tool). LiteLLM maps these from OpenAI's `finish_reason` (`stop`, `length`, `stop_sequence`, `tool_calls`) automatically.

### 8.4 Streaming with Anthropic SSE events

Set `"stream": true` and you receive Anthropic-format SSE events. The event sequence is:

```
event: message_start
data: {"type":"message_start","message":{"id":"msg_xxx","role":"assistant","content":[],"model":"minimax-m3","stop_reason":null,"usage":{"input_tokens":18,"output_tokens":0}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"The"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" speed"}}

...

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null},"usage":{"output_tokens":21}}

event: message_stop
data: {"type":"message_stop"}
```

Test it with curl:

```bash
curl -N http://localhost:4000/v1/messages \
  -H "x-api-key: $LOCAL_PROXY_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "minimax-m3",
    "max_tokens": 100,
    "stream": true,
    "messages": [{"role":"user","content":"Count from 1 to 5 with one number per line."}]
  }'
```

### 8.5 Pointing Claude Code at the proxy

Claude Code reads its configuration from environment variables. Set the following before launching `claude` in a terminal:

```bash
# ~/.zshrc or a dedicated shell rc for claude code
export ANTHROPIC_BASE_URL="http://localhost:4000"
export ANTHROPIC_AUTH_TOKEN="$LOCAL_PROXY_KEY"
# Optional: pretend to be a specific Claude model so Claude Code's model picker doesn't complain
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
export ANTHROPIC_SMALL_FAST_MODEL="claude-3-5-sonnet-20241022"
```

Note that the URL is `http://localhost:4000` (no trailing `/v1`). Claude Code appends `/v1/messages` itself. `ANTHROPIC_AUTH_TOKEN` is preferred over `ANTHROPIC_API_KEY` when you're using a custom base URL — the latter is reserved for direct-to-Anthropic auth in some Claude Code versions.

Then launch Claude Code normally:

```bash
claude
```

The first request Claude Code makes is typically a `/v1/messages` call with a system prompt describing the agentic loop and the available tools (Read, Write, Edit, Bash, etc.). LiteLLM will translate this to OpenAI format, route it to MiniMax-M3 on NVIDIA NIM, and translate the response back. Tool calls initiated by MiniMax-M3 will be returned as Anthropic `tool_use` content blocks, which Claude Code knows how to execute locally. The result is that Claude Code "just works" against MiniMax-M3, complete with file edits, bash execution, and multi-turn tool use.

If you see an error like `401 unauthorized` from Claude Code, double-check that `ANTHROPIC_AUTH_TOKEN` exactly matches `LOCAL_PROXY_KEY`. If you see `404 not found` for `/v1/messages`, your LiteLLM version is too old — upgrade to 1.50+.

### 8.6 Using the official Anthropic Python SDK

Any code written against the official Anthropic SDK works unchanged once you point it at the proxy:

```python
# client_anthropic.py
import os
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:4000",
    api_key=os.environ["LOCAL_PROXY_KEY"],  # x-api-key header
)

# Non-streaming
msg = client.messages.create(
    model="minimax-m3",
    max_tokens=1024,
    system="You are a helpful coding assistant.",
    messages=[
        {"role": "user", "content": "Write a Python function that reverses a linked list."}
    ],
)
print(msg.content[0].text)

# Streaming
with client.messages.stream(
    model="minimax-m3",
    max_tokens=512,
    messages=[{"role": "user", "content": "Tell me a story in 3 sentences."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print()
```

The `system` field is a top-level parameter in the Anthropic API (not a message in the `messages` array). LiteLLM hoists it into an OpenAI `system` message before forwarding to NVIDIA, and hoists the upstream system message back into the Anthropic `system` field on the return path.

### 8.7 Anthropic-style tool use

Anthropic's tool schema differs from OpenAI's: instead of `tools: [{type: "function", function: {...}}]`, Anthropic uses `tools: [{name, description, input_schema}]`. LiteLLM handles the bidirectional translation:

```python
tools = [{
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name."},
        },
        "required": ["city"],
    },
}]

msg = client.messages.create(
    model="minimax-m3",
    max_tokens=512,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
)

# msg.content will be a list containing a tool_use block:
# [TextBlock(text="I'll check the weather for you."),
#  ToolUseBlock(id="toolu_xxx", name="get_weather", input={"city": "Tokyo"})]
for block in msg.content:
    if block.type == "tool_use":
        print(f"Tool call: {block.name}({block.input})")
```

To return a tool result, send a follow-up `user` message whose content is a `tool_result` block referencing the tool use ID:

```python
tool_use_id = next(b for b in msg.content if b.type == "tool_use").id
msg2 = client.messages.create(
    model="minimax-m3",
    max_tokens=512,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in Tokyo?"},
        {"role": "assistant", "content": msg.content},
        {"role": "user", "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": "Tokyo: 18°C, partly cloudy.",
            }
        ]},
    ],
)
print(msg2.content[0].text)
```

The Anthropic API requires that `tool_result` blocks appear first in the content array of the user message that follows a tool use; LiteLLM will validate this and surface a clear error if you get it wrong.

### 8.8 Multimodal input via the Anthropic surface

Anthropic's image format differs from OpenAI's: instead of `image_url` with a URL, Anthropic uses `image` with a `source` object that can be `{"type": "url", "url": "..."}` or `{"type": "base64", "media_type": "image/png", "data": "..."}`. LiteLLM translates both directions:

```python
msg = client.messages.create(
    model="minimax-m3",
    max_tokens=512,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image", "source": {
                "type": "url",
                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Cheetah_Masai_Mara.jpg/640px-Cheetah_Masai_Mara.jpg",
            }},
        ],
    }],
)
print(msg.content[0].text)
```

For video input, Anthropic's API has no first-class type. If you need video, use the OpenAI surface (§7.3) where MiniMax-M3 accepts `video_url` parts natively.

---

## 9. Docker Compose deployment

For a reproducible, portable deployment, run LiteLLM in Docker. Create `~/nvidia-proxy/docker-compose.yml`:

```yaml
# ~/nvidia-proxy/docker-compose.yml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    container_name: litellm
    ports:
      - "4000:4000"
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./litellm.db:/app/litellm.db
    environment:
      - NVIDIA_NIM_API_KEY=${NVIDIA_NIM_API_KEY}
      - LOCAL_PROXY_KEY=${LOCAL_PROXY_KEY}
    command: ["--config", "/app/config.yaml", "--port", "4000", "--num_workers", "4"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health/liveness"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Create a `.env` file in the same directory (do NOT commit it):

```bash
# ~/nvidia-proxy/.env
NVIDIA_NIM_API_KEY=nvapi-xxxx...
LOCAL_PROXY_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Launch with:

```bash
cd ~/nvidia-proxy
docker compose up -d
docker compose logs -f litellm   # tail logs
docker compose down               # stop
```

The `--num_workers 4` flag spawns four Uvicorn workers, which lets the proxy handle ~4× more concurrent requests on a multi-core host. Adjust to your CPU count.

---

## 10. Virtual keys and budget control

One of LiteLLM's killer features is **virtual keys**: you can mint per-client or per-team API keys, each with its own rate limit, monthly budget, and allowed-model list. This lets multiple applications share the same proxy while keeping their usage isolated and accountable.

To use virtual keys, you need a database (SQLite is fine for local use, Postgres for production — both are already configured in §5 via `database_url: sqlite:///./litellm.db`). The flow is:

1. **Create a virtual key** using the master key:

```bash
curl -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer $LOCAL_PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "claude-code-personal",
    "max_budget": 5.0,
    "budget_duration": "1mo",
    "rpm_limit": 30,
    "models": ["minimax-m3", "claude-3-5-sonnet-20241022"]
  }'
```

The response contains a new key starting with `sk-`. Save it.

2. **Use the virtual key in place of the master key** in any client:

```bash
export ANTHROPIC_AUTH_TOKEN="sk-<virtual-key-from-step-1>"
claude   # Claude Code now uses this key, subject to the budget and RPM cap
```

3. **Inspect spend** at any time:

```bash
curl http://localhost:4000/key/info?key=sk-<virtual-key> \
  -H "Authorization: Bearer $LOCAL_PROXY_KEY" | jq .
```

4. **Revoke a key**:

```bash
curl -X POST http://localhost:4000/key/delete \
  -H "Authorization: Bearer $LOCAL_PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{"keys": ["sk-<virtual-key>"]}'
```

The admin UI at `http://localhost:4000/ui` (login with the master key) provides a friendly interface for the same operations.

---

## 11. Observability: logs, metrics, health

LiteLLM exposes three layers of observability that you should wire into your local setup:

**Health probes** — Use these in your load balancer or process supervisor:

```bash
curl http://localhost:4000/health/liveness   # always 200 if the process is up
curl http://localhost:4000/health/readiness  # 200 only if upstream NVIDIA is reachable
```

**Prometheus metrics** — Available at `http://localhost:4000/metrics`. Key series include `litellm_requests_total`, `litellm_request_latency_seconds`, `litellm_total_tokens`, `litellm_deployment_latency_per_output_token`, and `litellm_deployment_success_failure_total`. If you already run Prometheus locally, add this scrape config:

```yaml
scrape_configs:
  - job_name: litellm
    static_configs:
      - targets: ["localhost:4000"]
```

**Structured logs** — LiteLLM logs every request in JSON format to stdout, including model, latency, token counts, status, and the masked key. For a more powerful setup, add a logging callback in `config.yaml`:

```yaml
litellm_settings:
  success_callback: ["langfuse"]   # or "otel", "datadog", "s3", "gcs"
  failure_callback: ["langfuse"]
```

Each callback has its own env-var setup documented at <https://docs.litellm.ai/docs/observability>. For purely local use, the default stdout logs plus `jq` are usually sufficient:

```bash
docker compose logs -f litellm | jq 'select(.status_code >= 400)'
```

---

## 12. Troubleshooting

**Symptom: 401 Unauthorized from the proxy.**
Cause: The client's `Authorization` (OpenAI) or `x-api-key` (Anthropic) header does not match `LOCAL_PROXY_KEY`. Verify with `echo $LOCAL_PROXY_KEY` in the shell where the client runs; remember that environment variables do not propagate to other shells automatically.

**Symptom: 401 Unauthorized from NVIDIA (visible in proxy logs).**
Cause: `NVIDIA_NIM_API_KEY` is wrong, expired, or not propagated into the LiteLLM process. If you use Docker Compose, confirm the variable is in the `.env` file and the container has it: `docker compose exec litellm env | grep NVIDIA`.

**Symptom: 429 Too Many Requests.**
Cause: You hit the `rpm: 35` cap in `config.yaml`, or NVIDIA's 40 RPM free-tier cap. LiteLLM returns a 429 with a `Retry-After` header that you should honour. For higher limits, request a quota increase on the NVIDIA developer forum or add a second NVIDIA account as a load-balanced deployment in `model_list`.

**Symptom: Streaming responses arrive all at once instead of incrementally.**
Cause: A buffering proxy (e.g. nginx with `proxy_buffering on`) sits in front of LiteLLM. Either remove the buffering proxy or set `proxy_buffering off;` and `X-Accel-Buffering: no` in nginx. LiteLLM itself sets the right headers, but intermediaries may override them.

**Symptom: Claude Code errors with "unexpected response from API".**
Cause: Usually a tool-use translation mismatch on a feature MiniMax-M3 doesn't fully support. Update LiteLLM to the latest version (`uv tool upgrade litellm`), and check the proxy logs for the failing request — the structured error will identify which field caused the issue.

**Symptom: `max_tokens` required errors on the OpenAI surface.**
Cause: A known NVIDIA NIM quirk with some models — `max_tokens` is required even though the OpenAI spec marks it optional. Set a sensible default in your client code (e.g. 4096) or add `default_headers` / `litellm_params.max_tokens: 4096` in the config.

**Symptom: Long-running requests time out at 60 seconds.**
Cause: The default `request_timeout` was not overridden. Make sure `litellm_settings.request_timeout: 600` is in your `config.yaml` (as in §5). For streaming, also set `streaming_timeout: 600`.

---

## 13. Production checklist

Before relying on this setup for real work, walk through this checklist:

- [ ] `NVIDIA_NIM_API_KEY` and `LOCAL_PROXY_KEY` are stored in a secrets manager or `.env` file, never in version control.
- [ ] `LOCAL_PROXY_KEY` is a 32+ character random string generated with `openssl rand -hex 24`.
- [ ] `config.yaml` uses `os.environ/...` for all secrets — no inline values.
- [ ] `request_timeout: 600` and `streaming_timeout: 600` are set, so 1M-token contexts don't time out.
- [ ] `rpm: 35` is configured to stay under NVIDIA's 40 RPM free-tier cap.
- [ ] `num_retries: 3` is set so transient 429/5xx errors are retried automatically.
- [ ] `drop_params: true` is set so unsupported Anthropic parameters are silently stripped.
- [ ] The proxy is running under a process supervisor (`systemd`, `pm2`, or Docker Compose with `restart: unless-stopped`).
- [ ] Health checks (`/health/liveness` and `/health/readiness`) are wired into your supervisor or load balancer.
- [ ] At least one smoke test from each surface (OpenAI curl + Anthropic curl) is scripted and run after every config change.
- [ ] Claude Code's `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` are set in the shell rc file where you launch `claude`.
- [ ] The `litellm.db` file (if using SQLite) is backed up periodically, or you've migrated to Postgres for production.
- [ ] You've tested failover by deliberately revoking the NVIDIA key and confirming the proxy returns a clear error rather than crashing.
- [ ] Logs are retained for at least 30 days for debugging and audit purposes.

Once everything above is checked off, your local proxy is ready for daily use. Local applications can call `http://localhost:4000` without any knowledge of NVIDIA, MiniMax-M3, or the upstream key — exactly the isolation property you set out to achieve.
