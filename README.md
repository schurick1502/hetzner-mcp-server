# Hetzner Cloud MCP Server

Ein vollständiger Model Context Protocol (MCP) Server für die Hetzner Cloud API mit **98 Tools** und moderner **Web-UI**.

🚀 **NEU:** Production-Ready Web-Interface mit FastAPI + React!

## ✨ Features

### MCP Server (Claude Integration)
- **98 MCP-Tools** - Vollständige Hetzner Cloud API Abdeckung
- **Server-Management**: Erstellen, löschen, starten, stoppen, rebuilden, resize, backups, rescue-mode, snapshots, metrics
- **Load Balancer**: Erstellen, konfigurieren, services, targets, health-checks
- **Firewall-Management**: Erstellen, regeln hinzufügen, auf Server anwenden
- **Volume-Management**: Erstellen, anhängen, trennen, vergrößern, protection
- **Network-Management**: Private Netzwerke, Subnets, Routes verwalten
- **Certificates**: SSL/TLS Management (Upload & Let's Encrypt Managed)
- **Floating IPs & Primary IPs**: Erstellen, zuweisen, DNS konfigurieren
- **Images & SSH-Keys**: Verwalten und aktualisieren
- **ISOs & Placement Groups**: Für erweiterte Setups
- **Actions**: Status-Tracking von API-Operationen

### 🎨 Web-UI (NEU!)
- **Modern Dashboard** - Übersicht aller Ressourcen
- **Server-Management** - Start/Stop/Reboot mit Buttons
- **Firewall-Verwaltung** - Visuelle Übersicht
- **Volume-Management** - Attach/Detach
- **Network-Übersicht** - Private Netzwerke
- **Responsive Design** - Desktop & Mobile
- **FastAPI Backend** - Auto-generierte API Docs
- **React Frontend** - TypeScript + Tailwind CSS
- **Docker-basiert** - Einfaches Deployment

## 📊 Statistik

- **98 MCP-Tools** (100% Hetzner Cloud API Abdeckung)
- **2 Deployment-Optionen**: MCP Server + Web-UI
- **Production-Ready** mit Docker
- **Type-Safe** TypeScript & Pydantic

## 🚀 Schnellstart

### Option 1: Web-UI (Empfohlen für Einsteiger)

```bash
# 1. Repository klonen
git clone https://github.com/schurick1502/hetzner-mcp-server.git
cd hetzner-mcp-server

# 2. Environment konfigurieren
cp web/.env.example web/.env
# Bearbeite web/.env und füge deinen HCLOUD_TOKEN ein

# 3. Docker Compose starten
docker-compose up -d

# 4. Öffne im Browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/api/docs
```

**Fertig!** Du hast jetzt eine vollständige Web-UI für Hetzner Cloud Management.

Siehe [Web-UI Dokumentation](web/README.md) für Details.

### Option 2: MCP Server (für Claude Integration)

#### Voraussetzungen
- Python 3.10 oder höher
- Hetzner Cloud Account mit API-Token

#### Installation

```bash
# Repository klonen
git clone https://github.com/schurick1502/hetzner-mcp-server.git
cd hetzner-mcp-server

# Virtual Environment erstellen
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Dependencies installieren
pip install -e .

# API-Token konfigurieren
cp .env.example .env
# Bearbeite .env und füge deinen HCLOUD_TOKEN ein
```

#### Konfiguration für Claude Desktop

Füge zu `%APPDATA%\Claude\claude_desktop_config.json` (Windows) hinzu:

```json
{
  "mcpServers": {
    "hetzner": {
      "command": "C:\\projekte\\hetzner-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "hetzner_mcp.server"],
      "env": {
        "HCLOUD_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

#### Konfiguration für Claude Code

Füge zu `~/.claude/mcp_settings.json` hinzu:

```json
{
  "mcpServers": {
    "hetzner": {
      "command": "python",
      "args": ["-m", "hetzner_mcp.server"],
      "env": {
        "HCLOUD_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

## 📚 Verfügbare Tools

### Server-Management (18 Tools)
- `server_list` - Alle Server auflisten
- `server_info` - Details zu einem Server
- `server_create` - Neuen Server erstellen
- `server_delete` - Server löschen (benötigt force=True)
- `server_power` - Server starten/stoppen/neustarten
- `server_rebuild` - Server mit neuem Image rebuilden
- `server_enable_backup` / `server_disable_backup` - Backups verwalten
- `server_enable_rescue` / `server_disable_rescue` - Rescue-Modus
- `server_create_image` - Snapshot/Backup erstellen
- `server_attach_iso` / `server_detach_iso` - ISO-Images
- `server_change_type` - Server-Typ ändern (Resize)
- `server_request_console` - VNC-Konsole anfordern
- `server_reset_password` - Root-Passwort zurücksetzen
- `server_change_dns_ptr` - Reverse DNS
- `server_change_protection` - Schutz-Einstellungen
- `server_update` - Metadaten aktualisieren
- `server_get_metrics` - CPU/Network/Disk Metriken

### Load Balancer-Management (9 Tools)
- `load_balancer_list` - Alle Load Balancer
- `load_balancer_create` - Load Balancer erstellen
- `load_balancer_delete` - Load Balancer löschen
- `load_balancer_add_service` - Service hinzufügen
- `load_balancer_delete_service` - Service entfernen
- `load_balancer_add_target` - Target hinzufügen
- `load_balancer_remove_target` - Target entfernen
- `load_balancer_change_algorithm` - Algorithmus ändern
- `load_balancer_update` - Metadaten aktualisieren

### Firewall-Management (8 Tools)
- `firewall_list` - Alle Firewalls auflisten
- `firewall_create` - Neue Firewall erstellen
- `firewall_delete` - Firewall löschen
- `firewall_add_rule` - Regel hinzufügen
- `firewall_set_rules` - Alle Regeln setzen (überschreibt!)
- `firewall_apply` - Firewall auf Server anwenden
- `firewall_remove_from_server` - Firewall von Server entfernen
- `firewall_update` - Metadaten aktualisieren

### Volume-Management (8 Tools)
- `volume_list` - Alle Volumes
- `volume_create` - Volume erstellen
- `volume_delete` - Volume löschen
- `volume_attach` - Volume an Server anhängen
- `volume_detach` - Volume von Server trennen
- `volume_resize` - Volume vergrößern
- `volume_change_protection` - Schutz-Einstellungen
- `volume_update` - Metadaten aktualisieren

### Network-Management (12 Tools)
- `network_list` - Private Netzwerke auflisten
- `network_create` - Netzwerk erstellen
- `network_delete` - Netzwerk löschen
- `network_add_subnet` - Subnet hinzufügen
- `network_delete_subnet` - Subnet entfernen
- `network_add_route` - Route hinzufügen
- `network_delete_route` - Route entfernen
- `network_change_ip_range` - IP-Bereich ändern
- `network_change_protection` - Schutz-Einstellungen
- `network_update` - Metadaten aktualisieren
- `server_attach_network` - Server mit Netzwerk verbinden
- `server_detach_network` - Server von Netzwerk trennen

### Certificate-Management (6 Tools)
- `certificate_list` - Alle Certificates
- `certificate_create` - Certificate hochladen
- `certificate_create_managed` - Managed Certificate (Let's Encrypt)
- `certificate_delete` - Certificate löschen
- `certificate_update` - Metadaten aktualisieren
- `certificate_retry_issuance` - Ausstellung erneut versuchen

### Floating IP-Management (8 Tools)
- `floating_ip_list` - Alle Floating IPs
- `floating_ip_create` - Floating IP erstellen
- `floating_ip_delete` - Floating IP löschen
- `floating_ip_assign` - Floating IP zuweisen
- `floating_ip_unassign` - Zuweisung entfernen
- `floating_ip_change_dns_ptr` - Reverse DNS
- `floating_ip_change_protection` - Schutz-Einstellungen
- `floating_ip_update` - Metadaten aktualisieren

### Primary IP-Management (8 Tools)
- `primary_ip_list` - Alle Primary IPs
- `primary_ip_create` - Primary IP erstellen
- `primary_ip_delete` - Primary IP löschen
- `primary_ip_assign` - Primary IP zuweisen
- `primary_ip_unassign` - Zuweisung entfernen
- `primary_ip_change_dns_ptr` - Reverse DNS
- `primary_ip_change_protection` - Schutz-Einstellungen
- `primary_ip_update` - Metadaten aktualisieren

### Image-Management (4 Tools)
- `image_list` - Verfügbare Images
- `image_update` - Image aktualisieren
- `image_delete` - Image löschen
- `image_change_protection` - Schutz-Einstellungen

### SSH Key-Management (4 Tools)
- `ssh_key_list` - SSH-Keys auflisten
- `ssh_key_create` - SSH-Key hinzufügen
- `ssh_key_delete` - SSH-Key löschen
- `ssh_key_update` - SSH-Key aktualisieren

### Placement Group-Management (4 Tools)
- `placement_group_list` - Placement Groups auflisten
- `placement_group_create` - Placement Group erstellen
- `placement_group_delete` - Placement Group löschen
- `placement_group_update` - Placement Group aktualisieren

### ISO-Management (2 Tools)
- `iso_list` - Verfügbare ISOs
- `iso_get` - ISO-Details

### Hilfsfunktionen (5 Tools)
- `server_type_list` - Verfügbare Server-Typen mit Preisen
- `location_list` - Verfügbare Locations
- `datacenter_list` - Verfügbare Datacenter
- `action_get` - Details zu einer Action
- `action_list` - Alle Actions

## 🎯 Beispiel-Workflows

### Web-UI: Server mit einem Klick starten/stoppen

```
1. Öffne http://localhost:5173
2. Gehe zu "Servers"
3. Klicke auf Play/Stop Button beim Server
4. Fertig!
```

### MCP: Einfachen Webserver mit Claude erstellen

```
Erstelle einen Ubuntu Server mit dem Namen "web-01" in Falkenstein mit Firewall für HTTP/HTTPS
```

Claude wird dann:
1. SSH-Keys auflisten (falls vorhanden)
2. Eine Firewall mit HTTP/HTTPS Regeln erstellen
3. Den Server erstellen und die Firewall anwenden
4. Die IP-Adresse und Zugangsdaten zurückgeben

### MCP: Backup-Volume erstellen und anhängen

```
Erstelle ein 100GB Volume "backup-vol" in Falkenstein und hänge es an Server "web-01"
```

## 🏗️ Architektur

### MCP Server
```
Claude Desktop/Code
        ↓
   MCP Protocol
        ↓
hetzner_mcp.server
        ↓
  hcloud Library
        ↓
 Hetzner Cloud API
```

### Web-UI
```
Browser (React)
        ↓
     Nginx
        ↓
 FastAPI Backend
        ↓
hetzner_mcp.tools
        ↓
  hcloud Library
        ↓
 Hetzner Cloud API
```

## 📁 Projekt-Struktur

```
hetzner-mcp-server/
├── src/hetzner_mcp/          # MCP Server
│   ├── server.py              # FastMCP Server (98 Tools)
│   ├── config.py              # Konfiguration
│   └── tools/                 # Tool-Implementierungen
│       ├── servers.py
│       ├── load_balancers.py
│       ├── firewalls.py
│       ├── volumes.py
│       ├── networks.py
│       ├── certificates.py
│       ├── isos.py
│       ├── placement_groups.py
│       └── misc.py
│
├── web/                       # Web-UI (NEU!)
│   ├── backend/               # FastAPI Backend
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py
│   │       └── api/routes/
│   └── frontend/              # React Frontend
│       ├── Dockerfile
│       ├── nginx.conf
│       └── src/
│           ├── App.tsx
│           ├── pages/
│           └── services/
│
├── docker-compose.yml         # Development
├── docker-compose.prod.yml    # Production
├── pyproject.toml
└── README.md
```

## 🐳 Docker Commands

```bash
# Development starten
docker-compose up -d

# Production starten
docker-compose -f docker-compose.prod.yml up -d

# Logs anzeigen
docker-compose logs -f

# Stoppen
docker-compose down

# Neu builden
docker-compose build
```

## 🔒 Sicherheitshinweise

- **API-Token schützen**: Niemals in Git committen oder teilen
- **Destruktive Aktionen**: Alle delete-Operationen benötigen `force=True` zur Bestätigung
- **Firewalls**: Standardmäßig blockieren Firewalls allen Traffic - explizite Regeln erforderlich
- **Web-UI**: Nutze HTTPS in Production und sichere Passwörter

## 🛠️ Entwicklung

### MCP Server entwickeln
```bash
pip install -e ".[dev]"
pytest
```

### Web-UI entwickeln
```bash
cd web/backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# In anderem Terminal
cd web/frontend
npm install
npm run dev
```

Siehe [Web-UI README](web/README.md) für Details.

## 📖 Dokumentation

- **MCP Tools**: Siehe Tool-Beschreibungen in `src/hetzner_mcp/tools/`
- **Web-UI**: [web/README.md](web/README.md)
- **API Docs**: http://localhost:8000/api/docs (wenn Backend läuft)
- **Workflows**: [WORKFLOWS.md](WORKFLOWS.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

## 🌟 Highlights

- ✅ **Vollständigste Hetzner Cloud MCP Implementation** (98 Tools!)
- ✅ **Production-Ready Web-UI** mit FastAPI + React
- ✅ **Docker-basiert** für einfaches Deployment
- ✅ **Type-Safe** mit TypeScript & Pydantic
- ✅ **Auto-Dokumentation** mit Swagger UI
- ✅ **Deutsche Dokumentation**
- ✅ **MIT License**

## 🆕 Updates

### Version 2.0 (Aktuell)
- ➕ Web-UI mit FastAPI + React + Docker
- ➕ 98 MCP-Tools (von 33 auf 98 erweitert)
- ➕ Load Balancer, Certificates, ISOs, Placement Groups
- ➕ Vollständige IP-Verwaltung (Floating & Primary)
- ➕ Server Metrics, Rescue-Mode, Snapshots
- ➕ Protection Settings für alle Ressourcen

### Version 1.0
- ✅ Initial Release mit 33 MCP-Tools
- ✅ Basic Server/Firewall/Volume/Network Management

## 🤝 Contributing

Contributions sind willkommen! Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 Lizenz

MIT License - Siehe [LICENSE](LICENSE)

## 🔗 Links

- **Repository**: https://github.com/schurick1502/hetzner-mcp-server
- **Issues**: https://github.com/schurick1502/hetzner-mcp-server/issues
- **Hetzner Cloud API**: https://docs.hetzner.cloud
- **FastMCP**: https://github.com/jlowin/fastmcp
- **hcloud-python**: https://github.com/hetznercloud/hcloud-python

## 💬 Support

Bei Fragen oder Problemen:
1. Prüfe die [Dokumentation](web/README.md)
2. Schaue in die [Issues](https://github.com/schurick1502/hetzner-mcp-server/issues)
3. Öffne ein neues Issue

---

**Gebaut mit ❤️ für die Hetzner Cloud Community**

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
