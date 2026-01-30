# Contributing

Vielen Dank für dein Interesse an diesem Projekt!

## Entwicklung

### Setup
```bash
git clone https://github.com/schurick1502/hetzner-mcp-server.git
cd hetzner-mcp-server
python -m venv venv
source venv/bin/activate  # oder venv\Scripts\activate auf Windows
pip install -e ".[dev]"
```

### Projekt-Struktur
```
src/hetzner_mcp/
├── __init__.py
├── server.py          # FastMCP Server & Tool-Registrierung
├── config.py          # Konfiguration & API-Client
└── tools/
    ├── servers.py     # Server-Management
    ├── firewalls.py   # Firewall-Tools
    ├── volumes.py     # Volume-Tools
    ├── networks.py    # Netzwerk-Tools
    └── misc.py        # SSH-Keys, Images, etc.
```

### Neue Tools hinzufügen

1. **Tool-Funktion schreiben** (z.B. in `tools/servers.py`):
```python
async def hcloud_server_backup_enable(identifier: str) -> dict:
    """Aktiviert Backups für einen Server."""
    try:
        client = get_client()
        # ... Implementation
        return {"success": True, "message": "..."}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

2. **Tool in server.py registrieren**:
```python
from .tools.servers import hcloud_server_backup_enable

@mcp.tool()
async def server_backup_enable(identifier: str) -> dict:
    """Aktiviert Backups für einen Server."""
    return await hcloud_server_backup_enable(identifier)
```

3. **Testen**:
```bash
# Server starten
python -m hetzner_mcp.server

# In anderem Terminal: mit Claude testen
```

### Code-Style

- Verwende aussagekräftige Funktions- und Variablennamen
- Docstrings für alle öffentlichen Funktionen
- Type Hints wo möglich
- Einheitliches Error-Handling (try/except mit success/error Dict)

### Error-Handling Pattern

Alle Tools sollten ein einheitliches Response-Format haben:

**Erfolg**:
```python
{
    "success": True,
    "message": "Operation erfolgreich",
    "data": {...}
}
```

**Fehler**:
```python
{
    "success": False,
    "error": "Beschreibung des Fehlers"
}
```

### Destruktive Aktionen

Alle destruktiven Aktionen (delete, rebuild, etc.) müssen:
- `force: bool = False` Parameter haben
- Ohne `force=True` mit Fehler abbrechen
- Bestätigungs-Meldung enthalten

```python
if not force:
    return {
        "success": False,
        "error": "Zum Löschen muss force=True gesetzt werden"
    }
```

### Testing

```bash
# Tests ausführen
pytest

# Mit Coverage
pytest --cov=hetzner_mcp
```

### Pull Requests

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/neue-funktion`)
3. Committe deine Änderungen
4. Push zum Branch
5. Öffne einen Pull Request

**PR-Checklist**:
- [ ] Code folgt dem Projekt-Style
- [ ] Neue Funktionen haben Docstrings
- [ ] Tests sind vorhanden (falls zutreffend)
- [ ] README.md aktualisiert (falls neue Features)
- [ ] WORKFLOWS.md aktualisiert (falls neue Workflows)

## Fehlende Features / TODOs

Hier sind Features die noch implementiert werden könnten:

### Hetzner Cloud API Features
- [ ] Load Balancers (create, delete, add/remove targets)
- [ ] Certificates (SSL/TLS Management)
- [ ] ISO Images (attach/detach custom ISOs)
- [ ] Placement Groups (für Server-Anti-Affinity)
- [ ] Server Actions (enable/disable backup, rescue mode)
- [ ] Floating IP Management (create, assign, unassign)
- [ ] Primary IP Management
- [ ] Server Metrics (CPU, Network, Disk)

### Convenience Features
- [ ] Bulk-Operationen (mehrere Server gleichzeitig)
- [ ] Templates/Presets für häufige Server-Konfigurationen
- [ ] Cost-Estimation vor Server-Erstellung
- [ ] Health-Checks / Status-Dashboard
- [ ] Server-Tags & erweiterte Label-Suche

### Testing & Qualität
- [ ] Unit Tests für alle Tools
- [ ] Integration Tests gegen Test-API
- [ ] Mock-API für Tests ohne echte Ressourcen
- [ ] CI/CD Pipeline (GitHub Actions)

### Dokumentation
- [ ] Video-Tutorial
- [ ] Mehr Workflow-Beispiele
- [ ] API-Referenz-Dokumentation
- [ ] Troubleshooting-Guide

## Fragen?

Öffne ein Issue auf GitHub: https://github.com/schurick1502/hetzner-mcp-server/issues
