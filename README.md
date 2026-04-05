# Gemini Web API Wrapper

REST API wrapper around [Google Gemini](https://gemini.google.com) — installable as a Python package with CLI.

## Installation

### Recommended: using a virtual environment

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### Install from GitHub (recommended)

```bash
pip install git+https://github.com/YOUR_USERNAME/gemini-web-api-wrapper.git
```

### Install from source

```bash
git clone https://github.com/YOUR_USERNAME/gemini-web-api-wrapper.git
cd gemini-web-api-wrapper
pip install .
```

> **Note:** The `gemini-webapi` dependency is installed automatically from its GitHub repository.

## Quick Start

### 1. Setup

```bash
gemini-web init
```

This will interactively ask for:
- **API key** — auto-generated or custom, used to authenticate requests to the wrapper
- **Google cookies** — `__Secure-1PSID` and `__Secure-1PSIDTS` from your browser

> **How to get cookies:** Open [gemini.google.com](https://gemini.google.com) → DevTools (F12) → Application → Cookies → copy the values.

### 2. Start the server

```bash
gemini-web serve
```

The API will be available at `http://localhost:8000`.

### 3. Send a message

```bash
curl http://localhost:8000/chat/send \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!"}'
```

## CLI Commands

| Command | Description |
|---------|-------------|
| **Setup** | |
| `gemini-web init` | Interactive first-time setup |
| `gemini-web serve` | Start the API server |
| `gemini-web serve --port 9000` | Start on a custom port |
| `gemini-web serve --reload` | Start with auto-reload (dev) |
| **Token management** | |
| `gemini-web token generate` | Generate a new random API token |
| `gemini-web token show` | Show current token (masked) |
| `gemini-web token reveal` | Show current token in plain text |
| `gemini-web token set <TOKEN>` | Set a custom token |
| `gemini-web token revoke` | Delete the current token |
| **Cookie management** | |
| `gemini-web cookies set` | Set Google cookies interactively |
| `gemini-web cookies show` | Show cookies (masked) |
| `gemini-web cookies clear` | Delete stored cookies |
| **Configuration** | |
| `gemini-web config show` | Show all configuration |
| `gemini-web config get KEY` | Get a single value |
| `gemini-web config set KEY VALUE` | Set a config value |
| `gemini-web config delete KEY` | Remove a config key |
| `gemini-web config path` | Print config directory path |
| `gemini-web config reset` | Delete all config and data |

## Configuration

All configuration lives in `~/.gemini-web/config.json`, managed entirely via CLI.

**No `.env` file needed.**

### Available settings

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | (auto-generated) | Bearer token for API authentication |
| `GEMINI_SECURE_1PSID` | — | Required Google cookie |
| `GEMINI_SECURE_1PSIDTS` | — | Optional Google cookie |
| `GEMINI_PROXY` | — | HTTP/HTTPS proxy URL |
| `GEMINI_MODEL` | `UNSPECIFIED` | Default model |
| `GEMINI_TIMEOUT` | `450` | Request timeout (seconds) |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |

> Environment variables still work as overrides (e.g. for Docker).

## API Endpoints

See [ROUTES.md](ROUTES.md) for the full API reference.

### Summary

| Category | Endpoints |
|----------|-----------|
| **Status** | `GET /health`, `GET /status`, `GET /cookies`, `POST /cookies/rotate` |
| **Chat** | `POST /chat/send`, `POST /chat/send/stream`, `POST /chat/send/upload`, `GET /chats`, `GET /chats/{cid}`, `DELETE /chats/{cid}` |
| **Models** | `GET /models` |
| **Gems** | `GET /gems`, `POST /gems`, `PUT /gems/{id}`, `DELETE /gems/{id}` |
| **Files** | `POST /files/upload`, `GET /files/download` |
| **Research** | `POST /research/plan`, `POST /research`, `POST /research/stream`, `GET /research/{cid}/status` |

## Docker

```bash
docker build -t gemini-web .
docker run -p 8000:8000 \
  -e GEMINI_SECURE_1PSID=your_cookie \
  -e API_KEY=your_key \
  -v gemini-web-data:/root/.gemini-web \
  gemini-web
```

## Development

```bash
git clone https://github.com/YOUR_USERNAME/gemini-web-api-wrapper.git
cd gemini-web-api-wrapper
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"

# Unit tests (mocked, fast)
pytest tests/ --ignore=tests/test_integration.py

# Integration tests (real API, requires valid cookies)
pytest tests/test_integration.py -v -s
```

## License

MIT
