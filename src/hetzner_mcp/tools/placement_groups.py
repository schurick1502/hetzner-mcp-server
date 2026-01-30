"""Placement Group-Management Tools für Hetzner Cloud."""

from typing import Optional
from ..config import get_client


async def hcloud_placement_group_list() -> dict:
    """
    Listet alle Placement Groups im Projekt auf.

    Returns:
        Dictionary mit Anzahl und Placement Group-Details
    """
    try:
        client = get_client()
        placement_groups = client.placement_groups.get_all()

        pg_list = []
        for pg in placement_groups:
            pg_list.append({
                "id": pg.id,
                "name": pg.name,
                "type": pg.type,
                "servers": [s.id for s in pg.servers] if pg.servers else [],
                "created": pg.created.isoformat(),
                "labels": pg.labels,
            })

        return {
            "success": True,
            "count": len(pg_list),
            "placement_groups": pg_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Placement Groups: {str(e)}"
        }


async def hcloud_placement_group_create(
    name: str,
    group_type: str = "spread",
    labels: Optional[dict] = None
) -> dict:
    """
    Erstellt eine neue Placement Group.

    Args:
        name: Placement Group Name
        group_type: Typ (spread für Anti-Affinity)
        labels: Labels (optional)

    Returns:
        Details der erstellten Placement Group
    """
    try:
        client = get_client()

        response = client.placement_groups.create(
            name=name,
            type=group_type,
            labels=labels
        )

        pg = response.placement_group

        return {
            "success": True,
            "placement_group": {
                "id": pg.id,
                "name": pg.name,
                "type": pg.type,
            },
            "message": f"Placement Group '{name}' erstellt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen der Placement Group: {str(e)}"
        }


async def hcloud_placement_group_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht eine Placement Group.

    Args:
        identifier: Placement Group-ID oder Name
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
            pg_id = int(identifier)
            pg = client.placement_groups.get_by_id(pg_id)
        except ValueError:
            pg = client.placement_groups.get_by_name(identifier)

        if not pg:
            return {
                "success": False,
                "error": f"Placement Group '{identifier}' nicht gefunden"
            }

        pg_name = pg.name
        pg_id = pg.id

        client.placement_groups.delete(pg)

        return {
            "success": True,
            "message": f"Placement Group '{pg_name}' (ID: {pg_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen der Placement Group: {str(e)}"
        }


async def hcloud_placement_group_update(
    identifier: str,
    name: Optional[str] = None,
    labels: Optional[dict] = None
) -> dict:
    """
    Aktualisiert Placement Group-Metadaten.

    Args:
        identifier: Placement Group-ID oder Name
        name: Neuer Name (optional)
        labels: Neue Labels (optional)

    Returns:
        Aktualisierte Details
    """
    try:
        client = get_client()

        try:
            pg_id = int(identifier)
            pg = client.placement_groups.get_by_id(pg_id)
        except ValueError:
            pg = client.placement_groups.get_by_name(identifier)

        if not pg:
            return {
                "success": False,
                "error": f"Placement Group '{identifier}' nicht gefunden"
            }

        pg = client.placement_groups.update(pg, name=name, labels=labels)

        return {
            "success": True,
            "message": "Placement Group aktualisiert",
            "placement_group": {
                "id": pg.id,
                "name": pg.name,
                "labels": pg.labels
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Aktualisieren der Placement Group: {str(e)}"
        }
