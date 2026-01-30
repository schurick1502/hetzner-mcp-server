# Hetzner Cloud MCP - Beispiel-Workflows

Dieses Dokument zeigt häufige Workflows und wie du Claude mit dem MCP Server nutzen kannst.

## Workflow 1: Einfachen Webserver erstellen

**Ziel**: Ubuntu Server mit Nginx, inkl. Firewall-Konfiguration

**Claude-Prompt**:
```
Erstelle einen Ubuntu 24.04 Server "web-01" in Falkenstein mit:
- Server-Typ: cx22
- Firewall mit HTTP (80), HTTPS (443) und SSH (22) von überall
- Meinen SSH-Key "laptop-key" verwenden
```

**Was passiert**:
1. Claude prüft verfügbare SSH-Keys (`ssh_key_list`)
2. Erstellt eine Firewall mit entsprechenden Regeln (`firewall_create`)
3. Erstellt den Server mit Firewall (`server_create`)
4. Gibt dir die IP-Adresse und Zugangsdaten

## Workflow 2: Server mit privatem Netzwerk

**Ziel**: Mehrere Server in einem privaten Netzwerk verbinden

**Claude-Prompt**:
```
Richte ein privates Netzwerk ein:
1. Netzwerk "app-network" mit IP-Bereich 10.0.0.0/16
2. Subnet 10.0.1.0/24 in eu-central
3. Erstelle zwei Server "app-01" und "app-02"
4. Verbinde beide mit dem Netzwerk
```

**Was passiert**:
1. Netzwerk wird erstellt (`network_create`)
2. Subnet wird hinzugefügt (`network_add_subnet`)
3. Server werden erstellt (`server_create`)
4. Server werden mit Netzwerk verbunden (`server_attach_network`)

## Workflow 3: Backup-Volume einrichten

**Ziel**: Zusätzlichen Speicher für Backups

**Claude-Prompt**:
```
Erstelle ein 100GB Volume "backup-vol" in Falkenstein und hänge es an Server "web-01"
```

**Was passiert**:
1. Volume wird erstellt (`volume_create`)
2. Volume wird an Server angehängt (`volume_attach`)
3. Du bekommst den Linux-Gerätepfad (z.B. /dev/disk/by-id/scsi-0HC_Volume_12345)

**Nächste Schritte** (manuell auf dem Server):
```bash
# Volume formatieren (falls nicht automatisch)
mkfs.ext4 /dev/disk/by-id/scsi-0HC_Volume_12345

# Mountpoint erstellen und mounten
mkdir /mnt/backup
mount /dev/disk/by-id/scsi-0HC_Volume_12345 /mnt/backup

# Permanent in /etc/fstab eintragen
echo "/dev/disk/by-id/scsi-0HC_Volume_12345 /mnt/backup ext4 discard,nofail,defaults 0 0" >> /etc/fstab
```

## Workflow 4: Load Balancer Setup

**Ziel**: Mehrere Webserver hinter einem Load Balancer

**Claude-Prompt**:
```
Erstelle eine Load-Balancer-Infrastruktur:
1. Privates Netzwerk "lb-network" (10.0.0.0/16)
2. Drei Ubuntu-Server "web-01", "web-02", "web-03" im Netzwerk
3. Firewall die nur HTTP/HTTPS von außen und alles im privaten Netz erlaubt
```

**Was passiert**:
1. Privates Netzwerk wird erstellt
2. Server werden im Netzwerk erstellt
3. Firewall wird konfiguriert und angewendet

**Hinweis**: Load Balancer selbst muss über Hetzner Console erstellt werden (noch nicht im MCP)

## Workflow 5: Development Environment

**Ziel**: Schnelle Dev-Umgebung für Tests

**Claude-Prompt**:
```
Erstelle einen günstigen Server für Development:
- Name: dev-playground
- Kleinster Server-Typ
- Ubuntu 24.04
- Location: Nürnberg
- Mein SSH-Key
- Cloud-init Script zum Installieren von Docker
```

**Cloud-init Script Beispiel**:
```yaml
#cloud-config
package_update: true
packages:
  - docker.io
  - docker-compose
  - git
  - vim
runcmd:
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker ubuntu
```

## Workflow 6: Server-Migration

**Ziel**: Server auf neuere OS-Version upgraden

**Claude-Prompt**:
```
Ich möchte Server "app-01" von Ubuntu 22.04 auf 24.04 upgraden.
Erstelle einen Snapshot zuerst, dann rebuild mit ubuntu-24.04
```

**Vorsicht**: Rebuild löscht alle Daten! Besser:
1. Volume für Daten verwenden (`volume_create` + `volume_attach`)
2. Volume vor Rebuild trennen (`volume_detach`)
3. Server rebuilden (`server_rebuild`)
4. Volume wieder anhängen (`volume_attach`)

## Workflow 7: Firewall nachträglich anpassen

**Claude-Prompt**:
```
Füge zur Firewall "web-fw" folgende Regeln hinzu:
- PostgreSQL Port 5432 von 10.0.0.0/16
- Custom App Port 8080 von überall
```

**Was passiert**:
1. Regeln werden zur Firewall hinzugefügt (`firewall_add_rule`)
2. Änderungen werden automatisch auf alle Server mit dieser Firewall angewendet

## Workflow 8: Kostenoptimierung

**Claude-Prompt**:
```
Zeige mir alle Server-Typen und ihre Preise. Ich suche einen Server mit mindestens 4 Cores und 8GB RAM.
```

**Was passiert**:
1. Server-Typen werden aufgelistet (`server_type_list`)
2. Claude filtert nach deinen Anforderungen
3. Zeigt Preis-Leistungs-Vergleich

## Workflow 9: Monitoring-Setup vorbereiten

**Claude-Prompt**:
```
Ich möchte einen Monitoring-Server aufsetzen:
1. Server "monitor-01" in Helsinki
2. Volume 50GB für Metriken
3. Firewall: SSH, Grafana (3000), Prometheus (9090)
4. In privatem Netzwerk mit meinen anderen Servern
```

## Workflow 10: Cleanup / Aufräumen

**Claude-Prompt**:
```
Zeige mir alle meine Ressourcen:
- Server
- Volumes
- Firewalls
- Netzwerke

Ich möchte alles löschen was "test-" im Namen hat.
```

**Was passiert**:
1. Alle Ressourcen werden aufgelistet
2. Claude identifiziert Test-Ressourcen
3. Fragt vor dem Löschen nach Bestätigung
4. Löscht Ressourcen in korrekter Reihenfolge

**Wichtig**: Immer `force=True` für delete-Operationen!

## Best Practices

### Sicherheit
- Immer SSH-Keys verwenden, nie Root-Passwörter
- Firewalls restriktiv konfigurieren
- Regelmäßig Snapshots erstellen
- Sensible Daten in Volumes, nicht auf Root-Disk

### Kosten
- Server ausschalten wenn nicht gebraucht (`server_power` mit action="stop")
- Alte Snapshots löschen
- Ungenutzte Floating IPs freigeben

### Namenskonventionen
- Umgebung als Präfix: `prod-web-01`, `dev-db-01`
- Location im Namen: `web-fsn-01`, `web-nbg-01`
- Funktion klar benennen: `postgres-master`, `redis-cache`

### Labels verwenden
Nutze Labels für bessere Organisation:
```python
labels = {
    "environment": "production",
    "project": "webshop",
    "managed-by": "claude-mcp"
}
```

## Hilfreiche Kommandos

### Alle Ressourcen übersichtlich
```
Zeige mir eine Übersicht aller meiner Hetzner-Ressourcen mit Kosten
```

### Verfügbarkeits-Check
```
Sind in Location Falkenstein Server-Typ cx32 verfügbar?
```

### Image-Suche
```
Welche Rocky Linux Images sind verfügbar?
```

### IP-Adressen finden
```
Was sind die IPs meiner Server?
```
