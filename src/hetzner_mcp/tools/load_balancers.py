"""Load Balancer-Management Tools für Hetzner Cloud."""

from typing import Optional
from hcloud.load_balancers.domain import (
    LoadBalancerService,
    LoadBalancerServiceHttp,
    LoadBalancerHealthCheck,
    LoadBalancerHealtCheckHttp,
    LoadBalancerTarget,
    LoadBalancerAlgorithm,
)
from ..config import get_client


async def hcloud_load_balancer_list() -> dict:
    """
    Listet alle Load Balancer im Projekt auf.

    Returns:
        Dictionary mit Anzahl und Load Balancer-Details
    """
    try:
        client = get_client()
        load_balancers = client.load_balancers.get_all()

        lb_list = []
        for lb in load_balancers:
            lb_list.append({
                "id": lb.id,
                "name": lb.name,
                "load_balancer_type": lb.load_balancer_type.name,
                "location": lb.location.name if lb.location else None,
                "public_ipv4": lb.public_net.ipv4.ip if lb.public_net and lb.public_net.ipv4 else None,
                "public_ipv6": str(lb.public_net.ipv6.ip) if lb.public_net and lb.public_net.ipv6 else None,
                "private_networks": [
                    {"network": net.network.name, "ip": net.ip}
                    for net in (lb.private_net or [])
                ],
                "algorithm": lb.algorithm.type if lb.algorithm else None,
                "services": len(lb.services),
                "targets": len(lb.targets),
                "created": lb.created.isoformat(),
                "labels": lb.labels,
            })

        return {
            "success": True,
            "count": len(lb_list),
            "load_balancers": lb_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Load Balancer: {str(e)}"
        }


async def hcloud_load_balancer_create(
    name: str,
    load_balancer_type: str,
    location: Optional[str] = None,
    network_zone: Optional[str] = None,
    labels: Optional[dict] = None,
    algorithm_type: str = "round_robin",
    public_interface: bool = True,
) -> dict:
    """
    Erstellt einen neuen Load Balancer.

    Args:
        name: Load Balancer Name
        load_balancer_type: Typ (lb11, lb21, lb31)
        location: Standort (optional, alternativ network_zone)
        network_zone: Netzwerk-Zone (eu-central, us-east, us-west)
        labels: Labels (optional)
        algorithm_type: round_robin, least_connections
        public_interface: Öffentliche IP zuweisen

    Returns:
        Details des erstellten Load Balancers
    """
    try:
        client = get_client()

        # Load Balancer-Typ abrufen
        lb_type = client.load_balancer_types.get_by_name(load_balancer_type)
        if not lb_type:
            return {
                "success": False,
                "error": f"Load Balancer-Typ '{load_balancer_type}' nicht gefunden"
            }

        # Location oder Network Zone
        loc = None
        if location:
            loc = client.locations.get_by_name(location)
            if not loc:
                return {
                    "success": False,
                    "error": f"Location '{location}' nicht gefunden"
                }

        # Algorithm
        algorithm = LoadBalancerAlgorithm(type=algorithm_type)

        # Load Balancer erstellen
        response = client.load_balancers.create(
            name=name,
            load_balancer_type=lb_type,
            location=loc,
            network_zone=network_zone,
            labels=labels,
            algorithm=algorithm,
            public_interface=public_interface,
        )

        lb = response.load_balancer
        action = response.action

        action.wait_until_finished()

        return {
            "success": True,
            "load_balancer": {
                "id": lb.id,
                "name": lb.name,
                "type": lb.load_balancer_type.name,
                "public_ipv4": lb.public_net.ipv4.ip if lb.public_net and lb.public_net.ipv4 else None,
                "public_ipv6": str(lb.public_net.ipv6.ip) if lb.public_net and lb.public_net.ipv6 else None,
            },
            "message": f"Load Balancer '{name}' erstellt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen des Load Balancers: {str(e)}"
        }


async def hcloud_load_balancer_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht einen Load Balancer.

    Args:
        identifier: Load Balancer-ID oder Name
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

        try:
            lb_id = int(identifier)
            lb = client.load_balancers.get_by_id(lb_id)
        except ValueError:
            lb = client.load_balancers.get_by_name(identifier)

        if not lb:
            return {
                "success": False,
                "error": f"Load Balancer '{identifier}' nicht gefunden"
            }

        lb_name = lb.name
        lb_id = lb.id

        client.load_balancers.delete(lb)

        return {
            "success": True,
            "message": f"Load Balancer '{lb_name}' (ID: {lb_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen des Load Balancers: {str(e)}"
        }


async def hcloud_load_balancer_add_service(
    identifier: str,
    protocol: str,
    listen_port: int,
    destination_port: int,
    proxyprotocol: bool = False,
    http_sticky_sessions: bool = False,
    http_redirect_http: bool = False,
    health_check_protocol: str = "tcp",
    health_check_port: int = None,
    health_check_interval: int = 15,
    health_check_timeout: int = 10,
    health_check_retries: int = 3,
) -> dict:
    """
    Fügt einen Service zu einem Load Balancer hinzu.

    Args:
        identifier: Load Balancer-ID oder Name
        protocol: tcp, http, https
        listen_port: Port auf dem Load Balancer
        destination_port: Port auf den Targets
        proxyprotocol: Proxy Protocol aktivieren
        http_sticky_sessions: Sticky Sessions (nur HTTP/HTTPS)
        http_redirect_http: HTTP zu HTTPS redirect
        health_check_protocol: tcp, http, https
        health_check_port: Port für Health Check
        health_check_interval: Intervall in Sekunden
        health_check_timeout: Timeout in Sekunden
        health_check_retries: Anzahl Wiederholungen

    Returns:
        Status der Aktion
    """
    try:
        client = get_client()

        try:
            lb_id = int(identifier)
            lb = client.load_balancers.get_by_id(lb_id)
        except ValueError:
            lb = client.load_balancers.get_by_name(identifier)

        if not lb:
            return {
                "success": False,
                "error": f"Load Balancer '{identifier}' nicht gefunden"
            }

        # Health Check
        health_check = LoadBalancerHealthCheck(
            protocol=health_check_protocol,
            port=health_check_port or destination_port,
            interval=health_check_interval,
            timeout=health_check_timeout,
            retries=health_check_retries,
        )

        # HTTP-spezifische Einstellungen
        http = None
        if protocol in ["http", "https"]:
            http = LoadBalancerServiceHttp(
                sticky_sessions=http_sticky_sessions,
                redirect_http=http_redirect_http,
            )

        service = LoadBalancerService(
            protocol=protocol,
            listen_port=listen_port,
            destination_port=destination_port,
            proxyprotocol=proxyprotocol,
            http=http,
            health_check=health_check,
        )

        actions = client.load_balancers.add_service(lb, service)
        for action in actions:
            action.wait_until_finished()

        return {
            "success": True,
            "message": f"Service (Port {listen_port}) zu Load Balancer '{lb.name}' hinzugefügt",
            "load_balancer_id": lb.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Hinzufügen des Service: {str(e)}"
        }


async def hcloud_load_balancer_delete_service(
    identifier: str,
    listen_port: int
) -> dict:
    """
    Entfernt einen Service von einem Load Balancer.

    Args:
        identifier: Load Balancer-ID oder Name
        listen_port: Port des zu entfernenden Service

    Returns:
        Status der Aktion
    """
    try:
        client = get_client()

        try:
            lb_id = int(identifier)
            lb = client.load_balancers.get_by_id(lb_id)
        except ValueError:
            lb = client.load_balancers.get_by_name(identifier)

        if not lb:
            return {
                "success": False,
                "error": f"Load Balancer '{identifier}' nicht gefunden"
            }

        # Service finden
        service = None
        for svc in lb.services:
            if svc.listen_port == listen_port:
                service = svc
                break

        if not service:
            return {
                "success": False,
                "error": f"Service auf Port {listen_port} nicht gefunden"
            }

        actions = client.load_balancers.delete_service(lb, service)
        for action in actions:
            action.wait_until_finished()

        return {
            "success": True,
            "message": f"Service (Port {listen_port}) von Load Balancer '{lb.name}' entfernt",
            "load_balancer_id": lb.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Entfernen des Service: {str(e)}"
        }


async def hcloud_load_balancer_add_target(
    identifier: str,
    target_type: str,
    server: Optional[str] = None,
    label_selector: Optional[str] = None,
    ip: Optional[str] = None,
    use_private_ip: bool = False,
) -> dict:
    """
    Fügt ein Target zu einem Load Balancer hinzu.

    Args:
        identifier: Load Balancer-ID oder Name
        target_type: server, label_selector, ip
        server: Server-Name oder ID (bei target_type=server)
        label_selector: Label-Selector (bei target_type=label_selector)
        ip: IP-Adresse (bei target_type=ip)
        use_private_ip: Private IP verwenden

    Returns:
        Status der Aktion
    """
    try:
        client = get_client()

        try:
            lb_id = int(identifier)
            lb = client.load_balancers.get_by_id(lb_id)
        except ValueError:
            lb = client.load_balancers.get_by_name(identifier)

        if not lb:
            return {
                "success": False,
                "error": f"Load Balancer '{identifier}' nicht gefunden"
            }

        target = None

        if target_type == "server":
            if not server:
                return {"success": False, "error": "server Parameter erforderlich"}

            try:
                server_id = int(server)
                server_obj = client.servers.get_by_id(server_id)
            except ValueError:
                server_obj = client.servers.get_by_name(server)

            if not server_obj:
                return {"success": False, "error": f"Server '{server}' nicht gefunden"}

            target = LoadBalancerTarget(
                type="server",
                server=server_obj,
                use_private_ip=use_private_ip
            )

        elif target_type == "label_selector":
            if not label_selector:
                return {"success": False, "error": "label_selector Parameter erforderlich"}

            target = LoadBalancerTarget(
                type="label_selector",
                label_selector=label_selector,
                use_private_ip=use_private_ip
            )

        elif target_type == "ip":
            if not ip:
                return {"success": False, "error": "ip Parameter erforderlich"}

            target = LoadBalancerTarget(type="ip", ip=ip)

        else:
            return {
                "success": False,
                "error": f"Ungültiger target_type: {target_type}"
            }

        actions = client.load_balancers.add_target(lb, target)
        for action in actions:
            action.wait_until_finished()

        return {
            "success": True,
            "message": f"Target zu Load Balancer '{lb.name}' hinzugefügt",
            "load_balancer_id": lb.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Hinzufügen des Targets: {str(e)}"
        }


async def hcloud_load_balancer_remove_target(
    identifier: str,
    target_type: str,
    server: Optional[str] = None,
    label_selector: Optional[str] = None,
    ip: Optional[str] = None,
) -> dict:
    """
    Entfernt ein Target von einem Load Balancer.

    Args:
        identifier: Load Balancer-ID oder Name
        target_type: server, label_selector, ip
        server: Server-Name oder ID
        label_selector: Label-Selector
        ip: IP-Adresse

    Returns:
        Status der Aktion
    """
    try:
        client = get_client()

        try:
            lb_id = int(identifier)
            lb = client.load_balancers.get_by_id(lb_id)
        except ValueError:
            lb = client.load_balancers.get_by_name(identifier)

        if not lb:
            return {
                "success": False,
                "error": f"Load Balancer '{identifier}' nicht gefunden"
            }

        target = None

        if target_type == "server":
            try:
                server_id = int(server)
                server_obj = client.servers.get_by_id(server_id)
            except ValueError:
                server_obj = client.servers.get_by_name(server)

            if not server_obj:
                return {"success": False, "error": f"Server '{server}' nicht gefunden"}

            target = LoadBalancerTarget(type="server", server=server_obj)

        elif target_type == "label_selector":
            target = LoadBalancerTarget(type="label_selector", label_selector=label_selector)

        elif target_type == "ip":
            target = LoadBalancerTarget(type="ip", ip=ip)

        actions = client.load_balancers.remove_target(lb, target)
        for action in actions:
            action.wait_until_finished()

        return {
            "success": True,
            "message": f"Target von Load Balancer '{lb.name}' entfernt",
            "load_balancer_id": lb.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Entfernen des Targets: {str(e)}"
        }


async def hcloud_load_balancer_change_algorithm(
    identifier: str,
    algorithm_type: str
) -> dict:
    """
    Ändert den Algorithmus eines Load Balancers.

    Args:
        identifier: Load Balancer-ID oder Name
        algorithm_type: round_robin, least_connections

    Returns:
        Status der Änderung
    """
    try:
        client = get_client()

        try:
            lb_id = int(identifier)
            lb = client.load_balancers.get_by_id(lb_id)
        except ValueError:
            lb = client.load_balancers.get_by_name(identifier)

        if not lb:
            return {
                "success": False,
                "error": f"Load Balancer '{identifier}' nicht gefunden"
            }

        algorithm = LoadBalancerAlgorithm(type=algorithm_type)
        action = client.load_balancers.change_algorithm(lb, algorithm)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Algorithmus für Load Balancer '{lb.name}' auf '{algorithm_type}' geändert",
            "load_balancer_id": lb.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Ändern des Algorithmus: {str(e)}"
        }


async def hcloud_load_balancer_update(
    identifier: str,
    name: Optional[str] = None,
    labels: Optional[dict] = None
) -> dict:
    """
    Aktualisiert Load Balancer-Metadaten.

    Args:
        identifier: Load Balancer-ID oder Name
        name: Neuer Name (optional)
        labels: Neue Labels (optional)

    Returns:
        Aktualisierte Details
    """
    try:
        client = get_client()

        try:
            lb_id = int(identifier)
            lb = client.load_balancers.get_by_id(lb_id)
        except ValueError:
            lb = client.load_balancers.get_by_name(identifier)

        if not lb:
            return {
                "success": False,
                "error": f"Load Balancer '{identifier}' nicht gefunden"
            }

        lb = client.load_balancers.update(lb, name=name, labels=labels)

        return {
            "success": True,
            "message": "Load Balancer aktualisiert",
            "load_balancer": {
                "id": lb.id,
                "name": lb.name,
                "labels": lb.labels
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Aktualisieren des Load Balancers: {str(e)}"
        }
