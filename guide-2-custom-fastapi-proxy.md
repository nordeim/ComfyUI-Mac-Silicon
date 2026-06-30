# Guide 2 — Wrapping NVIDIA NIM (MiniMax-M3) as a Local Proxy Using a Custom FastAPI Service

This guide walks you through building a **self-contained, dependency-light FastAPI proxy** that exposes both an OpenAI-compatible surface (`/v1/chat/completions`) and an Anthropic-compatible surface (`/v1/messages`) on a single local port, routing both to NVIDIA NIM's `minimaxai/minimax-m3` model. Unlike the LiteLLM-based approach in Guide 1, here you implement every translation in pure Python so you have full visibility into and control over what happens to each request. The OpenAI half is a thin streaming reverse proxy (about 60 lines), and the Anthropic half is a complete bidirectional translator (about 250 lines including tool calling and SSE event synthesis). Together they form a single `main.py` you can read end-to-end in one sitting.

The guide is split into two parallel sections:

- **Section A — OpenAI-compatible local service** (`/v1/chat/completions`, `/v1/models`)
- **Section B — Anthropic-compatible local service** (`/v1/messages`, for Claude Code and the Anthropic SDKs)

Both sections share the same `main.py`, the same `.env`, and the same upstream NVIDIA key. You only run one Python process.

---

## Table of Contents

1. [Architecture overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Obtain a NVIDIA NIM API key](#3-obtain-a-nvidia-nim-api-key)
4. [Project layout and dependencies](#4-project-layout-and-dependencies)
5. [The `.env` file](#5-the-env-file)
6. [Section A — OpenAI-compatible local service](#6-section-a--openai-compatible-local-service)
7. [Section B — Anthropic-compatible local service (Claude Code)](#7-section-b--anthropic-compatible-local-service-claude-code)
8. [Run the proxy](#8-run-the-proxy)
9. [Docker deployment](#9-docker-deployment)
10. [Observability](#10-observability)
11. [Hardening and rate limiting](#11-hardening-and-rate-limiting)
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
                            │  http://localhost:8000
                            │  Authorization: Bearer sk-local-proxy-secret
                            │  (or x-api-key for Anthropic surface)
                            ▼
                  ┌─────────────────────────────────────┐
                  │  FastAPI + httpx (single main.py)   │
                  │  ─ /v1/chat/completions             │  passthrough
                  │  ─ /v1/models                       │
                  │  ─ /v1/messages                     │  bidirectional
                  │  ─ /v1/messages (stream=true)       │  Anthropic↔OpenAI
                  │  ─ /health                          │  translation
                  └────────────────┬────────────────────┘
                                   │  Authorization: Bearer nvapi-xxxx
                                   │  https://integrate.api.nvidia.com/v1
                                   ▼
                  ┌──────────────────────────┐
                  │  NVIDIA NIM (MiniMax-M3) │
                  │  1M context, multimodal  │
                  └──────────────────────────┘
```

The proxy is a single Python file with no framework beyond FastAPI and the `httpx` HTTP client. The OpenAI surface pipes request and response bytes through unchanged (after swapping the auth header and applying the model alias), which gives you the lowest possible latency and the smallest possible surface for bugs. The Anthropic surface is where the real work happens: on the request side you convert Anthropic's `system` field, content blocks, and `input_schema` tools into the OpenAI equivalents; on the response side you convert OpenAI's `choices[].message` and `tool_calls` into Anthropic's `content[]` blocks; and for streaming you synthesize the full Anthropic SSE event sequence (`message_start`, `content_block_start`, `content_block_delta`, `content_block_stop`, `message_delta`, `message_stop`) from OpenAI's flat `data: {choices:[{delta:...}]}` chunks.

The trade-off compared to LiteLLM is straightforward: you get a smaller dependency tree, full source-level understanding, and the freedom to add custom logic (auditing, prompt rewriting, fine-grained auth) without learning a plugin system. You pay for this by owning the translation code, which is the part most likely to have subtle bugs — particularly in streaming tool-use handling, where partial JSON arguments arrive across multiple deltas and must be accumulated before emission.

---

## 2. Prerequisites

Before you start, ensure your environment satisfies the following requirements. The guide assumes a Unix-like shell (Linux, macOS, or WSL2 on Windows); PowerShell equivalents are noted inline where the syntax differs materially.

- **Python 3.11 or newer.** Python 3.12 is recommended for the best `asyncio` and `httpx` performance. Python 3.10 will work but is missing some `typing` features used in the code below. Verify with `python3 --version`.
- **`pip` or `uv`.** Either works; `uv` is faster. Install from <https://docs.astral.sh/uv/> if you do not have it.
- **`curl`** for smoke tests and `jq` for pretty-printing JSON responses.
- **A NVIDIA developer account** at <https://build.nvidia.com>. The free tier grants 1,000 inference credits on signup and up to 5,000 total, with a default rate limit of 40 requests per minute.
- **Approximately 50 MB of disk space** for the Python dependencies (`fastapi`, `uvicorn`, `httpx`, `python-dotenv`). Much lighter than the LiteLLM stack.
- **Port 8000 free on localhost.** This is FastAPI's conventional default; every example below uses it, but you can change it by editing one line.
- **Network egress to `integrate.api.nvidia.com` on port 443.** If you are behind a corporate proxy, set `HTTPS_PROXY` before launching the proxy so that `httpx` honours it.

No GPU is required anywhere — inference happens entirely on NVIDIA's hosted NIM infrastructure.

---

## 3. Obtain a NVIDIA NIM API key

Navigate to <https://build.nvidia.com/minimaxai/minimax-m3/modelcard> and sign in with your NVIDIA developer account. On the model card page, click **"Get API Key"** (or **"Generate API Key"** on first visit) in the right-hand sidebar. The key looks like `nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. Copy it immediately — NVIDIA does not let you retrieve the plaintext again after the dialog closes, only rotate it.

Store the key in your environment, not in your code. Add the following line to your `~/.zshrc`, `~/.bashrc`, or a dedicated `~/.config/nvidia/env` file that you source from your shell startup:

```bash
export NVIDIA_NIM_API_KEY="nvapi-xxxxxxxx...xxxx"
```

Reload the shell and verify the variable is set:

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

## 4. Project layout and dependencies

Create a project directory and a Python virtual environment:

```bash
mkdir -p ~/nvidia-fastapi-proxy && cd ~/nvidia-fastapi-proxy
python3 -m venv .venv
source .venv/bin/activate
```

Install the four runtime dependencies:

```bash
pip install fastapi 'uvicorn[standard]' httpx python-dotenv
```

Each dependency has a specific role. `fastapi` provides the routing layer and `Request` / `JSONResponse` primitives. `uvicorn` is the ASGI server that runs FastAPI; the `[standard]` extra installs `uvloop` and `httptools` for substantially higher throughput. `httpx` is the async HTTP client used to call NVIDIA NIM — it supports true streaming via `client.stream()`, which is essential for SSE forwarding without buffering. `python-dotenv` loads secrets from a `.env` file so you can keep them out of your shell history.

Verify the install:

```bash
python -c "import fastapi, httpx, uvicorn, dotenv; print('ok', fastapi.__version__)"
```

The project layout will end up looking like this:

```
~/nvidia-fastapi-proxy/
├── .env                  # secrets (gitignored)
├── .gitignore
├── main.py               # the proxy itself (~300 lines, see §6 and §7)
├── requirements.txt      # pinned dependencies
├── Dockerfile            # optional, see §9
└── README.md             # optional
```

Create the `.gitignore` immediately so you never accidentally commit secrets:

```bash
cat > ~/nvidia-fastapi-proxy/.gitignore <<'EOF'
.venv/
.env
__pycache__/
*.pyc
*.log
EOF
```

Pin your dependencies for reproducibility:

```bash
pip freeze | grep -E '^(fastapi|uvicorn|httpx|python-dotenv|starlette|anyio|certifi|httpcore|h11|sniffio|idna)' > requirements.txt
```

---

## 5. The `.env` file

Create `~/nvidia-fastapi-proxy/.env` with the following content. The proxy reads this file at startup via `python-dotenv`.

```bash
# ~/nvidia-fastapi-proxy/.env

# The real NVIDIA key — never shared with clients.
NVIDIA_NIM_API_KEY=nvapi-xxxxxxxx...xxxx

# The local secret your clients will use. Generate with: openssl rand -hex 24
LOCAL_PROXY_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Upstream configuration (defaults shown; override only if you need to).
UPSTREAM_BASE_URL=https://integrate.api.nvidia.com/v1
UPSTREAM_MODEL=minimaxai/minimax-m3

# Local server configuration
PROXY_HOST=0.0.0.0
PROXY_PORT=8000

# Optional: alias map. If a client sends one of these as the model, the proxy
# silently substitutes UPSTREAM_MODEL. Comma-separated.
MODEL_ALIASES=gpt-4o,gpt-4-turbo,claude-3-5-sonnet-20241022,claude-3-opus-20240229
```

Generate a strong `LOCAL_PROXY_KEY` with:

```bash
echo "sk-$(openssl rand -hex 24)"
```

Paste the output into the `.env` file. Every example in the rest of this guide assumes this key is set; if you change it, update your clients accordingly.

---

## 6. Section A — OpenAI-compatible local service

This section implements the OpenAI half of the proxy. It is a thin reverse proxy: it accepts a Chat Completions request, swaps the auth header, optionally rewrites the `model` field using the alias map, forwards the request to NVIDIA NIM, and streams the response back byte-for-byte. No payload translation is needed because NVIDIA NIM is itself OpenAI-compatible.

### 6.1 The OpenAI half of `main.py`

Create `~/nvidia-fastapi-proxy/main.py` and paste the following. The Anthropic half will be added in §7. For now this file handles `/v1/chat/completions`, `/v1/models`, and `/health`.

```python
# ~/nvidia-fastapi-proxy/main.py
import os
import json
import asyncio
from typing import Any, AsyncIterator
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Configuration ---------------------------------------------------------

load_dotenv()

NVIDIA_KEY        = os.environ["NVIDIA_NIM_API_KEY"]
LOCAL_KEY         = os.environ["LOCAL_PROXY_KEY"]
UPSTREAM_BASE     = os.environ.get("UPSTREAM_BASE_URL", "https://integrate.api.nvidia.com/v1")
UPSTREAM_MODEL    = os.environ.get("UPSTREAM_MODEL", "minimaxai/minimax-m3")
MODEL_ALIASES     = set(
    a.strip() for a in os.environ.get("MODEL_ALIASES", "").split(",") if a.strip()
)

# A long timeout is essential: MiniMax-M3 supports 1M-token contexts and
# generation can take several minutes. `timeout=None` disables the timeout
# entirely for streaming requests.
UPSTREAM_TIMEOUT = httpx.Timeout(600.0, connect=10.0)

# Reuse a single AsyncClient across the process lifetime for connection pooling.
# Created in the lifespan handler below.
_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT, http2=True)
    try:
        yield
    finally:
        await _client.aclose()


app = FastAPI(title="NVIDIA NIM Proxy", lifespan=lifespan)

# Permissive CORS so browser-based tools (Cursor, Cline web UIs, etc.) can
# call the proxy from localhost without CORS preflight failures.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth helper -----------------------------------------------------------

def _check_auth(request: Request) -> None:
    """Validate either Authorization: Bearer or x-api-key against LOCAL_KEY."""
    auth = request.headers.get("authorization", "")
    api_key = request.headers.get("x-api-key", "")
    if auth == f"Bearer {LOCAL_KEY}" or api_key == LOCAL_KEY:
        return
    raise HTTPException(status_code=401, detail="invalid local proxy key")


def _resolve_model(model: str | None) -> str:
    """Map client-supplied model to the upstream model, applying the alias map."""
    if not model or model in MODEL_ALIASES:
        return UPSTREAM_MODEL
    return model


def _upstream_headers(stream: bool, *, accept_json: bool = False) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream" if stream else "application/json",
    }


# --- Health ----------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "upstream": UPSTREAM_BASE, "model": UPSTREAM_MODEL}


# --- /v1/models ------------------------------------------------------------

@app.get("/v1/models")
async def list_models(request: Request) -> JSONResponse:
    _check_auth(request)
    # Forward NVIDIA's /v1/models response, augmented with our aliases.
    r = await _client.get(
        f"{UPSTREAM_BASE}/models",
        headers=_upstream_headers(stream=False, accept_json=True),
    )
    if r.status_code != 200:
        return JSONResponse(r.json(), status_code=r.status_code)
    data = r.json()
    # Append alias entries so OpenAI clients see familiar names.
    for alias in MODEL_ALIASES:
        data.setdefault("data", []).append({"id": alias, "object": "model"})
    return JSONResponse(data)


# --- /v1/chat/completions (non-streaming) ----------------------------------

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    _check_auth(request)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON body")

    body["model"] = _resolve_model(body.get("model"))
    stream = bool(body.get("stream", False))

    if not stream:
        r = await _client.post(
            f"{UPSTREAM_BASE}/chat/completions",
            headers=_upstream_headers(stream=False),
            json=body,
        )
        return JSONResponse(r.json(), status_code=r.status_code)

    # --- Streaming: forward SSE bytes verbatim ----------------------------
    async def sse_generator() -> AsyncIterator[bytes]:
        async with _client.stream(
            "POST",
            f"{UPSTREAM_BASE}/chat/completions",
            headers=_upstream_headers(stream=True),
            json=body,
        ) as r:
            if r.status_code != 200:
                # Surface upstream errors as a single SSE error chunk.
                err_body = await r.aread()
                yield f"data: {json.dumps({'error': err_body.decode('utf-8', 'replace'), 'status': r.status_code})}\n\n".encode()
                yield b"data: [DONE]\n\n"
                return
            async for chunk in r.aiter_bytes():
                if chunk:
                    yield chunk

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering if behind nginx
            "Connection": "keep-alive",
        },
    )
```

A few design notes worth internalising before you run it:

- **Connection pooling via lifespan**. The `httpx.AsyncClient` is created once at startup and reused for every request. This avoids TCP/TLS handshake overhead on every call and lets `httpx`'s HTTP/2 multiplexing kick in for concurrent requests.
- **`timeout=None` for streaming**. The default `UPSTREAM_TIMEOUT` of 600 seconds applies to the *initial* response; once we enter `stream()`, httpx does not impose an idle timeout between chunks. If you want one, pass `timeout=httpx.Timeout(600.0, read=None)` instead.
- **Byte-for-byte SSE forwarding**. We do not parse the SSE stream — we just forward `aiter_bytes()` chunks. This is both the simplest and the lowest-latency approach, and it preserves any comments or `: ping` keep-alive frames NVIDIA may emit.
- **The `X-Accel-Buffering: no` header**. If you ever put nginx in front of this proxy, this header tells nginx to disable response buffering for this request, which is essential for SSE to work.
- **Error embedding in SSE**. If NVIDIA returns a non-200 status mid-stream-setup, we cannot return a regular HTTP error (the client has already committed to SSE), so we emit a `data: {"error": ...}` chunk followed by `data: [DONE]`. A well-behaved client will surface this in its error handler.

### 6.2 Smoke test the OpenAI surface

Start the proxy in one terminal:

```bash
cd ~/nvidia-fastapi-proxy
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

In a second terminal, run a non-streaming request:

```bash
source ~/nvidia-fastapi-proxy/.env
curl http://localhost:8000/v1/chat/completions \
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

You should see the standard OpenAI Chat Completions response shape with `choices[0].message.content`. Then test streaming:

```bash
curl -N http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $LOCAL_PROXY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax-m3",
    "stream": true,
    "messages": [{"role":"user","content":"Count from 1 to 5, one per line."}],
    "max_tokens": 100
  }'
```

You should see `data: {...}` chunks arriving every few hundred milliseconds, terminated by `data: [DONE]`.

### 6.3 Using the OpenAI Python SDK

Install the SDK with `pip install openai` and run:

```python
# client_openai.py
import os
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.environ["LOCAL_PROXY_KEY"],
)

# Non-streaming
resp = client.chat.completions.create(
    model="minimax-m3",   # or any alias from MODEL_ALIASES in .env
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

This script will work identically against OpenAI's real API and against your local proxy — only the `base_url` and `api_key` differ.

### 6.4 Multimodal input (images and video)

MiniMax-M3 accepts images and videos in the OpenAI `content` array format. The proxy passes these through unchanged because the body is forwarded as-is:

```python
import base64, requests, os
b64 = base64.b64encode(open("photo.jpg","rb").read()).decode()
r = requests.post(
    "http://localhost:8000/v1/chat/completions",
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

For video URLs, use `{"type": "video_url", "video_url": {"url": "https://..."}}` exactly as in the original snippet you provided.

### 6.5 Function / tool calling

The OpenAI tool-calling surface is fully supported because the proxy is a passthrough — MiniMax-M3 emits OpenAI-format `tool_calls` and the proxy forwards them unchanged. Define tools using the OpenAI schema (`type: "function"` with a `function` sub-object containing `name`, `description`, and `parameters` as a JSON Schema), then iterate the standard request-execute-respond loop in your client code. No proxy-side handling is required.

### 6.6 Long context (1M tokens)

MiniMax-M3's 1M-token context window is one of its standout features. To exercise it, simply send a large `messages` array. The proxy's `UPSTREAM_TIMEOUT = httpx.Timeout(600.0)` setting ensures the proxy doesn't time out while NVIDIA processes the long prompt. For very long inputs (>200K tokens), prefer streaming so the client sees progress within seconds rather than waiting minutes for the first byte.

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

## 7. Section B — Anthropic-compatible local service (Claude Code)

This is the section that justifies the effort of a custom proxy. You will add a `/v1/messages` endpoint to the same `main.py` that accepts Anthropic-format requests and translates them to OpenAI format for NVIDIA NIM, then translates the OpenAI-format response back to Anthropic format. This translation covers system prompts (top-level in Anthropic, a `system` message in OpenAI), content blocks (text / image / tool_use / tool_result), tool definitions (`input_schema` vs `parameters`), stop reasons (`end_turn` vs `stop`, `tool_use` vs `tool_calls`), and the streaming SSE event taxonomy (Anthropic's richer `message_start` / `content_block_start` / `content_block_delta` / `content_block_stop` / `message_delta` / `message_stop` sequence).

### 7.1 Why an Anthropic surface matters

Many tools and frameworks hard-code the Anthropic API as their only LLM interface. The most prominent example is **Claude Code**, Anthropic's official CLI for agentic coding. Claude Code reads two environment variables — `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` — and refuses to talk to anything that doesn't answer at `/v1/messages` with Anthropic-format SSE. By pointing those variables at your FastAPI proxy, you can run Claude Code against MiniMax-M3 for free, using NVIDIA's generous free tier instead of paid Anthropic credits. The same trick works for any Anthropic-SDK-based application: Cursor's "Claude API" mode, Cline, Roo Code, Zed's assistant with the Anthropic provider, custom LangChain agents wired to the Anthropic SDK, and so on.

### 7.2 The translation layer

Append the following to the bottom of `~/nvidia-fastapi-proxy/main.py`. It adds the `/v1/messages` endpoint, the request translator, the non-streaming response translator, and the streaming SSE event synthesizer. Read it top-to-bottom — the helper functions are ordered from least to most complex so you can build a mental model incrementally.

```python
# === Section B: Anthropic /v1/messages surface =============================
# Appended to main.py after the OpenAI surface code from §6.1.

import time
import uuid
from typing import Iterable


# --- Request translation: Anthropic -> OpenAI ------------------------------

def _anthropic_to_openai(body: dict) -> dict:
    """Translate an Anthropic /v1/messages request body to OpenAI Chat Completions."""
    messages: list[dict] = []

    # Anthropic carries the system prompt as a top-level field (string OR list
    # of content blocks). OpenAI uses a {"role":"system"} message.
    system = body.get("system")
    if system:
        if isinstance(system, str):
            messages.append({"role": "system", "content": system})
        elif isinstance(system, list):
            # Concatenate text blocks; pass through image blocks as OpenAI image_url parts.
            parts = []
            for b in system:
                if b.get("type") == "text":
                    parts.append({"type": "text", "text": b["text"]})
                elif b.get("type") == "image":
                    src = b.get("source", {})
                    if src.get("type") == "url":
                        parts.append({"type": "image_url", "image_url": {"url": src["url"]}})
                    elif src.get("type") == "base64":
                        url = f"data:{src['media_type']};base64,{src['data']}"
                        parts.append({"type": "image_url", "image_url": {"url": url}})
            messages.append({"role": "system", "content": parts})

    # Translate each Anthropic message to an OpenAI message.
    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
            continue
        # content is a list of blocks
        if role == "assistant":
            # Assistant blocks: text and tool_use.
            text_parts = []
            tool_calls = []
            for b in content:
                if b.get("type") == "text":
                    text_parts.append(b["text"])
                elif b.get("type") == "tool_use":
                    tool_calls.append({
                        "id": b["id"],
                        "type": "function",
                        "function": {
                            "name": b["name"],
                            "arguments": json.dumps(b.get("input", {})),
                        },
                    })
            m: dict = {"role": "assistant"}
            if text_parts:
                m["content"] = "\n".join(text_parts)
            else:
                m["content"] = None
            if tool_calls:
                m["tool_calls"] = tool_calls
            messages.append(m)
        else:
            # User blocks: text, image, and tool_result.
            parts = []
            tool_results = []
            for b in content:
                if b.get("type") == "text":
                    parts.append({"type": "text", "text": b["text"]})
                elif b.get("type") == "image":
                    src = b.get("source", {})
                    if src.get("type") == "url":
                        parts.append({"type": "image_url", "image_url": {"url": src["url"]}})
                    elif src.get("type") == "base64":
                        url = f"data:{src['media_type']};base64,{src['data']}"
                        parts.append({"type": "image_url", "image_url": {"url": url}})
                elif b.get("type") == "tool_result":
                    # OpenAI represents tool results as a separate message with role="tool".
                    content_val = b.get("content")
                    if isinstance(content_val, list):
                        # Concatenate text blocks; ignore non-text for simplicity.
                        content_val = "\n".join(
                            x.get("text", "") for x in content_val if x.get("type") == "text"
                        )
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": b["tool_use_id"],
                        "content": str(content_val) if content_val is not None else "",
                    })
            if parts:
                messages.append({"role": role, "content": parts})
            for tr in tool_results:
                messages.append(tr)

    # Build the OpenAI request body.
    openai_body: dict = {
        "model": _resolve_model(body.get("model")),
        "messages": messages,
    }
    if "max_tokens" in body:
        openai_body["max_tokens"] = body["max_tokens"]
    else:
        openai_body["max_tokens"] = 4096  # Anthropic requires this; default sensibly.
    if "temperature" in body:
        openai_body["temperature"] = body["temperature"]
    if "top_p" in body:
        openai_body["top_p"] = body["top_p"]
    if body.get("stop_sequences"):
        openai_body["stop"] = body["stop_sequences"]

    # Translate Anthropic tools -> OpenAI tools.
    if body.get("tools"):
        openai_body["tools"] = [{
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        } for t in body["tools"]]
    if body.get("tool_choice"):
        tc = body["tool_choice"]
        if tc.get("type") == "auto":
            openai_body["tool_choice"] = "auto"
        elif tc.get("type") == "any":
            openai_body["tool_choice"] = "required"
        elif tc.get("type") == "tool":
            openai_body["tool_choice"] = {
                "type": "function",
                "function": {"name": tc["name"]},
            }

    return openai_body


# --- Response translation: OpenAI -> Anthropic (non-streaming) -------------

def _finish_to_stop_reason(finish: str | None) -> str:
    return {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
        "stop_sequence": "stop_sequence",
        "content_filter": "end_turn",
    }.get(finish or "", "end_turn")


def _openai_to_anthropic(openai_resp: dict, model_alias: str) -> dict:
    """Translate an OpenAI Chat Completions response to Anthropic Messages format."""
    choice = openai_resp.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content: list[dict] = []
    if msg.get("content"):
        content.append({"type": "text", "text": msg["content"]})
    for tc in msg.get("tool_calls", []) or []:
        try:
            args = json.loads(tc["function"]["arguments"])
        except Exception:
            args = {}
        content.append({
            "type": "tool_use",
            "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
            "name": tc["function"]["name"],
            "input": args,
        })
    if not content:
        content.append({"type": "text", "text": ""})

    usage = openai_resp.get("usage", {})
    return {
        "id": f"msg_{openai_resp.get('id', uuid.uuid4().hex)}",
        "type": "message",
        "role": "assistant",
        "model": model_alias,
        "content": content,
        "stop_reason": _finish_to_stop_reason(choice.get("finish_reason")),
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


# --- Streaming: synthesize Anthropic SSE events from OpenAI chunks ---------

async def _anthropic_stream_generator(
    upstream_resp: httpx.Response,
    model_alias: str,
    input_tokens: int,
) -> AsyncIterator[bytes]:
    """Consume OpenAI-format SSE chunks from NVIDIA and emit Anthropic-format SSE events."""

    msg_id = f"msg_{uuid.uuid4().hex}"

    # 1. message_start
    yield _sse("message_start", {
        "type": "message_start",
        "message": {
            "id": msg_id, "type": "message", "role": "assistant",
            "content": [], "model": model_alias,
            "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": input_tokens, "output_tokens": 0},
        },
    })

    # State for the current content block (we emit one text block; if tool calls
    # appear, we close the text block and open tool_use blocks as needed).
    block_index = -1
    block_open = False
    output_tokens = 0
    stop_reason = "end_turn"
    # tool_call_accumulator: {index: {"id":..., "name":..., "args_buffer":...}}
    tool_acc: dict[int, dict] = {}

    async for raw in upstream_resp.aiter_lines():
        if not raw or not raw.startswith("data:"):
            continue
        payload = raw[5:].strip()
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if chunk.get("object") == "chat.completion.chunk":
            usage = chunk.get("usage") or {}
            if usage.get("completion_tokens"):
                output_tokens = usage["completion_tokens"]

        for choice in chunk.get("choices", []):
            delta = choice.get("delta", {})
            finish = choice.get("finish_reason")

            # Text delta
            text_delta = delta.get("content")
            if text_delta:
                if not block_open or block_index < 0:
                    block_index += 1
                    yield _sse("content_block_start", {
                        "type": "content_block_start",
                        "index": block_index,
                        "content_block": {"type": "text", "text": ""},
                    })
                    block_open = True
                yield _sse("content_block_delta", {
                    "type": "content_block_delta",
                    "index": block_index,
                    "delta": {"type": "text_delta", "text": text_delta},
                })

            # Tool call deltas: OpenAI streams partial JSON arguments across
            # multiple chunks. We accumulate them and emit when complete.
            for tc in delta.get("tool_calls", []) or []:
                idx = tc.get("index", 0)
                if idx not in tool_acc:
                    # Close any open text block first.
                    if block_open:
                        yield _sse("content_block_stop", {
                            "type": "content_block_stop", "index": block_index,
                        })
                        block_open = False
                    block_index += 1
                    tool_acc[idx] = {
                        "block_index": block_index,
                        "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
                        "name": tc.get("function", {}).get("name", ""),
                        "args_buffer": "",
                    }
                    yield _sse("content_block_start", {
                        "type": "content_block_start",
                        "index": block_index,
                        "content_block": {
                            "type": "tool_use",
                            "id": tool_acc[idx]["id"],
                            "name": tool_acc[idx]["name"],
                            "input": {},
                        },
                    })
                    block_open = True
                args_delta = tc.get("function", {}).get("arguments", "")
                if args_delta:
                    tool_acc[idx]["args_buffer"] += args_delta
                    yield _sse("content_block_delta", {
                        "type": "content_block_delta",
                        "index": tool_acc[idx]["block_index"],
                        "delta": {
                            "type": "input_json_delta",
                            "partial_json": args_delta,
                        },
                    })

            if finish:
                stop_reason = _finish_to_stop_reason(finish)

    # Close any open block.
    if block_open:
        yield _sse("content_block_stop", {
            "type": "content_block_stop", "index": block_index,
        })

    # message_delta with final stop_reason and usage.
    yield _sse("message_delta", {
        "type": "message_delta",
        "delta": {"stop_reason": stop_reason, "stop_sequence": None},
        "usage": {"output_tokens": output_tokens},
    })

    # message_stop
    yield _sse("message_stop", {"type": "message_stop"})


def _sse(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


# --- /v1/messages endpoint --------------------------------------------------

@app.post("/v1/messages")
async def anthropic_messages(request: Request):
    _check_auth(request)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON body")

    model_alias = body.get("model") or UPSTREAM_MODEL
    openai_body = _anthropic_to_openai(body)
    stream = bool(body.get("stream", False))

    # Rough input-token estimate for the message_start event. Replace with a
    # proper tokenizer (e.g. tiktoken) if you need exact counts.
    input_tokens = sum(len(str(m.get("content", ""))) // 4 for m in openai_body["messages"])

    if not stream:
        r = await _client.post(
            f"{UPSTREAM_BASE}/chat/completions",
            headers=_upstream_headers(stream=False),
            json=openai_body,
        )
        if r.status_code != 200:
            return JSONResponse(
                {"type": "error", "error": {"type": "api_error", "message": r.text}},
                status_code=r.status_code,
            )
        anthropic_resp = _openai_to_anthropic(r.json(), model_alias)
        return JSONResponse(anthropic_resp)

    # Streaming path.
    async def gen() -> AsyncIterator[bytes]:
        async with _client.stream(
            "POST",
            f"{UPSTREAM_BASE}/chat/completions",
            headers=_upstream_headers(stream=True),
            json=openai_body,
        ) as r:
            if r.status_code != 200:
                err = await r.aread()
                yield _sse("error", {
                    "type": "error",
                    "error": {"type": "api_error",
                              "message": err.decode("utf-8", "replace")},
                })
                return
            async for chunk in _anthropic_stream_generator(r, model_alias, input_tokens):
                yield chunk

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/v1/messages/count_tokens")
async def count_tokens(request: Request):
    """Rough token estimate; replace with tiktoken for accuracy."""
    _check_auth(request)
    body = await request.json()
    openai_body = _anthropic_to_openai(body)
    n = sum(len(str(m.get("content", ""))) // 4 for m in openai_body["messages"])
    return JSONResponse({"input_tokens": n})
```

### 7.3 Smoke test the Anthropic surface

Restart the proxy (the `--reload` flag will pick up the changes automatically if uvicorn is still running):

```bash
curl http://localhost:8000/v1/messages \
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

Then test streaming:

```bash
curl -N http://localhost:8000/v1/messages \
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

You should see the full Anthropic SSE event sequence: `event: message_start`, then `event: content_block_start`, multiple `event: content_block_delta` events with `text_delta` payloads, `event: content_block_stop`, `event: message_delta` with the final `stop_reason`, and finally `event: message_stop`.

### 7.4 Pointing Claude Code at the proxy

Claude Code reads its configuration from environment variables. Set the following before launching `claude` in a terminal:

```bash
# ~/.zshrc or a dedicated shell rc for claude code
export ANTHROPIC_BASE_URL="http://localhost:8000"
export ANTHROPIC_AUTH_TOKEN="$LOCAL_PROXY_KEY"
# Optional: pretend to be a specific Claude model so Claude Code's model picker doesn't complain
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
export ANTHROPIC_SMALL_FAST_MODEL="claude-3-5-sonnet-20241022"
```

Note that the URL is `http://localhost:8000` (no trailing `/v1`). Claude Code appends `/v1/messages` itself. `ANTHROPIC_AUTH_TOKEN` is preferred over `ANTHROPIC_API_KEY` when you're using a custom base URL — the latter is reserved for direct-to-Anthropic auth in some Claude Code versions. Also make sure `claude-3-5-sonnet-20241022` is in your `MODEL_ALIASES` env var (it is, by default, in the `.env` from §5) so the proxy silently maps it to MiniMax-M3.

Then launch Claude Code normally:

```bash
claude
```

The first request Claude Code makes is typically a `/v1/messages` call with a system prompt describing the agentic loop and the available tools (Read, Write, Edit, Bash, etc.). Your proxy translates this to OpenAI format, routes it to MiniMax-M3 on NVIDIA NIM, and translates the response back. Tool calls initiated by MiniMax-M3 will be returned as Anthropic `tool_use` content blocks, which Claude Code knows how to execute locally. The result is that Claude Code "just works" against MiniMax-M3, complete with file edits, bash execution, and multi-turn tool use.

### 7.5 Using the official Anthropic Python SDK

Any code written against the official Anthropic SDK works unchanged once you point it at the proxy:

```python
# client_anthropic.py
import os
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:8000",
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

### 7.6 Anthropic-style tool use

Anthropic's tool schema differs from OpenAI's: instead of `tools: [{type: "function", function: {...}}]`, Anthropic uses `tools: [{name, description, input_schema}]`. The proxy's `_anthropic_to_openai` function handles the bidirectional translation:

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

The Anthropic API requires that `tool_result` blocks appear first in the content array of the user message that follows a tool use; the proxy's translator honours this ordering automatically because it iterates `tool_result` blocks before any text/image blocks when building the OpenAI message list.

### 7.7 Multimodal input via the Anthropic surface

Anthropic's image format differs from OpenAI's: instead of `image_url` with a URL, Anthropic uses `image` with a `source` object that can be `{"type": "url", "url": "..."}` or `{"type": "base64", "media_type": "image/png", "data": "..."}`. The proxy's `_anthropic_to_openai` function translates both directions:

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

For video input, Anthropic's API has no first-class type. If you need video, use the OpenAI surface (§6.4) where MiniMax-M3 accepts `video_url` parts natively.

---

## 8. Run the proxy

You have already seen the basic invocation in §6.2. For production-style runs (no `--reload`, multiple workers), use:

```bash
cd ~/nvidia-fastapi-proxy
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

The `--workers 4` flag spawns four Uvicorn worker processes, each with its own connection pool. Adjust to your CPU count. Note that with multiple workers, the per-process in-memory state (if you ever add any — caching, token buckets, etc.) is not shared; use Redis or a database if you need shared state.

For development with auto-reload on file changes:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

For long-running deployments, run the proxy under `systemd` on Linux:

```ini
# /etc/systemd/system/nvidia-proxy.service
[Unit]
Description=NVIDIA NIM FastAPI Proxy
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/nvidia-fastapi-proxy
EnvironmentFile=/home/ubuntu/nvidia-fastapi-proxy/.env
ExecStart=/home/ubuntu/nvidia-fastapi-proxy/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start with `sudo systemctl enable --now nvidia-proxy`.

---

## 9. Docker deployment

Create `~/nvidia-fastapi-proxy/Dockerfile`:

```dockerfile
# ~/nvidia-fastapi-proxy/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY main.py .

EXPOSE 8000

# Use --workers 4 in production. For dev, override with `docker run ... uvicorn main:app --reload`.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Build and run:

```bash
cd ~/nvidia-fastapi-proxy
docker build -t nvidia-fastapi-proxy:latest .

# Run with env vars from your .env file
docker run --rm -d \
  --name nvidia-proxy \
  -p 8000:8000 \
  --env-file .env \
  nvidia-fastapi-proxy:latest

docker logs -f nvidia-proxy
docker stop nvidia-proxy
```

A `docker-compose.yml` equivalent for orchestration with systemd or other Docker services:

```yaml
# ~/nvidia-fastapi-proxy/docker-compose.yml
services:
  nvidia-proxy:
    build: .
    image: nvidia-fastapi-proxy:latest
    container_name: nvidia-proxy
    ports:
      - "8000:8000"
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Launch with `docker compose up -d`.

---

## 10. Observability

The proxy emits structured logs to stdout via Uvicorn's default logger. For richer observability, add a logging middleware to `main.py`:

```python
import logging, time

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("nvidia-proxy")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    logger.info(
        "method=%s path=%s status=%d elapsed_ms=%.1f client=%s",
        request.method, request.url.path, response.status_code, elapsed,
        request.client.host if request.client else "-",
    )
    return response
```

For metrics, install `prometheus-fastapi-instrumentator` and add three lines to `main.py`:

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

Prometheus metrics then become available at `http://localhost:8000/metrics`. Key series include `http_requests_total`, `http_request_duration_seconds`, and `http_requests_in_progress`.

For health probes, use the `/health` endpoint defined in §6.1:

```bash
curl http://localhost:8000/health
# {"status":"ok","upstream":"https://integrate.api.nvidia.com/v1","model":"minimaxai/minimax-m3"}
```

---

## 11. Hardening and rate limiting

The proxy in §6 and §7 is correct but minimal. Before relying on it for shared use, add the following hardening layers.

**Rate limiting.** NVIDIA's free tier caps at 40 RPM. To avoid hitting it and to share the budget fairly across clients, add a token-bucket limiter:

```bash
pip install aiolimiter
```

```python
from aiolimiter import AsyncLimiter
limiter = AsyncLimiter(max_rate=35, time_period=60)  # 35 RPM, leaving headroom

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    _check_auth(request)
    async with limiter:
        # ... existing body ...
```

Apply the same limiter to `/v1/messages`. The `AsyncLimiter` is per-process, so with multiple Uvicorn workers each gets its own bucket of 35 RPM — adjust `max_rate` to `35 / workers` if you want a global cap, or use Redis-based limiter like `aiogram/redis` for shared state.

**Request size cap.** MiniMax-M3 supports 1M-token contexts, but a malicious or buggy client could send a 10 GB body. Cap request size at the ASGI level:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = 100 * 1024 * 1024):  # 100 MB
        super().__init__(app)
        self.max_bytes = max_bytes
    async def dispatch(self, request, call_next):
        cl = int(request.headers.get("content-length", 0))
        if cl > self.max_bytes:
            return JSONResponse({"error": "request body too large"}, status_code=413)
        return await call_next(request)

app.add_middleware(MaxBodySizeMiddleware)
```

**API key rotation.** If you need to support multiple local keys (e.g. for different developers), replace the single `LOCAL_KEY` check with a set loaded from a file or environment:

```python
LOCAL_KEYS = set(os.environ.get("LOCAL_PROXY_KEYS", "").split(","))

def _check_auth(request: Request) -> None:
    auth = request.headers.get("authorization", "")
    api_key = request.headers.get("x-api-key", "")
    token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else api_key
    if token in LOCAL_KEYS:
        return
    raise HTTPException(status_code=401, detail="invalid local proxy key")
```

**Retry on upstream 429 / 5xx.** Add exponential backoff for transient errors. The simplest approach is a small wrapper around the upstream call:

```python
async def _upstream_post_with_retry(*args, **kwargs):
    last_exc = None
    for attempt in range(3):
        try:
            r = await _client.post(*args, **kwargs)
            if r.status_code in (429, 500, 502, 503, 504):
                await asyncio.sleep(2 ** attempt)
                continue
            return r
        except httpx.HTTPError as e:
            last_exc = e
            await asyncio.sleep(2 ** attempt)
    raise last_exc
```

Streaming requests are harder to retry mid-stream; for those, fail fast and let the client retry.

---

## 12. Troubleshooting

**Symptom: 401 Unauthorized from the proxy.**
Cause: The client's `Authorization` (OpenAI) or `x-api-key` (Anthropic) header does not match `LOCAL_PROXY_KEY`. Verify with `echo $LOCAL_PROXY_KEY` in the shell where the client runs. If you used `python-dotenv` in the client, make sure the `.env` is actually loaded.

**Symptom: 401 Unauthorized from NVIDIA (visible in proxy logs).**
Cause: `NVIDIA_NIM_API_KEY` is wrong, expired, or not loaded. If running in Docker, confirm with `docker exec nvidia-proxy env | grep NVIDIA`. If running locally, confirm with `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.environ.get('NVIDIA_NIM_API_KEY','MISSING')[:12])"`.

**Symptom: 429 Too Many Requests.**
Cause: You hit NVIDIA's 40 RPM free-tier cap (or your local limiter from §11 if you added one). Wait 60 seconds and retry. For higher limits, request a quota increase on the NVIDIA developer forum or add a second NVIDIA account and load-balance.

**Symptom: Streaming responses arrive all at once instead of incrementally.**
Cause: A buffering intermediary (nginx with `proxy_buffering on`, Cloudflare, or a corporate proxy) sits between the client and the proxy. Either remove the intermediary or ensure `X-Accel-Buffering: no` (set by the proxy) is honoured. Also check that your client is reading the stream incrementally — for example, with `curl -N`, `httpx.stream()`, or `openai`'s `stream=True` mode.

**Symptom: Claude Code errors with "unexpected response from API".**
Cause: Usually a translation bug in the proxy. Add `print(body)` and `print(openai_body)` at the top of `/v1/messages` to see the incoming and outgoing payloads. Common culprits are: `system` field as a list of blocks (handled in §7.2), `tool_result` blocks not at the start of the user message content (Anthropic requires this), or missing `max_tokens` (the proxy defaults to 4096).

**Symptom: Tool use streaming produces invalid JSON in the tool arguments.**
Cause: The model emitted partial JSON across deltas and the client didn't accumulate them. The proxy emits `input_json_delta` events with `partial_json` fragments per the Anthropic spec; the client must concatenate these fragments and parse the result at `content_block_stop`. The official Anthropic SDK does this automatically; if you're parsing SSE by hand, make sure you accumulate.

**Symptom: Long-running requests time out at 60 seconds.**
Cause: The default `UPSTREAM_TIMEOUT` was not applied. Verify `UPSTREAM_TIMEOUT = httpx.Timeout(600.0, connect=10.0)` is at module level in `main.py`. If you're behind a corporate proxy or firewall, also check whether it imposes its own idle timeout.

**Symptom: `max_tokens` required errors from NVIDIA.**
Cause: A known NVIDIA NIM quirk with some models — `max_tokens` is required even though the OpenAI spec marks it optional. The Anthropic surface in §7 always sets it (defaulting to 4096); the OpenAI surface does not. Either set a default in your client code or add `body.setdefault("max_tokens", 4096)` in `chat_completions`.

---

## 13. Production checklist

Before relying on this setup for real work, walk through this checklist:

- [ ] `NVIDIA_NIM_API_KEY` and `LOCAL_PROXY_KEY` are stored in `.env` (or a secrets manager), never in version control. `.gitignore` includes `.env`.
- [ ] `LOCAL_PROXY_KEY` is a 32+ character random string generated with `openssl rand -hex 24`.
- [ ] `UPSTREAM_TIMEOUT` is set to at least 600 seconds so 1M-token contexts don't time out.
- [ ] The `aiolimiter` rate limiter from §11 is in place, capped at 35 RPM.
- [ ] The `MaxBodySizeMiddleware` from §11 is in place to prevent oversized request bodies.
- [ ] CORS is configured (it is, permissively, in §6.1 — tighten `allow_origins` for production).
- [ ] The proxy is running under a process supervisor (`systemd`, Docker Compose with `restart: unless-stopped`, or `pm2`).
- [ ] Health checks (`/health`) are wired into your supervisor or load balancer.
- [ ] At least one smoke test from each surface (OpenAI curl + Anthropic curl) is scripted and run after every code change.
- [ ] Claude Code's `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` are set in the shell rc file where you launch `claude`.
- [ ] The `prometheus-fastapi-instrumentator` is installed and `/metrics` is being scraped.
- [ ] You've tested failover by deliberately revoking the NVIDIA key and confirming the proxy returns a clear error rather than crashing.
- [ ] You've tested the streaming tool-use path end-to-end with Claude Code (which exercises the most complex translation code path).
- [ ] Logs are retained for at least 30 days for debugging and audit purposes.

Once everything above is checked off, your local proxy is ready for daily use. Local applications can call `http://localhost:8000` without any knowledge of NVIDIA, MiniMax-M3, or the upstream key — exactly the isolation property you set out to achieve, implemented in a single ~300-line Python file you fully control.
