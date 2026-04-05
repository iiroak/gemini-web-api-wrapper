# API Routes

All endpoints (except `/health`) require a `Bearer` token in the `Authorization` header.

```
Authorization: Bearer <API_KEY>
```

---

## Status

| Method | Path               | Description                    | Auth |
|--------|--------------------|--------------------------------|------|
| GET    | `/health`          | Health check                   | No   |
| GET    | `/status`          | Account status from Gemini     | Yes  |
| GET    | `/cookies`         | View cookies (values masked)   | Yes  |
| POST   | `/cookies/rotate`  | Force rotate `1PSIDTS` cookie  | Yes  |

### `GET /health`
```json
{ "status": "ok" }
```

### `GET /status`
Returns the Gemini account status dict.

### `GET /cookies`
```json
{ "cookies": { "__Secure-1PSID": "g.a0***0076", ... } }
```

### `POST /cookies/rotate`
```json
{ "rotated": true, "message": "Cookies persisted to DB" }
```

---

## Chat

| Method | Path                  | Description                          | Auth |
|--------|-----------------------|--------------------------------------|------|
| POST   | `/chat/send`          | Send a message, get full response    | Yes  |
| POST   | `/chat/send/stream`   | Send a message, stream SSE chunks    | Yes  |
| POST   | `/chat/send/upload`   | Send message with file attachments   | Yes  |
| GET    | `/chats`              | List all chat sessions               | Yes  |
| GET    | `/chats/{cid}`        | Read chat history                    | Yes  |
| DELETE | `/chats/{cid}`        | Delete a chat                        | Yes  |

### `POST /chat/send`
**Body (JSON):**
```json
{
  "prompt": "Hello!",
  "cid": null,
  "model": null,
  "gem_id": null,
  "temporary": false
}
```
- `prompt` (required): The message to send.
- `cid` (optional): Existing conversation ID to continue.
- `model` (optional): Model override (e.g. `"gemini-3-pro"`).
- `gem_id` (optional): Gem ID to use.
- `temporary` (optional): If `true`, message is not saved in history.

**Response:**
```json
{
  "metadata": ["cid", "rid", "rcid", ...],
  "candidates": [
    {
      "rcid": "rc_...",
      "text": "Hello!",
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
  "text": "Hello!",
  "text_delta": "",
  "thoughts": null,
  "thoughts_delta": ""
}
```

### `POST /chat/send/stream`
Same body as `/chat/send`. Returns `text/event-stream` (SSE):
```
event: chunk
data: {"text_delta": "Hel", "thoughts_delta": "", "metadata": [...]}

event: chunk
data: {"text_delta": "lo!", "thoughts_delta": "", "metadata": [...]}

event: done
data: { ...full ModelOutput response... }
```

### `POST /chat/send/upload`
**Form data (multipart):**
- `prompt` (string, required)
- `cid` (string, optional)
- `model` (string, optional)
- `gem_id` (string, optional)
- `temporary` (bool, optional)
- `files` (file(s), optional)

Returns same response as `/chat/send`.

### `GET /chats`
```json
[
  { "cid": "c_...", "title": "My chat", "is_pinned": false, "timestamp": 1700000000.0 }
]
```

### `GET /chats/{cid}?limit=30`
```json
{
  "cid": "c_...",
  "turns": [
    { "role": "user", "text": "Hi" },
    { "role": "model", "text": "Hello!" }
  ]
}
```

### `DELETE /chats/{cid}`
Returns `204 No Content`.

---

## Models

| Method | Path      | Description              | Auth |
|--------|-----------|--------------------------|------|
| GET    | `/models` | List available models    | Yes  |

### `GET /models`
```json
[
  {
    "model_id": "gemini-3-pro",
    "model_name": "gemini-3-pro",
    "display_name": "Gemini 3 Pro",
    "description": "...",
    "capacity": 100,
    "is_available": true
  }
]
```

---

## Gems

| Method | Path              | Description        | Auth |
|--------|-------------------|--------------------|------|
| GET    | `/gems`           | List all gems      | Yes  |
| POST   | `/gems`           | Create a gem       | Yes  |
| PUT    | `/gems/{gem_id}`  | Update a gem       | Yes  |
| DELETE | `/gems/{gem_id}`  | Delete a gem       | Yes  |

### `POST /gems`
**Body:**
```json
{ "name": "My Gem", "prompt": "Be helpful", "description": "A helpful gem" }
```
**Response (201):**
```json
{ "id": "gem_...", "name": "My Gem", "description": "A helpful gem", "prompt": "Be helpful", "predefined": false }
```

### `PUT /gems/{gem_id}`
Same body as POST. Returns updated gem.

### `DELETE /gems/{gem_id}`
Returns `204 No Content`.

---

## Files

| Method | Path              | Description               | Auth |
|--------|-------------------|---------------------------|------|
| POST   | `/files/upload`   | Upload a file to Gemini   | Yes  |
| GET    | `/files/download` | Download/proxy a file URL | Yes  |

### `POST /files/upload`
**Form data:** `file` (file, required)
```json
{ "reference": "...", "filename": "doc.pdf" }
```

### `GET /files/download?url=https://...`
Proxies the download through the authenticated Gemini session. Returns the file content with appropriate `Content-Type`.

---

## Deep Research

| Method | Path                                | Description                        | Auth |
|--------|-------------------------------------|------------------------------------|------|
| POST   | `/research/plan`                    | Create a research plan             | Yes  |
| POST   | `/research/plan/{research_id}/start`| Start research from a plan         | Yes  |
| GET    | `/research/{cid}/status`            | Poll research status               | Yes  |
| POST   | `/research`                         | Full research (blocking)           | Yes  |
| POST   | `/research/stream`                  | Full research (SSE stream)         | Yes  |

### `POST /research/plan`
**Body:**
```json
{ "prompt": "Research topic", "model": null }
```
**Response:**
```json
{ "research_id": "...", "title": "...", "query": "...", "steps": ["Step 1", "Step 2"], "eta_text": "~5 min", "cid": "..." }
```

### `POST /research/plan/{research_id}/start`
**Body (optional):**
```json
{ "confirm_prompt": null }
```
Returns `ModelOutputResponse`.

### `GET /research/{cid}/status`
```json
{ "research_id": "...", "state": "running", "title": "...", "done": false, "notes": ["..."] }
```

### `POST /research`
Full blocking research. Same body as `/research/plan`. Returns `DeepResearchResultResponse`.

### `POST /research/stream`
SSE stream with events: `plan`, `status`, `done`.
