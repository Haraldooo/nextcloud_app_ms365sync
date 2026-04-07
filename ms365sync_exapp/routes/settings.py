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
    nextcloudUrl: str | None = None


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
        raise HTTPException(400, f"connection failed: {exc}") from exc
    storage.save_tenant(t)
    return {"status": "valid"}


# ----- Container / target config --------------------------------------------


@router.get("/container")
def get_container():
    return storage.get_container_config()


@router.put("/container")
def set_container(body: ContainerCfgIn):
    cfg = storage.get_container_config()
    if body.nextcloudUrl is not None:
        cfg["nextcloudUrl"] = body.nextcloudUrl
    return storage.set_container_config(cfg)
