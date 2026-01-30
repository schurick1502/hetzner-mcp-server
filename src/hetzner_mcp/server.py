"""Hetzner Cloud MCP Server - Hauptdatei."""

from fastmcp import FastMCP

# Tools importieren
from .tools.servers import (
    hcloud_server_list,
    hcloud_server_info,
    hcloud_server_create,
    hcloud_server_delete,
    hcloud_server_power,
    hcloud_server_rebuild,
)
from .tools.firewalls import (
    hcloud_firewall_list,
    hcloud_firewall_create,
    hcloud_firewall_delete,
    hcloud_firewall_add_rule,
    hcloud_firewall_apply,
    hcloud_firewall_remove_from_server,
)
from .tools.volumes import (
    hcloud_volume_list,
    hcloud_volume_create,
    hcloud_volume_delete,
    hcloud_volume_attach,
    hcloud_volume_detach,
    hcloud_volume_resize,
)
from .tools.networks import (
    hcloud_network_list,
    hcloud_network_create,
    hcloud_network_delete,
    hcloud_network_add_subnet,
    hcloud_server_attach_network,
    hcloud_server_detach_network,
)
from .tools.misc import (
    hcloud_ssh_key_list,
    hcloud_ssh_key_create,
    hcloud_ssh_key_delete,
    hcloud_image_list,
    hcloud_server_type_list,
    hcloud_location_list,
    hcloud_datacenter_list,
    hcloud_floating_ip_list,
    hcloud_primary_ip_list,
)

# FastMCP Server initialisieren
mcp = FastMCP("Hetzner Cloud MCP Server")

# ===== SERVER-MANAGEMENT =====
@mcp.tool()
async def server_list() -> dict:
    """Liste aller Server im Hetzner Cloud Projekt."""
    return await hcloud_server_list()


@mcp.tool()
async def server_info(identifier: str) -> dict:
    """
    Detaillierte Informationen zu einem Server.

    Args:
        identifier: Server-ID oder Name
    """
    return await hcloud_server_info(identifier)


@mcp.tool()
async def server_create(
    name: str,
    server_type: str = "cx22",
    image: str = "ubuntu-24.04",
    location: str = "fsn1",
    ssh_keys: list[str] | None = None,
    firewalls: list[str] | None = None,
    user_data: str | None = None,
) -> dict:
    """
    Erstellt einen neuen Hetzner Cloud Server.

    Args:
        name: Servername
        server_type: Server-Typ (z.B. cx22, cx32)
        image: OS-Image (z.B. ubuntu-24.04)
        location: Standort (fsn1, nbg1, hel1)
        ssh_keys: Liste von SSH-Key Namen
        firewalls: Liste von Firewall Namen
        user_data: Cloud-init Script (optional)
    """
    return await hcloud_server_create(
        name=name,
        server_type=server_type,
        image=image,
        location=location,
        ssh_keys=ssh_keys,
        firewalls=firewalls,
        user_data=user_data,
    )


@mcp.tool()
async def server_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht einen Server (destruktive Aktion!).

    Args:
        identifier: Server-ID oder Name
        force: Muss True sein zur Bestätigung
    """
    return await hcloud_server_delete(identifier, force)


@mcp.tool()
async def server_power(identifier: str, action: str) -> dict:
    """
    Führt Power-Aktionen auf einem Server aus.

    Args:
        identifier: Server-ID oder Name
        action: start, stop, shutdown, reboot, reset
    """
    return await hcloud_server_power(identifier, action)


@mcp.tool()
async def server_rebuild(identifier: str, image: str) -> dict:
    """
    Rebuilt einen Server mit neuem Image.

    Args:
        identifier: Server-ID oder Name
        image: Neues OS-Image
    """
    return await hcloud_server_rebuild(identifier, image)


# ===== FIREWALL-MANAGEMENT =====
@mcp.tool()
async def firewall_list() -> dict:
    """Liste aller Firewalls im Projekt."""
    return await hcloud_firewall_list()


@mcp.tool()
async def firewall_create(
    name: str,
    rules: list[dict] | None = None,
    labels: dict | None = None,
) -> dict:
    """
    Erstellt eine neue Firewall.

    Args:
        name: Firewall-Name
        rules: Liste von Regeln (optional)
        labels: Labels (optional)
    """
    return await hcloud_firewall_create(name, rules, labels)


@mcp.tool()
async def firewall_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht eine Firewall.

    Args:
        identifier: Firewall-ID oder Name
        force: Muss True sein zur Bestätigung
    """
    return await hcloud_firewall_delete(identifier, force)


@mcp.tool()
async def firewall_add_rule(
    identifier: str,
    direction: str,
    protocol: str,
    source_ips: list[str] | None = None,
    destination_ips: list[str] | None = None,
    port: str | None = None,
) -> dict:
    """
    Fügt eine Regel zu einer Firewall hinzu.

    Args:
        identifier: Firewall-ID oder Name
        direction: "in" oder "out"
        protocol: tcp, udp, icmp, esp, gre
        source_ips: Quell-IPs (bei direction=in)
        destination_ips: Ziel-IPs (bei direction=out)
        port: Port oder Port-Range (bei tcp/udp)
    """
    return await hcloud_firewall_add_rule(
        identifier, direction, protocol, source_ips, destination_ips, port
    )


@mcp.tool()
async def firewall_apply(identifier: str, server: str) -> dict:
    """
    Wendet eine Firewall auf einen Server an.

    Args:
        identifier: Firewall-ID oder Name
        server: Server-ID oder Name
    """
    return await hcloud_firewall_apply(identifier, server)


@mcp.tool()
async def firewall_remove_from_server(identifier: str, server: str) -> dict:
    """
    Entfernt eine Firewall von einem Server.

    Args:
        identifier: Firewall-ID oder Name
        server: Server-ID oder Name
    """
    return await hcloud_firewall_remove_from_server(identifier, server)


# ===== VOLUME-MANAGEMENT =====
@mcp.tool()
async def volume_list() -> dict:
    """Liste aller Volumes im Projekt."""
    return await hcloud_volume_list()


@mcp.tool()
async def volume_create(
    name: str,
    size: int,
    location: str,
    format_volume: str = "ext4",
) -> dict:
    """
    Erstellt ein neues Volume.

    Args:
        name: Volume-Name
        size: Größe in GB (min. 10)
        location: Standort
        format_volume: Dateisystem (ext4 oder xfs)
    """
    return await hcloud_volume_create(name, size, location, format_volume)


@mcp.tool()
async def volume_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht ein Volume.

    Args:
        identifier: Volume-ID oder Name
        force: Muss True sein zur Bestätigung
    """
    return await hcloud_volume_delete(identifier, force)


@mcp.tool()
async def volume_attach(volume: str, server: str, automount: bool = False) -> dict:
    """
    Hängt ein Volume an einen Server an.

    Args:
        volume: Volume-ID oder Name
        server: Server-ID oder Name
        automount: Automatisch mounten
    """
    return await hcloud_volume_attach(volume, server, automount)


@mcp.tool()
async def volume_detach(volume: str) -> dict:
    """
    Trennt ein Volume von seinem Server.

    Args:
        volume: Volume-ID oder Name
    """
    return await hcloud_volume_detach(volume)


@mcp.tool()
async def volume_resize(volume: str, size: int) -> dict:
    """
    Vergrößert ein Volume.

    Args:
        volume: Volume-ID oder Name
        size: Neue Größe in GB
    """
    return await hcloud_volume_resize(volume, size)


# ===== NETZWERK-MANAGEMENT =====
@mcp.tool()
async def network_list() -> dict:
    """Liste aller privaten Netzwerke."""
    return await hcloud_network_list()


@mcp.tool()
async def network_create(name: str, ip_range: str) -> dict:
    """
    Erstellt ein privates Netzwerk.

    Args:
        name: Netzwerk-Name
        ip_range: IP-Bereich (z.B. 10.0.0.0/16)
    """
    return await hcloud_network_create(name, ip_range)


@mcp.tool()
async def network_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht ein Netzwerk.

    Args:
        identifier: Netzwerk-ID oder Name
        force: Muss True sein zur Bestätigung
    """
    return await hcloud_network_delete(identifier, force)


@mcp.tool()
async def network_add_subnet(
    identifier: str,
    ip_range: str,
    network_zone: str,
    subnet_type: str = "cloud",
) -> dict:
    """
    Fügt ein Subnet zu einem Netzwerk hinzu.

    Args:
        identifier: Netzwerk-ID oder Name
        ip_range: IP-Bereich (z.B. 10.0.1.0/24)
        network_zone: eu-central, us-east, us-west
        subnet_type: cloud, server, vswitch
    """
    return await hcloud_network_add_subnet(identifier, ip_range, network_zone, subnet_type)


@mcp.tool()
async def server_attach_network(
    server: str,
    network: str,
    ip: str | None = None,
) -> dict:
    """
    Verbindet einen Server mit einem Netzwerk.

    Args:
        server: Server-ID oder Name
        network: Netzwerk-ID oder Name
        ip: Gewünschte IP (optional)
    """
    return await hcloud_server_attach_network(server, network, ip)


@mcp.tool()
async def server_detach_network(server: str, network: str) -> dict:
    """
    Trennt einen Server von einem Netzwerk.

    Args:
        server: Server-ID oder Name
        network: Netzwerk-ID oder Name
    """
    return await hcloud_server_detach_network(server, network)


# ===== HILFSFUNKTIONEN =====
@mcp.tool()
async def ssh_key_list() -> dict:
    """Liste aller SSH-Keys."""
    return await hcloud_ssh_key_list()


@mcp.tool()
async def ssh_key_create(name: str, public_key: str) -> dict:
    """
    Fügt einen SSH-Key hinzu.

    Args:
        name: Key-Name
        public_key: Öffentlicher SSH-Key
    """
    return await hcloud_ssh_key_create(name, public_key)


@mcp.tool()
async def ssh_key_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht einen SSH-Key.

    Args:
        identifier: Key-ID oder Name
        force: Muss True sein zur Bestätigung
    """
    return await hcloud_ssh_key_delete(identifier, force)


@mcp.tool()
async def image_list(image_type: str | None = None) -> dict:
    """
    Liste verfügbarer Images.

    Args:
        image_type: system, snapshot, backup, app (optional)
    """
    return await hcloud_image_list(image_type)


@mcp.tool()
async def server_type_list() -> dict:
    """Liste aller Server-Typen mit Preisen."""
    return await hcloud_server_type_list()


@mcp.tool()
async def location_list() -> dict:
    """Liste aller verfügbaren Standorte."""
    return await hcloud_location_list()


@mcp.tool()
async def datacenter_list() -> dict:
    """Liste aller Rechenzentren."""
    return await hcloud_datacenter_list()


@mcp.tool()
async def floating_ip_list() -> dict:
    """Liste aller Floating IPs."""
    return await hcloud_floating_ip_list()


@mcp.tool()
async def primary_ip_list() -> dict:
    """Liste aller Primary IPs."""
    return await hcloud_primary_ip_list()


def main():
    """Startet den MCP Server."""
    import sys

    # Debug-Modus wenn --debug Flag gesetzt
    debug = "--debug" in sys.argv

    if debug:
        print("Hetzner Cloud MCP Server startet im Debug-Modus...")

    # Server starten
    mcp.run()


if __name__ == "__main__":
    main()
