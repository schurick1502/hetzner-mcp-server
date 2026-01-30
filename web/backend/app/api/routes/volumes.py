"""Volume API Routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.volumes import (
    hcloud_volume_list,
    hcloud_volume_create,
    hcloud_volume_delete,
    hcloud_volume_attach,
    hcloud_volume_detach,
    hcloud_volume_resize,
)

router = APIRouter()


class VolumeCreateRequest(BaseModel):
    name: str
    size: int
    location: str
    format_volume: str = "ext4"


@router.get("/")
async def list_volumes():
    """Liste aller Volumes."""
    result = await hcloud_volume_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/")
async def create_volume(request: VolumeCreateRequest):
    """Neues Volume erstellen."""
    result = await hcloud_volume_create(
        request.name,
        request.size,
        request.location,
        request.format_volume
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}")
async def delete_volume(identifier: str, force: bool = False):
    """Volume löschen."""
    result = await hcloud_volume_delete(identifier, force)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{volume}/attach/{server}")
async def attach_volume(volume: str, server: str, automount: bool = False):
    """Volume an Server anhängen."""
    result = await hcloud_volume_attach(volume, server, automount)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{volume}/detach")
async def detach_volume(volume: str):
    """Volume von Server trennen."""
    result = await hcloud_volume_detach(volume)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{volume}/resize")
async def resize_volume(volume: str, size: int):
    """Volume vergrößern."""
    result = await hcloud_volume_resize(volume, size)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
