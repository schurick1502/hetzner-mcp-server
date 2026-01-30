"""Netzwerk-Management Tools für Hetzner Cloud."""

from typing import Optional
from hcloud.networks.domain import NetworkSubnet
from ..config import get_client


async def hcloud_network_list() -> dict:
    """
    Listet alle privaten Netzwerke im Hetzner Cloud Projekt auf.

    Returns:
        Dictionary mit Anzahl und Netzwerk-Details
    """
    try:
        client = get_client()
        networks = client.networks.get_all()

        network_list = []
        for net in networks:
            network_list.append({
                "id": net.id,
                "name": net.name,
                "ip_range": net.ip_range,
                "subnets": [
                    {
                        "type": subnet.type,
                        "ip_range": subnet.ip_range,
                        "network_zone": subnet.network_zone,
                        "gateway": subnet.gateway,
                    }
                    for subnet in net.subnets
                ],
                "servers": [server.name for server in net.servers],
                "created": net.created.isoformat(),
                "labels": net.labels,
            })

        return {
            "success": True,
            "count": len(network_list),
            "networks": network_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Netzwerke: {str(e)}"
        }


async def hcloud_network_create(
    name: str,
    ip_range: str,
    labels: Optional[dict] = None,
) -> dict:
    """
    Erstellt ein neues privates Netzwerk.

    Args:
        name: Netzwerk-Name
        ip_range: IP-Bereich im CIDR-Format (z.B. 10.0.0.0/16)
        labels: Dictionary mit Labels (optional)

    Returns:
        Details des erstellten Netzwerks
    """
    try:
        client = get_client()

        # Netzwerk erstellen
        network = client.networks.create(
            name=name,
            ip_range=ip_range,
            labels=labels,
        )

        return {
            "success": True,
            "network": {
                "id": network.network.id,
                "name": network.network.name,
                "ip_range": network.network.ip_range,
            },
            "message": f"Netzwerk '{name}' mit IP-Bereich {ip_range} wurde erstellt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen des Netzwerks: {str(e)}"
        }


async def hcloud_network_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht ein privates Netzwerk (destruktive Aktion!).

    Args:
        identifier: Netzwerk-ID oder Name
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

        # Netzwerk finden
        try:
            net_id = int(identifier)
            network = client.networks.get_by_id(net_id)
        except ValueError:
            network = client.networks.get_by_name(identifier)

        if not network:
            return {
                "success": False,
                "error": f"Netzwerk '{identifier}' nicht gefunden"
            }

        net_name = network.name
        net_id = network.id

        # Netzwerk löschen
        client.networks.delete(network)

        return {
            "success": True,
            "message": f"Netzwerk '{net_name}' (ID: {net_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen des Netzwerks: {str(e)}"
        }


async def hcloud_network_add_subnet(
    identifier: str,
    ip_range: str,
    network_zone: str,
    subnet_type: str = "cloud",
) -> dict:
    """
    Fügt ein Subnet zu einem Netzwerk hinzu.

    Args:
        identifier: Netzwerk-ID oder Name
        ip_range: IP-Bereich des Subnets im CIDR-Format (z.B. 10.0.1.0/24)
        network_zone: Netzwerk-Zone (eu-central, us-east, us-west)
        subnet_type: Typ des Subnets ("cloud", "server", "vswitch")

    Returns:
        Status und Details
    """
    try:
        client = get_client()

        # Netzwerk finden
        try:
            net_id = int(identifier)
            network = client.networks.get_by_id(net_id)
        except ValueError:
            network = client.networks.get_by_name(identifier)

        if not network:
            return {
                "success": False,
                "error": f"Netzwerk '{identifier}' nicht gefunden"
            }

        # Subnet erstellen
        subnet = NetworkSubnet(
            ip_range=ip_range,
            type=subnet_type,
            network_zone=network_zone,
        )

        # Subnet hinzufügen
        action = client.networks.add_subnet(network, subnet)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Subnet {ip_range} zu Netzwerk '{network.name}' hinzugefügt",
            "network_id": network.id,
            "subnet": {
                "ip_range": ip_range,
                "type": subnet_type,
                "network_zone": network_zone,
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Hinzufügen des Subnets: {str(e)}"
        }


async def hcloud_server_attach_network(
    server: str,
    network: str,
    ip: Optional[str] = None,
    alias_ips: Optional[list[str]] = None,
) -> dict:
    """
    Verbindet einen Server mit einem privaten Netzwerk.

    Args:
        server: Server-ID oder Name
        network: Netzwerk-ID oder Name
        ip: Gewünschte IP-Adresse im Netzwerk (optional, wird automatisch zugewiesen)
        alias_ips: Liste von Alias-IP-Adressen (optional)

    Returns:
        Status und zugewiesene IP
    """
    try:
        client = get_client()

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

        # Netzwerk finden
        try:
            net_id = int(network)
            network_obj = client.networks.get_by_id(net_id)
        except ValueError:
            network_obj = client.networks.get_by_name(network)

        if not network_obj:
            return {
                "success": False,
                "error": f"Netzwerk '{network}' nicht gefunden"
            }

        # Server ans Netzwerk anhängen
        action = client.servers.attach_to_network(
            server_obj,
            network_obj,
            ip=ip,
            alias_ips=alias_ips,
        )
        action.wait_until_finished()

        # Server neu abrufen für aktualisierte Netzwerk-Infos
        server_obj = client.servers.get_by_id(server_obj.id)

        # IP-Adresse finden
        assigned_ip = None
        for private_net in server_obj.private_net:
            if private_net.network.id == network_obj.id:
                assigned_ip = private_net.ip
                break

        return {
            "success": True,
            "message": f"Server '{server_obj.name}' mit Netzwerk '{network_obj.name}' verbunden",
            "server_id": server_obj.id,
            "network_id": network_obj.id,
            "assigned_ip": assigned_ip,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Verbinden des Servers mit dem Netzwerk: {str(e)}"
        }


async def hcloud_server_detach_network(server: str, network: str) -> dict:
    """
    Trennt einen Server von einem privaten Netzwerk.

    Args:
        server: Server-ID oder Name
        network: Netzwerk-ID oder Name

    Returns:
        Status der Trennung
    """
    try:
        client = get_client()

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

        # Netzwerk finden
        try:
            net_id = int(network)
            network_obj = client.networks.get_by_id(net_id)
        except ValueError:
            network_obj = client.networks.get_by_name(network)

        if not network_obj:
            return {
                "success": False,
                "error": f"Netzwerk '{network}' nicht gefunden"
            }

        # Server vom Netzwerk trennen
        action = client.servers.detach_from_network(server_obj, network_obj)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Server '{server_obj.name}' von Netzwerk '{network_obj.name}' getrennt",
            "server_id": server_obj.id,
            "network_id": network_obj.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Trennen des Servers vom Netzwerk: {str(e)}"
        }
