---
name: gemini-web-api
description: "Use when: making HTTP requests to the Gemini Web API Wrapper; sending messages to Gemini; managing chats, gems, models, or deep research via REST API; streaming responses from Gemini; uploading files to Gemini; checking Gemini account status. This skill provides the complete API reference, authentication details, request/response formats, and usage patterns for the gemini-web-api-wrapper REST server."
---

# Gemini Web API Wrapper — Skill Reference

## Overview

This is a REST API wrapper around Google Gemini Web. It exposes Gemini functionality via standard HTTP endpoints with Bearer token authentication.

**Base URL:** `http://localhost:8000` (default)

## Authentication

Every request (except `GET /health`) requires a Bearer token:

```
Authorization: Bearer <API_KEY>
```

The API key is configured via `gemini-web token show` or `gemini-web config get API_KEY`.

## Installation & Setup

### Prerequisites

- Linux system with Python 3.10+ and git
- On Debian/Ubuntu: `sudo apt install python3 python3-venv git`

### Quick install (system-wide)

```bash
git clone https://github.com/iiroak/gemini-web-api-wrapper.git
cd gemini-web-api-wrapper
sudo bash install.sh
```

This installs `gemini-web` to `/usr/local/bin/` (available system-wide, no venv activation needed).

### Setup

```bash
# First-time setup (cookies + token)
gemini-web init

# Start server manually
gemini-web serve

# Or run as systemd service
sudo systemctl enable gemini-web
sudo systemctl start gemini-web
```

## CLI Commands

```
gemini-web init                    # Interactive setup
gemini-web check                   # Validate config & test connection
gemini-web update                  # Pull latest code & reinstall
gemini-web serve                   # Start API server
gemini-web serve --port 9000       # Custom port
gemini-web serve --reload          # Dev mode with auto-reload

gemini-web token generate          # New random API token
gemini-web token show              # View token (masked)
gemini-web token reveal            # View token (plain text)
gemini-web token set <TOKEN>       # Set custom token
gemini-web token revoke            # Delete token

gemini-web cookies set             # Set Google cookies interactively
gemini-web cookies show            # View cookies (masked)
gemini-web cookies clear           # Delete cookies

gemini-web config show             # View all config
gemini-web config get <KEY>        # Get a value
gemini-web config set <KEY> <VAL>  # Set a value
gemini-web config delete <KEY>     # Remove a key
gemini-web config path             # Config directory path
gemini-web config reset            # Delete all config + data
```

Config stored in `$GEMINI_WEB_HOME/config.json` (default: `~/.gemini-web/config.json`, fallback: `/opt/gemini-web/data/config.json`).

---

## API Endpoints

### Status

#### `GET /health`
No auth required.
```json
{"status": "ok"}
```

#### `GET /status`
Returns Gemini account status.
```json
{"account_type": "...", "status": "AVAILABLE", ...}
```

#### `GET /cookies`
Returns cookies with masked values.
```json
{"cookies": {"__Secure-1PSID": "g.a000***0076", ...}}
```

#### `POST /cookies/rotate`
Force-rotate the `__Secure-1PSIDTS` cookie.
```json
{"rotated": true, "message": "Cookies persisted to DB"}
```

---

### Chat

#### `POST /chat/send`
Send a message and get the full response.

**Request:**
```json
{
  "prompt": "Hello!",
  "cid": null,
  "model": null,
  "gem_id": null,
  "temporary": false
}
```
- `prompt` (string, required): Message text
- `cid` (string, optional): Conversation ID to continue an existing chat
- `model` (string, optional): Model override, e.g. `"gemini-3-pro"`, `"gemini-3-flash"`
- `gem_id` (string, optional): Use a specific Gem
- `temporary` (bool, optional): If true, message not saved in Gemini history

**Response:**
```json
{
  "metadata": ["c_abc123", "r_def456", "rc_ghi789", null, ...],
  "candidates": [
    {
      "rcid": "rc_ghi789",
      "text": "Hello! How can I help?",
      "text_delta": "",
      "thoughts": null,
      "thoughts_delta": "",
      "web_images": [],
      "generated_images": [],
      "generated_videos": [],
      "generated_media": []
    }
  ],
  "chosen": 0,
  "text": "Hello! How can I help?",
  "text_delta": "",
  "thoughts": null,
  "thoughts_delta": ""
}
```

The `metadata[0]` is the conversation ID (`cid`) — use it in subsequent requests to continue the conversation.

#### `POST /chat/send/stream`
Same request body as `/chat/send`. Returns Server-Sent Events (SSE):

```
event: chunk
data: {"text_delta": "Hello", "thoughts_delta": "", "metadata": ["c_abc", "r_def"]}

event: chunk
data: {"text_delta": "! How can I help?", "thoughts_delta": "", "metadata": ["c_abc", "r_def"]}

event: done
data: { ...full ModelOutput response... }
```

#### `POST /chat/send/upload`
Send a message with file attachments. Uses `multipart/form-data`:

- `prompt` (string, required)
- `cid` (string, optional)
- `model` (string, optional)
- `gem_id` (string, optional)
- `temporary` (bool, optional)
- `files` (file(s), optional)

Returns same response as `/chat/send`.

#### `GET /chats`
List all chat sessions.
```json
[
  {"cid": "c_abc123", "title": "My Chat", "is_pinned": false, "timestamp": 1700000000.0}
]
```

#### `GET /chats/{cid}?limit=30`
Read chat history for a specific conversation.
```json
{
  "cid": "c_abc123",
  "turns": [
    {"role": "user", "text": "Hi"},
    {"role": "model", "text": "Hello!"}
  ]
}
```

#### `DELETE /chats/{cid}`
Delete a chat. Returns `204 No Content`.

---

### Models

#### `GET /models`
List available Gemini models.
```json
[
  {
    "model_id": "gemini-3-pro",
    "model_name": "gemini-3-pro",
    "display_name": "Gemini 3 Pro",
    "description": "Most capable model",
    "capacity": 100,
    "is_available": true
  }
]
```

---

### Gems

#### `GET /gems`
List all gems (custom and predefined).
```json
[
  {"id": "gem_abc", "name": "Translator", "description": "Translates text", "prompt": "You are a translator", "predefined": false}
]
```

#### `POST /gems`
Create a new gem.
```json
{"name": "My Gem", "prompt": "Be helpful", "description": "A helpful gem"}
```
Returns `201` with the created gem.

#### `PUT /gems/{gem_id}`
Update an existing gem. Same body as POST.

#### `DELETE /gems/{gem_id}`
Delete a gem. Returns `204 No Content`.

---

### Files

#### `POST /files/upload`
Upload a file to Gemini. Uses `multipart/form-data` with field `file`.
```json
{"reference": "...", "filename": "doc.pdf"}
```

#### `GET /files/download?url=https://...`
Proxy a file download through the authenticated Gemini session. Returns the file content with appropriate `Content-Type`.

---

### Deep Research

#### `POST /research/plan`
Create a research plan.
```json
{"prompt": "Research quantum computing advances in 2025", "model": null}
```
Response:
```json
{
  "research_id": "r_abc",
  "title": "Quantum Computing Advances",
  "query": "...",
  "steps": ["Step 1: ...", "Step 2: ..."],
  "eta_text": "~5 minutes",
  "cid": "c_def"
}
```

#### `POST /research/plan/{research_id}/start`
Start executing a research plan.
```json
{"confirm_prompt": null}
```
Returns a `ModelOutputResponse`.

#### `GET /research/{cid}/status`
Poll the status of an ongoing research.
```json
{"research_id": "r_abc", "state": "running", "title": "...", "done": false, "notes": ["Searching..."]}
```

#### `POST /research`
Full blocking research — creates plan, executes, and waits for completion.
```json
{"prompt": "Research topic"}
```
Returns the full `DeepResearchResultResponse`.

#### `POST /research/stream`
Full research with SSE streaming:
```
event: plan
data: {"research_id": "...", "steps": [...], ...}

event: status
data: {"state": "running", "done": false, "notes": [...]}

event: done
data: { ...full result... }
```

---

## Important Notes

### Model Selection
- **Do NOT invent model names.** Only use models returned by `GET /models`.
- Common models: `gemini-3-flash` (fast), `gemini-3-flash-thinking` (reasoning), `gemini-3-pro` (advanced).
- If unsure which model to use, **omit the `model` field** — the server uses the default.
- To generate images, **do NOT specify a model**. Just describe the image in the prompt (e.g. "Draw a chibi Hatsune Miku"). Gemini selects the appropriate model automatically.

### Image Generation
- Image generation can take **several minutes** (1-5+ minutes depending on complexity). **Set HTTP timeout to at least 480 seconds** (8 minutes) for image requests.
- Generated images appear in `candidates[].generated_images` as URLs.
- The response `text` field may contain a description alongside the image.
- To save a generated image, download it from the URL in `generated_images` or use `GET /files/download?url=<image_url>`.
- **Do NOT cancel or retry** if the request seems slow — image generation is inherently slow.

### Token Management
- After changing the token with `gemini-web token generate` or `gemini-web token set`, the **server must be restarted** for the new token to take effect.
- Use `gemini-web token reveal` to see the current token in plain text.
- Always use the token from the config file, not a previously cached value.

### Conversation IDs
- `metadata[0]` in the response is the conversation ID (`cid`).
- Pass `cid` in subsequent requests to continue the same conversation.
- Without `cid`, each request starts a new conversation.

---

## Usage Patterns

### Simple question-answer
```bash
curl -X POST http://localhost:8000/chat/send \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

### Continue a conversation
```bash
# First message — note the cid from metadata[0]
# Second message — pass the cid
curl -X POST http://localhost:8000/chat/send \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me more", "cid": "c_abc123"}'
```

### Use a specific model
```bash
curl -X POST http://localhost:8000/chat/send \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "gemini-3-pro"}'
```

### Stream a response (Python)
```python
import httpx

with httpx.stream("POST", "http://localhost:8000/chat/send/stream",
    headers={"Authorization": "Bearer TOKEN"},
    json={"prompt": "Write a poem"},
    timeout=480,
) as resp:
    for line in resp.iter_lines():
        if line.startswith("data:"):
            print(line[5:])
```

## Error Responses

| Status | Error Key | Cause |
|--------|-----------|-------|
| 401 | — | Missing or invalid Bearer token |
| 400 | `model_invalid` | Unrecognized model name |
| 429 | `usage_limit_exceeded` | Gemini rate limit hit |
| 502 | `auth_error` | Google cookie authentication failed |
| 502 | `gemini_error` | Generic Gemini API error |
| 503 | `temporarily_blocked` | Account temporarily blocked |
| 504 | `timeout` | Request timed out |

All error responses follow:
```json
{"error": "error_key", "message": "Human-readable description"}
```