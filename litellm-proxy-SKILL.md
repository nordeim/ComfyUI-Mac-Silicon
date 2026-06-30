# LiteLLM Proxy Setup for macOS

## Overview

Sets up a local LiteLLM proxy on macOS that wraps NVIDIA NIM (MiniMax-M3) as a local gateway, providing both OpenAI-compatible (`/v1/chat/completions`) and Anthropic-compatible (`/v1/messages`) endpoints on `http://localhost:4000`.

## Trigger

Use this skill when the user wants to:
- Install and configure LiteLLM proxy on macOS
- Set up a local AI gateway for NVIDIA NIM models
- Set up a local AI gateway for OpenRouter.ai (200+ models)
- Configure Claude Code to use a custom/local API endpoint
- Create a launchd service for LiteLLM
- Set up OpenAI/Anthropic SDK env vars for local proxy

## Prerequisites

- macOS (tested on Apple Silicon)
- Python 3.11+ (Python 3.13 recommended)
- Homebrew installed
- NVIDIA developer account with API key from https://build.nvidia.com
- Port 4000 free on localhost

---

## Step 1: Install Python 3.13

```bash
brew install python@3.13
```

Verify:
```bash
/opt/homebrew/bin/python3.13 --version
```

---

## Step 2: Create LiteLLM Virtual Environment

```bash
# Stop any existing litellm proxy
kill $(lsof -ti :4000) 2>/dev/null

# Remove old venv if exists
rm -rf ~/.venvs/litellm

# Create new venv with Python 3.13
/opt/homebrew/bin/python3.13 -m venv ~/.venvs/litellm

# Install litellm with proxy extras
~/.venvs/litellm/bin/pip install 'litellm[proxy]'
```

Verify:
```bash
~/.venvs/litellm/bin/python --version   # Should show Python 3.13.x
~/.venvs/litellm/bin/litellm --version  # Should show 1.50+
```

---

## Step 3: Create Config Directory and config.yaml

```bash
mkdir -p ~/nvidia-proxy
```

Create `~/nvidia-proxy/config.yaml`:

```yaml
# ~/nvidia-proxy/config.yaml
# LiteLLM Proxy configuration for NVIDIA NIM (minimaxai/minimax-m3)
# Supports both OpenAI and Anthropic API surfaces on port 4000.

model_list:
  # Primary alias
  - model_name: minimax-m3
    litellm_params:
      model: nvidia_nim/minimaxai/minimax-m3
      api_key: os.environ/NVIDIA_NIM_API_KEY
      rpm: 35

  # Convenience aliases for client compatibility
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

litellm_settings:
  drop_params: true
  num_retries: 3
  request_timeout: 600
  streaming_timeout: 600

general_settings:
  # master_key: os.environ/LOCAL_PROXY_KEY  # Commented: no admin needed
  # database_url: sqlite:///./litellm.db    # Commented: no DB needed
  disable_admin_ui: true
```

**Key config notes:**
- `rpm: 35` stays under NVIDIA's 40 RPM free-tier cap
- `drop_params: true` silently strips unsupported Anthropic params
- `request_timeout: 600` supports 1M token contexts
- `master_key` and `database_url` commented out for basic proxy-only use

---

## Step 4: Configure Shell Environment Variables

### 4.1 Ensure NVIDIA API Key is Set

Add to `~/.zshrc` and `~/.bashrc` (if not already present):

```bash
export NVIDIA_NIM_API_KEY="nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 4.2 Add LiteLLM Proxy Variables

Append to both `~/.zshrc` and `~/.bashrc`:

```bash
# --- LiteLLM Proxy (http://localhost:4000) ---
# source ~/venvs/mlx-env/bin/activate  # Comment out if present: conflicts with litellm venv
export OPENAI_API_BASE="http://localhost:4000/v1"
export OPENAI_API_KEY="sk-local-proxy"
export ANTHROPIC_BASE_URL="http://localhost:4000"
export ANTHROPIC_AUTH_TOKEN="sk-local-proxy"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
export ANTHROPIC_SMALL_FAST_MODEL="claude-3-5-sonnet-20241022"
```

### 4.3 Comment Out Conflicting Variables

In both `~/.zshrc` and `~/.bashrc`, comment out:
- `NVIDIA_API_KEY` (duplicate of `NVIDIA_NIM_API_KEY`)
- `source ~/venvs/mlx-env/bin/activate` (activates wrong venv)

---

## Step 5: Create launchd Service (Auto-Start on Login)

### 5.1 Create the plist

```bash
mkdir -p ~/Library/LaunchAgents
```

Create `~/Library/LaunchAgents/com.litellm.proxy.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.litellm.proxy</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/.venvs/litellm/bin/litellm</string>
        <string>--config</string>
        <string>/Users/YOUR_USERNAME/nvidia-proxy/config.yaml</string>
        <string>--port</string>
        <string>4000</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/nvidia-proxy</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/nvidia-proxy/litellm.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/nvidia-proxy/litellm.err.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>NVIDIA_NIM_API_KEY</key>
        <string>nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</string>
    </dict>
</dict>
</plist>
```

**IMPORTANT:** Replace `YOUR_USERNAME` and the NVIDIA API key with actual values.

### 5.2 Load the Service

```bash
launchctl load ~/Library/LaunchAgents/com.litellm.proxy.plist
```

Verify:
```bash
launchctl list | grep litellm
# Should show: PID STATUS com.litellm.proxy
```

---

## Step 6: Configure Claude Code

### 6.1 Create Settings Directory

```bash
mkdir -p ~/.claude
```

### 6.2 Create `~/.claude/settings.json`

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-local-proxy",
    "ANTHROPIC_MODEL": "claude-3-5-sonnet-20241022",
    "ANTHROPIC_SMALL_FAST_MODEL": "claude-3-5-sonnet-20241022"
  },
  "apiBaseUrl": "http://localhost:4000",
  "model": "claude-3-5-sonnet-20241022"
}
```

### 6.3 Create `~/.claude.json` (Skip Onboarding)

```json
{
  "hasCompletedOnboarding": true
}
```

### 6.4 Create `~/.claude/.credentials.json` (Skip Login)

```json
{
  "apiKey": "sk-local-proxy",
  "hasCompletedOnboarding": true
}
```

### 6.5 Install Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

---

## Step 7: Testing

### 7.1 Health Check

```bash
curl http://localhost:4000/health/liveness
# Expected: "I'm alive!"
```

### 7.2 List Models

```bash
curl -s http://localhost:4000/v1/models | python3 -m json.tool
# Expected: 3 models (minimax-m3, gpt-4o, claude-3-5-sonnet-20241022)
```

### 7.3 OpenAI-Compatible Test

```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax-m3",
    "messages": [{"role":"user","content":"Say hi in 3 words."}],
    "max_tokens": 32
  }' | python3 -m json.tool
```

### 7.4 Anthropic-Compatible Test

```bash
curl -s http://localhost:4000/v1/messages \
  -H "x-api-key: $NVIDIA_NIM_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role":"user","content":"Say hi in 3 words."}]
  }' | python3 -m json.tool
```

### 7.5 Claude Code CLI Test

```bash
source ~/.zshrc
claude -p "Say hello in 5 words"
# Expected: Response from minimax-m3 via proxy
```

### 7.6 Verify Proxy Logs

```bash
tail -5 ~/nvidia-proxy/litellm.log
# Expected: POST /v1/messages?beta=true HTTP/1.1 200 OK
```

---

## Management Commands

### Service Control

```bash
# Stop proxy
launchctl unload ~/Library/LaunchAgents/com.litellm.proxy.plist

# Start proxy
launchctl load ~/Library/LaunchAgents/com.litellm.proxy.plist

# Check status
launchctl list | grep litellm
```

### View Logs

```bash
# Stdout logs
tail -f ~/nvidia-proxy/litellm.log

# Error logs
tail -f ~/nvidia-proxy/litellm.err.log
```

### Manual Run (Foreground)

```bash
source ~/.venvs/litellm/bin/activate
cd ~/nvidia-proxy
litellm --config config.yaml --port 4000
```

---

## File Structure

```
~/
├── .zshrc                          # Shell env vars (OPENAI_*, ANTHROPIC_*)
├── .bashrc                         # Shell env vars (same as zshrc)
├── .claude.json                    # Skip onboarding flag
├── .claude/
│   ├── settings.json               # Claude Code proxy config
│   └── .credentials.json           # Skip login flag
├── .venvs/
│   └── litellm/                    # Python 3.13 venv with litellm
├── nvidia-proxy/
│   ├── config.yaml                 # LiteLLM proxy config
│   ├── litellm.log                 # Stdout logs
│   └── litellm.err.log             # Stderr logs
└── Library/
    └── LaunchAgents/
        └── com.litellm.proxy.plist # launchd service definition
```

---

## Troubleshooting

### Port 4000 Already in Use

```bash
lsof -ti :4000 | xargs kill -9
```

### Proxy Won't Start

1. Check error log: `cat ~/nvidia-proxy/litellm.err.log`
2. Verify Python version: `~/.venvs/litellm/bin/python --version`
3. Verify NVIDIA key: `echo ${NVIDIA_NIM_API_KEY:0:12}...`
4. Test config: `cd ~/nvidia-proxy && ~/.venvs/litellm/bin/litellm --config config.yaml --port 4000`

### Claude Code Shows 401 Unauthorized

1. Verify env vars: `echo $ANTHROPIC_AUTH_TOKEN`
2. Check credentials file: `cat ~/.claude/.credentials.json`
3. Restart terminal to reload env vars

### Claude Code Prompts for Login

1. Verify onboarding flag: `cat ~/.claude.json`
2. Verify credentials: `cat ~/.claude/.credentials.json`
3. Delete and recreate both files

### Requests Timing Out

1. Check `request_timeout` in config.yaml (default: 600s)
2. Check NVIDIA NIM status at https://status.nvidia.com
3. Test direct to NVIDIA: `curl https://integrate.api.nvidia.com/v1/chat/completions -H "Authorization: Bearer $NVIDIA_NIM_API_KEY" -H "Content-Type: application/json" -d '{"model":"minimaxai/minimax-m3","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'`

### 429 Too Many Requests

- NVIDIA free tier: 40 RPM
- Config sets `rpm: 35` to stay under limit
- Wait 60 seconds and retry
- Check usage at https://build.nvidia.com

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Local Applications                                                   │
│  ─ OpenAI SDK (Python/Node)        ─ Claude Code CLI                 │
│  ─ LangChain, LlamaIndex           ─ Anthropic SDK                   │
│  ─ curl, httpx, fetch              ─ Cursor, Cline, Zed              │
└───────────────────────────┬──────────────────────────────────────────┘
                            │  http://localhost:4000
                            ▼
                  ┌──────────────────────────┐
                  │  LiteLLM Proxy (Python)  │
                  │  ─ /v1/chat/completions  │  OpenAI surface
                  │  ─ /v1/models            │
                  │  ─ /v1/messages          │  Anthropic surface
                  │  ─ /health/liveness      │
                  └────────────┬─────────────┘
                               │  Authorization: Bearer nvapi-xxxx
                               │  https://integrate.api.nvidia.com/v1
                               ▼
                  ┌──────────────────────────┐
                  │  NVIDIA NIM (MiniMax-M3) │
                  │  1M context, multimodal  │
                  └──────────────────────────┘
```

---

## Model Aliases

| Alias | Upstream Model | Use Case |
|-------|----------------|----------|
| `minimax-m3` | nvidia_nim/minimaxai/minimax-m3 | Primary, direct access |
| `gpt-4o` | nvidia_nim/minimaxai/minimax-m3 | OpenAI SDK compatibility |
| `claude-3-5-sonnet-20241022` | nvidia_nim/minimaxai/minimax-m3 | Claude Code, Anthropic SDK |

All aliases route to the same upstream model. Use whichever matches your client's expected model name.

---

## Environment Variables Reference

| Variable | Value | Purpose |
|----------|-------|---------|
| `NVIDIA_NIM_API_KEY` | `nvapi-xxxx` | Upstream NVIDIA auth (NVIDIA config) |
| `OPENROUTER_API_KEY` | `sk-or-xxxx` | Upstream OpenRouter auth (OpenRouter config) |
| `OPENAI_API_BASE` | `http://localhost:4000/v1` | OpenAI SDK base URL |
| `OPENAI_API_KEY` | `sk-local-proxy` | OpenAI SDK auth (any value works) |
| `ANTHROPIC_BASE_URL` | `http://localhost:4000` | Anthropic SDK / Claude Code base URL |
| `ANTHROPIC_AUTH_TOKEN` | `sk-local-proxy` | Anthropic SDK auth (any value works) |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Claude Code default model |
| `ANTHROPIC_SMALL_FAST_MODEL` | `claude-3-5-sonnet-20241022` | Claude Code fast tasks model |

---

## Appendix A: OpenRouter Configuration

An alternative upstream provider is [OpenRouter.ai](https://openrouter.ai), which provides access to 200+ models from multiple providers (Anthropic, OpenAI, Google, Meta, DeepSeek, etc.) through a single API key.

### OpenRouter vs NVIDIA NIM

| Feature | NVIDIA NIM | OpenRouter |
|---------|------------|------------|
| Models | MiniMax-M3 only | 200+ models |
| Free tier | 1,000-5,000 credits | Pay-per-use |
| Rate limit | 40 RPM | Varies by model |
| Setup | Requires NVIDIA account | Requires OpenRouter account |

### Step A1: Get OpenRouter API Key

1. Sign up at https://openrouter.ai
2. Go to https://openrouter.ai/keys
3. Create a new API key (starts with `sk-or-`)
4. Add credits if needed (some models require paid access)

### Step A2: Add OpenRouter Env Var

Add to `~/.zshrc` and `~/.bashrc`:

```bash
export OPENROUTER_API_KEY="sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Reload shell:
```bash
source ~/.zshrc
```

### Step A3: Create OpenRouter Config

Create `~/nvidia-proxy/openrouter.yaml`:

```yaml
# ~/nvidia-proxy/openrouter.yaml
# LiteLLM Proxy configuration for OpenRouter.ai as upstream provider.

model_list:
  # Anthropic Models
  - model_name: claude-3-5-sonnet-20241022
    litellm_params:
      model: openrouter/anthropic/claude-3.5-sonnet
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  - model_name: claude-sonnet-4-20250514
    litellm_params:
      model: openrouter/anthropic/claude-sonnet-4
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  # OpenAI Models
  - model_name: gpt-4o
    litellm_params:
      model: openrouter/openai/gpt-4o
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  - model_name: gpt-4o-mini
    litellm_params:
      model: openrouter/openai/gpt-4o-mini
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  - model_name: o3-mini
    litellm_params:
      model: openrouter/openai/o3-mini
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  # Google Models
  - model_name: gemini-2.5-pro-preview
    litellm_params:
      model: openrouter/google/gemini-2.5-pro-preview
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  # Meta Models
  - model_name: llama-3.3-70b
    litellm_params:
      model: openrouter/meta-llama/llama-3.3-70b-instruct
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  # DeepSeek Models
  - model_name: deepseek-r1
    litellm_params:
      model: openrouter/deepseek/deepseek-r1
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  - model_name: deepseek-v3
    litellm_params:
      model: openrouter/deepseek/deepseek-chat-v3-0324
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

  # Qwen Models
  - model_name: qwen-2.5-72b
    litellm_params:
      model: openrouter/qwen/qwen-2.5-72b-instruct
      api_key: os.environ/OPENROUTER_API_KEY
      rpm: 35

litellm_settings:
  drop_params: true
  num_retries: 3
  request_timeout: 600
  streaming_timeout: 600

general_settings:
  # master_key: os.environ/LOCAL_PROXY_KEY
  # database_url: sqlite:///./litellm.db
  disable_admin_ui: true
```

### Step A4: Switch launchd Service to OpenRouter

Edit `~/Library/LaunchAgents/com.litellm.proxy.plist`:

Change this line:
```xml
<string>/Users/YOUR_USERNAME/nvidia-proxy/config.yaml</string>
```
To:
```xml
<string>/Users/YOUR_USERNAME/nvidia-proxy/openrouter.yaml</string>
```

Also update the `EnvironmentVariables` section:
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>OPENROUTER_API_KEY</key>
    <string>sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</string>
</dict>
```

Reload the service:
```bash
launchctl unload ~/Library/LaunchAgents/com.litellm.proxy.plist
launchctl load ~/Library/LaunchAgents/com.litellm.proxy.plist
```

### OpenRouter Model Aliases

| Alias | OpenRouter Model | Provider |
|-------|------------------|----------|
| `claude-3-5-sonnet-20241022` | anthropic/claude-3.5-sonnet | Anthropic |
| `claude-sonnet-4-20250514` | anthropic/claude-sonnet-4 | Anthropic |
| `gpt-4o` | openai/gpt-4o | OpenAI |
| `gpt-4o-mini` | openai/gpt-4o-mini | OpenAI |
| `o3-mini` | openai/o3-mini | OpenAI |
| `gemini-2.5-pro-preview` | google/gemini-2.5-pro-preview | Google |
| `llama-3.3-70b` | meta-llama/llama-3.3-70b-instruct | Meta |
| `deepseek-r1` | deepseek/deepseek-r1 | DeepSeek |
| `deepseek-v3` | deepseek/deepseek-chat-v3-0324 | DeepSeek |
| `qwen-2.5-72b` | qwen/qwen-2.5-72b-instruct | Alibaba |

### OpenRouter Testing

```bash
# Health check
curl http://localhost:4000/health/liveness

# List models
curl -s http://localhost:4000/v1/models | python3 -m json.tool

# Test Claude via OpenRouter
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role":"user","content":"Say hi in 3 words."}],
    "max_tokens": 32
  }' | python3 -m json.tool

# Test GPT-4o via OpenRouter
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role":"user","content":"Say hi in 3 words."}],
    "max_tokens": 32
  }' | python3 -m json.tool

# Test DeepSeek R1 via OpenRouter
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1",
    "messages": [{"role":"user","content":"Say hi in 3 words."}],
    "max_tokens": 32
  }' | python3 -m json.tool
```

### Switching Between NVIDIA and OpenRouter

To switch back to NVIDIA NIM:
```bash
# Edit plist
sed -i '' 's|openrouter.yaml|config.yaml|' ~/Library/LaunchAgents/com.litellm.proxy.plist

# Reload
launchctl unload ~/Library/LaunchAgents/com.litellm.proxy.plist
launchctl load ~/Library/LaunchAgents/com.litellm.proxy.plist
```

To switch to OpenRouter:
```bash
# Edit plist
sed -i '' 's|config.yaml|openrouter.yaml|' ~/Library/LaunchAgents/com.litellm.proxy.plist

# Reload
launchctl unload ~/Library/LaunchAgents/com.litellm.proxy.plist
launchctl load ~/Library/LaunchAgents/com.litellm.proxy.plist
```

---

## Notes

- **No master key needed**: Since `master_key` is commented out, the proxy accepts any API key value. Clients just need to send a non-empty `Authorization` or `x-api-key` header.
- **No database needed**: Without `database_url`, virtual keys and spend tracking are disabled. All requests are treated as internal.
- **Admin UI disabled**: `disable_admin_ui: true` prevents the `/ui` endpoint from being accessible.
- **Single process**: The launchd service runs one litellm process. For high concurrency, consider `--num_workers 4` in the command arguments.
- **Auto-restart**: `KeepAlive` with `SuccessfulExit: false` restarts the proxy if it crashes, but not on clean shutdown.

---

## Appendix B: Linux Configuration — Lessons Learned (Pop!_OS / Ubuntu)

This section distills the practical experience of configuring Claude Code to use a running LiteLLM proxy on a Linux host (tested on Pop!_OS 22.04, Python venv, Claude Code installed via npm global).

### Key Differences from macOS

| Concern | macOS | Linux |
|---------|-------|-------|
| Shell | `zsh` (default) | `bash` (default) — configure `~/.bashrc`, not `~/.zshrc` |
| Auto-start | `launchd` + `~/Library/LaunchAgents/` | `systemd` user service (see below) |
| Claude binary | `npm install -g` → `/usr/local/bin/claude` | `npm install -g` → `/usr/bin/claude` (symlinked) |
| Env var persistence | `~/.zshrc` | `~/.bashrc` (sourced by login shells) |

### The Critical Insight: `~/.claude/settings.json` > Shell Env Vars

On Linux, Claude Code does **not** reliably inherit shell environment variables exported in `~/.bashrc` when launched from a desktop shortcut, IDE terminal, or any non-login shell. The **only** persistent, reliable mechanism is the `env` block in `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-local-proxy",
    "ANTHROPIC_MODEL": "claude-3-5-sonnet-20241022",
    "ANTHROPIC_SMALL_FAST_MODEL": "claude-3-5-sonnet-20241022"
  },
  "apiBaseUrl": "http://localhost:4000",
  "model": "claude-3-5-sonnet-20241022"
}
```

This file is read by Claude Code on **every** invocation regardless of how it was launched. Always use this as the primary configuration method.

### Step-by-Step Linux Configuration

#### 1. Create `~/.claude/settings.json`

```bash
mkdir -p ~/.claude
```

Write the file above. The `env` block injects variables into the Claude process automatically.

#### 2. Create `~/.claude/.credentials.json` (Skip Login)

```json
{
  "apiKey": "sk-local-proxy",
  "hasCompletedOnboarding": true
}
```

Without this file, Claude Code will prompt for an Anthropic login even though the proxy doesn't need real credentials.

#### 3. Verify `~/.claude.json` Has Onboarding Flag

```bash
python3 -c "import json; d=json.load(open('/home/pete/.claude.json')); print(d.get('hasCompletedOnboarding'))"
```

If `hasCompletedOnboarding` is missing or `false`, add it:

```json
{
  "hasCompletedOnboarding": true
}
```

#### 4. Add Shell Exports to `~/.bashrc` (For Other Tools)

While Claude Code uses `settings.json`, other tools (OpenAI SDK, curl, scripts) need shell env vars:

```bash
# --- LiteLLM Proxy (http://localhost:4000) ---
export OPENAI_API_BASE="http://localhost:4000/v1"
export OPENAI_API_KEY="sk-local-proxy"
export ANTHROPIC_BASE_URL="http://localhost:4000"
export ANTHROPIC_AUTH_TOKEN="sk-local-proxy"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
export ANTHROPIC_SMALL_FAST_MODEL="claude-3-5-sonnet-20241022"
```

#### 5. Verify the Proxy Is Running

```bash
curl -s http://localhost:4000/health/liveness
# Expected: "I'm alive!"
```

#### 6. Test the Anthropic Endpoint Directly

```bash
curl -s http://localhost:4000/v1/messages \
  -H "x-api-key: sk-local-proxy" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":50,"messages":[{"role":"user","content":"Say hi in 3 words."}]}'
```

#### 7. Run Claude Code

```bash
claude -p "Say hello in 5 words"
# Expected: Response from minimax-m3 via proxy, no login prompt
```

### Tips & Best Practices

1. **Auth token value is arbitrary** — Since `master_key` is commented out in `config.yaml`, the proxy accepts any non-empty auth token. `sk-local-proxy` is the convention, but `dummy-key` or anything else works too.

2. **Don't set `ANTHROPIC_API_KEY`** — Claude Code reads `ANTHROPIC_AUTH_TOKEN` for proxy auth. Setting `ANTHROPIC_API_KEY` can cause confusion or conflicts. Use `ANTHROPIC_AUTH_TOKEN` only.

3. **Model name must match a proxy alias** — The `ANTHROPIC_MODEL` value must be one of the `model_name` entries in `config.yaml` (`claude-3-5-sonnet-20241022`, `minimax-m3`, or `gpt-4o`). If you use a name not in the list, you'll get a 404.

4. **Check proxy logs to confirm routing** — After running `claude`, verify the request hit the proxy:
   ```bash
   tail -5 ~/nvidia-proxy/litellm.log
   # Look for: POST /v1/messages?beta=true HTTP/1.1 200 OK
   ```

5. **The `LITELLM_MASTER_KEY` warning is harmless** — The CRITICAL log line about `LITELLM_MASTER_KEY` not being set is expected for basic proxy-only use. It just means all requests are treated as internal users with no admin access — which is fine for a personal proxy.

6. **Cache cost warnings are cosmetic** — The `register_model: model=... not in built-in cost map` warnings mean LiteLLM doesn't know MiniMax-M3's pricing. Costs will show as $0.00 in logs. This doesn't affect functionality.

### Challenges Encountered & Solutions

| Challenge | Root Cause | Solution |
|-----------|------------|----------|
| Claude Code prompts for login despite env vars set | Env vars were in current shell session but not in `settings.json`; new `claude` invocations from fresh terminals didn't inherit them | Created `~/.claude/.credentials.json` with `apiKey` + `hasCompletedOnboarding` |
| `ANTHROPIC_AUTH_TOKEN` value mismatch between docs and running session | Skill says `sk-local-proxy`, but existing session used `dummy-key` | Either works — proxy accepts any non-empty token when `master_key` is unset. Standardized on `sk-local-proxy` for consistency. |
| `~/.bashrc` had commented-out `OPENAI_API_KEY` lines | Previous OpenAI key experiments left behind | Left them commented; added clean LiteLLM proxy section at end of file |
| No `~/.claude/settings.json` existed | Fresh Linux install — only `~/.claude.json` (onboarding state) was present | Created `settings.json` with the `env` block — this is the critical file |

### Troubleshooting on Linux

#### Claude Code Returns 401 or "Unauthorized"

```bash
# 1. Verify proxy is running
curl -s http://localhost:4000/health/liveness

# 2. Check credentials file
cat ~/.claude/.credentials.json

# 3. Check settings.json env block
cat ~/.claude/settings.json

# 4. Test endpoint manually
curl -s http://localhost:4000/v1/messages \
  -H "x-api-key: sk-local-proxy" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

#### Claude Code Prompts for Login on Every Start

```bash
# Recreate credentials file
cat > ~/.claude/.credentials.json << 'EOF'
{
  "apiKey": "sk-local-proxy",
  "hasCompletedOnboarding": true
}
EOF

# Verify onboarding flag in ~/.claude.json
python3 -c "import json; json.load(open('/home/pete/.claude.json'))['hasCompletedOnboarding']"
```

#### Proxy Not Running After Reboot

On Linux, use a systemd user service instead of macOS `launchd`:

```bash
mkdir -p ~/.config/systemd/user
```

Create `~/.config/systemd/user/litellm-proxy.service`:

```ini
[Unit]
Description=LiteLLM Proxy
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/nvidia-proxy
Environment=NVIDIA_NIM_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ExecStart=%h/.venvs/litellm/bin/litellm --config %h/nvidia-proxy/config.yaml --port 4000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable litellm-proxy
systemctl --user start litellm-proxy
systemctl --user status litellm-proxy
```

#### "Model not found" Error

The model name in `ANTHROPIC_MODEL` must exactly match a `model_name` in `config.yaml`. Check available models:

```bash
curl -s http://localhost:4000/v1/models | python3 -m json.tool
```

#### Port 4000 Already in Use

```bash
# Find and kill
sudo lsof -ti :4000 | xargs kill -9

# Or with fuser
fuser -k 4000/tcp
```

### Verification Checklist

After configuration, confirm all of these:

- [ ] `curl http://localhost:4000/health/liveness` → `"I'm alive!"`
- [ ] `cat ~/.claude/settings.json` → has `env` block with `ANTHROPIC_BASE_URL`
- [ ] `cat ~/.claude/.credentials.json` → has `apiKey` and `hasCompletedOnboarding`
- [ ] `claude -p "Say hello in 5 words"` → returns a response (not a login prompt)
- [ ] `tail ~/nvidia-proxy/litellm.log` → shows `POST /v1/messages` 200 OK

### Linux File Structure

```
~/
├── .bashrc                         # Shell env vars (OPENAI_*, ANTHROPIC_*)
├── .claude.json                    # Skip onboarding flag
├── .claude/
│   ├── settings.json               # Claude Code proxy config (CRITICAL)
│   └── .credentials.json           # Skip login flag
├── .venvs/
│   └── litellm/                    # Python venv with litellm
├── nvidia-proxy/
│   ├── config.yaml                 # LiteLLM proxy config
│   ├── litellm.log                 # Stdout logs
│   └── litellm.err.log             # Stderr logs
└── .config/
    └── systemd/
        └── user/
            └── litellm-proxy.service  # Auto-start on login
```
