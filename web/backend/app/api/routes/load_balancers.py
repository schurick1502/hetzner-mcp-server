"""Load Balancer API Routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.load_balancers import (
    hcloud_load_balancer_list,
    hcloud_load_balancer_create,
    hcloud_load_balancer_delete,
    hcloud_load_balancer_add_service,
    hcloud_load_balancer_delete_service,
    hcloud_load_balancer_add_target,
    hcloud_load_balancer_remove_target,
    hcloud_load_balancer_change_algorithm,
    hcloud_load_balancer_update,
)

router = APIRouter()


class LBCreateRequest(BaseModel):
    name: str
    load_balancer_type: str = "lb11"
    location: str = "fsn1"


class LBServiceRequest(BaseModel):
    protocol: str = "tcp"
    listen_port: int = 80
    destination_port: int = 80
    proxyprotocol: bool = False
    health_check_protocol: str = "tcp"
    health_check_port: Optional[int] = None
    health_check_interval: int = 15
    health_check_timeout: int = 10
    health_check_retries: int = 3


class LBTargetRequest(BaseModel):
    target_type: str = "server"
    server: Optional[str] = None
    label_selector: Optional[str] = None
    ip: Optional[str] = None
    use_private_ip: bool = False


class LBAlgorithmRequest(BaseModel):
    algorithm_type: str = "round_robin"


@router.get("/")
async def list_load_balancers():
    """Liste aller Load Balancer."""
    result = await hcloud_load_balancer_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/")
async def create_load_balancer(request: LBCreateRequest):
    """Neuen Load Balancer erstellen."""
    result = await hcloud_load_balancer_create(request.name, request.load_balancer_type, request.location)
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


@router.post("/{identifier}/services")
async def add_service(identifier: str, request: LBServiceRequest):
    """Service zu Load Balancer hinzufügen."""
    result = await hcloud_load_balancer_add_service(
        identifier,
        request.protocol,
        request.listen_port,
        request.destination_port,
        request.proxyprotocol,
        health_check_protocol=request.health_check_protocol,
        health_check_port=request.health_check_port,
        health_check_interval=request.health_check_interval,
        health_check_timeout=request.health_check_timeout,
        health_check_retries=request.health_check_retries,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}/services/{listen_port}")
async def delete_service(identifier: str, listen_port: int):
    """Service von Load Balancer entfernen."""
    result = await hcloud_load_balancer_delete_service(identifier, listen_port)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/targets")
async def add_target(identifier: str, request: LBTargetRequest):
    """Target zu Load Balancer hinzufügen."""
    result = await hcloud_load_balancer_add_target(
        identifier,
        request.target_type,
        request.server,
        request.label_selector,
        request.ip,
        request.use_private_ip,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}/targets")
async def remove_target(identifier: str, request: LBTargetRequest):
    """Target von Load Balancer entfernen."""
    result = await hcloud_load_balancer_remove_target(
        identifier,
        request.target_type,
        request.server,
        request.label_selector,
        request.ip,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.put("/{identifier}/algorithm")
async def change_algorithm(identifier: str, request: LBAlgorithmRequest):
    """Algorithmus des Load Balancers ändern."""
    result = await hcloud_load_balancer_change_algorithm(identifier, request.algorithm_type)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
