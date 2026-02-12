"""Cost Dashboard API Routes."""

from fastapi import APIRouter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.servers import hcloud_server_list
from src.hetzner_mcp.tools.volumes import hcloud_volume_list
from src.hetzner_mcp.tools.misc import (
    hcloud_server_type_list,
    hcloud_image_list,
    hcloud_floating_ip_list,
    hcloud_primary_ip_list,
)
from src.hetzner_mcp.tools.load_balancers import hcloud_load_balancer_list

router = APIRouter()

# Hetzner Festpreise (EUR, brutto, Stand 2024/2025)
VOLUME_PRICE_PER_GB = 0.0440       # €/GB/Monat
SNAPSHOT_PRICE_PER_GB = 0.0119     # €/GB/Monat
FLOATING_IP_V4_PRICE = 4.63       # €/Monat (wenn nicht zugewiesen)
PRIMARY_IP_V4_PRICE = 4.63        # €/Monat (unabhängig von Zuweisung)


@router.get("/")
async def get_costs():
    """Berechnet geschätzte monatliche Kosten aller Ressourcen."""
    # Alle Daten parallel abrufen
    servers_result = await hcloud_server_list()
    types_result = await hcloud_server_type_list()
    volumes_result = await hcloud_volume_list()
    snapshots_result = await hcloud_image_list(image_type="snapshot")
    floating_ips_result = await hcloud_floating_ip_list()
    primary_ips_result = await hcloud_primary_ip_list()
    lb_result = await hcloud_load_balancer_list()

    # Server-Typen Preise als Lookup
    type_prices = {}
    server_types_list = []
    if types_result.get("success"):
        for st in types_result.get("server_types", []):
            prices = st.get("prices", {})
            monthly = float(prices.get("monthly_gross", 0))
            hourly = float(prices.get("hourly_gross", 0))
            type_prices[st["name"]] = monthly
            server_types_list.append({
                "name": st["name"],
                "description": st.get("description", ""),
                "cores": st["cores"],
                "memory": st["memory"],
                "disk": st["disk"],
                "storage_type": st.get("storage_type", ""),
                "cpu_type": st.get("cpu_type", ""),
                "architecture": st.get("architecture", ""),
                "price_hourly": hourly,
                "price_monthly": monthly,
                "included_traffic": st.get("included_traffic", 0),
            })

    # Server-Kosten
    server_costs = []
    total_servers = 0.0
    if servers_result.get("success"):
        for srv in servers_result.get("servers", []):
            server_type = srv.get("server_type", "")
            monthly = type_prices.get(server_type, 0)
            total_servers += monthly
            server_costs.append({
                "name": srv["name"],
                "type": server_type,
                "location": srv.get("location", ""),
                "status": srv.get("status", ""),
                "monthly": monthly,
            })

    # Volume-Kosten
    volume_costs = []
    total_volumes = 0.0
    if volumes_result.get("success"):
        for vol in volumes_result.get("volumes", []):
            size = vol.get("size", 0)
            monthly = size * VOLUME_PRICE_PER_GB
            total_volumes += monthly
            volume_costs.append({
                "name": vol["name"],
                "size_gb": size,
                "server": vol.get("server"),
                "monthly": round(monthly, 2),
            })

    # Snapshot-Kosten
    snapshot_costs = []
    total_snapshots = 0.0
    if snapshots_result.get("success"):
        for img in snapshots_result.get("images", []):
            size = img.get("disk_size", 0)
            monthly = size * SNAPSHOT_PRICE_PER_GB
            total_snapshots += monthly
            snapshot_costs.append({
                "name": img.get("description") or img.get("name", f"Snapshot #{img['id']}"),
                "size_gb": size,
                "monthly": round(monthly, 2),
            })

    # Floating IP-Kosten
    floating_ip_costs = []
    total_floating_ips = 0.0
    if floating_ips_result.get("success"):
        for fip in floating_ips_result.get("floating_ips", []):
            if fip.get("type") == "ipv4":
                monthly = FLOATING_IP_V4_PRICE if not fip.get("server") else 0
                total_floating_ips += monthly
                floating_ip_costs.append({
                    "ip": fip["ip"],
                    "name": fip.get("name", ""),
                    "server": fip.get("server"),
                    "monthly": monthly,
                })

    # Primary IP-Kosten
    primary_ip_costs = []
    total_primary_ips = 0.0
    if primary_ips_result.get("success"):
        for pip in primary_ips_result.get("primary_ips", []):
            if pip.get("type") == "ipv4":
                monthly = PRIMARY_IP_V4_PRICE
                total_primary_ips += monthly
                primary_ip_costs.append({
                    "ip": pip["ip"],
                    "name": pip.get("name", ""),
                    "assignee": pip.get("assignee_id"),
                    "monthly": monthly,
                })

    # Load Balancer-Kosten (vereinfacht)
    lb_costs = []
    total_lbs = 0.0
    if lb_result.get("success"):
        for lb in lb_result.get("load_balancers", []):
            monthly = 5.83  # lb11 Standard-Preis
            total_lbs += monthly
            lb_costs.append({
                "name": lb["name"],
                "type": lb.get("load_balancer_type", "lb11"),
                "monthly": monthly,
            })

    total_monthly = total_servers + total_volumes + total_snapshots + total_floating_ips + total_primary_ips + total_lbs

    return {
        "success": True,
        "data": {
            "total_monthly": round(total_monthly, 2),
            "breakdown": {
                "servers": {"total": round(total_servers, 2), "items": server_costs},
                "volumes": {"total": round(total_volumes, 2), "items": volume_costs},
                "snapshots": {"total": round(total_snapshots, 2), "items": snapshot_costs},
                "floating_ips": {"total": round(total_floating_ips, 2), "items": floating_ip_costs},
                "primary_ips": {"total": round(total_primary_ips, 2), "items": primary_ip_costs},
                "load_balancers": {"total": round(total_lbs, 2), "items": lb_costs},
            },
            "server_types": server_types_list,
        },
    }
