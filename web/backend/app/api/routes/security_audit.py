"""Security Audit API Routes."""

from fastapi import APIRouter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.hetzner_mcp.tools.firewalls import hcloud_firewall_list
from src.hetzner_mcp.tools.servers import hcloud_server_list

router = APIRouter()

# Ports die als gefährlich gelten wenn sie für 0.0.0.0/0 offen sind
DANGEROUS_PORTS = {
    "22": "SSH - Brute-Force-Angriffe möglich",
    "3306": "MySQL - Datenbank sollte nicht öffentlich erreichbar sein",
    "5432": "PostgreSQL - Datenbank sollte nicht öffentlich erreichbar sein",
    "6379": "Redis - Kein Auth standardmäßig, sehr gefährlich",
    "27017": "MongoDB - Datenbank sollte nicht öffentlich erreichbar sein",
    "9200": "Elasticsearch - Sollte nicht öffentlich erreichbar sein",
    "11211": "Memcached - Sollte nicht öffentlich erreichbar sein",
    "2375": "Docker API (unverschlüsselt) - Kritische Sicherheitslücke",
    "2376": "Docker API - Sollte nur intern erreichbar sein",
    "8080": "HTTP Alt - Oft Debug/Admin-Interfaces",
    "23": "Telnet - Unverschlüsselt, veraltet",
    "21": "FTP - Unverschlüsselt, veraltet",
}


def _is_open_to_all(ips: list[str]) -> bool:
    """Check if IPs include 0.0.0.0/0 or ::/0."""
    if not ips:
        return False
    return "0.0.0.0/0" in ips or "::/0" in ips


def _port_in_range(port_spec: str, check_port: str) -> bool:
    """Check if a specific port is within a port specification (e.g. '80', '8000-9000')."""
    if not port_spec:
        return True  # No port = all ports
    if "-" in port_spec:
        start, end = port_spec.split("-", 1)
        try:
            return int(start) <= int(check_port) <= int(end)
        except ValueError:
            return False
    return port_spec == check_port


def _analyze_firewalls(firewalls: list, servers: list) -> list[dict]:
    """Analyze firewalls and return security findings."""
    findings = []

    # Sammle alle Server die einer Firewall zugeordnet sind
    protected_servers = set()
    for fw in firewalls:
        for applied in (fw.get("applied_to") or []):
            if applied.get("server"):
                protected_servers.add(applied["server"])

    # Check: Server ohne Firewall
    for server in servers:
        if server["name"] not in protected_servers and server.get("status") == "running":
            findings.append({
                "severity": "critical",
                "category": "Server",
                "title": f"Server '{server['name']}' hat keine Firewall",
                "description": "Laufende Server sollten immer durch eine Firewall geschützt sein.",
                "resource": server["name"],
                "recommendation": "Erstelle eine Firewall und wende sie auf diesen Server an.",
            })

    for fw in firewalls:
        rules = fw.get("rules") or []
        has_inbound = any(r["direction"] == "in" for r in rules)
        has_outbound = any(r["direction"] == "out" for r in rules)

        # Check: Firewall ohne Regeln
        if len(rules) == 0:
            findings.append({
                "severity": "warning",
                "category": "Firewall",
                "title": f"Firewall '{fw['name']}' hat keine Regeln",
                "description": "Eine Firewall ohne Regeln blockiert standardmäßig allen Traffic, bietet aber keinen definierten Schutz.",
                "resource": fw["name"],
                "recommendation": "Definiere explizite Regeln für erlaubten Traffic.",
            })

        # Check: Keine Outbound-Regeln
        if has_inbound and not has_outbound:
            findings.append({
                "severity": "info",
                "category": "Firewall",
                "title": f"Firewall '{fw['name']}' hat keine Outbound-Regeln",
                "description": "Ohne Outbound-Regeln ist ausgehender Traffic nicht eingeschränkt. Dies kann bei einem kompromittierten Server zum Problem werden.",
                "resource": fw["name"],
                "recommendation": "Erwäge Outbound-Regeln um ausgehenden Traffic einzuschränken.",
            })

        # Check: Firewall nicht auf Server angewendet
        applied_to = fw.get("applied_to") or []
        if len(applied_to) == 0 and len(rules) > 0:
            findings.append({
                "severity": "warning",
                "category": "Firewall",
                "title": f"Firewall '{fw['name']}' ist keinem Server zugeordnet",
                "description": "Diese Firewall hat Regeln, ist aber keinem Server zugewiesen und damit wirkungslos.",
                "resource": fw["name"],
                "recommendation": "Weise die Firewall einem Server zu oder lösche sie.",
            })

        # Check: Gefährliche Port-Regeln
        for rule in rules:
            if rule["direction"] != "in":
                continue

            source_ips = rule.get("source_ips") or []
            is_open = _is_open_to_all(source_ips)

            if not is_open:
                continue

            port = rule.get("port")
            protocol = rule.get("protocol", "")

            # Check: Alle Ports offen
            if not port and protocol in ("tcp", "udp"):
                findings.append({
                    "severity": "critical",
                    "category": "Firewall",
                    "title": f"Firewall '{fw['name']}': Alle {protocol.upper()}-Ports offen für alle IPs",
                    "description": f"Regel erlaubt {protocol.upper()}-Traffic auf allen Ports von 0.0.0.0/0. Dies ist extrem unsicher.",
                    "resource": fw["name"],
                    "recommendation": "Beschränke die Regel auf spezifische Ports.",
                })
                continue

            # Check: Spezifische gefährliche Ports
            if port:
                for dangerous_port, desc in DANGEROUS_PORTS.items():
                    if _port_in_range(port, dangerous_port):
                        severity = "critical" if dangerous_port in ("2375", "6379", "27017", "23") else "warning"
                        findings.append({
                            "severity": severity,
                            "category": "Firewall",
                            "title": f"Firewall '{fw['name']}': Port {dangerous_port} offen für alle IPs",
                            "description": f"{desc}. Port {dangerous_port}/{protocol.upper()} ist für 0.0.0.0/0 erreichbar.",
                            "resource": fw["name"],
                            "recommendation": f"Beschränke den Zugriff auf Port {dangerous_port} auf spezifische IP-Adressen.",
                        })

    return findings


def _calculate_score(findings: list[dict]) -> int:
    """Calculate security score (0-100) based on findings."""
    if not findings:
        return 100

    penalty = 0
    for f in findings:
        if f["severity"] == "critical":
            penalty += 20
        elif f["severity"] == "warning":
            penalty += 10
        elif f["severity"] == "info":
            penalty += 3

    return max(0, 100 - penalty)


@router.get("/audit")
async def security_audit():
    """Führt einen Security-Audit durch."""
    fw_result = await hcloud_firewall_list()
    srv_result = await hcloud_server_list()

    firewalls = fw_result.get("firewalls", []) if fw_result.get("success") else []
    servers = srv_result.get("servers", []) if srv_result.get("success") else []

    findings = _analyze_firewalls(firewalls, servers)

    # Sortiere nach Severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: severity_order.get(f["severity"], 3))

    score = _calculate_score(findings)

    summary = {
        "critical": sum(1 for f in findings if f["severity"] == "critical"),
        "warning": sum(1 for f in findings if f["severity"] == "warning"),
        "info": sum(1 for f in findings if f["severity"] == "info"),
    }

    return {
        "success": True,
        "data": {
            "score": score,
            "summary": summary,
            "findings": findings,
            "total_firewalls": len(firewalls),
            "total_servers": len(servers),
            "protected_servers": len(set(
                a["server"]
                for fw in firewalls
                for a in (fw.get("applied_to") or [])
                if a.get("server")
            )),
        },
    }
