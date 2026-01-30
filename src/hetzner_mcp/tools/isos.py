"""ISO-Management Tools für Hetzner Cloud."""

from typing import Optional
from ..config import get_client


async def hcloud_iso_list(iso_type: Optional[str] = None) -> dict:
    """
    Listet alle verfügbaren ISOs auf.

    Args:
        iso_type: Filter nach Typ: "public" oder "private"

    Returns:
        Dictionary mit Anzahl und ISO-Details
    """
    try:
        client = get_client()

        if iso_type:
            isos = client.isos.get_all(type=iso_type)
        else:
            isos = client.isos.get_all()

        iso_list = []
        for iso in isos:
            iso_list.append({
                "id": iso.id,
                "name": iso.name,
                "description": iso.description,
                "type": iso.type,
                "architecture": iso.architecture if hasattr(iso, 'architecture') else None,
                "deprecated": iso.deprecated.isoformat() if iso.deprecated else None,
            })

        return {
            "success": True,
            "count": len(iso_list),
            "isos": iso_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der ISOs: {str(e)}"
        }


async def hcloud_iso_get(identifier: str) -> dict:
    """
    Ruft Details zu einem ISO ab.

    Args:
        identifier: ISO-ID oder Name

    Returns:
        ISO-Details
    """
    try:
        client = get_client()

        try:
            iso_id = int(identifier)
            iso = client.isos.get_by_id(iso_id)
        except ValueError:
            iso = client.isos.get_by_name(identifier)

        if not iso:
            return {
                "success": False,
                "error": f"ISO '{identifier}' nicht gefunden"
            }

        return {
            "success": True,
            "iso": {
                "id": iso.id,
                "name": iso.name,
                "description": iso.description,
                "type": iso.type,
                "architecture": iso.architecture if hasattr(iso, 'architecture') else None,
                "deprecated": iso.deprecated.isoformat() if iso.deprecated else None,
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen des ISO: {str(e)}"
        }
