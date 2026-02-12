"""Network API Routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.networks import (
    hcloud_network_list,
    hcloud_network_create,
    hcloud_network_delete,
    hcloud_network_add_subnet,
    hcloud_network_delete_subnet,
    hcloud_network_add_route,
    hcloud_network_delete_route,
)

router = APIRouter()


class NetworkCreateRequest(BaseModel):
    name: str
    ip_range: str


class SubnetRequest(BaseModel):
    ip_range: str
    network_zone: str = "eu-central"
    subnet_type: str = "cloud"


class SubnetDeleteRequest(BaseModel):
    ip_range: str


class RouteRequest(BaseModel):
    destination: str
    gateway: str


@router.get("/")
async def list_networks():
    """Liste aller Netzwerke."""
    result = await hcloud_network_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/")
async def create_network(request: NetworkCreateRequest):
    """Neues Netzwerk erstellen."""
    result = await hcloud_network_create(request.name, request.ip_range)
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


@router.post("/{identifier}/subnets")
async def add_subnet(identifier: str, request: SubnetRequest):
    """Subnet zu Netzwerk hinzufügen."""
    result = await hcloud_network_add_subnet(
        identifier, request.ip_range, request.network_zone, request.subnet_type
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}/subnets")
async def delete_subnet(identifier: str, request: SubnetDeleteRequest):
    """Subnet von Netzwerk entfernen."""
    result = await hcloud_network_delete_subnet(identifier, request.ip_range)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/routes")
async def add_route(identifier: str, request: RouteRequest):
    """Route zu Netzwerk hinzufügen."""
    result = await hcloud_network_add_route(identifier, request.destination, request.gateway)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}/routes")
async def delete_route(identifier: str, request: RouteRequest):
    """Route von Netzwerk entfernen."""
    result = await hcloud_network_delete_route(identifier, request.destination, request.gateway)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
