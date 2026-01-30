"""Konfiguration für Hetzner Cloud MCP Server."""

import os
from typing import Optional
from dotenv import load_dotenv
from hcloud import Client

# Lade Environment Variables
load_dotenv()


class HetznerConfig:
    """Konfiguration für Hetzner Cloud API."""

    def __init__(self):
        self.api_token = os.getenv("HCLOUD_TOKEN")
        if not self.api_token:
            raise ValueError(
                "HCLOUD_TOKEN nicht gesetzt. Bitte in .env Datei oder Environment konfigurieren."
            )

        self.default_location = os.getenv("HCLOUD_DEFAULT_LOCATION", "fsn1")
        self.default_ssh_key = os.getenv("HCLOUD_DEFAULT_SSH_KEY", "")

    def get_client(self) -> Client:
        """Erstellt einen neuen Hetzner Cloud API Client."""
        return Client(token=self.api_token)


# Globale Config-Instanz
_config: Optional[HetznerConfig] = None


def get_config() -> HetznerConfig:
    """Gibt die globale Config-Instanz zurück."""
    global _config
    if _config is None:
        _config = HetznerConfig()
    return _config


def get_client() -> Client:
    """Gibt einen neuen Hetzner Cloud API Client zurück."""
    return get_config().get_client()
