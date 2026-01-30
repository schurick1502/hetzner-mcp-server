# Hetzner Cloud MCP Server

Ein Model Context Protocol (MCP) Server für die Hetzner Cloud API. Ermöglicht Claude die direkte Verwaltung von Hetzner Cloud Ressourcen.

## Features

- **Server-Management**: Erstellen, löschen, starten, stoppen, rebuilden
- **Firewall-Management**: Firewalls erstellen und konfigurieren
- **Volume-Management**: Volumes erstellen und an Server anhängen
- **Netzwerk-Management**: Private Netzwerke und Subnets verwalten
- **Hilfsfunktionen**: SSH-Keys, Images, Locations, Datacenter

## Installation

### Voraussetzungen

- Python 3.10 oder höher
- Hetzner Cloud Account mit API-Token

### Setup

1. **Repository klonen:**
   ```bash
   git clone https://github.com/schurick1502/hetzner-mcp-server.git
   cd hetzner-mcp-server
   ```

2. **Virtual Environment erstellen:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oder
   venv\Scripts\activate  # Windows
   ```

3. **Dependencies installieren:**
   ```bash
   pip install -e .
   ```

4. **API-Token konfigurieren:**
   ```bash
   cp .env.example .env
   # Bearbeite .env und füge deinen HCLOUD_TOKEN ein
   ```

## Konfiguration für Claude Desktop

Füge folgendes zu deiner Claude Desktop Config hinzu (`%APPDATA%\Claude\claude_desktop_config.json` auf Windows):

```json
{
  "mcpServers": {
    "hetzner": {
      "command": "C:\\projekte\\hetzner-mcp-server\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "hetzner_mcp.server"
      ],
      "env": {
        "HCLOUD_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

## Konfiguration für Claude Code

Füge folgendes zu `~/.claude/mcp_settings.json` hinzu:

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

## Verfügbare Tools

### Server-Management
- `hcloud_server_list` - Alle Server auflisten
- `hcloud_server_info` - Details zu einem Server
- `hcloud_server_create` - Neuen Server erstellen
- `hcloud_server_delete` - Server löschen (benötigt force=True)
- `hcloud_server_power` - Server starten/stoppen/neustarten
- `hcloud_server_rebuild` - Server mit neuem Image rebuilden

### Firewall-Management
- `hcloud_firewall_list` - Alle Firewalls auflisten
- `hcloud_firewall_create` - Neue Firewall erstellen
- `hcloud_firewall_delete` - Firewall löschen
- `hcloud_firewall_add_rule` - Regel hinzufügen
- `hcloud_firewall_apply` - Firewall auf Server anwenden

### Volume-Management
- `hcloud_volume_list` - Alle Volumes auflisten
- `hcloud_volume_create` - Volume erstellen
- `hcloud_volume_delete` - Volume löschen
- `hcloud_volume_attach` - Volume an Server anhängen
- `hcloud_volume_detach` - Volume von Server trennen

### Netzwerk-Management
- `hcloud_network_list` - Private Netzwerke auflisten
- `hcloud_network_create` - Netzwerk erstellen
- `hcloud_network_delete` - Netzwerk löschen
- `hcloud_network_add_subnet` - Subnet hinzufügen
- `hcloud_server_attach_network` - Server ins Netzwerk einbinden

### Hilfsfunktionen
- `hcloud_ssh_key_list` - SSH-Keys auflisten
- `hcloud_ssh_key_create` - SSH-Key hinzufügen
- `hcloud_ssh_key_delete` - SSH-Key löschen
- `hcloud_image_list` - Verfügbare Images
- `hcloud_server_type_list` - Verfügbare Server-Typen mit Preisen
- `hcloud_location_list` - Verfügbare Locations
- `hcloud_datacenter_list` - Verfügbare Datacenter

## Beispiel-Workflows

### Einfachen Webserver erstellen

```
Erstelle einen Ubuntu Server mit dem Namen "web-01" in Falkenstein mit Firewall für HTTP/HTTPS
```

Claude wird dann:
1. SSH-Keys auflisten (falls vorhanden)
2. Eine Firewall mit HTTP/HTTPS Regeln erstellen
3. Den Server erstellen und die Firewall anwenden
4. Die IP-Adresse und Zugangsdaten zurückgeben

### Backup-Volume erstellen und anhängen

```
Erstelle ein 100GB Volume "backup-vol" in Falkenstein und hänge es an Server "web-01"
```

## Sicherheitshinweise

- **API-Token schützen**: Niemals in Git committen oder teilen
- **Destruktive Aktionen**: Alle delete-Operationen benötigen `force=True` zur Bestätigung
- **Firewalls**: Standardmäßig blockieren Firewalls allen Traffic - explizite Regeln erforderlich

## Entwicklung

### Tests ausführen

```bash
pip install -e ".[dev]"
pytest
```

### Debugging

Starte den Server mit Debug-Output:
```bash
python -m hetzner_mcp.server --debug
```

## Lizenz

MIT

## Support

Bei Problemen oder Fragen öffne ein Issue auf GitHub:
https://github.com/schurick1502/hetzner-mcp-server/issues
