"""Microsoft Graph client (port of MicrosoftGraphService.php).

Uses client_credentials grant for app-only access. Tokens are cached
in-memory keyed by tenant+client.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

_token_cache: dict[str, tuple[str, float]] = {}


def get_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    key = f"{tenant_id}:{client_id}"
    cached = _token_cache.get(key)
    if cached and cached[1] > time.time():
        return cached[0]

    resp = httpx.post(
        TOKEN_URL.format(tenant=tenant_id),
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data["access_token"]
    _token_cache[key] = (token, time.time() + int(data["expires_in"]) - 60)
    return token


def _get(token: str, path: str) -> Any:
    resp = httpx.get(
        f"{GRAPH_BASE}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("value", data)


def list_sites(token: str) -> list[dict]:
    return _get(token, "/sites?search=*")


def list_site_drives(token: str, site_id: str) -> list[dict]:
    return _get(token, f"/sites/{site_id}/drives")


def list_users(token: str) -> list[dict]:
    return _get(token, "/users?$select=id,displayName,mail,userPrincipalName")


def list_user_drives(token: str, user_id: str) -> list[dict]:
    return _get(token, f"/users/{user_id}/drives")
