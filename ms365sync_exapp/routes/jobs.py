"""Sync job CRUD and lifecycle."""

from __future__ import annotations

import time
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .. import storage

router = APIRouter()


class JobIn(BaseModel):
    tenantId: int
    name: str
    sourceType: str
    sourceDriveId: str
    sourceDriveName: str = ""
    sourceSiteId: str | None = None
    destPath: str = ""
    destUser: str = ""
    syncMode: str = "copy"
    schedule: str = "manual"
    enabled: bool = True


def _from_in(j: storage.SyncJob | None, body: JobIn) -> storage.SyncJob:
    if j is None:
        j = storage.SyncJob(
            id=0,
            tenant_id=body.tenantId,
            name=body.name,
            source_type=body.sourceType,
            source_drive_id=body.sourceDriveId,
        )
    j.tenant_id = body.tenantId
    j.name = body.name
    j.source_type = body.sourceType
    j.source_drive_id = body.sourceDriveId
    j.source_drive_name = body.sourceDriveName
    j.source_site_id = body.sourceSiteId
    j.dest_path = body.destPath
    j.dest_user = body.destUser
    j.sync_mode = body.syncMode
    j.schedule = body.schedule
    j.enabled = body.enabled
    return j


@router.get("")
def list_jobs():
    return [asdict(j) for j in storage.list_jobs()]


@router.get("/{jid}")
def get_job(jid: int):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")
    return asdict(j)


@router.post("")
def create_job(body: JobIn):
    j = storage.save_job(_from_in(None, body))
    return asdict(j)


@router.put("/{jid}")
def update_job(jid: int, body: JobIn):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")
    j = storage.save_job(_from_in(j, body))
    return asdict(j)


@router.delete("/{jid}")
def delete_job(jid: int):
    storage.delete_job(jid)
    return {"ok": True}


@router.post("/{jid}/start")
def start_job(jid: int, request: Request):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")
    tenant = storage.get_tenant(j.tenant_id)
    if not tenant:
        raise HTTPException(400, "tenant missing")

    cfg = storage.get_container_config()
    nc_url = cfg.get("nextcloudUrl") or ""
    if not nc_url:
        raise HTTPException(400, "container nextcloudUrl not configured")

    # The destination app password is provisioned by the operator and stored
    # in app config under "dest_app_password_<user>". This avoids generating
    # short-lived credentials per request, which depends on AppAPI version.
    app_password = storage.nc_app.appconfig_ex.get_value(
        f"dest_app_password_{j.dest_user}", default=""
    ) if hasattr(storage.nc_app, "appconfig_ex") else ""
    if not app_password:
        raise HTTPException(
            400,
            f"no app password configured for user {j.dest_user!r}; "
            "set it via /api/v1/settings/container",
        )

    rclone = request.app.state.rclone
    try:
        rid = rclone.start_sync(
            nc_job_id=j.id,
            tenant_id=tenant.tenant_id,
            client_id=tenant.client_id,
            client_secret=tenant.client_secret,
            drive_id=j.source_drive_id,
            nextcloud_url=nc_url,
            dest_user=j.dest_user,
            app_password=app_password,
            dest_path=j.dest_path,
            sync_mode=j.sync_mode,
        )
    except Exception as exc:  # noqa: BLE001
        j.status = "error"
        j.last_error = str(exc)
        storage.save_job(j)
        raise HTTPException(500, str(exc)) from exc

    j.status = "running"
    j.rclone_job_id = rid
    j.last_run_at = time.time()
    j.last_error = ""
    storage.save_job(j)
    return asdict(j)


@router.post("/{jid}/stop")
def stop_job(jid: int, request: Request):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")
    request.app.state.rclone.stop_sync(j.id)
    j.status = "idle"
    j.rclone_job_id = None
    storage.save_job(j)
    return asdict(j)


@router.get("/{jid}/progress")
def progress(jid: int, request: Request):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")
    st = request.app.state.rclone.status(j.id)
    if st.get("finished"):
        j.status = "completed" if st.get("success") else "error"
        j.last_error = st.get("error", "")
        j.bytes_transferred = int(st.get("bytes", 0))
        j.files_transferred = int(st.get("files", 0))
        j.rclone_job_id = None
        storage.save_job(j)
    return st
