"""Snapshot Scheduler API Route."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import os
import uuid
from datetime import datetime

router = APIRouter()

SCHEDULES_FILE = os.path.join(os.path.dirname(__file__), '../../snapshot_schedules.json')


def _load_schedules():
    if os.path.exists(SCHEDULES_FILE):
        with open(SCHEDULES_FILE, 'r') as f:
            return json.load(f)
    return []


def _save_schedules(schedules):
    with open(SCHEDULES_FILE, 'w') as f:
        json.dump(schedules, f, indent=2)


class ScheduleRequest(BaseModel):
    server: str
    interval: str = "daily"  # daily, weekly
    time: str = "03:00"
    retention: int = 5
    enabled: bool = True


@router.get("/")
async def list_schedules():
    """Liste aller Snapshot-Zeitpläne."""
    schedules = _load_schedules()
    return {"success": True, "data": schedules}


@router.post("/")
async def create_schedule(request: ScheduleRequest):
    """Neuen Snapshot-Zeitplan erstellen."""
    schedules = _load_schedules()

    # Prüfen ob Server bereits einen Zeitplan hat
    existing = [s for s in schedules if s["server"] == request.server]
    if existing:
        raise HTTPException(status_code=400, detail=f"Server '{request.server}' hat bereits einen Zeitplan")

    schedule = {
        "id": str(uuid.uuid4())[:8],
        "server": request.server,
        "interval": request.interval,
        "time": request.time,
        "retention": request.retention,
        "enabled": request.enabled,
        "created": datetime.now().isoformat(),
        "last_run": None,
        "next_run": None,
    }

    schedules.append(schedule)
    _save_schedules(schedules)

    return {"success": True, "data": schedule}


@router.put("/{schedule_id}")
async def update_schedule(schedule_id: str, request: ScheduleRequest):
    """Zeitplan aktualisieren."""
    schedules = _load_schedules()
    for s in schedules:
        if s["id"] == schedule_id:
            s["server"] = request.server
            s["interval"] = request.interval
            s["time"] = request.time
            s["retention"] = request.retention
            s["enabled"] = request.enabled
            _save_schedules(schedules)
            return {"success": True, "data": s}

    raise HTTPException(status_code=404, detail="Zeitplan nicht gefunden")


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Zeitplan löschen."""
    schedules = _load_schedules()
    new_schedules = [s for s in schedules if s["id"] != schedule_id]
    if len(new_schedules) == len(schedules):
        raise HTTPException(status_code=404, detail="Zeitplan nicht gefunden")

    _save_schedules(new_schedules)
    return {"success": True, "message": "Zeitplan gelöscht"}


@router.post("/{schedule_id}/run")
async def run_schedule_now(schedule_id: str):
    """Zeitplan sofort ausführen (manueller Trigger)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))
    from src.hetzner_mcp.tools.servers import hcloud_server_create_image

    schedules = _load_schedules()
    schedule = None
    for s in schedules:
        if s["id"] == schedule_id:
            schedule = s
            break

    if not schedule:
        raise HTTPException(status_code=404, detail="Zeitplan nicht gefunden")

    result = await hcloud_server_create_image(
        schedule["server"],
        description=f"Scheduled snapshot {schedule['server']} {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        image_type="snapshot",
    )

    if result.get("success"):
        schedule["last_run"] = datetime.now().isoformat()
        _save_schedules(schedules)

    return {
        "success": result.get("success", False),
        "data": result,
    }
