"""
CLI entry point for gemini-web-api-wrapper.

Usage:
    gemini-web init                   # Interactive first-time setup
    gemini-web check                  # Validate config & test connection
    gemini-web serve                  # Start the API server
    gemini-web token generate         # Generate a new API token
    gemini-web token show             # Show current token (masked)
    gemini-web token set <TOKEN>      # Set a custom token
    gemini-web token revoke           # Delete the current token
    gemini-web cookies set            # Set Google cookies interactively
    gemini-web cookies show           # Show cookies (masked)
    gemini-web cookies clear          # Delete stored cookies
    gemini-web config show            # Show all config
    gemini-web config set KEY VALUE   # Set a config value
    gemini-web config get KEY         # Get a config value
    gemini-web config delete KEY      # Delete a config key
    gemini-web config path            # Show config directory
    gemini-web config reset           # Delete all configuration
"""
from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

import os

import click


# ── Config directory ─────────────────────────────────────────────

def _config_dir() -> Path:
    """Return config directory. Priority: GEMINI_WEB_HOME env > ~/.gemini-web."""
    env = os.environ.get("GEMINI_WEB_HOME")
    if env:
        d = Path(env)
    else:
        d = Path.home() / ".gemini-web"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _config_file() -> Path:
    return _config_dir() / "config.json"


def _load_config() -> dict:
    f = _config_file()
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}


def _save_config(cfg: dict) -> None:
    f = _config_file()
    f.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def _mask(val: str, show: int = 6) -> str:
    """Mask a sensitive string, keeping first and last `show` chars."""
    if not val or len(val) <= show * 2:
        return "***"
    return val[:show] + "..." + val[-show:]


# ── Root CLI group ───────────────────────────────────────────────

@click.group()
@click.version_option(package_name="gemini-web-api-wrapper")
def cli():
    """Gemini Web API Wrapper — REST API for Google Gemini."""
    pass


# ── init ─────────────────────────────────────────────────────────

@cli.command()
def init():
    """Interactive first-time setup."""
    cfg = _load_config()
    click.echo("🔧 Gemini Web API Wrapper — Setup\n")

    # API token
    existing_key = cfg.get("API_KEY", "")
    if existing_key and existing_key != "changeme":
        if click.confirm(f"API token already set ({_mask(existing_key)}). Regenerate?", default=False):
            cfg["API_KEY"] = _generate_token()
    else:
        cfg["API_KEY"] = _generate_token()

    # Cookies
    click.echo("\n📋 Google Gemini cookies")
    click.echo("   (Browser → gemini.google.com → F12 → Application → Cookies)\n")
    cfg["GEMINI_SECURE_1PSID"] = click.prompt(
        "  __Secure-1PSID",
        default=cfg.get("GEMINI_SECURE_1PSID", ""),
    ).strip()
    cfg["GEMINI_SECURE_1PSIDTS"] = click.prompt(
        "  __Secure-1PSIDTS (optional, Enter to skip)",
        default=cfg.get("GEMINI_SECURE_1PSIDTS", ""),
    ).strip()

    # Network
    click.echo("\n⚙️  Server settings (Enter for defaults)")
    cfg["HOST"] = click.prompt("  Host", default=cfg.get("HOST", "0.0.0.0")).strip()
    cfg["PORT"] = click.prompt("  Port", default=cfg.get("PORT", 8000), type=int)
    proxy = click.prompt("  HTTP proxy (blank = none)", default=cfg.get("GEMINI_PROXY", "")).strip()
    cfg["GEMINI_PROXY"] = proxy if proxy else ""

    _save_config(cfg)
    click.echo(f"\n✅ Config saved to {_config_file()}")
    click.echo(f"   API token: {cfg['API_KEY']}")
    click.echo("   Run `gemini-web serve` to start the server.")


def _generate_token() -> str:
    key = secrets.token_urlsafe(32)
    click.echo(f"  🔑 Generated token: {key}")
    return key


# ══════════════════════════════════════════════════════════════════
# token subcommand
# ══════════════════════════════════════════════════════════════════

@cli.group()
def token():
    """Manage the API authentication token."""
    pass


@token.command("generate")
def token_generate():
    """Generate a new random API token (replaces the old one)."""
    cfg = _load_config()
    old = cfg.get("API_KEY", "")
    new_key = secrets.token_urlsafe(32)
    cfg["API_KEY"] = new_key
    _save_config(cfg)
    if old and old != "changeme":
        click.echo(f"  Old: {_mask(old)}")
    click.echo(f"  New: {new_key}")
    click.echo("  ⚠️  Restart the server for this to take effect.")


@token.command("show")
def token_show():
    """Show the current API token (masked)."""
    cfg = _load_config()
    key = cfg.get("API_KEY", "")
    if not key or key == "changeme":
        click.echo("  No token set. Run `gemini-web init` or `gemini-web token generate`.")
    else:
        click.echo(f"  {_mask(key)}")


@token.command("reveal")
def token_reveal():
    """Show the current API token in plain text."""
    cfg = _load_config()
    key = cfg.get("API_KEY", "")
    if not key or key == "changeme":
        click.echo("  No token set.")
    else:
        click.echo(f"  {key}")


@token.command("set")
@click.argument("value")
def token_set(value: str):
    """Set a custom API token."""
    cfg = _load_config()
    cfg["API_KEY"] = value.strip()
    _save_config(cfg)
    click.echo(f"  Token set: {_mask(value.strip())}")
    click.echo("  ⚠️  Restart the server for this to take effect.")


@token.command("revoke")
def token_revoke():
    """Delete the current API token (server won't accept requests)."""
    cfg = _load_config()
    if "API_KEY" in cfg:
        if click.confirm("Delete the API token? The server will reject all requests."):
            del cfg["API_KEY"]
            _save_config(cfg)
            click.echo("  Token revoked.")
    else:
        click.echo("  No token to revoke.")


# ══════════════════════════════════════════════════════════════════
# cookies subcommand
# ══════════════════════════════════════════════════════════════════

@cli.group()
def cookies():
    """Manage Google Gemini cookies."""
    pass


@cookies.command("set")
def cookies_set():
    """Set Google cookies interactively."""
    cfg = _load_config()
    click.echo("📋 Enter your Google Gemini cookies")
    click.echo("   (Browser → gemini.google.com → F12 → Application → Cookies)\n")
    cfg["GEMINI_SECURE_1PSID"] = click.prompt(
        "  __Secure-1PSID",
        default=cfg.get("GEMINI_SECURE_1PSID", ""),
    ).strip()
    cfg["GEMINI_SECURE_1PSIDTS"] = click.prompt(
        "  __Secure-1PSIDTS (optional, Enter to skip)",
        default=cfg.get("GEMINI_SECURE_1PSIDTS", ""),
    ).strip()
    _save_config(cfg)
    click.echo("  ✅ Cookies saved. Restart the server for changes to take effect.")


@cookies.command("show")
def cookies_show():
    """Show stored cookies (masked)."""
    cfg = _load_config()
    psid = cfg.get("GEMINI_SECURE_1PSID", "")
    psidts = cfg.get("GEMINI_SECURE_1PSIDTS", "")
    click.echo(f"  __Secure-1PSID:   {_mask(psid) if psid else '(not set)'}")
    click.echo(f"  __Secure-1PSIDTS: {_mask(psidts) if psidts else '(not set)'}")


@cookies.command("clear")
def cookies_clear():
    """Delete stored cookies from config."""
    cfg = _load_config()
    changed = False
    for key in ("GEMINI_SECURE_1PSID", "GEMINI_SECURE_1PSIDTS"):
        if key in cfg:
            del cfg[key]
            changed = True
    if changed:
        _save_config(cfg)
        click.echo("  Cookies cleared.")
    else:
        click.echo("  No cookies stored.")


# ══════════════════════════════════════════════════════════════════
# config subcommand
# ══════════════════════════════════════════════════════════════════

@cli.group()
def config():
    """View or update configuration."""
    pass


@config.command("show")
def config_show():
    """Display all configuration values."""
    cfg = _load_config()
    if not cfg:
        click.echo("No configuration found. Run `gemini-web init` first.")
        return
    # Sensitive keys to mask
    sensitive = {"API_KEY", "GEMINI_SECURE_1PSID", "GEMINI_SECURE_1PSIDTS"}
    for key, val in sorted(cfg.items()):
        display = _mask(str(val)) if key in sensitive and val else val
        click.echo(f"  {key} = {display}")
    click.echo(f"\n  📁 Config file: {_config_file()}")
    click.echo(f"  📁 Data dir:    {_config_dir()}")


@config.command("get")
@click.argument("key")
def config_get(key: str):
    """Get a single config value."""
    cfg = _load_config()
    key_upper = key.upper()
    if key_upper in cfg:
        click.echo(f"  {key_upper} = {cfg[key_upper]}")
    elif key in cfg:
        click.echo(f"  {key} = {cfg[key]}")
    else:
        click.echo(f"  '{key}' not found in config.")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value. Example: gemini-web config set PORT 9000"""
    cfg = _load_config()
    # Preserve type for known numeric fields
    int_keys = {"PORT", "GEMINI_TIMEOUT", "GEMINI_WATCHDOG_TIMEOUT"}
    if key.upper() in int_keys:
        try:
            value = int(value)
        except ValueError:
            pass
    bool_keys = {"GEMINI_AUTO_REFRESH"}
    if key.upper() in bool_keys:
        value = value.lower() in ("true", "1", "yes")
    cfg[key] = value
    _save_config(cfg)
    click.echo(f"  {key} = {value}")


@config.command("delete")
@click.argument("key")
def config_delete(key: str):
    """Remove a config key."""
    cfg = _load_config()
    if key in cfg:
        del cfg[key]
        _save_config(cfg)
        click.echo(f"  Deleted '{key}'.")
    else:
        click.echo(f"  '{key}' not found in config.")


@config.command("path")
def config_path():
    """Print the config directory path."""
    click.echo(str(_config_dir()))


@config.command("reset")
def config_reset():
    """Delete ALL configuration and data."""
    cfg_file = _config_file()
    db_file = _config_dir() / "gemini.db"
    files = [f for f in (cfg_file, db_file) if f.exists()]
    if not files:
        click.echo("  Nothing to delete.")
        return
    click.echo("  Will delete:")
    for f in files:
        click.echo(f"    {f}")
    if click.confirm("  Proceed?"):
        for f in files:
            f.unlink()
        click.echo("  ✅ Configuration reset.")


# ══════════════════════════════════════════════════════════════════
# check
# ══════════════════════════════════════════════════════════════════

@cli.command()
def check():
    """Validate configuration and test Gemini connection."""
    import asyncio

    cfg = _load_config()
    ok = True

    # 1. Config file
    if _config_file().exists():
        click.echo("  ✅ Config file exists")
    else:
        click.echo("  ❌ Config file not found. Run `gemini-web init`.")
        sys.exit(1)

    # 2. API token
    api_key = cfg.get("API_KEY", "")
    if api_key and api_key != "changeme":
        click.echo(f"  ✅ API token set ({_mask(api_key)})")
    else:
        click.echo("  ❌ API token not set. Run `gemini-web token generate`.")
        ok = False

    # 3. Cookies
    psid = cfg.get("GEMINI_SECURE_1PSID", "")
    psidts = cfg.get("GEMINI_SECURE_1PSIDTS", "")
    if psid:
        click.echo(f"  ✅ __Secure-1PSID set ({_mask(psid)})")
    else:
        click.echo("  ❌ __Secure-1PSID not set. Run `gemini-web cookies set`.")
        ok = False
    if psidts:
        click.echo(f"  ✅ __Secure-1PSIDTS set ({_mask(psidts)})")
    else:
        click.echo("  ⚠️  __Secure-1PSIDTS not set (optional but recommended)")

    # 4. Test Gemini connection
    if psid:
        click.echo("\n  🔄 Testing Gemini connection...")
        try:
            from gemini_webapi import GeminiClient

            async def _test():
                proxy = cfg.get("GEMINI_PROXY") or None
                client = GeminiClient(
                    secure_1psid=psid,
                    secure_1psidts=psidts or None,
                    proxy=proxy,
                )
                await client.init(timeout=30, auto_close=False, close_delay=0)
                await client.close()

            asyncio.run(_test())
            click.echo("  ✅ Gemini connection OK")
        except Exception as e:
            click.echo(f"  ❌ Gemini connection failed: {e}")
            ok = False

    # 5. Database
    db_path = cfg.get("DATABASE_PATH", str(_config_dir() / "gemini.db"))
    db_file = Path(db_path)
    if db_file.exists():
        click.echo(f"  ✅ Database exists ({db_file})")
    else:
        click.echo(f"  ⚠️  Database not found ({db_file}) — will be created on first run")

    # Summary
    click.echo()
    if ok:
        click.echo("  ✅ All checks passed. Ready to run `gemini-web serve`.")
    else:
        click.echo("  ❌ Some checks failed. Fix the issues above before starting.")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════
# serve
# ══════════════════════════════════════════════════════════════════

@cli.command()
@click.option("--host", default=None, help="Bind host (overrides config)")
@click.option("--port", default=None, type=int, help="Bind port (overrides config)")
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev mode)")
def serve(host: str | None, port: int | None, reload: bool):
    """Start the API server."""
    import uvicorn

    cfg = _load_config()

    if not cfg.get("GEMINI_SECURE_1PSID"):
        click.echo("❌ No cookies configured. Run `gemini-web init` first.")
        sys.exit(1)

    if not cfg.get("API_KEY") or cfg["API_KEY"] == "changeme":
        click.echo("⚠️  No API token set. Generating one...")
        cfg["API_KEY"] = secrets.token_urlsafe(32)
        _save_config(cfg)
        click.echo(f"   Token: {cfg['API_KEY']}")

    # Inject config into environment so Settings picks it up
    import os
    for key, val in cfg.items():
        if val is not None and str(val) and key not in os.environ:
            os.environ[key] = str(val)

    if "DATABASE_PATH" not in os.environ and "DATABASE_PATH" not in cfg:
        os.environ["DATABASE_PATH"] = str(_config_dir() / "gemini.db")

    final_host = host or cfg.get("HOST", "0.0.0.0")
    final_port = port or cfg.get("PORT", 8000)

    click.echo(f"🚀 Gemini Web API Wrapper")
    click.echo(f"   Server:  http://{final_host}:{final_port}")
    click.echo(f"   Token:   {_mask(cfg['API_KEY'])}")
    click.echo(f"   Config:  {_config_file()}\n")

    uvicorn.run(
        "app.main:app",
        host=str(final_host),
        port=int(final_port),
        reload=reload,
    )


def main():
    cli()


if __name__ == "__main__":
    main()
