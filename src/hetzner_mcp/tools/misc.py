"""Hilfsfunktionen für Hetzner Cloud MCP Server."""

from typing import Optional
from ..config import get_client


async def hcloud_ssh_key_list() -> dict:
    """
    Listet alle SSH-Keys im Hetzner Cloud Projekt auf.

    Returns:
        Dictionary mit Anzahl und SSH-Key-Details
    """
    try:
        client = get_client()
        ssh_keys = client.ssh_keys.get_all()

        key_list = []
        for key in ssh_keys:
            key_list.append({
                "id": key.id,
                "name": key.name,
                "fingerprint": key.fingerprint,
                "public_key": key.public_key[:50] + "...",  # Gekürzt für Übersicht
                "created": key.created.isoformat(),
                "labels": key.labels,
            })

        return {
            "success": True,
            "count": len(key_list),
            "ssh_keys": key_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der SSH-Keys: {str(e)}"
        }


async def hcloud_ssh_key_create(name: str, public_key: str, labels: Optional[dict] = None) -> dict:
    """
    Fügt einen neuen SSH-Key hinzu.

    Args:
        name: Name des SSH-Keys
        public_key: Öffentlicher SSH-Key (kompletter Inhalt der .pub Datei)
        labels: Dictionary mit Labels (optional)

    Returns:
        Details des erstellten SSH-Keys
    """
    try:
        client = get_client()

        # SSH-Key erstellen
        ssh_key = client.ssh_keys.create(
            name=name,
            public_key=public_key.strip(),
            labels=labels,
        )

        return {
            "success": True,
            "ssh_key": {
                "id": ssh_key.ssh_key.id,
                "name": ssh_key.ssh_key.name,
                "fingerprint": ssh_key.ssh_key.fingerprint,
            },
            "message": f"SSH-Key '{name}' wurde hinzugefügt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen des SSH-Keys: {str(e)}"
        }


async def hcloud_ssh_key_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht einen SSH-Key (destruktive Aktion!).

    Args:
        identifier: SSH-Key-ID oder Name
        force: Muss True sein zur Bestätigung

    Returns:
        Status der Löschoperation
    """
    if not force:
        return {
            "success": False,
            "error": "Zum Löschen muss force=True gesetzt werden"
        }

    try:
        client = get_client()

        # SSH-Key finden
        try:
            key_id = int(identifier)
            ssh_key = client.ssh_keys.get_by_id(key_id)
        except ValueError:
            ssh_key = client.ssh_keys.get_by_name(identifier)

        if not ssh_key:
            return {
                "success": False,
                "error": f"SSH-Key '{identifier}' nicht gefunden"
            }

        key_name = ssh_key.name
        key_id = ssh_key.id

        # SSH-Key löschen
        client.ssh_keys.delete(ssh_key)

        return {
            "success": True,
            "message": f"SSH-Key '{key_name}' (ID: {key_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen des SSH-Keys: {str(e)}"
        }


async def hcloud_image_list(image_type: Optional[str] = None) -> dict:
    """
    Listet verfügbare Images auf.

    Args:
        image_type: Filter nach Typ: "system" (offizielle OS-Images),
                   "snapshot" (Server-Snapshots), "backup" (Server-Backups),
                   "app" (One-Click-Apps), None für alle

    Returns:
        Dictionary mit Anzahl und Image-Details
    """
    try:
        client = get_client()

        if image_type:
            images = client.images.get_all(type=image_type)
        else:
            images = client.images.get_all()

        image_list = []
        for img in images:
            image_list.append({
                "id": img.id,
                "name": img.name,
                "description": img.description,
                "type": img.type,
                "os_flavor": img.os_flavor,
                "os_version": img.os_version,
                "architecture": img.architecture,
                "disk_size": img.disk_size,
                "created": img.created.isoformat() if img.created else None,
                "deprecated": img.deprecated.isoformat() if img.deprecated else None,
            })

        return {
            "success": True,
            "count": len(image_list),
            "images": image_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Images: {str(e)}"
        }


async def hcloud_server_type_list() -> dict:
    """
    Listet alle verfügbaren Server-Typen mit Spezifikationen und Preisen auf.

    Returns:
        Dictionary mit Anzahl und Server-Typ-Details
    """
    try:
        client = get_client()
        server_types = client.server_types.get_all()

        type_list = []
        for st in server_types:
            type_list.append({
                "id": st.id,
                "name": st.name,
                "description": st.description,
                "cores": st.cores,
                "memory": st.memory,
                "disk": st.disk,
                "storage_type": st.storage_type,
                "cpu_type": st.cpu_type,
                "architecture": st.architecture,
                "prices": {
                    "hourly_gross": st.prices[0].price_hourly.gross if st.prices else None,
                    "monthly_gross": st.prices[0].price_monthly.gross if st.prices else None,
                },
                "included_traffic": st.included_traffic,
            })

        return {
            "success": True,
            "count": len(type_list),
            "server_types": type_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Server-Typen: {str(e)}"
        }


async def hcloud_location_list() -> dict:
    """
    Listet alle verfügbaren Standorte (Locations) auf.

    Returns:
        Dictionary mit Anzahl und Standort-Details
    """
    try:
        client = get_client()
        locations = client.locations.get_all()

        location_list = []
        for loc in locations:
            location_list.append({
                "id": loc.id,
                "name": loc.name,
                "description": loc.description,
                "country": loc.country,
                "city": loc.city,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "network_zone": loc.network_zone,
            })

        return {
            "success": True,
            "count": len(location_list),
            "locations": location_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Locations: {str(e)}"
        }


async def hcloud_datacenter_list() -> dict:
    """
    Listet alle verfügbaren Rechenzentren auf.

    Returns:
        Dictionary mit Anzahl und Rechenzentrum-Details
    """
    try:
        client = get_client()
        datacenters = client.datacenters.get_all()

        dc_list = []
        for dc in datacenters:
            dc_list.append({
                "id": dc.id,
                "name": dc.name,
                "description": dc.description,
                "location": {
                    "name": dc.location.name,
                    "city": dc.location.city,
                    "country": dc.location.country,
                },
                "network_zones": dc.network_zones,
                "supported_types": [st.name for st in dc.server_types.supported],
            })

        return {
            "success": True,
            "count": len(dc_list),
            "datacenters": dc_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Datacenter: {str(e)}"
        }


async def hcloud_floating_ip_list() -> dict:
    """
    Listet alle Floating IPs im Projekt auf.

    Returns:
        Dictionary mit Anzahl und Floating IP-Details
    """
    try:
        client = get_client()
        floating_ips = client.floating_ips.get_all()

        ip_list = []
        for fip in floating_ips:
            ip_list.append({
                "id": fip.id,
                "name": fip.name,
                "ip": fip.ip,
                "type": fip.type,
                "server": fip.server.name if fip.server else None,
                "location": fip.home_location.name if fip.home_location else None,
                "blocked": fip.blocked,
                "dns_ptr": [{"ip": ptr["ip"], "dns_ptr": ptr["dns_ptr"]} for ptr in fip.dns_ptr],
                "created": fip.created.isoformat(),
                "labels": fip.labels,
            })

        return {
            "success": True,
            "count": len(ip_list),
            "floating_ips": ip_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Floating IPs: {str(e)}"
        }


async def hcloud_primary_ip_list() -> dict:
    """
    Listet alle Primary IPs im Projekt auf.

    Returns:
        Dictionary mit Anzahl und Primary IP-Details
    """
    try:
        client = get_client()
        primary_ips = client.primary_ips.get_all()

        ip_list = []
        for pip in primary_ips:
            ip_list.append({
                "id": pip.id,
                "name": pip.name,
                "ip": pip.ip,
                "type": pip.type,
                "assignee_id": pip.assignee_id,
                "assignee_type": pip.assignee_type,
                "datacenter": pip.datacenter.name if pip.datacenter else None,
                "blocked": pip.blocked,
                "auto_delete": pip.auto_delete,
                "created": pip.created.isoformat(),
                "labels": pip.labels,
            })

        return {
            "success": True,
            "count": len(ip_list),
            "primary_ips": ip_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Primary IPs: {str(e)}"
        }
