"""Certificate-Management Tools für Hetzner Cloud."""

from typing import Optional
from ..config import get_client


async def hcloud_certificate_list() -> dict:
    """
    Listet alle Certificates im Projekt auf.

    Returns:
        Dictionary mit Anzahl und Certificate-Details
    """
    try:
        client = get_client()
        certificates = client.certificates.get_all()

        cert_list = []
        for cert in certificates:
            cert_list.append({
                "id": cert.id,
                "name": cert.name,
                "type": cert.type,
                "domain_names": cert.domain_names,
                "fingerprint": cert.fingerprint,
                "not_valid_before": cert.not_valid_before.isoformat() if cert.not_valid_before else None,
                "not_valid_after": cert.not_valid_after.isoformat() if cert.not_valid_after else None,
                "status": cert.status if hasattr(cert, 'status') else None,
                "created": cert.created.isoformat(),
                "labels": cert.labels,
            })

        return {
            "success": True,
            "count": len(cert_list),
            "certificates": cert_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Abrufen der Certificates: {str(e)}"
        }


async def hcloud_certificate_create(
    name: str,
    certificate: str,
    private_key: str,
    labels: Optional[dict] = None
) -> dict:
    """
    Erstellt ein neues Certificate (Upload).

    Args:
        name: Certificate-Name
        certificate: PEM-encoded Certificate
        private_key: PEM-encoded Private Key
        labels: Labels (optional)

    Returns:
        Details des erstellten Certificates
    """
    try:
        client = get_client()

        response = client.certificates.create(
            name=name,
            certificate=certificate,
            private_key=private_key,
            labels=labels
        )

        cert = response.certificate

        return {
            "success": True,
            "certificate": {
                "id": cert.id,
                "name": cert.name,
                "domain_names": cert.domain_names,
                "fingerprint": cert.fingerprint,
            },
            "message": f"Certificate '{name}' erstellt"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen des Certificates: {str(e)}"
        }


async def hcloud_certificate_create_managed(
    name: str,
    domain_names: list[str],
    labels: Optional[dict] = None
) -> dict:
    """
    Erstellt ein Managed Certificate (automatisch von Let's Encrypt).

    Args:
        name: Certificate-Name
        domain_names: Liste von Domains
        labels: Labels (optional)

    Returns:
        Details des erstellten Certificates
    """
    try:
        client = get_client()

        response = client.certificates.create_managed(
            name=name,
            domain_names=domain_names,
            labels=labels
        )

        cert = response.certificate

        return {
            "success": True,
            "certificate": {
                "id": cert.id,
                "name": cert.name,
                "domain_names": cert.domain_names,
                "type": cert.type,
                "status": cert.status if hasattr(cert, 'status') else None,
            },
            "message": f"Managed Certificate '{name}' erstellt (wird automatisch ausgestellt)"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Erstellen des Managed Certificates: {str(e)}"
        }


async def hcloud_certificate_delete(identifier: str, force: bool = False) -> dict:
    """
    Löscht ein Certificate.

    Args:
        identifier: Certificate-ID oder Name
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
            cert_id = int(identifier)
            cert = client.certificates.get_by_id(cert_id)
        except ValueError:
            cert = client.certificates.get_by_name(identifier)

        if not cert:
            return {
                "success": False,
                "error": f"Certificate '{identifier}' nicht gefunden"
            }

        cert_name = cert.name
        cert_id = cert.id

        client.certificates.delete(cert)

        return {
            "success": True,
            "message": f"Certificate '{cert_name}' (ID: {cert_id}) wurde gelöscht"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Löschen des Certificates: {str(e)}"
        }


async def hcloud_certificate_update(
    identifier: str,
    name: Optional[str] = None,
    labels: Optional[dict] = None
) -> dict:
    """
    Aktualisiert Certificate-Metadaten.

    Args:
        identifier: Certificate-ID oder Name
        name: Neuer Name (optional)
        labels: Neue Labels (optional)

    Returns:
        Aktualisierte Details
    """
    try:
        client = get_client()

        try:
            cert_id = int(identifier)
            cert = client.certificates.get_by_id(cert_id)
        except ValueError:
            cert = client.certificates.get_by_name(identifier)

        if not cert:
            return {
                "success": False,
                "error": f"Certificate '{identifier}' nicht gefunden"
            }

        cert = client.certificates.update(cert, name=name, labels=labels)

        return {
            "success": True,
            "message": "Certificate aktualisiert",
            "certificate": {
                "id": cert.id,
                "name": cert.name,
                "labels": cert.labels
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim Aktualisieren des Certificates: {str(e)}"
        }


async def hcloud_certificate_retry_issuance(identifier: str) -> dict:
    """
    Versucht die Ausstellung eines Managed Certificates erneut.

    Args:
        identifier: Certificate-ID oder Name

    Returns:
        Status der Aktion
    """
    try:
        client = get_client()

        try:
            cert_id = int(identifier)
            cert = client.certificates.get_by_id(cert_id)
        except ValueError:
            cert = client.certificates.get_by_name(identifier)

        if not cert:
            return {
                "success": False,
                "error": f"Certificate '{identifier}' nicht gefunden"
            }

        action = client.certificates.retry_issuance(cert)
        action.wait_until_finished()

        return {
            "success": True,
            "message": f"Ausstellung für Certificate '{cert.name}' erneut versucht",
            "certificate_id": cert.id
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fehler beim erneuten Versuch der Ausstellung: {str(e)}"
        }
