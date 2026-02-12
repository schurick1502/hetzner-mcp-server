"""Health Check API Routes."""

from fastapi import APIRouter
import asyncio
import socket
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.servers import hcloud_server_list

router = APIRouter()


async def _tcp_check(host: str, port: int, timeout: float = 5.0) -> dict:
    """Perform a TCP connect check."""
    start = time.time()
    try:
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        await loop.run_in_executor(None, sock.connect, (host, port))
        elapsed = (time.time() - start) * 1000
        sock.close()
        return {"reachable": True, "response_ms": round(elapsed, 1), "port": port}
    except Exception:
        elapsed = (time.time() - start) * 1000
        return {"reachable": False, "response_ms": round(elapsed, 1), "port": port}


async def _check_server(server: dict) -> dict:
    """Check a single server's health."""
    ip = server.get("public_ipv4")
    name = server.get("name", "unknown")
    status = server.get("status", "unknown")

    if status != "running":
        return {
            "server": name,
            "ip": ip,
            "status": "off",
            "hetzner_status": status,
            "checks": [],
        }

    if not ip:
        return {
            "server": name,
            "ip": None,
            "status": "unknown",
            "hetzner_status": status,
            "checks": [],
        }

    # Run checks in parallel
    checks = await asyncio.gather(
        _tcp_check(ip, 80, timeout=5),
        _tcp_check(ip, 443, timeout=5),
        _tcp_check(ip, 22, timeout=5),
    )

    http_ok = checks[0]["reachable"]
    https_ok = checks[1]["reachable"]
    ssh_ok = checks[2]["reachable"]

    # Determine overall status
    if http_ok or https_ok:
        overall = "healthy"
    elif ssh_ok:
        overall = "degraded"
    else:
        overall = "down"

    best_response = min(
        (c["response_ms"] for c in checks if c["reachable"]),
        default=0,
    )

    return {
        "server": name,
        "ip": ip,
        "status": overall,
        "hetzner_status": status,
        "response_ms": best_response,
        "checks": [
            {"port": 80, "name": "HTTP", "reachable": http_ok, "response_ms": checks[0]["response_ms"]},
            {"port": 443, "name": "HTTPS", "reachable": https_ok, "response_ms": checks[1]["response_ms"]},
            {"port": 22, "name": "SSH", "reachable": ssh_ok, "response_ms": checks[2]["response_ms"]},
        ],
    }


@router.get("/")
async def health_checks():
    """Führt Health-Checks für alle Server durch."""
    result = await hcloud_server_list()
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Fehler beim Laden der Server")}

    servers = result.get("servers", [])
    checks = await asyncio.gather(*[_check_server(s) for s in servers])

    summary = {
        "healthy": sum(1 for c in checks if c["status"] == "healthy"),
        "degraded": sum(1 for c in checks if c["status"] == "degraded"),
        "down": sum(1 for c in checks if c["status"] == "down"),
        "off": sum(1 for c in checks if c["status"] == "off"),
    }

    return {
        "success": True,
        "data": {
            "checks": checks,
            "summary": summary,
            "total": len(checks),
        },
    }
