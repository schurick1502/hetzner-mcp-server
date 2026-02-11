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
                    "hourly_gross": st.prices[0]["price_hourly"]["gross"] if st.prices else None,
                    "monthly_gross": st.prices[0]["price_monthly"]["gross"] if st.prices else None,
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


# ===== FLOATING IP ERWEITERTE FUNKTIONEN =====

async def hcloud_floating_ip_create(
    floating_type: str,
    location: Optional[str] = None,
    home_location: Optional[str] = None,
    server: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[dict] = None,
    name: Optional[str] = None,
) -> dict:
    """
    Erstellt eine neue Floating IP.

    Args:
        floating_type: ipv4 oder ipv6
        location: Location-Name (optional)
        home_location: Home-Location-Name (optional)
        server: Server-ID oder Name zum sofortigen Zuweisen (optional)
        description: Beschreibung (optional)
        labels: Labels (optional)
        name: Name (optional)

    Returns:
        Details der erstellten Floating IP
    """
    try:
        client = get_client()

        loc = None
        if location:
            loc = client.locations.get_by_name(location)
            if not loc:
                return {"success": False, "error": f"Location '{location}' nicht gefunden"}

        home_loc = None
        if home_location:
            home_loc = client.locations.get_by_name(home_location)
            if not home_loc:
                return {"success": False, "error": f"Home-Location '{home_location}' nicht gefunden"}

        server_obj = None
        if server:
            try:
                server_id = int(server)
                server_obj = client.servers.get_by_id(server_id)
            except ValueError:
                server_obj = client.servers.get_by_name(server)

            if not server_obj:
                return {"success": False, "error": f"Server '{server}' nicht gefunden"}

        response = client.floating_ips.create(
            type=floating_type,
            location=loc,
            home_location=home_loc,
            server=server_obj,
            description=description,
            labels=labels,
            name=name,
        )

        fip = response.floating_ip

        return {
            "success": True,
            "floating_ip": {
                "id": fip.id,
                "name": fip.name,
                "ip": fip.ip,
                "type": fip.type,
                "location": fip.home_location.name if fip.home_location else None,
            },
            "message": f"Floating IP '{fip.ip}' erstellt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen der Floating IP: {str(e)}"
        }


async def hcloud_floating_ip_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht eine Floating IP.

    Args:
        identifier: Floating IP-ID oder Name
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

        try:
            fip_id = int(identifier)
            fip = client.floating_ips.get_by_id(fip_id)
        except ValueError:
            fip = client.floating_ips.get_by_name(identifier)

        if not fip:
            return {
                "success": False,
                "error": f"Floating IP '{identifier}' nicht gefunden"
            }

        fip_ip = fip.ip
        fip_id = fip.id

        client.floating_ips.delete(fip)

        return {
            "success": True,
            "message": f"Floating IP '{fip_ip}' (ID: {fip_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen der Floating IP: {str(e)}"
        }


async def hcloud_floating_ip_assign(identifier: str, server: str) -> dict:
    """
    Weist eine Floating IP einem Server zu.

    Args:
        identifier: Floating IP-ID oder Name
        server: Server-ID oder Name

    Returns:
        Status der Zuweisung
    """
    try:
        client = get_client()

        try:
            fip_id = int(identifier)
            fip = client.floating_ips.get_by_id(fip_id)
        except ValueError:
            fip = client.floating_ips.get_by_name(identifier)

        if not fip:
            return {
                "success": False,
                "error": f"Floating IP '{identifier}' nicht gefunden"
            }

        try:
            server_id = int(server)
            server_obj = client.servers.get_by_id(server_id)
        except ValueError:
            server_obj = client.servers.get_by_name(server)

        if not server_obj:
            return {
                "success": False,
                "error": f"Server '{server}' nicht gefunden"
            }

        action = client.floating_ips.assign(fip, server_obj)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Floating IP '{fip.ip}' zu Server '{server_obj.name}' zugewiesen",
            "floating_ip_id": fip.id,
            "server_id": server_obj.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Zuweisen der Floating IP: {str(e)}"
        }


async def hcloud_floating_ip_unassign(identifier: str) -> dict:
    """
    Entfernt die Zuweisung einer Floating IP.

    Args:
        identifier: Floating IP-ID oder Name

    Returns:
        Status der Aktion
    """
    try:
        client = get_client()

        try:
            fip_id = int(identifier)
            fip = client.floating_ips.get_by_id(fip_id)
        except ValueError:
            fip = client.floating_ips.get_by_name(identifier)

        if not fip:
            return {
                "success": False,
                "error": f"Floating IP '{identifier}' nicht gefunden"
            }

        action = client.floating_ips.unassign(fip)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Floating IP '{fip.ip}' Zuweisung entfernt",
            "floating_ip_id": fip.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Entfernen der Zuweisung: {str(e)}"
        }


async def hcloud_floating_ip_change_dns_ptr(
    identifier: str,
    ip: str,
    dns_ptr: Optional[str]
) -> dict:
    """
    Ändert den Reverse DNS für eine Floating IP.

    Args:
        identifier: Floating IP-ID oder Name
        ip: IP-Adresse
        dns_ptr: DNS-Pointer, None zum Zurücksetzen

    Returns:
        Status der Änderung
    """
    try:
        client = get_client()

        try:
            fip_id = int(identifier)
            fip = client.floating_ips.get_by_id(fip_id)
        except ValueError:
            fip = client.floating_ips.get_by_name(identifier)

        if not fip:
            return {
                "success": False,
                "error": f"Floating IP '{identifier}' nicht gefunden"
            }

        action = client.floating_ips.change_dns_ptr(fip, ip, dns_ptr)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Reverse DNS für IP {ip} auf '{dns_ptr}' gesetzt",
            "floating_ip_id": fip.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ändern des Reverse DNS: {str(e)}"
        }


async def hcloud_floating_ip_change_protection(
    identifier: str,
    delete: Optional[bool] = None
) -> dict:
    """
    Ändert den Schutz-Status einer Floating IP.

    Args:
        identifier: Floating IP-ID oder Name
        delete: Schutz vor Löschen aktivieren/deaktivieren

    Returns:
        Status der Änderung
    """
    try:
        client = get_client()

        try:
            fip_id = int(identifier)
            fip = client.floating_ips.get_by_id(fip_id)
        except ValueError:
            fip = client.floating_ips.get_by_name(identifier)

        if not fip:
            return {
                "success": False,
                "error": f"Floating IP '{identifier}' nicht gefunden"
            }

        action = client.floating_ips.change_protection(fip, delete=delete)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Schutz-Einstellungen für Floating IP '{fip.ip}' geändert",
            "floating_ip_id": fip.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ändern der Schutz-Einstellungen: {str(e)}"
        }


async def hcloud_floating_ip_update(
    identifier: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[dict] = None
) -> dict:
    """
    Aktualisiert Floating IP-Metadaten.

    Args:
        identifier: Floating IP-ID oder Name
        name: Neuer Name (optional)
        description: Neue Beschreibung (optional)
        labels: Neue Labels (optional)

    Returns:
        Aktualisierte Details
    """
    try:
        client = get_client()

        try:
            fip_id = int(identifier)
            fip = client.floating_ips.get_by_id(fip_id)
        except ValueError:
            fip = client.floating_ips.get_by_name(identifier)

        if not fip:
            return {
                "success": False,
                "error": f"Floating IP '{identifier}' nicht gefunden"
            }

        fip = client.floating_ips.update(fip, name=name, description=description, labels=labels)

        return {
            "success": True,
            "message": "Floating IP aktualisiert",
            "floating_ip": {
                "id": fip.id,
                "name": fip.name,
                "ip": fip.ip,
                "labels": fip.labels
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Aktualisieren der Floating IP: {str(e)}"
        }


# ===== PRIMARY IP ERWEITERTE FUNKTIONEN =====

async def hcloud_primary_ip_create(
    assignee_type: str,
    primary_type: str,
    datacenter: Optional[str] = None,
    assignee_id: Optional[int] = None,
    auto_delete: bool = True,
    name: Optional[str] = None,
    labels: Optional[dict] = None,
) -> dict:
    """
    Erstellt eine neue Primary IP.

    Args:
        assignee_type: server
        primary_type: ipv4 oder ipv6
        datacenter: Datacenter-Name (optional)
        assignee_id: Server-ID zum Zuweisen (optional)
        auto_delete: Automatisch löschen wenn Server gelöscht wird
        name: Name (optional)
        labels: Labels (optional)

    Returns:
        Details der erstellten Primary IP
    """
    try:
        client = get_client()

        dc = None
        if datacenter:
            dc = client.datacenters.get_by_name(datacenter)
            if not dc:
                return {"success": False, "error": f"Datacenter '{datacenter}' nicht gefunden"}

        response = client.primary_ips.create(
            type=primary_type,
            assignee_type=assignee_type,
            datacenter=dc,
            assignee_id=assignee_id,
            auto_delete=auto_delete,
            name=name,
            labels=labels,
        )

        pip = response.primary_ip

        return {
            "success": True,
            "primary_ip": {
                "id": pip.id,
                "name": pip.name,
                "ip": pip.ip,
                "type": pip.type,
            },
            "message": f"Primary IP '{pip.ip}' erstellt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen der Primary IP: {str(e)}"
        }


async def hcloud_primary_ip_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht eine Primary IP.

    Args:
        identifier: Primary IP-ID oder Name
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

        try:
            pip_id = int(identifier)
            pip = client.primary_ips.get_by_id(pip_id)
        except ValueError:
            pip = client.primary_ips.get_by_name(identifier)

        if not pip:
            return {
                "success": False,
                "error": f"Primary IP '{identifier}' nicht gefunden"
            }

        pip_ip = pip.ip
        pip_id = pip.id

        client.primary_ips.delete(pip)

        return {
            "success": True,
            "message": f"Primary IP '{pip_ip}' (ID: {pip_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen der Primary IP: {str(e)}"
        }


async def hcloud_primary_ip_assign(identifier: str, assignee_id: int) -> dict:
    """
    Weist eine Primary IP einem Server zu.

    Args:
        identifier: Primary IP-ID oder Name
        assignee_id: Server-ID

    Returns:
        Status der Zuweisung
    """
    try:
        client = get_client()

        try:
            pip_id = int(identifier)
            pip = client.primary_ips.get_by_id(pip_id)
        except ValueError:
            pip = client.primary_ips.get_by_name(identifier)

        if not pip:
            return {
                "success": False,
                "error": f"Primary IP '{identifier}' nicht gefunden"
            }

        action = client.primary_ips.assign(pip, assignee_id)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Primary IP '{pip.ip}' zu Server ID {assignee_id} zugewiesen",
            "primary_ip_id": pip.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Zuweisen der Primary IP: {str(e)}"
        }


async def hcloud_primary_ip_unassign(identifier: str) -> dict:
    """
    Entfernt die Zuweisung einer Primary IP.

    Args:
        identifier: Primary IP-ID oder Name

    Returns:
        Status der Aktion
    """
    try:
        client = get_client()

        try:
            pip_id = int(identifier)
            pip = client.primary_ips.get_by_id(pip_id)
        except ValueError:
            pip = client.primary_ips.get_by_name(identifier)

        if not pip:
            return {
                "success": False,
                "error": f"Primary IP '{identifier}' nicht gefunden"
            }

        action = client.primary_ips.unassign(pip)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Primary IP '{pip.ip}' Zuweisung entfernt",
            "primary_ip_id": pip.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Entfernen der Zuweisung: {str(e)}"
        }


async def hcloud_primary_ip_change_dns_ptr(
    identifier: str,
    ip: str,
    dns_ptr: Optional[str]
) -> dict:
    """
    Ändert den Reverse DNS für eine Primary IP.

    Args:
        identifier: Primary IP-ID oder Name
        ip: IP-Adresse
        dns_ptr: DNS-Pointer, None zum Zurücksetzen

    Returns:
        Status der Änderung
    """
    try:
        client = get_client()

        try:
            pip_id = int(identifier)
            pip = client.primary_ips.get_by_id(pip_id)
        except ValueError:
            pip = client.primary_ips.get_by_name(identifier)

        if not pip:
            return {
                "success": False,
                "error": f"Primary IP '{identifier}' nicht gefunden"
            }

        action = client.primary_ips.change_dns_ptr(pip, ip, dns_ptr)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Reverse DNS für IP {ip} auf '{dns_ptr}' gesetzt",
            "primary_ip_id": pip.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ändern des Reverse DNS: {str(e)}"
        }


async def hcloud_primary_ip_change_protection(
    identifier: str,
    delete: Optional[bool] = None
) -> dict:
    """
    Ändert den Schutz-Status einer Primary IP.

    Args:
        identifier: Primary IP-ID oder Name
        delete: Schutz vor Löschen aktivieren/deaktivieren

    Returns:
        Status der Änderung
    """
    try:
        client = get_client()

        try:
            pip_id = int(identifier)
            pip = client.primary_ips.get_by_id(pip_id)
        except ValueError:
            pip = client.primary_ips.get_by_name(identifier)

        if not pip:
            return {
                "success": False,
                "error": f"Primary IP '{identifier}' nicht gefunden"
            }

        action = client.primary_ips.change_protection(pip, delete=delete)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Schutz-Einstellungen für Primary IP '{pip.ip}' geändert",
            "primary_ip_id": pip.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ändern der Schutz-Einstellungen: {str(e)}"
        }


async def hcloud_primary_ip_update(
    identifier: str,
    name: Optional[str] = None,
    auto_delete: Optional[bool] = None,
    labels: Optional[dict] = None
) -> dict:
    """
    Aktualisiert Primary IP-Metadaten.

    Args:
        identifier: Primary IP-ID oder Name
        name: Neuer Name (optional)
        auto_delete: Auto-Delete aktivieren/deaktivieren (optional)
        labels: Neue Labels (optional)

    Returns:
        Aktualisierte Details
    """
    try:
        client = get_client()

        try:
            pip_id = int(identifier)
            pip = client.primary_ips.get_by_id(pip_id)
        except ValueError:
            pip = client.primary_ips.get_by_name(identifier)

        if not pip:
            return {
                "success": False,
                "error": f"Primary IP '{identifier}' nicht gefunden"
            }

        pip = client.primary_ips.update(pip, name=name, auto_delete=auto_delete, labels=labels)

        return {
            "success": True,
            "message": "Primary IP aktualisiert",
            "primary_ip": {
                "id": pip.id,
                "name": pip.name,
                "ip": pip.ip,
                "labels": pip.labels
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Aktualisieren der Primary IP: {str(e)}"
        }


# ===== IMAGE ERWEITERTE FUNKTIONEN =====

async def hcloud_image_update(
    identifier: str,
    description: Optional[str] = None,
    image_type: Optional[str] = None,
    labels: Optional[dict] = None
) -> dict:
    """
    Aktualisiert Image-Metadaten.

    Args:
        identifier: Image-ID oder Name
        description: Neue Beschreibung (optional)
        image_type: Neuer Typ: snapshot, backup (optional)
        labels: Neue Labels (optional)

    Returns:
        Aktualisierte Details
    """
    try:
        client = get_client()

        try:
            img_id = int(identifier)
            img = client.images.get_by_id(img_id)
        except ValueError:
            img = client.images.get_by_name(identifier)

        if not img:
            return {
                "success": False,
                "error": f"Image '{identifier}' nicht gefunden"
            }

        img = client.images.update(img, description=description, type=image_type, labels=labels)

        return {
            "success": True,
            "message": "Image aktualisiert",
            "image": {
                "id": img.id,
                "name": img.name,
                "description": img.description,
                "labels": img.labels
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Aktualisieren des Images: {str(e)}"
        }


async def hcloud_image_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht ein Image.

    Args:
        identifier: Image-ID oder Name
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

        try:
            img_id = int(identifier)
            img = client.images.get_by_id(img_id)
        except ValueError:
            img = client.images.get_by_name(identifier)

        if not img:
            return {
                "success": False,
                "error": f"Image '{identifier}' nicht gefunden"
            }

        img_name = img.name
        img_id = img.id

        client.images.delete(img)

        return {
            "success": True,
            "message": f"Image '{img_name}' (ID: {img_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen des Images: {str(e)}"
        }


async def hcloud_image_change_protection(
    identifier: str,
    delete: Optional[bool] = None
) -> dict:
    """
    Ändert den Schutz-Status eines Images.

    Args:
        identifier: Image-ID oder Name
        delete: Schutz vor Löschen aktivieren/deaktivieren

    Returns:
        Status der Änderung
    """
    try:
        client = get_client()

        try:
            img_id = int(identifier)
            img = client.images.get_by_id(img_id)
        except ValueError:
            img = client.images.get_by_name(identifier)

        if not img:
            return {
                "success": False,
                "error": f"Image '{identifier}' nicht gefunden"
            }

        action = client.images.change_protection(img, delete=delete)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Schutz-Einstellungen für Image '{img.name}' geändert",
            "image_id": img.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ändern der Schutz-Einstellungen: {str(e)}"
        }


# ===== SSH KEY UPDATE =====

async def hcloud_ssh_key_update(
    identifier: str,
    name: Optional[str] = None,
    labels: Optional[dict] = None
) -> dict:
    """
    Aktualisiert SSH-Key-Metadaten.

    Args:
        identifier: SSH-Key-ID oder Name
        name: Neuer Name (optional)
        labels: Neue Labels (optional)

    Returns:
        Aktualisierte Details
    """
    try:
        client = get_client()

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

        ssh_key = client.ssh_keys.update(ssh_key, name=name, labels=labels)

        return {
            "success": True,
            "message": "SSH-Key aktualisiert",
            "ssh_key": {
                "id": ssh_key.id,
                "name": ssh_key.name,
                "labels": ssh_key.labels
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Aktualisieren des SSH-Keys: {str(e)}"
        }


# ===== ACTIONS =====

async def hcloud_action_get(action_id: int) -> dict:
    """
    Ruft Details zu einer Action ab.

    Args:
        action_id: Action-ID

    Returns:
        Action-Details
    """
    try:
        client = get_client()
        action = client.actions.get_by_id(action_id)

        if not action:
            return {
                "success": False,
                "error": f"Action {action_id} nicht gefunden"
            }

        return {
            "success": True,
            "action": {
                "id": action.id,
                "command": action.command,
                "status": action.status,
                "progress": action.progress,
                "started": action.started.isoformat() if action.started else None,
                "finished": action.finished.isoformat() if action.finished else None,
                "error": {
                    "code": action.error.code if action.error else None,
                    "message": action.error.message if action.error else None,
                } if action.error else None,
                "resources": [
                    {"id": res.id, "type": res.type}
                    for res in action.resources
                ] if action.resources else []
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Action: {str(e)}"
        }


async def hcloud_action_list(status: Optional[list[str]] = None, sort: Optional[list[str]] = None) -> dict:
    """
    Listet alle Actions auf.

    Args:
        status: Filter nach Status (success, running, error)
        sort: Sortierung (id, command, status, progress)

    Returns:
        Liste von Actions
    """
    try:
        client = get_client()
        actions = client.actions.get_all(status=status, sort=sort)

        action_list = []
        for action in actions:
            action_list.append({
                "id": action.id,
                "command": action.command,
                "status": action.status,
                "progress": action.progress,
                "started": action.started.isoformat() if action.started else None,
                "finished": action.finished.isoformat() if action.finished else None,
                "resources": [
                    {"id": res.id, "type": res.type}
                    for res in action.resources
                ] if action.resources else []
            })

        return {
            "success": True,
            "count": len(action_list),
            "actions": action_list
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Actions: {str(e)}"
        }
