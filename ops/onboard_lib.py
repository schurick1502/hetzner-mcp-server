"""Reine, testbare Onboarding-Logik (nur stdlib, kein Docker/SSH/Netz)."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
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
            f"Umgebungsvariable fuer Slug '{slug}' existiert bereits "
            "(--update zum Ueberschreiben)."
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


def _read_monitor(env_path: str) -> str:
    """Liest DOCKER_MONITOR_SERVERS aus .env."""
    p = Path(env_path)
    if not p.exists():
        raise OnboardError(f".env nicht gefunden: {p}")
    for l in p.read_text(encoding="utf-8").splitlines():
        if _is_assignment(l, "DOCKER_MONITOR_SERVERS"):
            return l.split("=", 1)[1]
    return ""


def _cli(argv=None) -> int:
    """CLI-Einstiegspunkt für update-env Befehl."""
    parser = argparse.ArgumentParser(prog="ops.onboard_lib")
    sub = parser.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("update-env")
    u.add_argument("--env-file", default=".env")
    u.add_argument("--slug", required=True)
    u.add_argument("--host", required=True)
    u.add_argument("--alias", default=None)
    u.add_argument("--user", default="root")
    u.add_argument("--port", default="22")
    u.add_argument("--update", action="store_true")
    u.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        slug = validate_slug(args.slug)
        entry = build_entry(slug, args.host, alias=args.alias,
                            user=args.user, port=args.port)
        token = os.environ.get("ONBOARD_TOKEN", "")
        if not token:
            raise OnboardError("ONBOARD_TOKEN (Prozess-Env) ist leer.")
        if args.dry_run:
            preview = merge_monitor_servers(
                _read_monitor(args.env_file), entry, allow_update=True)
            print(f"[dry-run] HCLOUD_TOKEN_{slug.upper()}=*** (verborgen)")
            print(f"[dry-run] DOCKER_MONITOR_SERVERS={preview}")
            return 0
        info = update_env_file(args.env_file, slug, token, entry,
                               allow_update=args.update)
        print(f"OK token_key={info['token_key']}")
        print(f"OK DOCKER_MONITOR_SERVERS={info['monitor_json']}")
        return 0
    except OnboardError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
