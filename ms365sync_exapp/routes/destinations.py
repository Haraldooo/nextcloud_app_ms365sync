"""Browse destination Nextcloud user file trees via WebDAV.

Used by the Add-Job wizard's destination picker. Operates against the
configured container Nextcloud URL using the per-user app password the
admin stored in Settings → App Passwords. Group Folders the user is a
member of show up at the WebDAV root automatically — no special-case
needed here.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

import httpx
from fastapi import APIRouter, HTTPException, Query

from .. import storage

router = APIRouter()

DAV_NS = "{DAV:}"
PROPFIND_BODY = (
    '<?xml version="1.0"?>'
    '<d:propfind xmlns:d="DAV:">'
    "<d:prop>"
    "<d:resourcetype/>"
    "<d:displayname/>"
    "</d:prop>"
    "</d:propfind>"
)


def _normalize(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    # Collapse trailing slashes except the root.
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path


@router.get("/{user}/browse")
def browse(user: str, path: str = Query("/")):
    cfg = storage.get_container_config()
    nc_url = (cfg.get("nextcloudUrl") or "").rstrip("/")
    if not nc_url:
        raise HTTPException(400, "container nextcloudUrl not configured")

    app_password = storage.get_app_password(user)
    if not app_password:
        raise HTTPException(
            400,
            f"no app password configured for user {user!r}; "
            "set one in Settings → App Passwords",
        )

    rel = _normalize(path)
    base = f"{nc_url}/remote.php/dav/files/{user}"
    url = f"{base}{rel}"
    if not url.endswith("/"):
        url += "/"

    try:
        resp = httpx.request(
            "PROPFIND",
            url,
            content=PROPFIND_BODY,
            headers={"Depth": "1", "Content-Type": "application/xml"},
            auth=(user, app_password),
            timeout=15,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"webdav request failed: {exc}") from exc

    if resp.status_code == 401:
        raise HTTPException(401, "webdav auth failed — check app password")
    if resp.status_code == 404:
        raise HTTPException(404, f"path not found: {rel}")
    if resp.status_code >= 400:
        raise HTTPException(502, f"webdav error {resp.status_code}: {resp.text[:200]}")

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as exc:
        raise HTTPException(502, f"invalid webdav response: {exc}") from exc

    # The collection itself is the first <response>; skip it.
    self_href = f"/remote.php/dav/files/{user}{rel}"
    if not self_href.endswith("/"):
        self_href += "/"

    entries: list[dict] = []
    for r in root.findall(f"{DAV_NS}response"):
        href_el = r.find(f"{DAV_NS}href")
        if href_el is None or not href_el.text:
            continue
        href = href_el.text
        # Decode percent-encoding for display + return.
        from urllib.parse import unquote
        href_decoded = unquote(href)
        if href_decoded.rstrip("/") == self_href.rstrip("/"):
            continue

        is_dir = r.find(f".//{DAV_NS}collection") is not None
        if not is_dir:
            # We only care about folders for the picker.
            continue

        # Strip the dav prefix to expose a path relative to the user root.
        prefix = f"/remote.php/dav/files/{user}"
        if href_decoded.startswith(prefix):
            rel_path = href_decoded[len(prefix):] or "/"
        else:
            rel_path = href_decoded
        rel_path = rel_path.rstrip("/") or "/"

        name = rel_path.rsplit("/", 1)[-1] or "/"
        entries.append({"name": name, "path": rel_path, "isDir": True})

    entries.sort(key=lambda e: e["name"].lower())
    return {"path": rel, "entries": entries}
