# Kundenserver-Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein wiederholbares Bash-Skript + Runbook, das einen neuen Kundenserver mit einem Lauf vollständig ins hetzner-mcp-Monitoring aufnimmt (Cloud-API-Account + Docker/Live-Metriken-SSH).

**Architecture:** Die riskante, deterministische Logik (Slug-Regel, JSON-Merge von `DOCKER_MONITOR_SERVERS`, atomare `.env`-Mutation) liegt in einem reinen, mit pytest testbaren Python-Modul `ops/onboard_lib.py` (nur stdlib, keine Docker-/SSH-/Netz-Aufrufe). Das Bash-Skript `ops/add-customer-server.sh` orchestriert: Eingaben sammeln → Token & SSH im laufenden Backend-Container validieren → `.env` über das Modul aktualisieren → Backend neu erzeugen → live nachprüfen. Ansatz A: `.env` wird nur bei erfolgreicher Vorab-Validierung geändert.

**Tech Stack:** Bash (Git Bash unter Windows), Python 3.11 stdlib, pytest, Docker Compose, curl.

## Global Constraints

- Slug nur `[a-z0-9_]`, **keine Bindestriche** (wird Env-Var-Name `HCLOUD_TOKEN_<SLUG_UPPER>`); `config.py` lowercased das Suffix zur Account-ID.
- Token niemals als CLI-Argument, in Logs, in `stdout` oder in `.env.bak`-Ausgaben sichtbar machen. Übergabe an Python-Modul ausschließlich per Prozess-Env `ONBOARD_TOKEN`.
- `.env` ist gitignored und wird **nie committet**. Vor jeder Mutation Backup nach `.env.bak`.
- `onboard_lib.py` importiert nur die Standardbibliothek (json, re, shutil, pathlib, os, argparse) — muss ohne laufenden Stack und ohne hcloud/paramiko laufen.
- Bash-Skript und Skript-Tests laufen gegen das **Haupt-Verzeichnis** `C:\projekte\hetzner-mcp-server` (echte `.env`, laufender Compose-Stack). Der Worktree dient nur der Feature-Entwicklung.
- Docker-Zugriff immer über `docker compose exec -T backend …` (nicht über festen Containernamen).
- Monitor-`name` == Account-Slug (damit `?account=<slug>` und der SSH-Match zusammenpassen).

---

### Task 1: Reine Logik — Slug, Entry, JSON-Merge

**Files:**
- Create: `ops/onboard_lib.py`
- Test: `tests/test_onboard_lib.py`

**Interfaces:**
- Produces:
  - `class OnboardError(Exception)`
  - `validate_slug(slug: str) -> str` — normalisiert (lower/strip), wirft `OnboardError` bei ungültig
  - `build_entry(name: str, host: str, alias: str | None = None, user: str = "root", port: int | str = 22) -> dict` — liefert `{"name","host","user","port","aliases":[...]}`
  - `merge_monitor_servers(current_json: str, entry: dict, allow_update: bool = False) -> str` — mergt Entry in ein JSON-Array; wirft `OnboardError` wenn `name` existiert und nicht `allow_update`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_onboard_lib.py
import json
import pytest
from ops.onboard_lib import (
    OnboardError, validate_slug, build_entry, merge_monitor_servers,
)


def test_validate_slug_ok():
    assert validate_slug("Ehmen") == "ehmen"
    assert validate_slug("acme_01") == "acme_01"


@pytest.mark.parametrize("bad", ["tsv-ehmen", "acme server", "", "a.b"])
def test_validate_slug_rejects(bad):
    with pytest.raises(OnboardError):
        validate_slug(bad)


def test_build_entry_defaults_and_alias():
    e = build_entry("acme", "100.0.0.1", alias="1.2.3.4")
    assert e == {"name": "acme", "host": "100.0.0.1", "user": "root",
                 "port": 22, "aliases": ["1.2.3.4"]}
    assert build_entry("acme", "1.1.1.1")["aliases"] == []


def test_merge_appends_new():
    cur = '[{"name":"a","host":"h1","user":"root","port":22,"aliases":[]}]'
    out = json.loads(merge_monitor_servers(cur, build_entry("b", "h2")))
    assert [s["name"] for s in out] == ["a", "b"]


def test_merge_empty_current():
    out = json.loads(merge_monitor_servers("", build_entry("b", "h2")))
    assert out[0]["name"] == "b"


def test_merge_duplicate_without_update_raises():
    cur = '[{"name":"a","host":"h1","user":"root","port":22,"aliases":[]}]'
    with pytest.raises(OnboardError):
        merge_monitor_servers(cur, build_entry("a", "hX"))


def test_merge_duplicate_with_update_replaces():
    cur = '[{"name":"a","host":"h1","user":"root","port":22,"aliases":[]}]'
    out = json.loads(merge_monitor_servers(cur, build_entry("a", "hNEW"), allow_update=True))
    assert len(out) == 1 and out[0]["host"] == "hNEW"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/projekte/hetzner-mcp-server-onboarding && python -m pytest tests/test_onboard_lib.py -v`
Expected: FAIL mit `ModuleNotFoundError: No module named 'ops.onboard_lib'`

- [ ] **Step 3: Write minimal implementation**

```python
# ops/onboard_lib.py
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
```

Außerdem sicherstellen, dass `ops/` als Paket importierbar ist:

```bash
# ops/__init__.py anlegen (leer), damit `from ops.onboard_lib import ...` greift
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_onboard_lib.py -v`
Expected: PASS (8 Tests grün)

- [ ] **Step 5: Commit**

```bash
git add ops/__init__.py ops/onboard_lib.py tests/test_onboard_lib.py
git commit -m "feat(onboard): reine Logik für Slug/Entry/Monitor-Merge + Tests"
```

---

### Task 2: Atomare `.env`-Aktualisierung

**Files:**
- Modify: `ops/onboard_lib.py` (Funktion `update_env_file` ergänzen)
- Test: `tests/test_onboard_lib.py` (Tests ergänzen)

**Interfaces:**
- Consumes: `merge_monitor_servers`, `build_entry`, `OnboardError` (Task 1)
- Produces:
  - `update_env_file(env_path: str, slug: str, token: str, entry: dict, allow_update: bool = False) -> dict` — sichert `.env` nach `.env.bak`, ergänzt/ersetzt `HCLOUD_TOKEN_<SLUG_UPPER>` und `DOCKER_MONITOR_SERVERS`; gibt `{"token_key": str, "monitor_json": str}` zurück. Wirft `OnboardError` wenn Token-Key existiert und nicht `allow_update`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_onboard_lib.py  (ergänzen)
from pathlib import Path
from ops.onboard_lib import update_env_file


def _write(tmp_path, body):
    p = tmp_path / ".env"
    p.write_text(body, encoding="utf-8")
    return p


BASE_ENV = (
    "HCLOUD_TOKEN=abc\n"
    'DOCKER_MONITOR_SERVERS=[{"name":"main","host":"10.0.0.1","user":"root","port":22,"aliases":[]}]\n'
)


def test_update_env_adds_token_and_monitor(tmp_path):
    p = _write(tmp_path, BASE_ENV)
    info = update_env_file(str(p), "acme", "TOK123", build_entry("acme", "100.0.0.2", alias="9.9.9.9"))
    text = p.read_text(encoding="utf-8")
    assert "HCLOUD_TOKEN_ACME=TOK123" in text
    assert '"name": "acme"' in text.replace(" ", " ")  # Eintrag vorhanden
    assert info["token_key"] == "HCLOUD_TOKEN_ACME"
    # Backup wurde angelegt und enthält den Originalinhalt
    assert (tmp_path / ".env.bak").read_text(encoding="utf-8") == BASE_ENV


def test_update_env_duplicate_token_without_update_raises(tmp_path):
    p = _write(tmp_path, BASE_ENV + "HCLOUD_TOKEN_ACME=old\n")
    with pytest.raises(OnboardError):
        update_env_file(str(p), "acme", "TOK123", build_entry("acme", "100.0.0.2"))


def test_update_env_update_replaces_token(tmp_path):
    p = _write(tmp_path, BASE_ENV + "HCLOUD_TOKEN_ACME=old\n")
    update_env_file(str(p), "acme", "NEW", build_entry("acme", "100.0.0.2"), allow_update=True)
    text = p.read_text(encoding="utf-8")
    assert "HCLOUD_TOKEN_ACME=NEW" in text and "HCLOUD_TOKEN_ACME=old" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_onboard_lib.py -k update_env -v`
Expected: FAIL mit `ImportError: cannot import name 'update_env_file'`

- [ ] **Step 3: Write minimal implementation**

```python
# ops/onboard_lib.py  (ergänzen)
import shutil
from pathlib import Path


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_onboard_lib.py -v`
Expected: PASS (alle Tests grün)

- [ ] **Step 5: Commit**

```bash
git add ops/onboard_lib.py tests/test_onboard_lib.py
git commit -m "feat(onboard): atomare .env-Aktualisierung mit Backup + Idempotenz"
```

---

### Task 3: CLI-Wrapper für das Modul (Aufruf aus Bash)

**Files:**
- Modify: `ops/onboard_lib.py` (argparse-CLI + `__main__`)
- Test: `tests/test_onboard_cli.py`

**Interfaces:**
- Consumes: `validate_slug`, `build_entry`, `update_env_file` (Tasks 1–2)
- Produces: CLI `python -m ops.onboard_lib update-env --env-file <p> --slug <s> --host <h> [--alias <a>] [--user <u>] [--port <p>] [--update] [--dry-run]`. Token kommt aus Env `ONBOARD_TOKEN`. Exit 0 = OK, 2 = `OnboardError`. Bei `--dry-run` wird nichts geschrieben; Ausgabe der geplanten Änderung.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_onboard_cli.py
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASE_ENV = (
    "HCLOUD_TOKEN=abc\n"
    'DOCKER_MONITOR_SERVERS=[{"name":"main","host":"10.0.0.1","user":"root","port":22,"aliases":[]}]\n'
)


def _run(args, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run([sys.executable, "-m", "ops.onboard_lib", *args],
                          cwd=REPO, env=env, capture_output=True, text=True)


def test_cli_dry_run_does_not_write(tmp_path):
    p = tmp_path / ".env"; p.write_text(BASE_ENV, encoding="utf-8")
    r = _run(["update-env", "--env-file", str(p), "--slug", "acme",
              "--host", "100.0.0.2", "--dry-run"],
             {"ONBOARD_TOKEN": "TOK"})
    assert r.returncode == 0, r.stderr
    assert p.read_text(encoding="utf-8") == BASE_ENV  # unverändert
    assert "acme" in r.stdout


def test_cli_writes_and_is_idempotent(tmp_path):
    p = tmp_path / ".env"; p.write_text(BASE_ENV, encoding="utf-8")
    r1 = _run(["update-env", "--env-file", str(p), "--slug", "acme",
               "--host", "100.0.0.2"], {"ONBOARD_TOKEN": "TOK"})
    assert r1.returncode == 0, r1.stderr
    assert "HCLOUD_TOKEN_ACME=TOK" in p.read_text(encoding="utf-8")
    # Zweiter Lauf ohne --update -> Exit 2, Token bleibt in Ausgabe unsichtbar
    r2 = _run(["update-env", "--env-file", str(p), "--slug", "acme",
               "--host", "100.0.0.2"], {"ONBOARD_TOKEN": "TOK"})
    assert r2.returncode == 2
    assert "TOK" not in (r2.stdout + r2.stderr)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_onboard_cli.py -v`
Expected: FAIL (Exit != 0 / kein CLI-Handler; `update-env` unbekannt)

- [ ] **Step 3: Write minimal implementation**

```python
# ops/onboard_lib.py  (am Ende ergänzen)
import argparse
import json as _json
import os
import sys


def _cli(argv=None) -> int:
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


def _read_monitor(env_path: str) -> str:
    p = Path(env_path)
    if not p.exists():
        raise OnboardError(f".env nicht gefunden: {p}")
    for l in p.read_text(encoding="utf-8").splitlines():
        if _is_assignment(l, "DOCKER_MONITOR_SERVERS"):
            return l.split("=", 1)[1]
    return ""


if __name__ == "__main__":
    raise SystemExit(_cli())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_onboard_cli.py -v && python -m pytest -q`
Expected: PASS (alle Tests grün)

- [ ] **Step 5: Commit**

```bash
git add ops/onboard_lib.py tests/test_onboard_cli.py
git commit -m "feat(onboard): CLI-Wrapper (update-env/--dry-run) + Subprozess-Tests"
```

---

### Task 4: Orchestrierungs-Skript `ops/add-customer-server.sh`

**Files:**
- Create: `ops/add-customer-server.sh`
- Test: `tests/test_add_customer_server_smoke.py`

**Interfaces:**
- Consumes: `python -m ops.onboard_lib update-env …` (Task 3); laufender Compose-Stack.
- Produces: ausführbares Skript. Flags: `--slug --host [--alias --user --port --update --dry-run --env-file --repo-dir]`. Token via verstecktem Prompt (`read -s`) oder Env `ONBOARD_TOKEN`. Exit 0 = alles grün.

- [ ] **Step 1: Write the failing test (Smoke: Syntax + Usage)**

```python
# tests/test_add_customer_server_smoke.py
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "ops" / "add-customer-server.sh"


def test_script_exists_and_valid_bash():
    assert SCRIPT.exists()
    r = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr  # Syntax ok


def test_usage_on_missing_args():
    r = subprocess.run(["bash", str(SCRIPT), "--help"], capture_output=True, text=True)
    assert "add-customer-server.sh" in (r.stdout + r.stderr)
    assert "--slug" in (r.stdout + r.stderr)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_add_customer_server_smoke.py -v`
Expected: FAIL (`SCRIPT.exists()` falsch)

- [ ] **Step 3: Write the script**

```bash
#!/usr/bin/env bash
# ops/add-customer-server.sh
# Nimmt einen neuen Kundenserver ins hetzner-mcp-Monitoring auf:
#   1) Cloud-API-Account (HCLOUD_TOKEN_<SLUG>)  2) Docker/Live-Metriken-SSH-Eintrag.
# Ansatz A: erst Token+SSH validieren, .env nur bei Erfolg ändern.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
ENV_FILE="${ENV_FILE:-$REPO_DIR/.env}"
SLUG="" HOST="" ALIAS="" USER_NAME="root" PORT="22" UPDATE="" DRY_RUN=""

usage() {
  cat <<'EOF'
add-customer-server.sh — Kundenserver ins hetzner-mcp-Monitoring aufnehmen

  --slug <name>     Kunden-Slug [a-z0-9_], keine Bindestriche (Pflicht)
  --host <ip/dns>   SSH-Host für das Monitoring (Pflicht)
  --alias <ip>      optional: z. B. Public-IP, falls host=Tailscale-IP
  --user <name>     SSH-User (Default: root)
  --port <n>        SSH-Port (Default: 22)
  --update          bestehenden Account/Eintrag überschreiben
  --dry-run         nur anzeigen, nichts ändern (validiert trotzdem)
  --env-file <p>    abweichende .env
  -h|--help         diese Hilfe

Token: versteckter Prompt, oder Env ONBOARD_TOKEN (nicht als Flag!).
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --slug) SLUG="$2"; shift 2;;
    --host) HOST="$2"; shift 2;;
    --alias) ALIAS="$2"; shift 2;;
    --user) USER_NAME="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --update) UPDATE="1"; shift;;
    --dry-run) DRY_RUN="1"; shift;;
    --env-file) ENV_FILE="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unbekannte Option: $1" >&2; usage; exit 1;;
  esac
done

[ -n "$SLUG" ] && [ -n "$HOST" ] || { echo "FEHLER: --slug und --host sind Pflicht." >&2; usage; exit 1; }

dc() { (cd "$REPO_DIR" && docker compose "$@"); }

# --- Token einlesen (nie echoen) ---
if [ -z "${ONBOARD_TOKEN:-}" ]; then
  printf "Hetzner-API-Token für '%s' (versteckt): " "$SLUG" >&2
  read -rs ONBOARD_TOKEN; echo >&2
fi
export ONBOARD_TOKEN
[ -n "$ONBOARD_TOKEN" ] || { echo "FEHLER: kein Token angegeben." >&2; exit 1; }

echo "==> Vorab-Validierung (nichts wird geändert)…" >&2

# 1) Cloud-API-Token im Backend-Container prüfen
if ! dc exec -T -e ONBOARD_TMP="$ONBOARD_TOKEN" backend python -c '
import os, sys
from hcloud import Client
srv = Client(token=os.environ["ONBOARD_TMP"]).servers.get_all()
print("   API OK:", len(srv), "Server:", [s.name for s in srv])
' >&2; then
  echo "FEHLER: Cloud-API-Token ungültig oder API nicht erreichbar. .env unverändert." >&2
  exit 1
fi

# 2) SSH-Erreichbarkeit im Backend-Container prüfen (gemounteter hetzner_key)
if ! dc exec -T backend python -c "
import sys; sys.path.insert(0,'/app')
from app.api.routes.docker_monitoring import SSHConnection
out, err, rc = SSHConnection.execute('$HOST', '$USER_NAME', $PORT, 'hostname')
print('   SSH OK:', out.strip()) if rc == 0 else sys.stderr.write('SSH rc=%s %s\n' % (rc, err))
sys.exit(0 if rc == 0 else 1)
" >&2; then
  echo "FEHLER: SSH zu $USER_NAME@$HOST:$PORT fehlgeschlagen. .env unverändert." >&2
  exit 1
fi

# --- .env aktualisieren (über getestetes Python-Modul) ---
PY_ARGS=(update-env --env-file "$ENV_FILE" --slug "$SLUG" --host "$HOST"
         --user "$USER_NAME" --port "$PORT")
[ -n "$ALIAS" ] && PY_ARGS+=(--alias "$ALIAS")
[ -n "$UPDATE" ] && PY_ARGS+=(--update)
[ -n "$DRY_RUN" ] && PY_ARGS+=(--dry-run)

echo "==> .env aktualisieren…" >&2
(cd "$REPO_DIR" && python -m ops.onboard_lib "${PY_ARGS[@]}")

if [ -n "$DRY_RUN" ]; then
  echo "==> dry-run: keine Änderung, kein Neustart." >&2
  exit 0
fi

# --- Backend neu erzeugen (lädt neue .env) ---
echo "==> Backend neu erzeugen…" >&2
dc up -d --force-recreate backend >&2
for i in $(seq 1 20); do
  code="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8501/ || true)"
  [ "$code" = "200" ] && break
  sleep 1
done

# --- Nach-Validierung (live) ---
echo "==> Nach-Validierung…" >&2
python - "$SLUG" "$HOST" <<'PY'
import sys, json, urllib.request
slug, host = sys.argv[1], sys.argv[2]
def get(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.load(r)
acc = get("http://localhost:8501/api/accounts")
assert any(a["id"] == slug for a in acc["accounts"]), "Account fehlt in /api/accounts"
srv = get(f"http://localhost:8501/api/servers/?account={slug}")
assert srv.get("success"), srv
met = get(f"http://localhost:8501/api/docker/system-metrics?server={host}")
ok = "metrics" in met or met.get("cpu_percent") is not None
print(f"   Account '{slug}' aktiv, {len(srv.get('servers', []))} Server, "
      f"Live-Metriken: {'OK' if ok else 'noch keine'}")
PY

echo "==> FERTIG: '$SLUG' ($HOST) ist im Monitoring." >&2
```

Danach ausführbar machen:

```bash
chmod +x ops/add-customer-server.sh
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_add_customer_server_smoke.py -v`
Expected: PASS (Syntax ok, Usage zeigt `--slug`)

- [ ] **Step 5: Commit**

```bash
git add ops/add-customer-server.sh tests/test_add_customer_server_smoke.py
git commit -m "feat(onboard): Orchestrierungs-Skript add-customer-server.sh + Smoke-Test"
```

---

### Task 5: Runbook `ops/ONBOARDING.md`

**Files:**
- Create: `ops/ONBOARDING.md`

**Interfaces:**
- Consumes: das Skript aus Task 4 (Dokumentation, kein Code).

- [ ] **Step 1: Runbook schreiben**

```markdown
# Kundenserver ins Monitoring aufnehmen

Automatisiert per `ops/add-customer-server.sh` (Ansatz A: validieren, dann `.env` ändern).

## Voraussetzungen
- Kundenserver hat den **Public-Key zu `~/.ssh/hetzner_key`** in `root@…:~/.ssh/authorized_keys`.
- Hetzner-API-Token mit **Read/Write** für das Kundenprojekt.
- SSH-Host vom Monitor-Host erreichbar (Tailscale: beide im Tailnet; Public-IP: Port 22 offen).
- Compose-Stack läuft (`docker compose ps` → `backend` up).

## Aufruf (aus dem Repo-Root)
```bash
# Public-IP direkt:
bash ops/add-customer-server.sh --slug acme --host 203.0.113.10
# Tailscale-IP + Public-IP als Alias:
bash ops/add-customer-server.sh --slug acme --host 100.100.0.5 --alias 203.0.113.10
```
Der Token wird versteckt abgefragt. `--dry-run` zeigt die geplante Änderung ohne Schreiben.
`--update` überschreibt einen bestehenden Slug.

## Slug-Regel
Nur `[a-z0-9_]`, **keine Bindestriche** — wird Env-Var-Name `HCLOUD_TOKEN_<SLUG>`
(daher z. B. `ehmen`, nicht `tsv-ehmen`).

## Was passiert
1. Token + SSH werden im Backend-Container getestet.
2. `.env` wird gesichert (`.env.bak`) und um `HCLOUD_TOKEN_<SLUG>` + `DOCKER_MONITOR_SERVERS`-Eintrag ergänzt.
3. `docker compose up -d --force-recreate backend`.
4. Live-Check: `/api/accounts`, `/api/servers/?account=<slug>`, `/api/docker/system-metrics`.

## Manueller Fallback
`.env` von Hand:
```
HCLOUD_TOKEN_ACME=<token>
DOCKER_MONITOR_SERVERS=[…, {"name":"acme","host":"<host>","aliases":["<public-ip>"],"user":"root","port":22}]
```
dann `docker compose up -d --force-recreate backend`.

## Troubleshooting
- **API-Fehler:** Token-Scope (Read/Write) / richtiges Projekt prüfen.
- **SSH-Timeout:** Erreichbarkeit (Tailnet/UFW), `hetzner_key` in `authorized_keys`.
- **Rollback:** `cp .env.bak .env && docker compose up -d --force-recreate backend`.
```

- [ ] **Step 2: Commit**

```bash
git add ops/ONBOARDING.md
git commit -m "docs(onboard): Runbook ops/ONBOARDING.md"
```

---

### Task 6: Integrationsvalidierung gegen den laufenden Stack

**Files:** keine (manuelle Validierung mit dokumentierten Erwartungen)

**Interfaces:**
- Consumes: fertiges Skript (Task 4), laufender Stack im Haupt-Verzeichnis.

> **Wichtig:** Diese Tests laufen im **Haupt-Verzeichnis** `C:\projekte\hetzner-mcp-server` (echte `.env`, laufender Stack), NICHT im Worktree. Skript + `ops/`-Modul dafür ins Haupt-Verzeichnis bringen (Merge des Branches oder temporäres Kopieren).

- [ ] **Step 1: Negativfall — ungültiger Token (nichts darf sich ändern)**

Run:
```bash
cp .env /tmp/env.check
ONBOARD_TOKEN=deadbeef bash ops/add-customer-server.sh --slug testneg --host 100.66.228.71
diff -q .env /tmp/env.check
```
Expected: Skript bricht mit „Cloud-API-Token ungültig" ab, Exit != 0; `diff` meldet **keine** Änderung.

- [ ] **Step 2: Negativfall — nicht erreichbarer SSH-Host**

Run:
```bash
ONBOARD_TOKEN="$(grep '^HCLOUD_TOKEN=' .env | cut -d= -f2)" \
  bash ops/add-customer-server.sh --slug testneg --host 192.0.2.1
diff -q .env /tmp/env.check
```
Expected: gültige API, aber „SSH … fehlgeschlagen", Exit != 0; `.env` unverändert.

- [ ] **Step 3: Idempotenz — bestehenden Slug ablehnen**

Run:
```bash
ONBOARD_TOKEN="$(grep '^HCLOUD_TOKEN_EHMEN=' .env | cut -d= -f2)" \
  bash ops/add-customer-server.sh --slug ehmen --host 167.233.229.83
```
Expected: Vorab-Validierung grün, dann Exit 2 „HCLOUD_TOKEN_EHMEN existiert bereits", `.env` unverändert.

- [ ] **Step 4: Dry-Run — Vorschau ohne Schreiben**

Run:
```bash
ONBOARD_TOKEN="$(grep '^HCLOUD_TOKEN=' .env | cut -d= -f2)" \
  bash ops/add-customer-server.sh --slug demo --host 100.66.228.71 --alias 46.225.53.7 --dry-run
diff -q .env /tmp/env.check
```
Expected: zeigt geplanten `HCLOUD_TOKEN_DEMO` (verborgen) + Monitor-JSON; `.env` unverändert.

- [ ] **Step 5: Ergebnis festhalten**

Wenn alle 4 Fälle wie erwartet → Feature verifiziert. Beobachtungen kurz in der PR-Beschreibung notieren.

---

## Self-Review (durchgeführt)

- **Spec-Abdeckung:** Cloud-API-Account (Tasks 2–4), SSH-Monitor-Eintrag + Alias (Tasks 1–4), Ansatz-A-Validierung (Task 4 + Negativfälle Task 6), gemeinsamer Key (im Skript über gemounteten `hetzner_key`), Slug-ohne-Bindestrich (Task 1), Backup/Idempotenz (Tasks 2–3), Runbook (Task 5). Kein Watchdog/Provisioning — bewusst außen vor.
- **Placeholder-Scan:** keine TBD/TODO; jeder Code-Step enthält lauffähigen Code.
- **Typ-Konsistenz:** `validate_slug`/`build_entry`/`merge_monitor_servers`/`update_env_file`/CLI-Namen über Tasks hinweg identisch verwendet.
