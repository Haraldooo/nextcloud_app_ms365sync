"""Tenant CRUD + container/Nextcloud-target config."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import graph, storage

router = APIRouter()


class TenantIn(BaseModel):
    name: str
    tenantId: str
    clientId: str
    clientSecret: str


class ContainerCfgIn(BaseModel):
    # Optional override; leave empty to use the auto-detected NEXTCLOUD_URL
    # that AppAPI provides to the container.
    nextcloudUrl: str | None = None


class AppPasswordIn(BaseModel):
    user: str
    password: str


def _serialize(t: storage.AzureTenant) -> dict:
    d = asdict(t)
    # Never expose the secret to the UI
    d.pop("client_secret", None)
    return d


# ----- Tenants ---------------------------------------------------------------


@router.get("/tenants")
def list_tenants():
    return [_serialize(t) for t in storage.list_tenants()]


@router.post("/tenants")
def create_tenant(body: TenantIn):
    t = storage.AzureTenant(
        id=0,
        name=body.name,
        tenant_id=body.tenantId,
        client_id=body.clientId,
        client_secret=body.clientSecret,
    )
    return _serialize(storage.save_tenant(t))


@router.put("/tenants/{tid}")
def update_tenant(tid: int, body: TenantIn):
    t = storage.get_tenant(tid)
    if not t:
        raise HTTPException(404, "tenant not found")
    t.name = body.name
    t.tenant_id = body.tenantId
    t.client_id = body.clientId
    if body.clientSecret:
        t.client_secret = body.clientSecret
    t.status = "unchecked"
    return _serialize(storage.save_tenant(t))


@router.delete("/tenants/{tid}")
def delete_tenant(tid: int):
    storage.delete_tenant(tid)
    return {"ok": True}


@router.post("/tenants/{tid}/test")
def test_tenant(tid: int):
    t = storage.get_tenant(tid)
    if not t:
        raise HTTPException(404, "tenant not found")
    try:
        graph.get_token(t.tenant_id, t.client_id, t.client_secret)
        t.status = "valid"
    except Exception as exc:  # noqa: BLE001
        t.status = "invalid"
        storage.save_tenant(t)
        raise HTTPException(
            400,
            {"status": "invalid", "message": f"connection failed: {exc}"},
        ) from exc
    storage.save_tenant(t)
    return {"status": "valid", "message": "Connection OK"}


# ----- Container / target config --------------------------------------------


@router.get("/container")
def get_container():
    cfg = storage.get_container_config()
    override = (cfg.get("nextcloudUrl") or "").strip()
    detected = storage.detect_nextcloud_url()
    return {
        # Operator override (empty string means "use detected").
        "nextcloudUrl": override,
        # What we'll actually use, so the UI can show it.
        "nextcloudUrlEffective": override or detected,
        "nextcloudUrlDetected": detected,
    }


@router.put("/container")
def set_container(body: ContainerCfgIn):
    cfg = storage.get_container_config()
    if body.nextcloudUrl is not None:
        cfg["nextcloudUrl"] = body.nextcloudUrl.strip()
    storage.set_container_config(cfg)
    return get_container()


# ----- Per-user WebDAV app passwords ----------------------------------------


@router.get("/app-passwords")
def list_app_passwords():
    """Return the list of users that have a stored app password.

    The password itself is never returned to the UI."""
    return [{"user": u} for u in storage.list_app_password_users()]


@router.put("/app-passwords")
def set_app_password(body: AppPasswordIn):
    if not body.user or not body.password:
        raise HTTPException(400, "user and password are required")
    storage.set_app_password(body.user, body.password)
    storage.add_app_password_user(body.user)
    return {"user": body.user, "ok": True}


@router.delete("/app-passwords/{user}")
def delete_app_password(user: str):
    storage.delete_app_password(user)
    storage.remove_app_password_user(user)
    return {"ok": True}
