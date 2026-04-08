"""Persistence for tenants and jobs via Nextcloud app config (AppAPI).

The ExApp must be stateless, so all records live in Nextcloud's
``appconfig_ex`` key/value store, accessed through ``nc_py_api``.
Each record is JSON-encoded under a single key per id; an index key
keeps the list of ids so we can enumerate without scanning.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Iterable

from nc_py_api import NextcloudApp


def _nc():
    # nc_app from nc_py_api.ex_app is a FastAPI dependency factory, not an
    # instance. Instantiate NextcloudApp directly for use outside request scope.
    return NextcloudApp()

TENANT_INDEX_KEY = "tenants_index"
TENANT_KEY_PREFIX = "tenant_"
JOB_INDEX_KEY = "jobs_index"
JOB_KEY_PREFIX = "job_"
CONTAINER_CFG_KEY = "container_config"
APP_PASSWORD_KEY_PREFIX = "dest_app_password_"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass
class AzureTenant:
    id: int
    name: str
    tenant_id: str
    client_id: str
    client_secret: str
    status: str = "unchecked"  # unchecked|valid|invalid
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class SyncJob:
    id: int
    tenant_id: int
    name: str
    source_type: str  # onedrive|sharepoint
    source_drive_id: str
    source_drive_name: str = ""
    source_site_id: str | None = None
    dest_path: str = ""
    dest_user: str = ""
    sync_mode: str = "copy"  # copy|sync
    schedule: str = "manual"
    status: str = "idle"  # idle|running|completed|error
    last_run_at: float | None = None
    last_error: str = ""
    bytes_transferred: int = 0
    files_transferred: int = 0
    rclone_job_id: int | None = None
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _get(key: str) -> str | None:
    return _nc().appconfig_ex.get_value(key, default=None)


def _set(key: str, value: str) -> None:
    _nc().appconfig_ex.set_value(key, value)


def _delete(key: str) -> None:
    """Delete an app-config key.

    nc_py_api renamed the API across versions: ``delete`` (single key) vs
    ``delete_values`` (list). Try both rather than swallowing failures
    silently — silent swallowing accumulates dead keys forever.
    """
    api = _nc().appconfig_ex
    if hasattr(api, "delete"):
        api.delete(key)
    elif hasattr(api, "delete_values"):
        api.delete_values([key])
    else:
        raise RuntimeError(
            "appconfig_ex exposes neither delete() nor delete_values()"
        )


def _load_index(key: str) -> list[int]:
    raw = _get(key)
    if not raw:
        return []
    try:
        return list(json.loads(raw))
    except Exception:
        return []


def _save_index(key: str, ids: Iterable[int]) -> None:
    _set(key, json.dumps(sorted(set(ids))))


def _next_id(index: list[int]) -> int:
    return (max(index) + 1) if index else 1


# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------


def list_tenants() -> list[AzureTenant]:
    out: list[AzureTenant] = []
    for tid in _load_index(TENANT_INDEX_KEY):
        raw = _get(f"{TENANT_KEY_PREFIX}{tid}")
        if raw:
            out.append(AzureTenant(**json.loads(raw)))
    return out


def get_tenant(tid: int) -> AzureTenant | None:
    raw = _get(f"{TENANT_KEY_PREFIX}{tid}")
    return AzureTenant(**json.loads(raw)) if raw else None


def save_tenant(t: AzureTenant) -> AzureTenant:
    index = _load_index(TENANT_INDEX_KEY)
    if not t.id:
        t.id = _next_id(index)
    t.updated_at = time.time()
    _set(f"{TENANT_KEY_PREFIX}{t.id}", json.dumps(asdict(t)))
    if t.id not in index:
        index.append(t.id)
        _save_index(TENANT_INDEX_KEY, index)
    return t


def delete_tenant(tid: int) -> None:
    _delete(f"{TENANT_KEY_PREFIX}{tid}")
    index = [i for i in _load_index(TENANT_INDEX_KEY) if i != tid]
    _save_index(TENANT_INDEX_KEY, index)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


def list_jobs() -> list[SyncJob]:
    out: list[SyncJob] = []
    for jid in _load_index(JOB_INDEX_KEY):
        raw = _get(f"{JOB_KEY_PREFIX}{jid}")
        if raw:
            out.append(SyncJob(**json.loads(raw)))
    return out


def get_job(jid: int) -> SyncJob | None:
    raw = _get(f"{JOB_KEY_PREFIX}{jid}")
    return SyncJob(**json.loads(raw)) if raw else None


def save_job(j: SyncJob) -> SyncJob:
    index = _load_index(JOB_INDEX_KEY)
    if not j.id:
        j.id = _next_id(index)
    j.updated_at = time.time()
    _set(f"{JOB_KEY_PREFIX}{j.id}", json.dumps(asdict(j)))
    if j.id not in index:
        index.append(j.id)
        _save_index(JOB_INDEX_KEY, index)
    return j


def delete_job(jid: int) -> None:
    _delete(f"{JOB_KEY_PREFIX}{jid}")
    index = [i for i in _load_index(JOB_INDEX_KEY) if i != jid]
    _save_index(JOB_INDEX_KEY, index)


# ---------------------------------------------------------------------------
# Container / Nextcloud target config
# ---------------------------------------------------------------------------


def get_container_config() -> dict:
    raw = _get(CONTAINER_CFG_KEY)
    return json.loads(raw) if raw else {"nextcloudUrl": ""}


def set_container_config(cfg: dict) -> dict:
    _set(CONTAINER_CFG_KEY, json.dumps(cfg))
    return cfg


# ---------------------------------------------------------------------------
# Per-user WebDAV app passwords
# ---------------------------------------------------------------------------
#
# Each sync job writes to a Nextcloud user's WebDAV root, so we need an app
# password for that user. AppAPI does not expose a stable cross-version API
# for an ExApp to mint a password on behalf of an arbitrary user, so the
# admin sets one per user via the Settings UI. We store them in app config
# (encrypted at rest by Nextcloud's secrets store) keyed by user id.


def get_app_password(user: str) -> str:
    return _get(f"{APP_PASSWORD_KEY_PREFIX}{user}") or ""


def set_app_password(user: str, password: str) -> None:
    _set(f"{APP_PASSWORD_KEY_PREFIX}{user}", password)


def delete_app_password(user: str) -> None:
    _delete(f"{APP_PASSWORD_KEY_PREFIX}{user}")


def list_app_password_users() -> list[str]:
    """Return the list of user ids that have a stored app password.

    The appconfig_ex API doesn't support prefix scans on every nc_py_api
    version, so we maintain an index alongside the values."""
    raw = _get("dest_app_password_users")
    if not raw:
        return []
    try:
        return list(json.loads(raw))
    except Exception:
        return []


def _save_app_password_users(users: list[str]) -> None:
    _set("dest_app_password_users", json.dumps(sorted(set(users))))


def add_app_password_user(user: str) -> None:
    users = list_app_password_users()
    if user not in users:
        users.append(user)
        _save_app_password_users(users)


def remove_app_password_user(user: str) -> None:
    users = [u for u in list_app_password_users() if u != user]
    _save_app_password_users(users)
