"""API credential storage.

Keys are stored in the Windows Credential Manager via :mod:`keyring`. As a
fallback (e.g. on systems without a keyring backend) an environment variable
can be used. Keys are never written to the config file, logs or exports.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)
SERVICE = "PersonalAITutor"

try:  # pragma: no cover - import guard
    import keyring
    from keyring.errors import KeyringError
except Exception:  # pragma: no cover
    keyring = None
    KeyringError = Exception


def get_api_key(name: str) -> str | None:
    if keyring is not None:
        try:
            value = keyring.get_password(SERVICE, name)
            if value:
                return value
        except KeyringError as exc:
            log.warning("Keyring unavailable: %s", type(exc).__name__)
    return os.environ.get(name) or None


def set_api_key(name: str, value: str) -> bool:
    if keyring is None:
        return False
    try:
        keyring.set_password(SERVICE, name, value)
        return True
    except KeyringError as exc:
        log.warning("Could not store API key: %s", type(exc).__name__)
        return False


def delete_api_key(name: str) -> None:
    if keyring is None:
        return
    try:
        keyring.delete_password(SERVICE, name)
    except Exception:
        pass


def mask(value: str | None) -> str:
    if not value:
        return "(not set)"
    return value[:3] + "…" + value[-2:] if len(value) > 8 else "•••"
