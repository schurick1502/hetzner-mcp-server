"""Firewall-Management Tools für Hetzner Cloud."""

from typing import Optional
from hcloud.firewalls.domain import FirewallRule, FirewallResource
from ..config import get_client


async def hcloud_firewall_list() -> dict:
    """
    Listet alle Firewalls im Hetzner Cloud Projekt auf.

    Returns:
        Dictionary mit Anzahl und Firewall-Details
    """
    try:
        client = get_client()
        firewalls = client.firewalls.get_all()

        firewall_list = []
        for fw in firewalls:
            firewall_list.append({
                "id": fw.id,
                "name": fw.name,
                "rules_count": len(fw.rules),
                "applied_to": [
                    {
                        "type": res.type,
                        "server": res.server.name if res.server else None,
                    }
                    for res in fw.applied_to
                ],
                "created": fw.created.isoformat(),
                "labels": fw.labels,
            })

        return {
            "success": True,
            "count": len(firewall_list),
            "firewalls": firewall_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Firewalls: {str(e)}"
        }


async def hcloud_firewall_create(
    name: str,
    rules: Optional[list[dict]] = None,
    labels: Optional[dict] = None,
) -> dict:
    """
    Erstellt eine neue Firewall.

    Args:
        name: Firewall-Name
        rules: Liste von Firewall-Regeln (optional). Jede Regel enthält:
            - direction: "in" oder "out"
            - protocol: "tcp", "udp", "icmp", "esp", "gre"
            - source_ips: Liste von IP-Bereichen (bei direction=in)
            - destination_ips: Liste von IP-Bereichen (bei direction=out)
            - port: Port oder Port-Range (z.B. "80" oder "8000-9000", nur bei tcp/udp)
        labels: Dictionary mit Labels (optional)

    Returns:
        Details der erstellten Firewall

    Beispiel-Regel:
        {
            "direction": "in",
            "protocol": "tcp",
            "source_ips": ["0.0.0.0/0", "::/0"],
            "port": "443"
        }
    """
    try:
        client = get_client()

        # Regeln konvertieren
        rule_objects = []
        if rules:
            for rule in rules:
                try:
                    rule_obj = FirewallRule(
                        direction=rule["direction"],
                        protocol=rule["protocol"],
                        source_ips=rule.get("source_ips", []),
                        destination_ips=rule.get("destination_ips", []),
                        port=rule.get("port"),
                    )
                    rule_objects.append(rule_obj)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Ungültige Regel: {str(e)}"
                    }

        # Firewall erstellen
        firewall = client.firewalls.create(
            name=name,
            rules=rule_objects if rule_objects else [],
            labels=labels,
        )

        return {
            "success": True,
            "firewall": {
                "id": firewall.firewall.id,
                "name": firewall.firewall.name,
                "rules_count": len(firewall.firewall.rules),
            },
            "message": f"Firewall '{name}' wurde erstellt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen der Firewall: {str(e)}"
        }


async def hcloud_firewall_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht eine Firewall (destruktive Aktion!).

    Args:
        identifier: Firewall-ID oder Name
        force: Muss True sein zur Bestätigung

    Returns:
        Status der Löschoperation
    """
    if not force:
        return {
            "success": False,
            "error": "Zum Löschen muss force=True gesetzt werden"
        }

    try:
        client = get_client()

        # Firewall finden
        try:
            fw_id = int(identifier)
            firewall = client.firewalls.get_by_id(fw_id)
        except ValueError:
            firewall = client.firewalls.get_by_name(identifier)

        if not firewall:
            return {
                "success": False,
                "error": f"Firewall '{identifier}' nicht gefunden"
            }

        fw_name = firewall.name
        fw_id = firewall.id

        # Firewall löschen
        client.firewalls.delete(firewall)

        return {
            "success": True,
            "message": f"Firewall '{fw_name}' (ID: {fw_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen der Firewall: {str(e)}"
        }


async def hcloud_firewall_add_rule(
    identifier: str,
    direction: str,
    protocol: str,
    source_ips: Optional[list[str]] = None,
    destination_ips: Optional[list[str]] = None,
    port: Optional[str] = None,
) -> dict:
    """
    Fügt eine neue Regel zu einer Firewall hinzu.

    Args:
        identifier: Firewall-ID oder Name
        direction: "in" für eingehend oder "out" für ausgehend
        protocol: "tcp", "udp", "icmp", "esp", "gre"
        source_ips: Liste von Quell-IPs/Bereichen (bei direction=in)
        destination_ips: Liste von Ziel-IPs/Bereichen (bei direction=out)
        port: Port oder Port-Range (nur bei tcp/udp, z.B. "80" oder "8000-9000")

    Returns:
        Status und aktualisierte Firewall-Details
    """
    if direction not in ["in", "out"]:
        return {
            "success": False,
            "error": "direction muss 'in' oder 'out' sein"
        }

    if protocol not in ["tcp", "udp", "icmp", "esp", "gre"]:
        return {
            "success": False,
            "error": "protocol muss 'tcp', 'udp', 'icmp', 'esp' oder 'gre' sein"
        }

    try:
        client = get_client()

        # Firewall finden
        try:
            fw_id = int(identifier)
            firewall = client.firewalls.get_by_id(fw_id)
        except ValueError:
            firewall = client.firewalls.get_by_name(identifier)

        if not firewall:
            return {
                "success": False,
                "error": f"Firewall '{identifier}' nicht gefunden"
            }

        # Neue Regel erstellen
        new_rule = FirewallRule(
            direction=direction,
            protocol=protocol,
            source_ips=source_ips or [],
            destination_ips=destination_ips or [],
            port=port,
        )

        # Bestehende Regeln + neue Regel
        rules = list(firewall.rules) + [new_rule]

        # Regeln setzen
        actions = client.firewalls.set_rules(firewall, rules)
        for action in actions:
            action.wait_until_finished()

        return {
            "success": True,
            "message": f"Regel zu Firewall '{firewall.name}' hinzugefügt",
            "firewall_id": firewall.id,
            "rules_count": len(rules)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Hinzufügen der Regel: {str(e)}"
        }


async def hcloud_firewall_apply(identifier: str, server: str) -> dict:
    """
    Wendet eine Firewall auf einen Server an.

    Args:
        identifier: Firewall-ID oder Name
        server: Server-ID oder Name

    Returns:
        Status der Anwendung
    """
    try:
        client = get_client()

        # Firewall finden
        try:
            fw_id = int(identifier)
            firewall = client.firewalls.get_by_id(fw_id)
        except ValueError:
            firewall = client.firewalls.get_by_name(identifier)

        if not firewall:
            return {
                "success": False,
                "error": f"Firewall '{identifier}' nicht gefunden"
            }

        # Server finden
        try:
            server_id = int(server)
            server_obj = client.servers.get_by_id(server_id)
        except ValueError:
            server_obj = client.servers.get_by_name(server)

        if not server_obj:
            return {
                "success": False,
                "error": f"Server '{server}' nicht gefunden"
            }

        # Firewall anwenden
        resource = FirewallResource(type="server", server=server_obj)
        actions = client.firewalls.apply_to_resources(firewall, [resource])

        for action in actions:
            action.wait_until_finished()

        return {
            "success": True,
            "message": f"Firewall '{firewall.name}' auf Server '{server_obj.name}' angewendet",
            "firewall_id": firewall.id,
            "server_id": server_obj.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Anwenden der Firewall: {str(e)}"
        }


async def hcloud_firewall_remove_from_server(identifier: str, server: str) -> dict:
    """
    Entfernt eine Firewall von einem Server.

    Args:
        identifier: Firewall-ID oder Name
        server: Server-ID oder Name

    Returns:
        Status der Entfernung
    """
    try:
        client = get_client()

        # Firewall finden
        try:
            fw_id = int(identifier)
            firewall = client.firewalls.get_by_id(fw_id)
        except ValueError:
            firewall = client.firewalls.get_by_name(identifier)

        if not firewall:
            return {
                "success": False,
                "error": f"Firewall '{identifier}' nicht gefunden"
            }

        # Server finden
        try:
            server_id = int(server)
            server_obj = client.servers.get_by_id(server_id)
        except ValueError:
            server_obj = client.servers.get_by_name(server)

        if not server_obj:
            return {
                "success": False,
                "error": f"Server '{server}' nicht gefunden"
            }

        # Firewall entfernen
        resource = FirewallResource(type="server", server=server_obj)
        actions = client.firewalls.remove_from_resources(firewall, [resource])

        for action in actions:
            action.wait_until_finished()

        return {
            "success": True,
            "message": f"Firewall '{firewall.name}' von Server '{server_obj.name}' entfernt",
            "firewall_id": firewall.id,
            "server_id": server_obj.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Entfernen der Firewall: {str(e)}"
        }
