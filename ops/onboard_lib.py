"""Reine, testbare Onboarding-Logik (nur stdlib, kein Docker/SSH/Netz)."""
from __future__ import annotations

import json
import re

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
