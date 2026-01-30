"""Network API Routes."""

from fastapi import APIRouter, HTTPException
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.networks import (
    hcloud_network_list,
    hcloud_network_create,
    hcloud_network_delete,
)

router = APIRouter()


@router.get("/")
async def list_networks():
    """Liste aller Netzwerke."""
    result = await hcloud_network_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/")
async def create_network(name: str, ip_range: str):
    """Neues Netzwerk erstellen."""
    result = await hcloud_network_create(name, ip_range)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}")
async def delete_network(identifier: str, force: bool = False):
    """Netzwerk löschen."""
    result = await hcloud_network_delete(identifier, force)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
