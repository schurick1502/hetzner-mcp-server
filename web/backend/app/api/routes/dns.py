"""DNS / PTR Records API Route."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.servers import hcloud_server_list, hcloud_server_change_dns_ptr
from src.hetzner_mcp.tools.misc import hcloud_floating_ip_list, hcloud_primary_ip_list

router = APIRouter()


class PtrUpdateRequest(BaseModel):
    ip: str
    ptr: str
    resource_type: str  # server, floating_ip, primary_ip
    resource_id: str  # server name oder IP name/id


@router.get("/")
async def list_dns_records():
    """Liste aller IP-Adressen mit PTR-Records."""
    records = []

    # Server-IPs
    servers_result = await hcloud_server_list()
    if servers_result.get("success"):
        for srv in servers_result.get("servers", []):
            ipv4 = srv.get("public_ipv4")
            if ipv4:
                records.append({
                    "ip": ipv4,
                    "type": "ipv4",
                    "resource_type": "server",
                    "resource_name": srv["name"],
                    "ptr": srv.get("dns_ptr_ipv4", ""),
                })
            ipv6 = srv.get("public_ipv6")
            if ipv6:
                records.append({
                    "ip": ipv6,
                    "type": "ipv6",
                    "resource_type": "server",
                    "resource_name": srv["name"],
                    "ptr": srv.get("dns_ptr_ipv6", ""),
                })

    # Floating IPs
    fip_result = await hcloud_floating_ip_list()
    if fip_result.get("success"):
        for fip in fip_result.get("floating_ips", []):
            records.append({
                "ip": fip["ip"],
                "type": fip.get("type", "ipv4"),
                "resource_type": "floating_ip",
                "resource_name": fip.get("name", f"FIP #{fip['id']}"),
                "ptr": fip.get("dns_ptr", ""),
            })

    # Primary IPs
    pip_result = await hcloud_primary_ip_list()
    if pip_result.get("success"):
        for pip in pip_result.get("primary_ips", []):
            records.append({
                "ip": pip["ip"],
                "type": pip.get("type", "ipv4"),
                "resource_type": "primary_ip",
                "resource_name": pip.get("name", f"PIP #{pip['id']}"),
                "ptr": pip.get("dns_ptr", ""),
            })

    return {"success": True, "data": records}


@router.patch("/")
async def update_ptr_record(request: PtrUpdateRequest):
    """PTR-Record aktualisieren."""
    if request.resource_type == "server":
        result = await hcloud_server_change_dns_ptr(
            request.resource_id,
            request.ip,
            request.ptr,
        )
    elif request.resource_type == "floating_ip":
        try:
            from src.hetzner_mcp.tools.misc import hcloud_floating_ip_change_dns_ptr
            result = await hcloud_floating_ip_change_dns_ptr(
                request.resource_id,
                request.ip,
                request.ptr,
            )
        except ImportError:
            raise HTTPException(status_code=501, detail="Floating IP DNS PTR nicht verfügbar")
    elif request.resource_type == "primary_ip":
        try:
            from src.hetzner_mcp.tools.misc import hcloud_primary_ip_change_dns_ptr
            result = await hcloud_primary_ip_change_dns_ptr(
                request.resource_id,
                request.ip,
                request.ptr,
            )
        except ImportError:
            raise HTTPException(status_code=501, detail="Primary IP DNS PTR nicht verfügbar")
    else:
        raise HTTPException(status_code=400, detail=f"Unbekannter Ressourcentyp: {request.resource_type}")

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result
