"""Firewall API Routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.firewalls import (
    hcloud_firewall_list,
    hcloud_firewall_create,
    hcloud_firewall_delete,
    hcloud_firewall_add_rule,
    hcloud_firewall_set_rules,
    hcloud_firewall_apply,
    hcloud_firewall_remove_from_server,
)

router = APIRouter()


class FirewallCreateRequest(BaseModel):
    name: str
    rules: Optional[list[dict]] = None
    labels: Optional[dict] = None


class FirewallRuleRequest(BaseModel):
    direction: str
    protocol: str
    source_ips: Optional[list[str]] = None
    destination_ips: Optional[list[str]] = None
    port: Optional[str] = None


@router.get("/")
async def list_firewalls():
    """Liste aller Firewalls."""
    result = await hcloud_firewall_list()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/")
async def create_firewall(request: FirewallCreateRequest):
    """Neue Firewall erstellen."""
    result = await hcloud_firewall_create(request.name, request.rules, request.labels)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}")
async def delete_firewall(identifier: str, force: bool = False):
    """Firewall löschen."""
    result = await hcloud_firewall_delete(identifier, force)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/rules")
async def add_rule(identifier: str, request: FirewallRuleRequest):
    """Regel hinzufügen."""
    result = await hcloud_firewall_add_rule(
        identifier,
        request.direction,
        request.protocol,
        request.source_ips,
        request.destination_ips,
        request.port,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


class FirewallSetRulesRequest(BaseModel):
    rules: list[dict]


@router.put("/{identifier}/rules")
async def set_rules(identifier: str, request: FirewallSetRulesRequest):
    """Alle Regeln einer Firewall setzen (überschreibt bestehende)."""
    result = await hcloud_firewall_set_rules(identifier, request.rules)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/{identifier}/apply/{server}")
async def apply_firewall(identifier: str, server: str):
    """Firewall auf Server anwenden."""
    result = await hcloud_firewall_apply(identifier, server)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/{identifier}/servers/{server}")
async def remove_from_server(identifier: str, server: str):
    """Firewall von Server entfernen."""
    result = await hcloud_firewall_remove_from_server(identifier, server)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
