"""Microsoft Graph client (port of MicrosoftGraphService.php).

Uses client_credentials grant for app-only access. Tokens are cached
in-memory keyed by tenant+client.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

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


def _get_all(token: str, url: str, max_pages: int = 50) -> list[dict]:
    """GET a collection, transparently following @odata.nextLink."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    items: list[dict] = []
    for _ in range(max_pages):
        resp = httpx.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("value", []))
        next_link = data.get("@odata.nextLink")
        if not next_link:
            break
        url = next_link
    return items


def list_sites(token: str, query: str = "") -> list[dict]:
    """List SharePoint sites in the tenant.

    Without a query, uses ``/sites/getAllSites`` which enumerates every
    site regardless of search-index state. With a query, uses
    ``/sites?search=`` which filters by display name / URL. Results are
    sorted alphabetically by display name.
    """
    term = query.strip()
    if term:
        url = f"{GRAPH_BASE}/sites?search={quote(term)}&$top=999"
    else:
        url = f"{GRAPH_BASE}/sites/getAllSites?$top=999"
    try:
        sites = _get_all(token, url)
    except httpx.HTTPStatusError:
        # getAllSites requires Sites.Read.All on some tenants and may 403;
        # fall back to the v1.0 search wildcard.
        if not term:
            sites = _get_all(token, f"{GRAPH_BASE}/sites?search=*&$top=999")
        else:
            raise
    sites.sort(key=lambda s: (s.get("displayName") or s.get("name") or "").lower())
    return sites


def list_site_drives(token: str, site_id: str) -> list[dict]:
    return _get(token, f"/sites/{site_id}/drives")


def list_users(token: str) -> list[dict]:
    return _get(token, "/users?$select=id,displayName,mail,userPrincipalName")


def list_user_drives(token: str, user_id: str) -> list[dict]:
    return _get(token, f"/users/{user_id}/drives")


def list_drive_children(token: str, drive_id: str, item_id: str = "") -> list[dict]:
    """List folder children within a drive.

    If *item_id* is empty, lists the root of the drive. Otherwise lists
    children of the given item (folder). Only folders are returned.
    """
    if item_id:
        path = f"/drives/{drive_id}/items/{item_id}/children"
    else:
        path = f"/drives/{drive_id}/root/children"
    items = _get(token, path + "?$top=200")
    return [i for i in items if "folder" in i]
