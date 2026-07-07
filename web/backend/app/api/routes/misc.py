"""Misc API Routes (SSH Keys, Images, Locations, etc.)."""

from fastapi import APIRouter, HTTPException
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.misc import (
    hcloud_ssh_key_list,
    hcloud_image_list,
    hcloud_server_type_list,
    hcloud_location_list,
    hcloud_datacenter_list,
)
from src.hetzner_mcp.config import get_available_accounts, get_default_account_id

router = APIRouter()


@router.get("/accounts")
async def list_accounts():
    """Liste aller konfigurierten Hetzner Accounts."""
    return {
        "success": True,
        "accounts": get_available_accounts(),
        "default_account": get_default_account_id(),
    }


@router.get("/ssh-keys")
async def list_ssh_keys():
    """Liste aller SSH-Keys."""
    result = await hcloud_ssh_key_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/images")
async def list_images(image_type: str = None):
    """Liste aller Images."""
    result = await hcloud_image_list(image_type)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/server-types")
async def list_server_types():
    """Liste aller Server-Typen."""
    result = await hcloud_server_type_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/locations")
async def list_locations():
    """Liste aller Locations."""
    result = await hcloud_location_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/datacenters")
async def list_datacenters():
    """Liste aller Datacenters."""
    result = await hcloud_datacenter_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result
