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
