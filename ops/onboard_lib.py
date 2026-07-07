"""Reine, testbare Onboarding-Logik (nur stdlib, kein Docker/SSH/Netz)."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9_]+$")


class OnboardError(Exception):
    """Fachlicher Fehler mit klarer Nutzer-Meldung."""


def validate_slug(slug: str) -> str:
    s = (slug or "").strip().lower()
    if not SLUG_RE.match(s):
        raise OnboardError(
            f"Ungueltiger Slug '{slug}': nur [a-z0-9_], keine Bindestriche "
            "(wird Teil des Env-Var-Namens HCLOUD_TOKEN_<SLUG>)."
        )
    return s


def build_entry(name, host, alias=None, user="root", port=22) -> dict:
    if isinstance(alias, str):
        alias_list = [alias]
    else:
        alias_list = list(alias or [])
    aliases = [a.strip() for a in alias_list if a and a.strip()]
    return {"name": name, "host": host, "user": user,
            "port": int(port), "aliases": aliases}


def merge_monitor_servers(current_json: str, entry: dict,
                          allow_update: bool = False) -> str:
    raw = (current_json or "").strip()
    servers = json.loads(raw) if raw else []
    if not isinstance(servers, list):
        raise OnboardError("DOCKER_MONITOR_SERVERS ist kein JSON-Array.")
    idx = next(
        (i for i, s in enumerate(servers)
         if isinstance(s, dict) and s.get("name") == entry["name"]),
        None,
    )
    if idx is not None:
        if not allow_update:
            raise OnboardError(
                f"Monitor-Eintrag '{entry['name']}' existiert bereits "
                "(--update zum Ueberschreiben)."
            )
        servers[idx] = entry
    else:
        servers.append(entry)
    return json.dumps(servers, ensure_ascii=False)


def _is_assignment(line: str, key: str) -> bool:
    if "=" not in line or line.lstrip().startswith("#"):
        return False
    return line.split("=", 1)[0].strip() == key


def update_env_file(env_path, slug, token, entry, allow_update=False) -> dict:
    path = Path(env_path)
    if not path.exists():
        raise OnboardError(f".env nicht gefunden: {path}")

    token_key = f"HCLOUD_TOKEN_{slug.upper()}"
    lines = path.read_text(encoding="utf-8").splitlines()

    if any(_is_assignment(l, token_key) for l in lines) and not allow_update:
        raise OnboardError(
            f"{token_key} existiert bereits (--update zum Ueberschreiben)."
        )

    current_monitor = ""
    for l in lines:
        if _is_assignment(l, "DOCKER_MONITOR_SERVERS"):
            current_monitor = l.split("=", 1)[1]
            break
    monitor_json = merge_monitor_servers(current_monitor, entry, allow_update=allow_update)

    # Backup erst NACH erfolgreicher Validierung (kein halber Zustand)
    shutil.copy2(path, path.with_name(path.name + ".bak"))

    out, wrote_token, wrote_monitor = [], False, False
    for l in lines:
        if _is_assignment(l, "DOCKER_MONITOR_SERVERS"):
            out.append(f"DOCKER_MONITOR_SERVERS={monitor_json}")
            wrote_monitor = True
        elif _is_assignment(l, token_key):
            out.append(f"{token_key}={token}")
            wrote_token = True
        else:
            out.append(l)
    if not wrote_token:
        out.append(f"{token_key}={token}")
    if not wrote_monitor:
        out.append(f"DOCKER_MONITOR_SERVERS={monitor_json}")

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return {"token_key": token_key, "monitor_json": monitor_json}
