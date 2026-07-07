# Kundenserver-Onboarding ins Monitoring — Design

**Datum:** 2026-07-07
**Status:** Freigegeben (Design)
**Scope:** hetzner-mcp-server (Cloud-API-Account + Docker/Live-Metriken-SSH). Watchdog ist NICHT Teil dieses Vorhabens.

## Ziel

Einen neuen Kundenserver mit einem einzigen, wiederholbaren Schritt vollständig ins
Monitoring des hetzner-mcp-servers aufnehmen — analog zum manuellen TSV-EHMEN-Onboarding
dieser Session, aber automatisiert und mit Vorab-Validierung.

Jedes Onboarding hat genau zwei Integrationspunkte, beide über `.env`:

1. **Hetzner Cloud-API** — pro Kunde ein API-Token als `HCLOUD_TOKEN_<SLUG>`.
   `config.py._load_account_tokens()` erkennt jede `HCLOUD_TOKEN_*`-Variable automatisch
   und legt daraus einen Account `<slug>` an. Kein Code-Change nötig.
2. **Docker/Live-Metriken per SSH** — ein Eintrag in `DOCKER_MONITOR_SERVERS`
   (`{"name","host","aliases","user","port"}`). Matching über `_match_server()`
   (Host, Name oder Alias) in `docker_monitoring.py`.

## Entscheidungen (aus dem Brainstorming)

| Achse | Entscheidung |
|---|---|
| Deliverable | Bash-Skript `ops/add-customer-server.sh` + Runbook `ops/ONBOARDING.md` |
| SSH-Weg | Host **und** optionaler Alias (Public-IP direkt ODER Tailscale-IP + Public-IP-Alias) |
| SSH-Key | Ein gemeinsamer Key (`~/.ssh/hetzner_key`, bereits read-only in den Container gemountet) |
| Scope | Nur hetzner-mcp-server (kein Watchdog) |
| Sicherheitsmodell | **Ansatz A**: erst beide Verbindungen validieren, `.env` nur bei Erfolg ändern |

## Komponenten

### 1. `ops/add-customer-server.sh` (Bash, läuft in Git Bash)

Einzige ausführbare Komponente. Verantwortung: Eingaben sammeln → validieren →
`.env` atomar erweitern → Backend neu erzeugen → live nachprüfen.

**Eingaben** (interaktive Prompts; Flags optional für nicht-interaktive Nutzung):

| Feld | Prompt | Default | Verwendung |
|---|---|---|---|
| Kunden-Slug | ja | — | Account-ID, Monitor-`name` **und** Env-Var-Suffix |
| API-Token | ja, versteckt (`read -s`) | — | `HCLOUD_TOKEN_<SLUG_UPPER>` |
| SSH-Host | ja | — | `DOCKER_MONITOR_SERVERS[].host` |
| Alias | ja (optional) | leer | `DOCKER_MONITOR_SERVERS[].aliases` |
| SSH-User | ja | `root` | `.user` |
| SSH-Port | ja | `22` | `.port` |

**Slug-Regel (wichtig):** Der Slug wird als Bestandteil eines Environment-Variablen-Namens
verwendet, daher nur `[a-z0-9_]` erlaubt — **keine Bindestriche** (deshalb `HCLOUD_TOKEN_EHMEN`,
nicht `…_TSV-EHMEN`). Das Skript schreibt die Variable als `HCLOUD_TOKEN_<SLUG in Großbuchstaben>`;
`config.py` lowercased das Suffix wieder zur Account-ID `<slug>`. Derselbe Slug wird 1:1 als
Monitor-`name` genutzt, damit `?account=<slug>` und der SSH-Match zusammenpassen. Ungültige
Eingaben (z. B. mit Bindestrich) → Abbruch mit Hinweis auf die erlaubten Zeichen.

### 2. `ops/ONBOARDING.md` (Runbook)

Kurze Markdown-Doku: Voraussetzungen, Aufruf des Skripts, manueller Fallback
(die exakten `.env`-Edits von Hand), Troubleshooting.

## Ablauf (Ansatz A — validate-before-write)

```
1. Eingaben sammeln + Format prüfen (Slug-Regex, Token nicht leer)
2. Idempotenz-Check gegen .env:
     - HCLOUD_TOKEN_<SLUG> existiert schon?      -> nachfragen (Update/Abbruch)
     - Monitor-name == <slug> existiert schon?    -> nachfragen (Update/Abbruch)
3. VORAB-VALIDIERUNG (nichts an .env geändert):
     a. Cloud-API: docker exec -e HCLOUD_TOKEN_TMP=<token> backend \
          python -c "hcloud.Client(TMP).servers.get_all()"   -> Token gültig? Server sichtbar?
     b. SSH:       docker exec backend \
          python -c "SSHConnection.execute(host,user,port,'hostname')"  -> rc==0?
     -> Beide grün? weiter. Sonst: Fehlermeldung, .env unangetastet, exit 1.
4. .env schreiben (Backup .env.bak zuerst):
     a. HCLOUD_TOKEN_<SLUG>=<token>  anhängen (falls neu)
     b. DOCKER_MONITOR_SERVERS-JSON per Python laden, Eintrag mergen, zurückschreiben
        {"name":<slug>,"host":<host>,"aliases":[<alias>?],"user":<user>,"port":<port>}
5. Backend neu erzeugen: docker compose up -d --force-recreate backend  (+ Health-Warteschleife)
6. NACH-VALIDIERUNG (live gegen laufende API):
     a. GET /api/accounts                         -> enthält <slug>
     b. GET /api/servers/?account=<slug>          -> listet den Server
     c. GET /api/docker/system-metrics?server=<host>  -> liefert Metriken
     -> grüne Zusammenfassung
```

### Warum Validierung im Backend-Container?

Sowohl der Token- als auch der SSH-Check laufen über `docker exec` in den
`hetzner-mcp-server-backend-1`-Container — also über **exakt denselben Netz-/Key-Pfad**
(gemounteter `hetzner_key`, Tailscale-Routing des Hosts), den die Produktion später nutzt.
Ein grüner Vorab-Check bedeutet damit, dass es auch im Betrieb funktioniert.

## Fehlerbehandlung & Sicherheit

- **Token-Geheimhaltung:** Einlesen per `read -s` (kein Echo), Übergabe an den Check-Container
  nur als Prozess-Env (`-e HCLOUD_TOKEN_TMP=`), landet dauerhaft ausschließlich in `.env`
  (gitignored). Nie in Logs/Ausgabe/`.env.bak`-Diffs sichtbar gemacht.
- **Kein halber Zustand:** Da vor jedem `.env`-Write validiert wird, kann kein kaputter
  Account/Monitor-Eintrag entstehen. `.env.bak` als zusätzliche Absicherung.
- **Backend-Neustart schlägt fehl / Nach-Check rot:** klare Meldung + Pfad zur `.env.bak`,
  Skript exit != 0.
- **Idempotenz:** Erneuter Lauf mit gleichem Slug ändert nichts ungefragt.

## Voraussetzungen (im Runbook dokumentiert)

- Kundenserver hat den **Public-Key zu `hetzner_key`** in `root@…:~/.ssh/authorized_keys`.
- Hetzner-API-Token mit **Read/Write** für das Kundenprojekt.
- SSH-Host ist **vom Monitor-Host aus erreichbar** (bei Tailscale: beide im Tailnet;
  bei Public-IP: Port 22 in UFW offen).
- Docker-Compose-Stack läuft (`hetzner-mcp-server-backend-1` aktiv).

## Bewusst NICHT im Scope (YAGNI)

- Keine Tailscale-Aufnahme des Servers (bleibt manueller Vorab-Schritt).
- Kein Watchdog-Satellit / HTTP-Health-Endpoint (eigenes Vorhaben).
- Kein Hetzner-Server-Provisioning (Server existiert bereits).
- Kein natives UI-/MCP-Tool (bewusst als Skript, nicht als Feature).

## Betroffene / neue Dateien

| Datei | Art |
|---|---|
| `ops/add-customer-server.sh` | neu |
| `ops/ONBOARDING.md` | neu |
| `.env` | zur Laufzeit verändert (gitignored, nicht committet) |

Kein Anwendungs-Code wird geändert — die Mechanik (`HCLOUD_TOKEN_*`-Autodetektion,
`aliases`/`_match_server`) existiert bereits aus den Fixes dieser Session.

## Teststrategie

- **Trockenlauf-Validierung:** Skript gegen den bereits eingebundenen `ehmen`-Slug/-Host
  laufen lassen → Idempotenz-Check muss greifen (nichts ändern).
- **Negativfälle:** ungültiger Token → Schritt 3a rot, `.env` unverändert; nicht erreichbarer
  SSH-Host → Schritt 3b rot, `.env` unverändert.
- **Positivfall:** (bei nächstem echten Kundenserver) vollständiger Durchlauf bis grüner
  Nach-Validierung inkl. Live-Metriken.
