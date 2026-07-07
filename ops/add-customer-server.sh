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

if ! printf '%s' "$SLUG" | grep -Eq '^[a-z0-9_]+$'; then
  echo "FEHLER: Slug '$SLUG' ungueltig — nur [a-z0-9_], keine Bindestriche." >&2
  exit 1
fi

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
# ONBOARD_TOKEN ist bereits in der Shell exportiert; "-e ONBOARD_TOKEN" ohne
# "=wert" leitet den Wert nur über die Umgebung weiter (nicht im argv des
# Host-docker-Prozesses sichtbar, z. B. via ps/proc/<pid>/cmdline).
if ! dc exec -T -e ONBOARD_TOKEN backend python -c '
import os, sys
from hcloud import Client
srv = Client(token=os.environ["ONBOARD_TOKEN"]).servers.get_all()
print("   API OK:", len(srv), "Server:", [s.name for s in srv])
' >&2; then
  echo "FEHLER: Cloud-API-Token ungültig oder API nicht erreichbar. .env unverändert." >&2
  exit 1
fi

# 2) SSH-Erreichbarkeit im Backend-Container prüfen (gemounteter hetzner_key)
# HOST/USER_NAME/PORT werden ausschließlich über die Umgebung übergeben und
# im Python-Snippet aus os.environ gelesen — keine Interpolation in den
# Quelltext, damit ein bösartiger --host keinen Code einschleusen kann.
export OH_HOST="$HOST" OH_USER="$USER_NAME" OH_PORT="$PORT"
if ! dc exec -T -e OH_HOST -e OH_USER -e OH_PORT backend python -c '
import os, sys
sys.path.insert(0, "/app")
from app.api.routes.docker_monitoring import SSHConnection
out, err, rc = SSHConnection.execute(os.environ["OH_HOST"], os.environ["OH_USER"], int(os.environ["OH_PORT"]), "hostname")
print("   SSH OK:", out.strip()) if rc == 0 else sys.stderr.write("SSH rc=%s %s\n" % (rc, err))
sys.exit(0 if rc == 0 else 1)
' >&2; then
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
