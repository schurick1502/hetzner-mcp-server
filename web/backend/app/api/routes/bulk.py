"""Bulk Operations API Route."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.servers import (
    hcloud_server_power,
    hcloud_server_create_image,
)

router = APIRouter()


class BulkActionRequest(BaseModel):
    action: str  # start, stop, reboot, snapshot
    server_names: List[str]


@router.post("/")
async def bulk_action(request: BulkActionRequest):
    """Bulk-Operation auf mehrere Server anwenden."""
    if request.action not in ("start", "stop", "reboot", "snapshot"):
        raise HTTPException(status_code=400, detail=f"Unbekannte Aktion: {request.action}")

    if not request.server_names:
        raise HTTPException(status_code=400, detail="Keine Server ausgewählt")

    results = []
    success_count = 0
    error_count = 0

    for server_name in request.server_names:
        try:
            if request.action == "snapshot":
                result = await hcloud_server_create_image(
                    server_name,
                    description=f"Bulk-Snapshot {server_name}",
                    image_type="snapshot",
                )
            else:
                result = await hcloud_server_power(server_name, request.action)

            if result.get("success"):
                success_count += 1
                results.append({
                    "server": server_name,
                    "success": True,
                    "message": result.get("message", "OK"),
                })
            else:
                error_count += 1
                results.append({
                    "server": server_name,
                    "success": False,
                    "error": result.get("error", "Unbekannter Fehler"),
                })
        except Exception as e:
            error_count += 1
            results.append({
                "server": server_name,
                "success": False,
                "error": str(e),
            })

    return {
        "success": error_count == 0,
        "data": {
            "action": request.action,
            "total": len(request.server_names),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
        },
    }
