"""Konfiguration für Hetzner Cloud MCP Server."""

import os
from contextvars import ContextVar, Token
from typing import Optional
from dotenv import load_dotenv
from hcloud import Client

# Lade Environment Variables
load_dotenv()

_active_account: ContextVar[Optional[str]] = ContextVar("hcloud_active_account", default=None)


class HetznerConfig:
    """Konfiguration für Hetzner Cloud API."""

    def __init__(self):
        self.account_tokens = self._load_account_tokens()
        if not self.account_tokens:
            raise ValueError(
                "Kein Hetzner API Token gesetzt. Bitte HCLOUD_TOKEN oder HCLOUD_TOKEN_* konfigurieren."
            )
        requested_default = os.getenv("HCLOUD_DEFAULT_ACCOUNT", "").strip().lower()
        if requested_default and requested_default in self.account_tokens:
            self.default_account = requested_default
        elif "default" in self.account_tokens:
            self.default_account = "default"
        else:
            self.default_account = next(iter(self.account_tokens.keys()))

        self.default_location = os.getenv("HCLOUD_DEFAULT_LOCATION", "fsn1")
        self.default_ssh_key = os.getenv("HCLOUD_DEFAULT_SSH_KEY", "")

    @staticmethod
    def _load_account_tokens() -> dict[str, str]:
        """Load all configured account tokens from env."""
        tokens: dict[str, str] = {}

        base = (os.getenv("HCLOUD_TOKEN") or "").strip()
        if base:
            tokens["default"] = base

        for key, value in os.environ.items():
            if not key.startswith("HCLOUD_TOKEN_"):
                continue
            token_value = (value or "").strip()
            if not token_value:
                continue
            account_id = key.replace("HCLOUD_TOKEN_", "", 1).strip().lower()
            if account_id:
                tokens[account_id] = token_value

        return tokens

    def list_accounts(self) -> list[dict]:
        """Return account metadata without exposing tokens."""
        accounts = []
        for account_id in self.account_tokens.keys():
            label = "Default" if account_id == "default" else account_id.upper()
            accounts.append({
                "id": account_id,
                "label": label,
                "is_default": account_id == self.default_account,
            })
        return accounts

    def get_client(self, account_id: Optional[str] = None) -> Client:
        """Erstellt einen neuen Hetzner Cloud API Client."""
        selected = (account_id or get_active_account() or self.default_account).strip().lower()
        token = self.account_tokens.get(selected)
        if not token:
            raise ValueError(f"Unbekannter Hetzner Account: {selected}")
        return Client(token=token)


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


def get_available_accounts() -> list[dict]:
    """List configured Hetzner accounts without secrets."""
    return get_config().list_accounts()


def get_default_account_id() -> str:
    """Return default account id."""
    return get_config().default_account


def get_active_account() -> Optional[str]:
    """Return currently active request account id."""
    return _active_account.get()


def set_active_account(account_id: Optional[str]) -> Token:
    """Set request-local active account id."""
    normalized = (account_id or "").strip().lower() or None
    if normalized and normalized not in get_config().account_tokens:
        raise ValueError(f"Unbekannter Hetzner Account: {normalized}")
    return _active_account.set(normalized)


def reset_active_account(token: Token) -> None:
    """Reset request-local active account id."""
    _active_account.reset(token)
