"""Hetzner Cloud MCP Server - Hauptdatei mit allen Tools."""

from fastmcp import FastMCP

# Server Tools importieren
from .tools.servers import (
    hcloud_server_list,
    hcloud_server_info,
    hcloud_server_create,
    hcloud_server_delete,
    hcloud_server_power,
    hcloud_server_rebuild,
    hcloud_server_enable_backup,
    hcloud_server_disable_backup,
    hcloud_server_enable_rescue,
    hcloud_server_disable_rescue,
    hcloud_server_create_image,
    hcloud_server_attach_iso,
    hcloud_server_detach_iso,
    hcloud_server_change_type,
    hcloud_server_request_console,
    hcloud_server_reset_password,
    hcloud_server_change_dns_ptr,
    hcloud_server_change_protection,
    hcloud_server_update,
    hcloud_server_get_metrics,
)

# Firewall Tools importieren
from .tools.firewalls import (
    hcloud_firewall_list,
    hcloud_firewall_create,
    hcloud_firewall_delete,
    hcloud_firewall_add_rule,
    hcloud_firewall_apply,
    hcloud_firewall_remove_from_server,
    hcloud_firewall_set_rules,
    hcloud_firewall_update,
)

# Volume Tools importieren
from .tools.volumes import (
    hcloud_volume_list,
    hcloud_volume_create,
    hcloud_volume_delete,
    hcloud_volume_attach,
    hcloud_volume_detach,
    hcloud_volume_resize,
    hcloud_volume_change_protection,
    hcloud_volume_update,
)

# Network Tools importieren
from .tools.networks import (
    hcloud_network_list,
    hcloud_network_create,
    hcloud_network_delete,
    hcloud_network_add_subnet,
    hcloud_server_attach_network,
    hcloud_server_detach_network,
    hcloud_network_add_route,
    hcloud_network_delete_route,
    hcloud_network_delete_subnet,
    hcloud_network_change_ip_range,
    hcloud_network_change_protection,
    hcloud_network_update,
)

# Load Balancer Tools importieren
from .tools.load_balancers import (
    hcloud_load_balancer_list,
    hcloud_load_balancer_create,
    hcloud_load_balancer_delete,
    hcloud_load_balancer_add_service,
    hcloud_load_balancer_delete_service,
    hcloud_load_balancer_add_target,
    hcloud_load_balancer_remove_target,
    hcloud_load_balancer_change_algorithm,
    hcloud_load_balancer_update,
)

# Certificate Tools importieren
from .tools.certificates import (
    hcloud_certificate_list,
    hcloud_certificate_create,
    hcloud_certificate_create_managed,
    hcloud_certificate_delete,
    hcloud_certificate_update,
    hcloud_certificate_retry_issuance,
)

# ISO Tools importieren
from .tools.isos import (
    hcloud_iso_list,
    hcloud_iso_get,
)

# Placement Group Tools importieren
from .tools.placement_groups import (
    hcloud_placement_group_list,
    hcloud_placement_group_create,
    hcloud_placement_group_delete,
    hcloud_placement_group_update,
)

# Misc Tools importieren (SSH Keys, Images, Locations, etc.)
from .tools.misc import (
    # SSH Keys
    hcloud_ssh_key_list,
    hcloud_ssh_key_create,
    hcloud_ssh_key_delete,
    hcloud_ssh_key_update,
    # Images
    hcloud_image_list,
    hcloud_image_update,
    hcloud_image_delete,
    hcloud_image_change_protection,
    # Server Types, Locations, Datacenters
    hcloud_server_type_list,
    hcloud_location_list,
    hcloud_datacenter_list,
    # Floating IPs
    hcloud_floating_ip_list,
    hcloud_floating_ip_create,
    hcloud_floating_ip_delete,
    hcloud_floating_ip_assign,
    hcloud_floating_ip_unassign,
    hcloud_floating_ip_change_dns_ptr,
    hcloud_floating_ip_change_protection,
    hcloud_floating_ip_update,
    # Primary IPs
    hcloud_primary_ip_list,
    hcloud_primary_ip_create,
    hcloud_primary_ip_delete,
    hcloud_primary_ip_assign,
    hcloud_primary_ip_unassign,
    hcloud_primary_ip_change_dns_ptr,
    hcloud_primary_ip_change_protection,
    hcloud_primary_ip_update,
    # Actions
    hcloud_action_get,
    hcloud_action_list,
)

# FastMCP Server initialisieren
mcp = FastMCP("Hetzner Cloud MCP Server")

# =============================================================================
# SERVER-MANAGEMENT (18 Tools)
# =============================================================================

@mcp.tool()
async def server_list() -> dict:
    """Liste aller Server im Projekt."""
    return await hcloud_server_list()


@mcp.tool()
async def server_info(identifier: str) -> dict:
    """Detaillierte Informationen zu einem Server."""
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
    """Erstellt einen neuen Server."""
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
    """Löscht einen Server (benötigt force=True)."""
    return await hcloud_server_delete(identifier, force)


@mcp.tool()
async def server_power(identifier: str, action: str) -> dict:
    """Power-Aktionen: start, stop, shutdown, reboot, reset."""
    return await hcloud_server_power(identifier, action)


@mcp.tool()
async def server_rebuild(identifier: str, image: str) -> dict:
    """Rebuilt einen Server mit neuem Image."""
    return await hcloud_server_rebuild(identifier, image)


@mcp.tool()
async def server_enable_backup(identifier: str) -> dict:
    """Aktiviert automatische Backups."""
    return await hcloud_server_enable_backup(identifier)


@mcp.tool()
async def server_disable_backup(identifier: str) -> dict:
    """Deaktiviert automatische Backups."""
    return await hcloud_server_disable_backup(identifier)


@mcp.tool()
async def server_enable_rescue(
    identifier: str,
    rescue_type: str = "linux64",
    ssh_keys: list[str] | None = None
) -> dict:
    """Aktiviert Rescue-Modus."""
    return await hcloud_server_enable_rescue(identifier, rescue_type, ssh_keys)


@mcp.tool()
async def server_disable_rescue(identifier: str) -> dict:
    """Deaktiviert Rescue-Modus."""
    return await hcloud_server_disable_rescue(identifier)


@mcp.tool()
async def server_create_image(
    identifier: str,
    description: str | None = None,
    image_type: str = "snapshot",
    labels: dict | None = None
) -> dict:
    """Erstellt ein Snapshot/Backup von einem Server."""
    return await hcloud_server_create_image(identifier, description, image_type, labels)


@mcp.tool()
async def server_attach_iso(identifier: str, iso: str) -> dict:
    """Hängt ein ISO-Image an."""
    return await hcloud_server_attach_iso(identifier, iso)


@mcp.tool()
async def server_detach_iso(identifier: str) -> dict:
    """Trennt das ISO-Image."""
    return await hcloud_server_detach_iso(identifier)


@mcp.tool()
async def server_change_type(
    identifier: str,
    server_type: str,
    upgrade_disk: bool = False
) -> dict:
    """Ändert den Server-Typ (Resize)."""
    return await hcloud_server_change_type(identifier, server_type, upgrade_disk)


@mcp.tool()
async def server_request_console(identifier: str) -> dict:
    """Fordert WebConsole (VNC) an."""
    return await hcloud_server_request_console(identifier)


@mcp.tool()
async def server_reset_password(identifier: str) -> dict:
    """Setzt Root-Passwort zurück."""
    return await hcloud_server_reset_password(identifier)


@mcp.tool()
async def server_change_dns_ptr(identifier: str, ip: str, dns_ptr: str | None) -> dict:
    """Ändert Reverse DNS."""
    return await hcloud_server_change_dns_ptr(identifier, ip, dns_ptr)


@mcp.tool()
async def server_change_protection(
    identifier: str,
    delete: bool | None = None,
    rebuild: bool | None = None
) -> dict:
    """Ändert Schutz-Einstellungen."""
    return await hcloud_server_change_protection(identifier, delete, rebuild)


@mcp.tool()
async def server_update(
    identifier: str,
    name: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Server-Metadaten."""
    return await hcloud_server_update(identifier, name, labels)


@mcp.tool()
async def server_get_metrics(
    identifier: str,
    metric_type: str,
    start: str,
    end: str
) -> dict:
    """Ruft Server-Metriken ab (CPU, Disk, Network)."""
    return await hcloud_server_get_metrics(identifier, metric_type, start, end)


# =============================================================================
# FIREWALL-MANAGEMENT (8 Tools)
# =============================================================================

@mcp.tool()
async def firewall_list() -> dict:
    """Liste aller Firewalls."""
    return await hcloud_firewall_list()


@mcp.tool()
async def firewall_create(
    name: str,
    rules: list[dict] | None = None,
    labels: dict | None = None,
) -> dict:
    """Erstellt eine neue Firewall."""
    return await hcloud_firewall_create(name, rules, labels)


@mcp.tool()
async def firewall_delete(identifier: str, force: bool = False) -> dict:
    """Löscht eine Firewall (benötigt force=True)."""
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
    """Fügt eine Regel hinzu."""
    return await hcloud_firewall_add_rule(
        identifier, direction, protocol, source_ips, destination_ips, port
    )


@mcp.tool()
async def firewall_set_rules(identifier: str, rules: list[dict]) -> dict:
    """Setzt alle Regeln (überschreibt bestehende!)."""
    return await hcloud_firewall_set_rules(identifier, rules)


@mcp.tool()
async def firewall_apply(identifier: str, server: str) -> dict:
    """Wendet Firewall auf Server an."""
    return await hcloud_firewall_apply(identifier, server)


@mcp.tool()
async def firewall_remove_from_server(identifier: str, server: str) -> dict:
    """Entfernt Firewall von Server."""
    return await hcloud_firewall_remove_from_server(identifier, server)


@mcp.tool()
async def firewall_update(
    identifier: str,
    name: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Firewall-Metadaten."""
    return await hcloud_firewall_update(identifier, name, labels)


# =============================================================================
# VOLUME-MANAGEMENT (8 Tools)
# =============================================================================

@mcp.tool()
async def volume_list() -> dict:
    """Liste aller Volumes."""
    return await hcloud_volume_list()


@mcp.tool()
async def volume_create(
    name: str,
    size: int,
    location: str,
    format_volume: str = "ext4",
) -> dict:
    """Erstellt ein neues Volume."""
    return await hcloud_volume_create(name, size, location, format_volume)


@mcp.tool()
async def volume_delete(identifier: str, force: bool = False) -> dict:
    """Löscht ein Volume (benötigt force=True)."""
    return await hcloud_volume_delete(identifier, force)


@mcp.tool()
async def volume_attach(volume: str, server: str, automount: bool = False) -> dict:
    """Hängt Volume an Server an."""
    return await hcloud_volume_attach(volume, server, automount)


@mcp.tool()
async def volume_detach(volume: str) -> dict:
    """Trennt Volume vom Server."""
    return await hcloud_volume_detach(volume)


@mcp.tool()
async def volume_resize(volume: str, size: int) -> dict:
    """Vergrößert ein Volume."""
    return await hcloud_volume_resize(volume, size)


@mcp.tool()
async def volume_change_protection(
    identifier: str,
    delete: bool | None = None
) -> dict:
    """Ändert Schutz-Einstellungen."""
    return await hcloud_volume_change_protection(identifier, delete)


@mcp.tool()
async def volume_update(
    identifier: str,
    name: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Volume-Metadaten."""
    return await hcloud_volume_update(identifier, name, labels)


# =============================================================================
# NETWORK-MANAGEMENT (12 Tools)
# =============================================================================

@mcp.tool()
async def network_list() -> dict:
    """Liste aller privaten Netzwerke."""
    return await hcloud_network_list()


@mcp.tool()
async def network_create(name: str, ip_range: str) -> dict:
    """Erstellt ein privates Netzwerk."""
    return await hcloud_network_create(name, ip_range)


@mcp.tool()
async def network_delete(identifier: str, force: bool = False) -> dict:
    """Löscht ein Netzwerk (benötigt force=True)."""
    return await hcloud_network_delete(identifier, force)


@mcp.tool()
async def network_add_subnet(
    identifier: str,
    ip_range: str,
    network_zone: str,
    subnet_type: str = "cloud",
) -> dict:
    """Fügt ein Subnet hinzu."""
    return await hcloud_network_add_subnet(identifier, ip_range, network_zone, subnet_type)


@mcp.tool()
async def network_delete_subnet(identifier: str, ip_range: str) -> dict:
    """Entfernt ein Subnet."""
    return await hcloud_network_delete_subnet(identifier, ip_range)


@mcp.tool()
async def network_add_route(identifier: str, destination: str, gateway: str) -> dict:
    """Fügt eine Route hinzu."""
    return await hcloud_network_add_route(identifier, destination, gateway)


@mcp.tool()
async def network_delete_route(identifier: str, destination: str, gateway: str) -> dict:
    """Entfernt eine Route."""
    return await hcloud_network_delete_route(identifier, destination, gateway)


@mcp.tool()
async def network_change_ip_range(identifier: str, ip_range: str) -> dict:
    """Ändert den IP-Bereich."""
    return await hcloud_network_change_ip_range(identifier, ip_range)


@mcp.tool()
async def network_change_protection(
    identifier: str,
    delete: bool | None = None
) -> dict:
    """Ändert Schutz-Einstellungen."""
    return await hcloud_network_change_protection(identifier, delete)


@mcp.tool()
async def network_update(
    identifier: str,
    name: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Netzwerk-Metadaten."""
    return await hcloud_network_update(identifier, name, labels)


@mcp.tool()
async def server_attach_network(
    server: str,
    network: str,
    ip: str | None = None,
) -> dict:
    """Verbindet Server mit Netzwerk."""
    return await hcloud_server_attach_network(server, network, ip)


@mcp.tool()
async def server_detach_network(server: str, network: str) -> dict:
    """Trennt Server von Netzwerk."""
    return await hcloud_server_detach_network(server, network)


# =============================================================================
# LOAD BALANCER-MANAGEMENT (9 Tools)
# =============================================================================

@mcp.tool()
async def load_balancer_list() -> dict:
    """Liste aller Load Balancer."""
    return await hcloud_load_balancer_list()


@mcp.tool()
async def load_balancer_create(
    name: str,
    load_balancer_type: str,
    location: str | None = None,
    network_zone: str | None = None,
    labels: dict | None = None,
    algorithm_type: str = "round_robin",
    public_interface: bool = True,
) -> dict:
    """Erstellt einen Load Balancer."""
    return await hcloud_load_balancer_create(
        name, load_balancer_type, location, network_zone, labels, algorithm_type, public_interface
    )


@mcp.tool()
async def load_balancer_delete(identifier: str, force: bool = False) -> dict:
    """Löscht einen Load Balancer (benötigt force=True)."""
    return await hcloud_load_balancer_delete(identifier, force)


@mcp.tool()
async def load_balancer_add_service(
    identifier: str,
    protocol: str,
    listen_port: int,
    destination_port: int,
    proxyprotocol: bool = False,
    http_sticky_sessions: bool = False,
    http_redirect_http: bool = False,
    health_check_protocol: str = "tcp",
    health_check_port: int | None = None,
    health_check_interval: int = 15,
    health_check_timeout: int = 10,
    health_check_retries: int = 3,
) -> dict:
    """Fügt einen Service hinzu."""
    return await hcloud_load_balancer_add_service(
        identifier, protocol, listen_port, destination_port, proxyprotocol,
        http_sticky_sessions, http_redirect_http, health_check_protocol,
        health_check_port, health_check_interval, health_check_timeout, health_check_retries
    )


@mcp.tool()
async def load_balancer_delete_service(identifier: str, listen_port: int) -> dict:
    """Entfernt einen Service."""
    return await hcloud_load_balancer_delete_service(identifier, listen_port)


@mcp.tool()
async def load_balancer_add_target(
    identifier: str,
    target_type: str,
    server: str | None = None,
    label_selector: str | None = None,
    ip: str | None = None,
    use_private_ip: bool = False,
) -> dict:
    """Fügt ein Target hinzu."""
    return await hcloud_load_balancer_add_target(
        identifier, target_type, server, label_selector, ip, use_private_ip
    )


@mcp.tool()
async def load_balancer_remove_target(
    identifier: str,
    target_type: str,
    server: str | None = None,
    label_selector: str | None = None,
    ip: str | None = None,
) -> dict:
    """Entfernt ein Target."""
    return await hcloud_load_balancer_remove_target(
        identifier, target_type, server, label_selector, ip
    )


@mcp.tool()
async def load_balancer_change_algorithm(identifier: str, algorithm_type: str) -> dict:
    """Ändert den Load-Balancing-Algorithmus."""
    return await hcloud_load_balancer_change_algorithm(identifier, algorithm_type)


@mcp.tool()
async def load_balancer_update(
    identifier: str,
    name: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Load Balancer-Metadaten."""
    return await hcloud_load_balancer_update(identifier, name, labels)


# =============================================================================
# CERTIFICATE-MANAGEMENT (6 Tools)
# =============================================================================

@mcp.tool()
async def certificate_list() -> dict:
    """Liste aller Certificates."""
    return await hcloud_certificate_list()


@mcp.tool()
async def certificate_create(
    name: str,
    certificate: str,
    private_key: str,
    labels: dict | None = None
) -> dict:
    """Erstellt ein Certificate (Upload)."""
    return await hcloud_certificate_create(name, certificate, private_key, labels)


@mcp.tool()
async def certificate_create_managed(
    name: str,
    domain_names: list[str],
    labels: dict | None = None
) -> dict:
    """Erstellt ein Managed Certificate (Let's Encrypt)."""
    return await hcloud_certificate_create_managed(name, domain_names, labels)


@mcp.tool()
async def certificate_delete(identifier: str, force: bool = False) -> dict:
    """Löscht ein Certificate (benötigt force=True)."""
    return await hcloud_certificate_delete(identifier, force)


@mcp.tool()
async def certificate_update(
    identifier: str,
    name: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Certificate-Metadaten."""
    return await hcloud_certificate_update(identifier, name, labels)


@mcp.tool()
async def certificate_retry_issuance(identifier: str) -> dict:
    """Versucht Ausstellung eines Managed Certificates erneut."""
    return await hcloud_certificate_retry_issuance(identifier)


# =============================================================================
# ISO-MANAGEMENT (2 Tools)
# =============================================================================

@mcp.tool()
async def iso_list(iso_type: str | None = None) -> dict:
    """Liste aller ISOs (Filter: public, private)."""
    return await hcloud_iso_list(iso_type)


@mcp.tool()
async def iso_get(identifier: str) -> dict:
    """Details zu einem ISO."""
    return await hcloud_iso_get(identifier)


# =============================================================================
# PLACEMENT GROUP-MANAGEMENT (4 Tools)
# =============================================================================

@mcp.tool()
async def placement_group_list() -> dict:
    """Liste aller Placement Groups."""
    return await hcloud_placement_group_list()


@mcp.tool()
async def placement_group_create(
    name: str,
    group_type: str = "spread",
    labels: dict | None = None
) -> dict:
    """Erstellt eine Placement Group."""
    return await hcloud_placement_group_create(name, group_type, labels)


@mcp.tool()
async def placement_group_delete(identifier: str, force: bool = False) -> dict:
    """Löscht eine Placement Group (benötigt force=True)."""
    return await hcloud_placement_group_delete(identifier, force)


@mcp.tool()
async def placement_group_update(
    identifier: str,
    name: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Placement Group-Metadaten."""
    return await hcloud_placement_group_update(identifier, name, labels)


# =============================================================================
# SSH KEY-MANAGEMENT (4 Tools)
# =============================================================================

@mcp.tool()
async def ssh_key_list() -> dict:
    """Liste aller SSH-Keys."""
    return await hcloud_ssh_key_list()


@mcp.tool()
async def ssh_key_create(name: str, public_key: str) -> dict:
    """Fügt einen SSH-Key hinzu."""
    return await hcloud_ssh_key_create(name, public_key)


@mcp.tool()
async def ssh_key_delete(identifier: str, force: bool = False) -> dict:
    """Löscht einen SSH-Key (benötigt force=True)."""
    return await hcloud_ssh_key_delete(identifier, force)


@mcp.tool()
async def ssh_key_update(
    identifier: str,
    name: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert SSH-Key-Metadaten."""
    return await hcloud_ssh_key_update(identifier, name, labels)


# =============================================================================
# IMAGE-MANAGEMENT (4 Tools)
# =============================================================================

@mcp.tool()
async def image_list(image_type: str | None = None) -> dict:
    """Liste aller Images (Filter: system, snapshot, backup, app)."""
    return await hcloud_image_list(image_type)


@mcp.tool()
async def image_update(
    identifier: str,
    description: str | None = None,
    image_type: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Image-Metadaten."""
    return await hcloud_image_update(identifier, description, image_type, labels)


@mcp.tool()
async def image_delete(identifier: str, force: bool = False) -> dict:
    """Löscht ein Image (benötigt force=True)."""
    return await hcloud_image_delete(identifier, force)


@mcp.tool()
async def image_change_protection(
    identifier: str,
    delete: bool | None = None
) -> dict:
    """Ändert Schutz-Einstellungen."""
    return await hcloud_image_change_protection(identifier, delete)


# =============================================================================
# FLOATING IP-MANAGEMENT (8 Tools)
# =============================================================================

@mcp.tool()
async def floating_ip_list() -> dict:
    """Liste aller Floating IPs."""
    return await hcloud_floating_ip_list()


@mcp.tool()
async def floating_ip_create(
    floating_type: str,
    location: str | None = None,
    home_location: str | None = None,
    server: str | None = None,
    description: str | None = None,
    labels: dict | None = None,
    name: str | None = None,
) -> dict:
    """Erstellt eine Floating IP."""
    return await hcloud_floating_ip_create(
        floating_type, location, home_location, server, description, labels, name
    )


@mcp.tool()
async def floating_ip_delete(identifier: str, force: bool = False) -> dict:
    """Löscht eine Floating IP (benötigt force=True)."""
    return await hcloud_floating_ip_delete(identifier, force)


@mcp.tool()
async def floating_ip_assign(identifier: str, server: str) -> dict:
    """Weist Floating IP einem Server zu."""
    return await hcloud_floating_ip_assign(identifier, server)


@mcp.tool()
async def floating_ip_unassign(identifier: str) -> dict:
    """Entfernt Zuweisung einer Floating IP."""
    return await hcloud_floating_ip_unassign(identifier)


@mcp.tool()
async def floating_ip_change_dns_ptr(
    identifier: str,
    ip: str,
    dns_ptr: str | None
) -> dict:
    """Ändert Reverse DNS."""
    return await hcloud_floating_ip_change_dns_ptr(identifier, ip, dns_ptr)


@mcp.tool()
async def floating_ip_change_protection(
    identifier: str,
    delete: bool | None = None
) -> dict:
    """Ändert Schutz-Einstellungen."""
    return await hcloud_floating_ip_change_protection(identifier, delete)


@mcp.tool()
async def floating_ip_update(
    identifier: str,
    name: str | None = None,
    description: str | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Floating IP-Metadaten."""
    return await hcloud_floating_ip_update(identifier, name, description, labels)


# =============================================================================
# PRIMARY IP-MANAGEMENT (8 Tools)
# =============================================================================

@mcp.tool()
async def primary_ip_list() -> dict:
    """Liste aller Primary IPs."""
    return await hcloud_primary_ip_list()


@mcp.tool()
async def primary_ip_create(
    assignee_type: str,
    primary_type: str,
    datacenter: str | None = None,
    assignee_id: int | None = None,
    auto_delete: bool = True,
    name: str | None = None,
    labels: dict | None = None,
) -> dict:
    """Erstellt eine Primary IP."""
    return await hcloud_primary_ip_create(
        assignee_type, primary_type, datacenter, assignee_id, auto_delete, name, labels
    )


@mcp.tool()
async def primary_ip_delete(identifier: str, force: bool = False) -> dict:
    """Löscht eine Primary IP (benötigt force=True)."""
    return await hcloud_primary_ip_delete(identifier, force)


@mcp.tool()
async def primary_ip_assign(identifier: str, assignee_id: int) -> dict:
    """Weist Primary IP einem Server zu."""
    return await hcloud_primary_ip_assign(identifier, assignee_id)


@mcp.tool()
async def primary_ip_unassign(identifier: str) -> dict:
    """Entfernt Zuweisung einer Primary IP."""
    return await hcloud_primary_ip_unassign(identifier)


@mcp.tool()
async def primary_ip_change_dns_ptr(
    identifier: str,
    ip: str,
    dns_ptr: str | None
) -> dict:
    """Ändert Reverse DNS."""
    return await hcloud_primary_ip_change_dns_ptr(identifier, ip, dns_ptr)


@mcp.tool()
async def primary_ip_change_protection(
    identifier: str,
    delete: bool | None = None
) -> dict:
    """Ändert Schutz-Einstellungen."""
    return await hcloud_primary_ip_change_protection(identifier, delete)


@mcp.tool()
async def primary_ip_update(
    identifier: str,
    name: str | None = None,
    auto_delete: bool | None = None,
    labels: dict | None = None
) -> dict:
    """Aktualisiert Primary IP-Metadaten."""
    return await hcloud_primary_ip_update(identifier, name, auto_delete, labels)


# =============================================================================
# SERVER TYPE / LOCATION / DATACENTER (3 Tools)
# =============================================================================

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


# =============================================================================
# ACTIONS (2 Tools)
# =============================================================================

@mcp.tool()
async def action_get(action_id: int) -> dict:
    """Ruft Details zu einer Action ab."""
    return await hcloud_action_get(action_id)


@mcp.tool()
async def action_list(
    status: list[str] | None = None,
    sort: list[str] | None = None
) -> dict:
    """Listet alle Actions auf."""
    return await hcloud_action_list(status, sort)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Startet den MCP Server."""
    import sys

    # Debug-Modus wenn --debug Flag gesetzt
    debug = "--debug" in sys.argv

    if debug:
        print("Hetzner Cloud MCP Server startet im Debug-Modus...")
        print("Registrierte Tools: 117+")

    # Server starten
    mcp.run()


if __name__ == "__main__":
    main()
