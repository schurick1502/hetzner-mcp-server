"""Volume-Management Tools für Hetzner Cloud."""

from typing import Optional
from ..config import get_client


async def hcloud_volume_list() -> dict:
    """
    Listet alle Volumes im Hetzner Cloud Projekt auf.

    Returns:
        Dictionary mit Anzahl und Volume-Details
    """
    try:
        client = get_client()
        volumes = client.volumes.get_all()

        volume_list = []
        for vol in volumes:
            volume_list.append({
                "id": vol.id,
                "name": vol.name,
                "size": vol.size,
                "location": vol.location.name if vol.location else None,
                "server": vol.server.name if vol.server else None,
                "status": vol.status,
                "format": vol.format,
                "linux_device": vol.linux_device,
                "created": vol.created.isoformat(),
                "labels": vol.labels,
            })

        return {
            "success": True,
            "count": len(volume_list),
            "volumes": volume_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Volumes: {str(e)}"
        }


async def hcloud_volume_create(
    name: str,
    size: int,
    location: str,
    format_volume: Optional[str] = "ext4",
    labels: Optional[dict] = None,
) -> dict:
    """
    Erstellt ein neues Volume.

    Args:
        name: Volume-Name
        size: Größe in GB (mindestens 10)
        location: Standort (fsn1, nbg1, hel1)
        format_volume: Dateisystem (ext4 oder xfs), None für unformatiert
        labels: Dictionary mit Labels (optional)

    Returns:
        Details des erstellten Volumes
    """
    if size < 10:
        return {
            "success": False,
            "error": "Volume-Größe muss mindestens 10 GB betragen"
        }

    try:
        client = get_client()

        # Location abrufen
        loc = client.locations.get_by_name(location)
        if not loc:
            return {
                "success": False,
                "error": f"Location '{location}' nicht gefunden"
            }

        # Volume erstellen
        response = client.volumes.create(
            size=size,
            name=name,
            location=loc,
            format=format_volume,
            labels=labels,
        )

        volume = response.volume
        action = response.action

        # Auf Abschluss warten
        action.wait_until_finished()

        return {
            "success": True,
            "volume": {
                "id": volume.id,
                "name": volume.name,
                "size": volume.size,
                "location": volume.location.name if volume.location else None,
                "format": volume.format,
                "linux_device": volume.linux_device,
            },
            "message": f"Volume '{name}' mit {size}GB wurde erstellt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen des Volumes: {str(e)}"
        }


async def hcloud_volume_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht ein Volume (destruktive Aktion!).

    Args:
        identifier: Volume-ID oder Name
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

        # Volume finden
        try:
            vol_id = int(identifier)
            volume = client.volumes.get_by_id(vol_id)
        except ValueError:
            volume = client.volumes.get_by_name(identifier)

        if not volume:
            return {
                "success": False,
                "error": f"Volume '{identifier}' nicht gefunden"
            }

        vol_name = volume.name
        vol_id = volume.id

        # Volume löschen
        client.volumes.delete(volume)

        return {
            "success": True,
            "message": f"Volume '{vol_name}' (ID: {vol_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen des Volumes: {str(e)}"
        }


async def hcloud_volume_attach(volume: str, server: str, automount: bool = False) -> dict:
    """
    Hängt ein Volume an einen Server an.

    Args:
        volume: Volume-ID oder Name
        server: Server-ID oder Name
        automount: Volume automatisch mounten (Linux only)

    Returns:
        Status und Details
    """
    try:
        client = get_client()

        # Volume finden
        try:
            vol_id = int(volume)
            volume_obj = client.volumes.get_by_id(vol_id)
        except ValueError:
            volume_obj = client.volumes.get_by_name(volume)

        if not volume_obj:
            return {
                "success": False,
                "error": f"Volume '{volume}' nicht gefunden"
            }

        # Server finden
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

        # Volume anhängen
        action = client.volumes.attach(volume_obj, server_obj, automount=automount)
        action.wait_until_finished()

        # Volume neu abrufen für aktualisierte Daten
        volume_obj = client.volumes.get_by_id(volume_obj.id)

        return {
            "success": True,
            "message": f"Volume '{volume_obj.name}' an Server '{server_obj.name}' angehängt",
            "volume_id": volume_obj.id,
            "server_id": server_obj.id,
            "linux_device": volume_obj.linux_device,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Anhängen des Volumes: {str(e)}"
        }


async def hcloud_volume_detach(volume: str) -> dict:
    """
    Trennt ein Volume von seinem Server.

    Args:
        volume: Volume-ID oder Name

    Returns:
        Status der Trennung
    """
    try:
        client = get_client()

        # Volume finden
        try:
            vol_id = int(volume)
            volume_obj = client.volumes.get_by_id(vol_id)
        except ValueError:
            volume_obj = client.volumes.get_by_name(volume)

        if not volume_obj:
            return {
                "success": False,
                "error": f"Volume '{volume}' nicht gefunden"
            }

        if not volume_obj.server:
            return {
                "success": False,
                "error": f"Volume '{volume_obj.name}' ist nicht an einen Server angehängt"
            }

        server_name = volume_obj.server.name

        # Volume trennen
        action = client.volumes.detach(volume_obj)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Volume '{volume_obj.name}' von Server '{server_name}' getrennt",
            "volume_id": volume_obj.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Trennen des Volumes: {str(e)}"
        }


async def hcloud_volume_resize(volume: str, size: int) -> dict:
    """
    Ändert die Größe eines Volumes (nur Vergrößerung möglich!).

    Args:
        volume: Volume-ID oder Name
        size: Neue Größe in GB (muss größer als aktuelle Größe sein)

    Returns:
        Status der Größenänderung
    """
    try:
        client = get_client()

        # Volume finden
        try:
            vol_id = int(volume)
            volume_obj = client.volumes.get_by_id(vol_id)
        except ValueError:
            volume_obj = client.volumes.get_by_name(volume)

        if not volume_obj:
            return {
                "success": False,
                "error": f"Volume '{volume}' nicht gefunden"
            }

        if size <= volume_obj.size:
            return {
                "success": False,
                "error": f"Neue Größe ({size}GB) muss größer als aktuelle Größe ({volume_obj.size}GB) sein"
            }

        old_size = volume_obj.size

        # Größe ändern
        action = client.volumes.resize(volume_obj, size)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Volume '{volume_obj.name}' von {old_size}GB auf {size}GB vergrößert",
            "volume_id": volume_obj.id,
            "old_size": old_size,
            "new_size": size
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ändern der Volume-Größe: {str(e)}"
        }


async def hcloud_volume_change_protection(
    identifier: str,
    delete: Optional[bool] = None
) -> dict:
    """
    Ändert den Schutz-Status eines Volumes.

    Args:
        identifier: Volume-ID oder Name
        delete: Schutz vor Löschen aktivieren/deaktivieren

    Returns:
        Status der Änderung
    """
    try:
        client = get_client()

        try:
            vol_id = int(identifier)
            volume = client.volumes.get_by_id(vol_id)
        except ValueError:
            volume = client.volumes.get_by_name(identifier)

        if not volume:
            return {
                "success": False,
                "error": f"Volume '{identifier}' nicht gefunden"
            }

        action = client.volumes.change_protection(volume, delete=delete)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Schutz-Einstellungen für Volume '{volume.name}' geändert",
            "volume_id": volume.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ändern der Schutz-Einstellungen: {str(e)}"
        }


async def hcloud_volume_update(
    identifier: str,
    name: Optional[str] = None,
    labels: Optional[dict] = None
) -> dict:
    """
    Aktualisiert Volume-Metadaten (Name, Labels).

    Args:
        identifier: Volume-ID oder Name
        name: Neuer Name (optional)
        labels: Neue Labels (optional)

    Returns:
        Aktualisierte Volume-Details
    """
    try:
        client = get_client()

        try:
            vol_id = int(identifier)
            volume = client.volumes.get_by_id(vol_id)
        except ValueError:
            volume = client.volumes.get_by_name(identifier)

        if not volume:
            return {
                "success": False,
                "error": f"Volume '{identifier}' nicht gefunden"
            }

        volume = client.volumes.update(volume, name=name, labels=labels)

        return {
            "success": True,
            "message": "Volume aktualisiert",
            "volume": {
                "id": volume.id,
                "name": volume.name,
                "labels": volume.labels
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Aktualisieren des Volumes: {str(e)}"
        }
