"""CLI API Routes - Eigenständige Hetzner Cloud CLI-Tools."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
from hcloud import Client
from hcloud.servers.domain import Server
from hcloud.firewalls.domain import Firewall
from hcloud.volumes.domain import Volume
from hcloud.networks.domain import Network

router = APIRouter()

# Hetzner Client initialisieren
def get_hcloud_client() -> Client:
    """Hetzner Cloud Client mit API-Token."""
    token = os.getenv("HCLOUD_TOKEN") or os.getenv("HETZNER_API_TOKEN")
    if not token:
        raise HTTPException(
            status_code=500,
            detail="HCLOUD_TOKEN oder HETZNER_API_TOKEN nicht konfiguriert"
        )
    return Client(token=token)


class CommandRequest(BaseModel):
    command: str
    args: Dict[str, Any] = {}


# Tool-Definitionen
CLI_TOOLS = [
    # Server Tools
    {
        "name": "server_list",
        "description": "Liste aller Server im Projekt",
        "parameters": []
    },
    {
        "name": "server_info",
        "description": "Detaillierte Informationen zu einem Server",
        "parameters": [
            {"name": "identifier", "type": "str", "required": True, "default": None}
        ]
    },
    {
        "name": "server_power",
        "description": "Power-Aktionen: start, stop, shutdown, reboot, reset",
        "parameters": [
            {"name": "identifier", "type": "str", "required": True, "default": None},
            {"name": "action", "type": "str", "required": True, "default": None}
        ]
    },
    # Firewall Tools
    {
        "name": "firewall_list",
        "description": "Liste aller Firewalls",
        "parameters": []
    },
    # Volume Tools
    {
        "name": "volume_list",
        "description": "Liste aller Volumes",
        "parameters": []
    },
    # Network Tools
    {
        "name": "network_list",
        "description": "Liste aller privaten Netzwerke",
        "parameters": []
    },
    # SSH Key Tools
    {
        "name": "ssh_key_list",
        "description": "Liste aller SSH-Keys",
        "parameters": []
    },
    # Image Tools
    {
        "name": "image_list",
        "description": "Liste aller Images (system, snapshot, backup, app)",
        "parameters": [
            {"name": "image_type", "type": "str", "required": False, "default": None}
        ]
    },
    # Server Type / Location
    {
        "name": "server_type_list",
        "description": "Liste aller Server-Typen mit Preisen",
        "parameters": []
    },
    {
        "name": "location_list",
        "description": "Liste aller verfügbaren Standorte",
        "parameters": []
    },
    {
        "name": "datacenter_list",
        "description": "Liste aller Rechenzentren",
        "parameters": []
    },
    # Floating IPs
    {
        "name": "floating_ip_list",
        "description": "Liste aller Floating IPs",
        "parameters": []
    },
    # Primary IPs
    {
        "name": "primary_ip_list",
        "description": "Liste aller Primary IPs",
        "parameters": []
    },
    # Load Balancers
    {
        "name": "load_balancer_list",
        "description": "Liste aller Load Balancer",
        "parameters": []
    },
    # Certificates
    {
        "name": "certificate_list",
        "description": "Liste aller Certificates",
        "parameters": []
    },
    # Placement Groups
    {
        "name": "placement_group_list",
        "description": "Liste aller Placement Groups",
        "parameters": []
    },
]


# Tool-Implementierungen
async def server_list() -> dict:
    """Liste aller Server."""
    client = get_hcloud_client()
    servers = client.servers.get_all()
    return {
        "servers": [
            {
                "id": s.id,
                "name": s.name,
                "status": s.status,
                "public_net": {
                    "ipv4": s.public_net.ipv4.ip if s.public_net.ipv4 else None,
                    "ipv6": s.public_net.ipv6.ip if s.public_net.ipv6 else None,
                },
                "server_type": s.server_type.name if s.server_type else None,
                "datacenter": s.datacenter.name if s.datacenter else None,
                "created": str(s.created) if s.created else None,
            }
            for s in servers
        ],
        "count": len(servers)
    }


async def server_info(identifier: str) -> dict:
    """Details zu einem Server."""
    client = get_hcloud_client()
    server = None

    # Suche nach ID oder Name
    if identifier.isdigit():
        server = client.servers.get_by_id(int(identifier))
    else:
        server = client.servers.get_by_name(identifier)

    if not server:
        return {"error": f"Server '{identifier}' nicht gefunden"}

    return {
        "id": server.id,
        "name": server.name,
        "status": server.status,
        "public_net": {
            "ipv4": server.public_net.ipv4.ip if server.public_net.ipv4 else None,
            "ipv6": server.public_net.ipv6.ip if server.public_net.ipv6 else None,
        },
        "server_type": {
            "name": server.server_type.name,
            "description": server.server_type.description,
            "cores": server.server_type.cores,
            "memory": server.server_type.memory,
            "disk": server.server_type.disk,
        } if server.server_type else None,
        "datacenter": {
            "name": server.datacenter.name,
            "location": server.datacenter.location.name if server.datacenter.location else None,
        } if server.datacenter else None,
        "image": server.image.name if server.image else None,
        "created": str(server.created) if server.created else None,
        "backup_window": server.backup_window,
        "rescue_enabled": server.rescue_enabled,
        "locked": server.locked,
        "labels": server.labels,
    }


async def server_power(identifier: str, action: str) -> dict:
    """Power-Aktion auf Server ausführen."""
    client = get_hcloud_client()
    server = None

    if identifier.isdigit():
        server = client.servers.get_by_id(int(identifier))
    else:
        server = client.servers.get_by_name(identifier)

    if not server:
        return {"error": f"Server '{identifier}' nicht gefunden"}

    valid_actions = ["start", "stop", "shutdown", "reboot", "reset"]
    if action not in valid_actions:
        return {"error": f"Ungültige Aktion: {action}. Erlaubt: {valid_actions}"}

    try:
        if action == "start":
            response = client.servers.power_on(server)
        elif action == "stop":
            response = client.servers.power_off(server)
        elif action == "shutdown":
            response = client.servers.shutdown(server)
        elif action == "reboot":
            response = client.servers.reboot(server)
        elif action == "reset":
            response = client.servers.reset(server)

        return {
            "success": True,
            "server": server.name,
            "action": action,
            "action_id": response.action.id if response and response.action else None,
        }
    except Exception as e:
        return {"error": str(e)}


async def firewall_list() -> dict:
    """Liste aller Firewalls."""
    client = get_hcloud_client()
    firewalls = client.firewalls.get_all()
    return {
        "firewalls": [
            {
                "id": f.id,
                "name": f.name,
                "rules_count": len(f.rules) if f.rules else 0,
                "applied_to_count": len(f.applied_to) if f.applied_to else 0,
                "created": str(f.created) if f.created else None,
            }
            for f in firewalls
        ],
        "count": len(firewalls)
    }


async def volume_list() -> dict:
    """Liste aller Volumes."""
    client = get_hcloud_client()
    volumes = client.volumes.get_all()
    return {
        "volumes": [
            {
                "id": v.id,
                "name": v.name,
                "size": v.size,
                "status": v.status,
                "server": v.server.name if v.server else None,
                "location": v.location.name if v.location else None,
                "linux_device": v.linux_device,
                "created": str(v.created) if v.created else None,
            }
            for v in volumes
        ],
        "count": len(volumes)
    }


async def network_list() -> dict:
    """Liste aller Netzwerke."""
    client = get_hcloud_client()
    networks = client.networks.get_all()
    return {
        "networks": [
            {
                "id": n.id,
                "name": n.name,
                "ip_range": n.ip_range,
                "subnets_count": len(n.subnets) if n.subnets else 0,
                "servers_count": len(n.servers) if n.servers else 0,
                "created": str(n.created) if n.created else None,
            }
            for n in networks
        ],
        "count": len(networks)
    }


async def ssh_key_list() -> dict:
    """Liste aller SSH-Keys."""
    client = get_hcloud_client()
    ssh_keys = client.ssh_keys.get_all()
    return {
        "ssh_keys": [
            {
                "id": k.id,
                "name": k.name,
                "fingerprint": k.fingerprint,
                "created": str(k.created) if k.created else None,
            }
            for k in ssh_keys
        ],
        "count": len(ssh_keys)
    }


async def image_list(image_type: Optional[str] = None) -> dict:
    """Liste aller Images."""
    client = get_hcloud_client()
    images = client.images.get_all()

    if image_type:
        images = [i for i in images if i.type == image_type]

    return {
        "images": [
            {
                "id": i.id,
                "name": i.name,
                "description": i.description,
                "type": i.type,
                "status": i.status,
                "os_flavor": i.os_flavor,
                "os_version": i.os_version,
                "disk_size": i.disk_size,
                "created": str(i.created) if i.created else None,
            }
            for i in images[:50]  # Limit für Performance
        ],
        "count": len(images),
        "showing": min(50, len(images))
    }


async def server_type_list() -> dict:
    """Liste aller Server-Typen."""
    client = get_hcloud_client()
    server_types = client.server_types.get_all()
    return {
        "server_types": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "cores": t.cores,
                "memory": t.memory,
                "disk": t.disk,
                "prices": [
                    {
                        "location": p["location"],
                        "price_hourly": p["price_hourly"]["gross"],
                        "price_monthly": p["price_monthly"]["gross"],
                    }
                    for p in (t.prices or [])[:3]
                ],
                "deprecated": t.deprecated,
            }
            for t in server_types
        ],
        "count": len(server_types)
    }


async def location_list() -> dict:
    """Liste aller Standorte."""
    client = get_hcloud_client()
    locations = client.locations.get_all()
    return {
        "locations": [
            {
                "id": l.id,
                "name": l.name,
                "description": l.description,
                "country": l.country,
                "city": l.city,
                "network_zone": l.network_zone,
            }
            for l in locations
        ],
        "count": len(locations)
    }


async def datacenter_list() -> dict:
    """Liste aller Rechenzentren."""
    client = get_hcloud_client()
    datacenters = client.datacenters.get_all()
    return {
        "datacenters": [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "location": d.location.name if d.location else None,
            }
            for d in datacenters
        ],
        "count": len(datacenters)
    }


async def floating_ip_list() -> dict:
    """Liste aller Floating IPs."""
    client = get_hcloud_client()
    floating_ips = client.floating_ips.get_all()
    return {
        "floating_ips": [
            {
                "id": f.id,
                "name": f.name,
                "ip": f.ip,
                "type": f.type,
                "server": f.server.name if f.server else None,
                "home_location": f.home_location.name if f.home_location else None,
                "blocked": f.blocked,
            }
            for f in floating_ips
        ],
        "count": len(floating_ips)
    }


async def primary_ip_list() -> dict:
    """Liste aller Primary IPs."""
    client = get_hcloud_client()
    primary_ips = client.primary_ips.get_all()
    return {
        "primary_ips": [
            {
                "id": p.id,
                "name": p.name,
                "ip": p.ip,
                "type": p.type,
                "datacenter": p.datacenter.name if p.datacenter else None,
                "auto_delete": p.auto_delete,
                "blocked": p.blocked,
            }
            for p in primary_ips
        ],
        "count": len(primary_ips)
    }


async def load_balancer_list() -> dict:
    """Liste aller Load Balancer."""
    client = get_hcloud_client()
    load_balancers = client.load_balancers.get_all()
    return {
        "load_balancers": [
            {
                "id": lb.id,
                "name": lb.name,
                "public_net": {
                    "ipv4": lb.public_net.ipv4.ip if lb.public_net and lb.public_net.ipv4 else None,
                    "ipv6": lb.public_net.ipv6.ip if lb.public_net and lb.public_net.ipv6 else None,
                },
                "load_balancer_type": lb.load_balancer_type.name if lb.load_balancer_type else None,
                "location": lb.location.name if lb.location else None,
                "services_count": len(lb.services) if lb.services else 0,
                "targets_count": len(lb.targets) if lb.targets else 0,
            }
            for lb in load_balancers
        ],
        "count": len(load_balancers)
    }


async def certificate_list() -> dict:
    """Liste aller Certificates."""
    client = get_hcloud_client()
    certificates = client.certificates.get_all()
    return {
        "certificates": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "domain_names": c.domain_names,
                "status": c.status.type if c.status else None,
                "not_valid_after": str(c.not_valid_after) if c.not_valid_after else None,
            }
            for c in certificates
        ],
        "count": len(certificates)
    }


async def placement_group_list() -> dict:
    """Liste aller Placement Groups."""
    client = get_hcloud_client()
    placement_groups = client.placement_groups.get_all()
    return {
        "placement_groups": [
            {
                "id": pg.id,
                "name": pg.name,
                "type": pg.type,
                "servers_count": len(pg.servers) if pg.servers else 0,
                "created": str(pg.created) if pg.created else None,
            }
            for pg in placement_groups
        ],
        "count": len(placement_groups)
    }


# Tool-Mapping
TOOL_FUNCTIONS = {
    "server_list": server_list,
    "server_info": server_info,
    "server_power": server_power,
    "firewall_list": firewall_list,
    "volume_list": volume_list,
    "network_list": network_list,
    "ssh_key_list": ssh_key_list,
    "image_list": image_list,
    "server_type_list": server_type_list,
    "location_list": location_list,
    "datacenter_list": datacenter_list,
    "floating_ip_list": floating_ip_list,
    "primary_ip_list": primary_ip_list,
    "load_balancer_list": load_balancer_list,
    "certificate_list": certificate_list,
    "placement_group_list": placement_group_list,
}


@router.get("/tools")
async def list_tools():
    """Liste aller verfügbaren CLI-Tools."""
    return {"tools": CLI_TOOLS}


@router.post("/execute")
async def execute_command(request: CommandRequest):
    """Führt ein CLI-Tool aus."""
    import time

    start_time = time.time()

    if request.command not in TOOL_FUNCTIONS:
        return {
            "success": False,
            "error": f"Tool '{request.command}' nicht gefunden. Verfügbar: {list(TOOL_FUNCTIONS.keys())}",
            "execution_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    tool_func = TOOL_FUNCTIONS[request.command]

    try:
        result = await tool_func(**request.args)
        execution_time = (time.time() - start_time) * 1000

        return {
            "success": True,
            "output": result,
            "execution_time_ms": round(execution_time, 2)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": round((time.time() - start_time) * 1000, 2)
        }
