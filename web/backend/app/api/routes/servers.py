"""Server API Routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path to import hetzner_mcp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.servers import (
    hcloud_server_list,
    hcloud_server_info,
    hcloud_server_create,
    hcloud_server_delete,
    hcloud_server_power,
    hcloud_server_rebuild,
    hcloud_server_enable_backup,
    hcloud_server_disable_backup,
    hcloud_server_enable_rescue,
    hcloud_server_disable_rescue,
    hcloud_server_create_image,
    hcloud_server_update,
    hcloud_server_get_metrics,
)

router = APIRouter()


# Pydantic Models
class ServerCreateRequest(BaseModel):
    name: str
    server_type: str = "cx22"
    image: str = "ubuntu-24.04"
    location: str = "fsn1"
    ssh_keys: Optional[list[str]] = None
    firewalls: Optional[list[str]] = None
    user_data: Optional[str] = None


class ServerPowerRequest(BaseModel):
    action: str  # start, stop, shutdown, reboot, reset


class ServerUpdateRequest(BaseModel):
    name: Optional[str] = None
    labels: Optional[dict] = None


@router.get("/")
async def list_servers():
    """Liste aller Server."""
    result = await hcloud_server_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/{identifier}")
async def get_server(identifier: str):
    """Server-Details abrufen."""
    result = await hcloud_server_info(identifier)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.post("/")
async def create_server(request: ServerCreateRequest):
    """Neuen Server erstellen."""
    result = await hcloud_server_create(
        name=request.name,
        server_type=request.server_type,
        image=request.image,
        location=request.location,
        ssh_keys=request.ssh_keys,
        firewalls=request.firewalls,
        user_data=request.user_data,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}")
async def delete_server(identifier: str, force: bool = False):
    """Server löschen."""
    result = await hcloud_server_delete(identifier, force)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/power")
async def power_server(identifier: str, request: ServerPowerRequest):
    """Power-Aktion ausführen."""
    result = await hcloud_server_power(identifier, request.action)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.patch("/{identifier}")
async def update_server(identifier: str, request: ServerUpdateRequest):
    """Server aktualisieren."""
    result = await hcloud_server_update(identifier, request.name, request.labels)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/backup/enable")
async def enable_backup(identifier: str):
    """Backup aktivieren."""
    result = await hcloud_server_enable_backup(identifier)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/backup/disable")
async def disable_backup(identifier: str):
    """Backup deaktivieren."""
    result = await hcloud_server_disable_backup(identifier)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/rescue/enable")
async def enable_rescue(identifier: str, rescue_type: str = "linux64"):
    """Rescue-Modus aktivieren."""
    result = await hcloud_server_enable_rescue(identifier, rescue_type)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/rescue/disable")
async def disable_rescue(identifier: str):
    """Rescue-Modus deaktivieren."""
    result = await hcloud_server_disable_rescue(identifier)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/snapshot")
async def create_snapshot(identifier: str, description: Optional[str] = None):
    """Snapshot erstellen."""
    result = await hcloud_server_create_image(identifier, description)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/{identifier}/metrics")
async def get_server_metrics(
    identifier: str,
    type: str = "cpu,disk,network",
    start: Optional[str] = None,
    end: Optional[str] = None
):
    """Server-Metriken abrufen (CPU, Disk, Network)."""
    from datetime import datetime, timedelta

    # Defaults: letzte Stunde
    if not end:
        end = datetime.now().isoformat()
    if not start:
        start = (datetime.now() - timedelta(hours=1)).isoformat()

    result = await hcloud_server_get_metrics(identifier, type, start, end)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result
