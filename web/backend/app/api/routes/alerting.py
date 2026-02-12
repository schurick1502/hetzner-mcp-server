"""Alerting API Route - Threshold-basiertes Alerting."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

router = APIRouter()

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '../../alerting_config.json')


def _load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"thresholds": {}, "global": {"cpu": 80, "ram": 90, "disk": 85}}


def _save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


class ThresholdConfig(BaseModel):
    cpu: int = 80
    ram: int = 90
    disk: int = 85


class AlertingConfig(BaseModel):
    global_thresholds: ThresholdConfig = ThresholdConfig()
    server_thresholds: Dict[str, ThresholdConfig] = {}


@router.get("/config")
async def get_config():
    """Alerting-Konfiguration abrufen."""
    config = _load_config()
    return {"success": True, "data": config}


@router.put("/config")
async def update_config(request: AlertingConfig):
    """Alerting-Konfiguration aktualisieren."""
    config = {
        "global": request.global_thresholds.model_dump(),
        "thresholds": {k: v.model_dump() for k, v in request.server_thresholds.items()},
    }
    _save_config(config)
    return {"success": True, "data": config}


@router.get("/status")
async def get_status():
    """Prüft aktuelle Werte gegen konfigurierte Schwellenwerte."""
    from src.hetzner_mcp.tools.servers import hcloud_server_list

    config = _load_config()
    global_thresh = config.get("global", {"cpu": 80, "ram": 90, "disk": 85})
    server_thresh = config.get("thresholds", {})

    servers_result = await hcloud_server_list()
    if not servers_result.get("success"):
        return {"success": False, "error": "Konnte Server nicht abrufen"}

    alerts = []
    server_statuses = []

    # Versuche SSH-Metriken für jeden Server zu holen
    try:
        from web.backend.app.api.routes.docker_monitoring import get_system_metrics_ssh
    except ImportError:
        get_system_metrics_ssh = None

    for srv in servers_result.get("servers", []):
        if srv.get("status") != "running":
            continue

        server_name = srv["name"]
        thresh = server_thresh.get(server_name, global_thresh)
        ip = srv.get("public_ipv4")

        status = {
            "server": server_name,
            "ip": ip,
            "thresholds": thresh,
            "metrics": None,
            "alerts": [],
        }

        # SSH-Metriken holen wenn möglich
        if get_system_metrics_ssh and ip:
            try:
                metrics = await get_system_metrics_ssh(ip)
                if metrics:
                    status["metrics"] = {
                        "cpu": metrics.get("cpu_percent", 0),
                        "ram": metrics.get("memory_percent", 0),
                        "disk": metrics.get("disk_percent", 0),
                    }

                    if metrics.get("cpu_percent", 0) > thresh.get("cpu", 80):
                        alert = {"server": server_name, "type": "cpu", "value": metrics["cpu_percent"], "threshold": thresh["cpu"]}
                        alerts.append(alert)
                        status["alerts"].append(alert)

                    if metrics.get("memory_percent", 0) > thresh.get("ram", 90):
                        alert = {"server": server_name, "type": "ram", "value": metrics["memory_percent"], "threshold": thresh["ram"]}
                        alerts.append(alert)
                        status["alerts"].append(alert)

                    if metrics.get("disk_percent", 0) > thresh.get("disk", 85):
                        alert = {"server": server_name, "type": "disk", "value": metrics["disk_percent"], "threshold": thresh["disk"]}
                        alerts.append(alert)
                        status["alerts"].append(alert)
            except Exception:
                pass

        server_statuses.append(status)

    return {
        "success": True,
        "data": {
            "alerts": alerts,
            "alert_count": len(alerts),
            "servers": server_statuses,
        },
    }
