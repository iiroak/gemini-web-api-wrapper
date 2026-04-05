"""
CLI entry point for gemini-web-api-wrapper.

Usage:
    gemini-web init          # Interactive first-time setup
    gemini-web config show   # Show current configuration
    gemini-web config set    # Set a config value
    gemini-web config path   # Print config directory path
    gemini-web serve         # Start the API server
"""
from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

import click

# ── Config directory ─────────────────────────────────────────────

def _config_dir() -> Path:
    """Return ~/.gemini-web (cross-platform)."""
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


# ── CLI ──────────────────────────────────────────────────────────

@click.group()
@click.version_option(package_name="gemini-web-api-wrapper")
def cli():
    """Gemini Web API Wrapper — REST API for Google Gemini."""
    pass


@cli.command()
def init():
    """Interactive first-time setup."""
    cfg = _load_config()
    click.echo("🔧 Gemini Web API Wrapper — Setup\n")

    # API key
    existing_key = cfg.get("API_KEY", "")
    if existing_key and existing_key != "changeme":
        if not click.confirm(f"API_KEY already set ({existing_key[:8]}...). Overwrite?", default=False):
            pass
        else:
            cfg["API_KEY"] = _prompt_api_key()
    else:
        cfg["API_KEY"] = _prompt_api_key()

    # Cookies
    click.echo("\n📋 Google Gemini cookies (from browser DevTools → Application → Cookies → gemini.google.com)")
    cfg["GEMINI_SECURE_1PSID"] = click.prompt(
        "  __Secure-1PSID",
        default=cfg.get("GEMINI_SECURE_1PSID", ""),
    )
    cfg["GEMINI_SECURE_1PSIDTS"] = click.prompt(
        "  __Secure-1PSIDTS (optional, press Enter to skip)",
        default=cfg.get("GEMINI_SECURE_1PSIDTS", ""),
    )

    # Optional settings
    click.echo("\n⚙️  Optional settings (press Enter for defaults)")
    cfg["HOST"] = click.prompt("  Host", default=cfg.get("HOST", "0.0.0.0"))
    cfg["PORT"] = click.prompt("  Port", default=cfg.get("PORT", 8000), type=int)
    cfg["GEMINI_PROXY"] = click.prompt(
        "  HTTP proxy (blank for none)",
        default=cfg.get("GEMINI_PROXY", ""),
    )

    _save_config(cfg)
    click.echo(f"\n✅ Config saved to {_config_file()}")
    click.echo("   Run `gemini-web serve` to start the server.")


def _prompt_api_key() -> str:
    choice = click.prompt(
        "  Generate a random API key or enter your own? [g/custom]",
        default="g",
    )
    if choice.lower() == "g":
        key = secrets.token_urlsafe(32)
        click.echo(f"  Generated: {key}")
        return key
    return click.prompt("  Enter API key")


# ── config subcommand ────────────────────────────────────────────

@cli.group()
def config():
    """View or update configuration."""
    pass


@config.command("show")
def config_show():
    """Display current configuration."""
    cfg = _load_config()
    if not cfg:
        click.echo("No configuration found. Run `gemini-web init` first.")
        return
    for key, val in sorted(cfg.items()):
        # Mask sensitive values
        if "1PSID" in key and val and len(val) > 12:
            display = val[:8] + "..." + val[-4:]
        elif key == "API_KEY" and val and len(val) > 12:
            display = val[:8] + "..." + val[-4:]
        else:
            display = val
        click.echo(f"  {key} = {display}")
    click.echo(f"\n  Config file: {_config_file()}")
    click.echo(f"  Data dir:    {_config_dir()}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value. Example: gemini-web config set PORT 9000"""
    cfg = _load_config()
    # Try to preserve type for known int fields
    if key in ("PORT", "GEMINI_TIMEOUT", "GEMINI_WATCHDOG_TIMEOUT"):
        try:
            value = int(value)
        except ValueError:
            pass
    cfg[key] = value
    _save_config(cfg)
    click.echo(f"  {key} = {value}")


@config.command("path")
def config_path():
    """Print the config directory path."""
    click.echo(str(_config_dir()))


@config.command("reset")
def config_reset():
    """Delete all configuration."""
    f = _config_file()
    if f.exists():
        if click.confirm(f"Delete {f}?"):
            f.unlink()
            click.echo("Configuration deleted.")
    else:
        click.echo("No configuration file found.")


# ── serve ────────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default=None, help="Bind host (overrides config)")
@click.option("--port", default=None, type=int, help="Bind port (overrides config)")
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev mode)")
def serve(host: str | None, port: int | None, reload: bool):
    """Start the API server."""
    import uvicorn

    cfg = _load_config()

    if not cfg.get("GEMINI_SECURE_1PSID") and not _has_env_cookies():
        click.echo("❌ No cookies configured. Run `gemini-web init` first.")
        sys.exit(1)

    # Inject config into environment so Settings (pydantic) picks it up
    import os
    for key, val in cfg.items():
        if val and key not in os.environ:  # env vars take precedence
            os.environ[key] = str(val)

    # Set database path to config dir if not overridden
    if "DATABASE_PATH" not in os.environ and "DATABASE_PATH" not in cfg:
        os.environ["DATABASE_PATH"] = str(_config_dir() / "gemini.db")

    final_host = host or cfg.get("HOST", "0.0.0.0")
    final_port = port or cfg.get("PORT", 8000)

    click.echo(f"🚀 Starting Gemini Web API Wrapper on {final_host}:{final_port}")
    uvicorn.run(
        "app.main:app",
        host=str(final_host),
        port=int(final_port),
        reload=reload,
    )


def _has_env_cookies() -> bool:
    """Check if cookies are available via env vars or .env file."""
    import os
    if os.environ.get("GEMINI_SECURE_1PSID"):
        return True
    if Path(".env").exists():
        content = Path(".env").read_text()
        for line in content.splitlines():
            if line.strip().startswith("GEMINI_SECURE_1PSID=") and len(line.split("=", 1)[1].strip()) > 5:
                return True
    return False


def main():
    cli()


if __name__ == "__main__":
    main()
