"""Manages rclone RC API calls and dynamic remote configuration."""

import json
import requests
import logging

logger = logging.getLogger(__name__)

RCLONE_RC = "http://127.0.0.1:5572"


def rc_call(endpoint, params=None):
    """Call rclone RC API endpoint."""
    url = f"{RCLONE_RC}/{endpoint}"
    resp = requests.post(url, json=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def rc_get(endpoint, params=None):
    """GET from rclone RC API."""
    url = f"{RCLONE_RC}/{endpoint}"
    resp = requests.post(url, json=params or {}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def create_onedrive_remote(remote_name, tenant_id, client_id, client_secret, drive_id):
    """Create a dynamic OneDrive remote via rclone RC config/create."""
    params = {
        "name": remote_name,
        "type": "onedrive",
        "parameters": {
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant": tenant_id,
            "drive_id": drive_id,
            "drive_type": "business",
            # Use client_credentials token flow
            "token": "",
            "auth_url": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
            "token_url": f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        },
    }
    return rc_call("config/create", params)


def create_webdav_remote(remote_name, nextcloud_url, dest_user, app_password):
    """Create a WebDAV remote pointing to Nextcloud."""
    # Ensure URL ends with the user's WebDAV path
    webdav_url = nextcloud_url.rstrip("/")
    if "/remote.php/dav/files/" not in webdav_url:
        webdav_url = f"{webdav_url}/remote.php/dav/files/{dest_user}"

    params = {
        "name": remote_name,
        "type": "webdav",
        "parameters": {
            "url": webdav_url,
            "vendor": "nextcloud",
            "user": dest_user,
            "pass": app_password,
        },
    }
    return rc_call("config/create", params)


def delete_remote(remote_name):
    """Delete a remote config."""
    try:
        rc_call("config/delete", {"name": remote_name})
    except Exception as e:
        logger.warning(f"Failed to delete remote {remote_name}: {e}")


def start_sync(src_remote, dst_remote, dst_path, sync_mode="copy", job_id=None):
    """Start an async rclone copy/sync operation.

    Returns the rclone job ID.
    """
    endpoint = "sync/copy" if sync_mode == "copy" else "sync/sync"

    params = {
        "srcFs": f"{src_remote}:",
        "dstFs": f"{dst_remote}:{dst_path}",
        "_async": True,
        "_config": {
            "Retries": 10,
            "RetrySleep": "30s",
            "LowLevelRetries": 10,
            "CheckSum": True,
        },
    }

    if job_id is not None:
        params["_group"] = f"job/{job_id}"

    result = rc_call(endpoint, params)
    return result.get("jobid")


def stop_job(rclone_job_id):
    """Stop a running rclone job."""
    return rc_call("job/stop", {"jobid": rclone_job_id})


def get_job_status(rclone_job_id):
    """Get status of a running rclone job."""
    return rc_call("job/status", {"jobid": rclone_job_id})


def get_stats(group=None):
    """Get transfer statistics."""
    params = {}
    if group:
        params["group"] = group
    return rc_call("core/stats", params)


def check_health():
    """Check if rclone RC is responsive."""
    try:
        result = rc_call("core/version")
        return {"status": "ok", "rclone_version": result.get("version", "unknown")}
    except Exception as e:
        return {"status": "error", "error": str(e)}
