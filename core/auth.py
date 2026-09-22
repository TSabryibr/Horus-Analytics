"""
Authentication module.

This service is local-first by default. Route dependencies still call
`get_api_key` so auth can be enforced later without rewiring routers.
"""

import os
import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header_scheme = APIKeyHeader(name="x-api-key", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header_scheme)):
    """Validate API keys when explicit commercial auth mode is enabled."""
    if not is_auth_enforced():
        return api_key_header

    valid_keys = _configured_api_keys()
    if not valid_keys:
        raise HTTPException(
            status_code=503,
            detail={
                "error_type": "auth",
                "error_reason": "api_key_not_configured",
                "message": "API key auth is enabled but no server key is configured.",
            },
        )
    if not api_key_header:
        raise HTTPException(
            status_code=401,
            detail={
                "error_type": "auth",
                "error_reason": "api_key_missing",
                "message": "x-api-key header is required.",
            },
        )
    if not any(secrets.compare_digest(api_key_header, candidate) for candidate in valid_keys):
        raise HTTPException(
            status_code=403,
            detail={
                "error_type": "auth",
                "error_reason": "api_key_invalid",
                "message": "API key is not authorized.",
            },
        )
    return api_key_header


def is_auth_enforced() -> bool:
    """Return True when explicit API-key auth mode is enabled."""
    return os.getenv("HORUS_AUTH_MODE", "disabled").strip().lower() == "api_key"


def is_valid_api_key(candidate: str | None) -> bool:
    """Check if candidate matches any configured server API key in constant time."""
    if not candidate:
        return False
    valid_keys = _configured_api_keys()
    if not valid_keys:
        return False
    return any(secrets.compare_digest(candidate, k) for k in valid_keys)


def _configured_api_keys() -> list[str]:
    keys = []
    for name in ("HORUS_ADMIN_API_KEY", "HORUS_API_KEY", "NEXT_PUBLIC_API_KEY", "API_KEY"):
        value = os.getenv(name, "").strip()
        if value and value not in keys:
            keys.append(value)
    return keys
