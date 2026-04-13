"""Sync job CRUD and lifecycle."""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .. import storage

router = APIRouter()


def _to_out(j: storage.SyncJob) -> dict:
    """Serialize a SyncJob into the camelCase shape the Vue UI expects."""
    return {
        "id": j.id,
        "tenantId": j.tenant_id,
        "name": j.name,
        "sourceType": j.source_type,
        "sourceDriveId": j.source_drive_id,
        "sourceDriveName": j.source_drive_name,
        "sourceSiteId": j.source_site_id,
        "sourcePath": j.source_path,
        "destType": "nextcloud",
        "destPath": j.dest_path,
        "destUser": j.dest_user,
        "syncMode": j.sync_mode,
        "schedule": j.schedule,
        "status": j.status,
        "lastRunAt": j.last_run_at,
        "lastError": j.last_error,
        "bytesTransferred": j.bytes_transferred,
        "filesTransferred": j.files_transferred,
        "rcloneJobId": j.rclone_job_id,
        "enabled": j.enabled,
        "createdAt": j.created_at,
        "updatedAt": j.updated_at,
    }


class JobIn(BaseModel):
    tenantId: int
    name: str
    sourceType: str
    sourceDriveId: str
    sourceDriveName: str = ""
    sourceSiteId: str | None = None
    sourcePath: str = ""
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
    j.source_path = body.sourcePath
    j.dest_path = body.destPath
    j.dest_user = body.destUser
    j.sync_mode = body.syncMode
    j.schedule = body.schedule
    j.enabled = body.enabled
    return j


@router.get("")
def list_jobs():
    return [_to_out(j) for j in storage.list_jobs()]


@router.get("/{jid}")
def get_job(jid: int):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")
    return _to_out(j)


@router.post("")
def create_job(body: JobIn):
    j = storage.save_job(_from_in(None, body))
    return _to_out(j)


@router.put("/{jid}")
def update_job(jid: int, body: JobIn):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")
    j = storage.save_job(_from_in(j, body))
    return _to_out(j)


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

    nc_url = storage.resolve_nextcloud_url()
    if not nc_url:
        raise HTTPException(
            400,
            "Could not determine Nextcloud URL: NEXTCLOUD_URL env var is not "
            "set and no override is configured in Settings.",
        )

    # The destination app password is provisioned by the operator via the
    # Settings UI (PUT /api/v1/settings/app-passwords) and stored per user.
    app_password = storage.get_app_password(j.dest_user)
    if not app_password:
        raise HTTPException(
            400,
            f"no app password configured for user {j.dest_user!r}; "
            "set one in Settings → App Passwords",
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
            source_path=j.source_path,
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
    return _to_out(j)


@router.post("/{jid}/stop")
def stop_job(jid: int, request: Request):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")
    request.app.state.rclone.stop_sync(j.id)
    j.status = "idle"
    j.rclone_job_id = None
    storage.save_job(j)
    return _to_out(j)


@router.get("/{jid}/progress")
def progress(jid: int, request: Request):
    j = storage.get_job(jid)
    if not j:
        raise HTTPException(404, "job not found")

    # If we don't have an active rclone job for it (not running, or restarted),
    # return the persisted stats so the UI can still show last-known progress.
    if j.status != "running" or j.rclone_job_id is None:
        return {
            "status": j.status,
            "finished": j.status in ("completed", "error", "idle"),
            "success": j.status == "completed",
            "error": j.last_error,
            "bytesTransferred": j.bytes_transferred,
            "filesTransferred": j.files_transferred,
            "totalBytes": 0,
            "totalFiles": 0,
            "speed": 0,
            "eta": 0,
        }

    st = request.app.state.rclone.status(j.id)
    bytes_xfer = int(st.get("bytes", 0) or 0)
    files_xfer = int(st.get("files", 0) or 0)

    if st.get("finished"):
        j.status = "completed" if st.get("success") else "error"
        j.last_error = st.get("error", "") or ""
        j.bytes_transferred = bytes_xfer
        j.files_transferred = files_xfer
        j.rclone_job_id = None
        storage.save_job(j)
    else:
        # Persist live counters so a refresh shows current progress.
        j.bytes_transferred = bytes_xfer
        j.files_transferred = files_xfer
        storage.save_job(j)

    return {
        "status": j.status,
        "finished": bool(st.get("finished", False)),
        "success": bool(st.get("success", False)),
        "error": st.get("error", "") or "",
        "bytesTransferred": bytes_xfer,
        "filesTransferred": files_xfer,
        "totalBytes": int(st.get("total_bytes", 0) or 0),
        "totalFiles": int(st.get("total_files", 0) or 0),
        "speed": st.get("speed", 0) or 0,
        "eta": st.get("eta", 0) or 0,
    }
