"""Server-Management Tools für Hetzner Cloud."""

from typing import Optional
from hcloud.servers.domain import Server
from hcloud.images.domain import Image
from hcloud.server_types.domain import ServerType
from hcloud.locations.domain import Location
from hcloud.ssh_keys.domain import SSHKey
from hcloud.firewalls.domain import Firewall
from ..config import get_client


async def hcloud_server_list() -> dict:
    """
    Listet alle Server im Hetzner Cloud Projekt auf.

    Returns:
        Dictionary mit Anzahl und Server-Details (Name, Status, IP, Typ, Location)
    """
    try:
        client = get_client()
        servers = client.servers.get_all()

        server_list = []
        for server in servers:
            server_list.append({
                "id": server.id,
                "name": server.name,
                "status": server.status,
                "public_ipv4": server.public_net.ipv4.ip if server.public_net.ipv4 else None,
                "public_ipv6": str(server.public_net.ipv6.ip) if server.public_net.ipv6 else None,
                "server_type": server.server_type.name,
                "location": server.datacenter.location.name,
                "created": server.created.isoformat(),
            })

        return {
            "success": True,
            "count": len(server_list),
            "servers": server_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Server: {str(e)}"
        }


async def hcloud_server_info(identifier: str) -> dict:
    """
    Gibt detaillierte Informationen zu einem Server zurück.

    Args:
        identifier: Server-ID (int) oder Name (string)

    Returns:
        Detaillierte Server-Informationen
    """
    try:
        client = get_client()

        # Versuche als ID zu parsen, sonst als Name
        try:
            server_id = int(identifier)
            server = client.servers.get_by_id(server_id)
        except ValueError:
            server = client.servers.get_by_name(identifier)

        if not server:
            return {
                "success": False,
                "error": f"Server '{identifier}' nicht gefunden"
            }

        return {
            "success": True,
            "server": {
                "id": server.id,
                "name": server.name,
                "status": server.status,
                "public_ipv4": server.public_net.ipv4.ip if server.public_net.ipv4 else None,
                "public_ipv6": str(server.public_net.ipv6.ip) if server.public_net.ipv6 else None,
                "private_networks": [
                    {"network": net.network.name, "ip": net.ip}
                    for net in server.private_net
                ],
                "server_type": {
                    "name": server.server_type.name,
                    "cores": server.server_type.cores,
                    "memory": server.server_type.memory,
                    "disk": server.server_type.disk,
                },
                "datacenter": server.datacenter.name,
                "location": server.datacenter.location.name,
                "image": server.image.name if server.image else None,
                "volumes": [vol.name for vol in server.volumes],
                "created": server.created.isoformat(),
                "backup_window": server.backup_window,
                "rescue_enabled": server.rescue_enabled,
                "locked": server.locked,
                "labels": server.labels,
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Server-Details: {str(e)}"
        }


async def hcloud_server_create(
    name: str,
    server_type: str = "cx22",
    image: str = "ubuntu-24.04",
    location: str = "fsn1",
    ssh_keys: Optional[list[str]] = None,
    firewalls: Optional[list[str]] = None,
    user_data: Optional[str] = None,
    start_after_create: bool = True,
    labels: Optional[dict] = None,
) -> dict:
    """
    Erstellt einen neuen Hetzner Cloud Server.

    Args:
        name: Servername (muss eindeutig sein)
        server_type: Server-Typ (z.B. cx22, cx32, cpx11)
        image: OS-Image (z.B. ubuntu-24.04, debian-12, rocky-9)
        location: Standort (fsn1=Falkenstein, nbg1=Nürnberg, hel1=Helsinki)
        ssh_keys: Liste von SSH-Key Namen oder IDs (optional)
        firewalls: Liste von Firewall Namen oder IDs (optional)
        user_data: Cloud-init Script für Server-Initialisierung (optional)
        start_after_create: Server nach Erstellung starten (Standard: True)
        labels: Dictionary mit Labels für den Server (optional)

    Returns:
        Server-Details inklusive IP-Adresse und Root-Passwort (falls kein SSH-Key)
    """
    try:
        client = get_client()

        # Server-Typ abrufen
        srv_type = client.server_types.get_by_name(server_type)
        if not srv_type:
            return {
                "success": False,
                "error": f"Server-Typ '{server_type}' nicht gefunden"
            }

        # Image abrufen
        img = client.images.get_by_name(image)
        if not img:
            return {
                "success": False,
                "error": f"Image '{image}' nicht gefunden"
            }

        # Location abrufen
        loc = client.locations.get_by_name(location)
        if not loc:
            return {
                "success": False,
                "error": f"Location '{location}' nicht gefunden"
            }

        # SSH-Keys verarbeiten
        ssh_key_objects = []
        if ssh_keys:
            for key_identifier in ssh_keys:
                try:
                    key_id = int(key_identifier)
                    key = client.ssh_keys.get_by_id(key_id)
                except ValueError:
                    key = client.ssh_keys.get_by_name(key_identifier)

                if key:
                    ssh_key_objects.append(key)
                else:
                    return {
                        "success": False,
                        "error": f"SSH-Key '{key_identifier}' nicht gefunden"
                    }

        # Firewalls verarbeiten
        firewall_objects = []
        if firewalls:
            for fw_identifier in firewalls:
                try:
                    fw_id = int(fw_identifier)
                    fw = client.firewalls.get_by_id(fw_id)
                except ValueError:
                    fw = client.firewalls.get_by_name(fw_identifier)

                if fw:
                    firewall_objects.append(fw)
                else:
                    return {
                        "success": False,
                        "error": f"Firewall '{fw_identifier}' nicht gefunden"
                    }

        # Server erstellen
        response = client.servers.create(
            name=name,
            server_type=srv_type,
            image=img,
            location=loc,
            ssh_keys=ssh_key_objects if ssh_key_objects else None,
            firewalls=firewall_objects if firewall_objects else None,
            user_data=user_data,
            start_after_create=start_after_create,
            labels=labels,
        )

        server = response.server
        action = response.action

        # Auf Abschluss der Erstellung warten
        action.wait_until_finished()

        # Server neu abrufen für aktuelle Daten
        server = client.servers.get_by_id(server.id)

        result = {
            "success": True,
            "server": {
                "id": server.id,
                "name": server.name,
                "status": server.status,
                "public_ipv4": server.public_net.ipv4.ip if server.public_net.ipv4 else None,
                "public_ipv6": str(server.public_net.ipv6.ip) if server.public_net.ipv6 else None,
                "server_type": server.server_type.name,
                "location": server.datacenter.location.name,
            },
            "action": {
                "id": action.id,
                "status": action.status,
                "progress": action.progress,
            }
        }

        # Root-Passwort nur wenn verfügbar (nicht bei SSH-Key)
        if response.root_password:
            result["root_password"] = response.root_password
            result["warning"] = "Root-Passwort nur einmal angezeigt - bitte sicher speichern!"

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen des Servers: {str(e)}"
        }


async def hcloud_server_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht einen Server (destruktive Aktion!).

    Args:
        identifier: Server-ID oder Name
        force: Muss True sein zur Bestätigung (Sicherheitsmaßnahme)

    Returns:
        Status der Löschoperation
    """
    if not force:
        return {
            "success": False,
            "error": "Zum Löschen muss force=True gesetzt werden (Bestätigung erforderlich)"
        }

    try:
        client = get_client()

        # Server finden
        try:
            server_id = int(identifier)
            server = client.servers.get_by_id(server_id)
        except ValueError:
            server = client.servers.get_by_name(identifier)

        if not server:
            return {
                "success": False,
                "error": f"Server '{identifier}' nicht gefunden"
            }

        server_name = server.name
        server_id = server.id

        # Server löschen
        action = client.servers.delete(server)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Server '{server_name}' (ID: {server_id}) wurde gelöscht",
            "action_status": action.status
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen des Servers: {str(e)}"
        }


async def hcloud_server_power(identifier: str, action: str) -> dict:
    """
    Führt Power-Aktionen auf einem Server aus.

    Args:
        identifier: Server-ID oder Name
        action: Aktion (start, stop, reboot, shutdown, reset)
            - start: Server einschalten
            - stop: Sofortiges Ausschalten (wie Stecker ziehen)
            - shutdown: Sauberes Herunterfahren (empfohlen)
            - reboot: Neustart
            - reset: Hard Reset

    Returns:
        Status der Aktion
    """
    valid_actions = ["start", "stop", "shutdown", "reboot", "reset"]
    if action not in valid_actions:
        return {
            "success": False,
            "error": f"Ungültige Aktion '{action}'. Erlaubt: {', '.join(valid_actions)}"
        }

    try:
        client = get_client()

        # Server finden
        try:
            server_id = int(identifier)
            server = client.servers.get_by_id(server_id)
        except ValueError:
            server = client.servers.get_by_name(identifier)

        if not server:
            return {
                "success": False,
                "error": f"Server '{identifier}' nicht gefunden"
            }

        # Aktion ausführen
        if action == "start":
            result = client.servers.power_on(server)
        elif action == "stop":
            result = client.servers.power_off(server)
        elif action == "shutdown":
            result = client.servers.shutdown(server)
        elif action == "reboot":
            result = client.servers.reboot(server)
        elif action == "reset":
            result = client.servers.reset(server)

        result.wait_until_finished()

        return {
            "success": True,
            "message": f"Aktion '{action}' auf Server '{server.name}' ausgeführt",
            "action_status": result.status,
            "server_id": server.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ausführen der Power-Aktion: {str(e)}"
        }


async def hcloud_server_rebuild(
    identifier: str,
    image: str,
    return_root_password: bool = True
) -> dict:
    """
    Rebuilt einen Server mit einem neuen Image (alle Daten gehen verloren!).

    Args:
        identifier: Server-ID oder Name
        image: Neues OS-Image (z.B. ubuntu-24.04, debian-12)
        return_root_password: Root-Passwort zurückgeben wenn kein SSH-Key

    Returns:
        Status und ggf. neues Root-Passwort
    """
    try:
        client = get_client()

        # Server finden
        try:
            server_id = int(identifier)
            server = client.servers.get_by_id(server_id)
        except ValueError:
            server = client.servers.get_by_name(identifier)

        if not server:
            return {
                "success": False,
                "error": f"Server '{identifier}' nicht gefunden"
            }

        # Image abrufen
        img = client.images.get_by_name(image)
        if not img:
            return {
                "success": False,
                "error": f"Image '{image}' nicht gefunden"
            }

        # Rebuild ausführen
        result = client.servers.rebuild(server, img, return_image=return_root_password)
        result.action.wait_until_finished()

        response = {
            "success": True,
            "message": f"Server '{server.name}' wurde mit Image '{image}' rebuilt",
            "action_status": result.action.status,
            "server_id": server.id
        }

        if result.root_password:
            response["root_password"] = result.root_password
            response["warning"] = "Root-Passwort nur einmal angezeigt - bitte sicher speichern!"

        return response

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Rebuilden des Servers: {str(e)}"
        }
