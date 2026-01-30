"""Load Balancer API Routes."""

from fastapi import APIRouter, HTTPException
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.load_balancers import (
    hcloud_load_balancer_list,
    hcloud_load_balancer_create,
    hcloud_load_balancer_delete,
)

router = APIRouter()


@router.get("/")
async def list_load_balancers():
    """Liste aller Load Balancer."""
    result = await hcloud_load_balancer_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/")
async def create_load_balancer(
    name: str,
    load_balancer_type: str,
    location: str = "fsn1"
):
    """Neuen Load Balancer erstellen."""
    result = await hcloud_load_balancer_create(name, load_balancer_type, location)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}")
async def delete_load_balancer(identifier: str, force: bool = False):
    """Load Balancer löschen."""
    result = await hcloud_load_balancer_delete(identifier, force)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
