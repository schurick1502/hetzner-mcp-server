"""Settings API Routes - Manage .env configuration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
from pathlib import Path

router = APIRouter()


def _get_env_file() -> Path:
    """Get path to .env file - mounted volume in Docker or project root."""
    docker_path = Path("/app/.env")
    if docker_path.exists():
        return docker_path
    return Path(__file__).resolve().parents[5] / ".env"


# Settings that can be configured
SETTING_GROUPS = {
    "hetzner": {
        "label": "Hetzner Cloud",
        "settings": {
            "HCLOUD_TOKEN": {"label": "API Token", "secret": True},
            "HCLOUD_TOKEN_OM": {"label": "API Token (OM)", "secret": True},
            "HCLOUD_DEFAULT_ACCOUNT": {"label": "Standard Account", "secret": False},
        },
    },
    "ai": {
        "label": "AI Provider",
        "settings": {
            "ANTHROPIC_API_KEY": {"label": "Anthropic API Key", "secret": True},
            "OPENAI_API_KEY": {"label": "OpenAI API Key", "secret": True},
            "GEMINI_API_KEY": {"label": "Gemini API Key", "secret": True},
            "DEFAULT_AI_PROVIDER": {"label": "Standard Provider", "secret": False},
            "DEFAULT_AI_MODEL": {"label": "Standard Model", "secret": False},
        },
    },
    "docker": {
        "label": "Docker Monitoring",
        "settings": {
            "DOCKER_MONITOR_SERVERS": {"label": "Server-Liste (JSON)", "secret": False},
        },
    },
}


def _validate_docker_servers(value: str) -> None:
    """Validate DOCKER_MONITOR_SERVERS JSON format."""
    if not value:
        return

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"DOCKER_MONITOR_SERVERS ist kein gueltiges JSON: {exc.msg}",
        ) from exc

    if not isinstance(parsed, list):
        raise HTTPException(
            status_code=400,
            detail="DOCKER_MONITOR_SERVERS muss ein JSON-Array sein.",
        )

    for idx, entry in enumerate(parsed, start=1):
        if not isinstance(entry, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Server-Eintrag {idx} muss ein Objekt sein.",
            )
        if not entry.get("host") or not entry.get("user"):
            raise HTTPException(
                status_code=400,
                detail=f"Server-Eintrag {idx} braucht mindestens 'host' und 'user'.",
            )


def _read_env_values() -> dict[str, str]:
    """Read settings values from .env file, falling back to os.environ."""
    values = {}
    env_file = _get_env_file()

    # Try reading from .env file first
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()

    # Fallback to os.environ for keys not found in file
    all_keys = set()
    for group in SETTING_GROUPS.values():
        all_keys.update(group["settings"].keys())

    for key in all_keys:
        if key not in values:
            env_val = os.environ.get(key, "")
            if env_val:
                values[key] = env_val

    return values


def _mask_value(value: str, is_secret: bool) -> str:
    """Mask secret values, showing only last 4 characters."""
    if not is_secret or not value:
        return value
    if len(value) <= 4:
        return "****"
    return "*" * (len(value) - 4) + value[-4:]


def _write_env_file(updates: dict[str, str]) -> None:
    """Update .env file, preserving comments and structure."""
    env_file = _get_env_file()

    if not env_file.exists():
        lines = []
        for key, value in updates.items():
            lines.append(f"{key}={value}")
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    existing_lines = env_file.read_text(encoding="utf-8").splitlines()
    updated_keys = set()
    new_lines = []

    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                if updates[key]:
                    new_lines.append(f"{key}={updates[key]}")
                else:
                    new_lines.append(line)
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Add new keys that weren't in the file
    for key, value in updates.items():
        if key not in updated_keys and value:
            new_lines.append(f"{key}={value}")

    env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


@router.get("/")
async def get_settings():
    """Get all settings with masked secret values."""
    env_values = _read_env_values()
    result = {}

    for group_key, group in SETTING_GROUPS.items():
        group_settings = {}
        for key, meta in group["settings"].items():
            raw_value = env_values.get(key, "")
            group_settings[key] = {
                "label": meta["label"],
                "value": _mask_value(raw_value, meta["secret"]),
                "is_secret": meta["secret"],
                "has_value": bool(raw_value),
            }
        result[group_key] = {
            "label": group["label"],
            "settings": group_settings,
        }

    return {"success": True, "data": result}


class SettingsUpdateRequest(BaseModel):
    settings: dict[str, str]


@router.put("/")
async def update_settings(request: SettingsUpdateRequest):
    """Update settings in .env file."""
    allowed_keys = set()
    for group in SETTING_GROUPS.values():
        allowed_keys.update(group["settings"].keys())

    invalid_keys = set(request.settings.keys()) - allowed_keys
    if invalid_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannte Einstellungen: {', '.join(invalid_keys)}",
        )

    updates = {}
    for key, value in request.settings.items():
        is_secret = any(
            key in group["settings"] and group["settings"][key]["secret"]
            for group in SETTING_GROUPS.values()
        )
        if is_secret and not value:
            continue
        if key == "DOCKER_MONITOR_SERVERS":
            _validate_docker_servers(value)
        updates[key] = value

    if updates:
        _write_env_file(updates)
        for key, value in updates.items():
            if value:
                os.environ[key] = value

    return {
        "success": True,
        "message": "Einstellungen gespeichert. Einige Änderungen erfordern einen Neustart des Backends.",
        "updated_keys": list(updates.keys()),
    }
