"""Topology API Route - Aggregates all resources and relationships."""

from fastapi import APIRouter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.servers import hcloud_server_list
from src.hetzner_mcp.tools.firewalls import hcloud_firewall_list
from src.hetzner_mcp.tools.volumes import hcloud_volume_list
from src.hetzner_mcp.tools.networks import hcloud_network_list
from src.hetzner_mcp.tools.load_balancers import hcloud_load_balancer_list

router = APIRouter()


@router.get("/")
async def get_topology():
    """Aggregiert alle Ressourcen und deren Beziehungen."""
    servers_result = await hcloud_server_list()
    firewalls_result = await hcloud_firewall_list()
    volumes_result = await hcloud_volume_list()
    networks_result = await hcloud_network_list()
    lb_result = await hcloud_load_balancer_list()

    nodes = []
    edges = []
    server_names = set()

    # Server-Nodes
    if servers_result.get("success"):
        for srv in servers_result.get("servers", []):
            server_names.add(srv["name"])
            nodes.append({
                "id": f"server-{srv['name']}",
                "type": "server",
                "name": srv["name"],
                "metadata": {
                    "status": srv.get("status", ""),
                    "server_type": srv.get("server_type", ""),
                    "location": srv.get("location", ""),
                    "ipv4": srv.get("public_ipv4", ""),
                },
            })

    # Firewall-Nodes + Edges
    if firewalls_result.get("success"):
        for fw in firewalls_result.get("firewalls", []):
            nodes.append({
                "id": f"firewall-{fw['name']}",
                "type": "firewall",
                "name": fw["name"],
                "metadata": {
                    "rules_count": fw.get("rules_count", 0),
                },
            })
            for applied in fw.get("applied_to", []):
                server_name = applied.get("server")
                if server_name and server_name in server_names:
                    edges.append({
                        "from": f"firewall-{fw['name']}",
                        "to": f"server-{server_name}",
                        "type": "firewall",
                    })

    # Volume-Nodes + Edges
    if volumes_result.get("success"):
        for vol in volumes_result.get("volumes", []):
            nodes.append({
                "id": f"volume-{vol['name']}",
                "type": "volume",
                "name": vol["name"],
                "metadata": {
                    "size": vol.get("size", 0),
                    "format": vol.get("format", ""),
                },
            })
            server_name = vol.get("server")
            if server_name and server_name in server_names:
                edges.append({
                    "from": f"volume-{vol['name']}",
                    "to": f"server-{server_name}",
                    "type": "volume",
                })

    # Network-Nodes + Edges
    if networks_result.get("success"):
        for net in networks_result.get("networks", []):
            nodes.append({
                "id": f"network-{net['name']}",
                "type": "network",
                "name": net["name"],
                "metadata": {
                    "ip_range": net.get("ip_range", ""),
                    "subnets": len(net.get("subnets", [])),
                },
            })
            for srv in net.get("servers", []):
                srv_name = str(srv)
                if srv_name in server_names:
                    edges.append({
                        "from": f"network-{net['name']}",
                        "to": f"server-{srv_name}",
                        "type": "network",
                    })

    # Load Balancer-Nodes + Edges
    if lb_result.get("success"):
        for lb in lb_result.get("load_balancers", []):
            nodes.append({
                "id": f"lb-{lb['name']}",
                "type": "load_balancer",
                "name": lb["name"],
                "metadata": {
                    "type": lb.get("load_balancer_type", "lb11"),
                    "algorithm": lb.get("algorithm", ""),
                    "public_ip": lb.get("public_ip", ""),
                },
            })
            for target in lb.get("targets", []):
                if target.get("type") == "server":
                    srv_name = target.get("server", {})
                    if isinstance(srv_name, dict):
                        srv_name = srv_name.get("name", "")
                    if srv_name and srv_name in server_names:
                        edges.append({
                            "from": f"lb-{lb['name']}",
                            "to": f"server-{srv_name}",
                            "type": "lb_target",
                        })

    return {
        "success": True,
        "data": {
            "nodes": nodes,
            "edges": edges,
            "counts": {
                "servers": len([n for n in nodes if n["type"] == "server"]),
                "firewalls": len([n for n in nodes if n["type"] == "firewall"]),
                "volumes": len([n for n in nodes if n["type"] == "volume"]),
                "networks": len([n for n in nodes if n["type"] == "network"]),
                "load_balancers": len([n for n in nodes if n["type"] == "load_balancer"]),
            },
        },
    }
