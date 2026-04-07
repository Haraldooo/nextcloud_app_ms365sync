"""Browse Microsoft 365 OneDrive / SharePoint resources."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import graph, storage

router = APIRouter()


def _token(tenant_id: int) -> str:
    t = storage.get_tenant(tenant_id)
    if not t:
        raise HTTPException(404, "tenant not found")
    try:
        return graph.get_token(t.tenant_id, t.client_id, t.client_secret)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"graph auth failed: {exc}") from exc


@router.get("/{tenant_id}/sites")
def list_sites(tenant_id: int):
    return graph.list_sites(_token(tenant_id))


@router.get("/{tenant_id}/sites/{site_id}/drives")
def list_site_drives(tenant_id: int, site_id: str):
    return graph.list_site_drives(_token(tenant_id), site_id)


@router.get("/{tenant_id}/users")
def list_users(tenant_id: int):
    return graph.list_users(_token(tenant_id))


@router.get("/{tenant_id}/users/{user_id}/drives")
def list_user_drives(tenant_id: int, user_id: str):
    return graph.list_user_drives(_token(tenant_id), user_id)


@router.get("/{tenant_id}/me/drives")
def list_my_drives(tenant_id: int, userId: str):  # noqa: N803 (matches Vue UI)
    # Application-only auth has no "me" — UI passes the chosen user id.
    return graph.list_user_drives(_token(tenant_id), userId)
