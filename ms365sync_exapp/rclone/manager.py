"""Embedded rclone daemon manager.

Spawns ``rclone rcd`` as a child process for the lifetime of the
container and exposes a thin Python API over its RC interface. This is a
direct port of the previous ``docker/wrapper/rclone_manager.py`` plus
the lifecycle bits that used to live in ``app.py``.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

RC_ADDR = "127.0.0.1:5572"
RC_URL = f"http://{RC_ADDR}"
LOG_FILE = Path(os.environ.get("RCLONE_LOG_FILE", "/tmp/rclone-daemon.log"))


class RcloneManager:
    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        # nc_job_id -> {rclone_jobid, src_remote, dst_remote, started_at}
        self._active: dict[int, dict[str, Any]] = {}

    # ------------------------------------------------------------------ lifecycle

    def start(self) -> None:
        if self._proc and self._proc.poll() is None:
            return
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        log_fp = LOG_FILE.open("ab")
        self._proc = subprocess.Popen(
            [
                "rclone",
                "rcd",
                f"--rc-addr={RC_ADDR}",
                "--rc-no-auth",
                "--log-level=INFO",
            ],
            stdout=log_fp,
            stderr=log_fp,
        )
        # Wait for it to come up.
        for _ in range(50):
            try:
                self._call("core/version")
                logger.info("rclone rcd is ready")
                return
            except Exception:
                time.sleep(0.1)
        raise RuntimeError("rclone rcd failed to start")

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    # ------------------------------------------------------------------ rc helpers

    def _call(self, endpoint: str, params: dict | None = None) -> dict:
        resp = httpx.post(f"{RC_URL}/{endpoint}", json=params or {}, timeout=30)
        if resp.status_code >= 400:
            # Surface rclone's own error message instead of an opaque HTTPError.
            try:
                err = resp.json().get("error") or resp.text
            except Exception:  # noqa: BLE001
                err = resp.text
            raise RuntimeError(f"rclone {endpoint} failed: {err}")
        return resp.json()

    def health(self) -> dict:
        try:
            v = self._call("core/version")
            return {"status": "ok", "rclone_version": v.get("version", "unknown")}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------ remotes

    def _create_onedrive_remote(
        self,
        remote_name: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        drive_id: str,
    ) -> None:
        # App-only auth: rclone's onedrive backend supports client_credentials
        # mode natively (rclone >= 1.65). With client_credentials=true rclone
        # mints + refreshes the token itself via the tenant token endpoint, so
        # we must NOT pass token=""  — that would push it into the interactive
        # OAuth flow and try to bind a localhost callback inside the container.
        self._call(
            "config/create",
            {
                "name": remote_name,
                "type": "onedrive",
                "parameters": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "tenant": tenant_id,
                    "drive_id": drive_id,
                    "drive_type": "business",
                    "client_credentials": "true",
                },
                "opt": {"nonInteractive": True},
            },
        )

    def _create_webdav_remote(
        self, remote_name: str, nextcloud_url: str, dest_user: str, app_password: str
    ) -> None:
        webdav_url = nextcloud_url.rstrip("/")
        if "/remote.php/dav/files/" not in webdav_url:
            webdav_url = f"{webdav_url}/remote.php/dav/files/{dest_user}"
        self._call(
            "config/create",
            {
                "name": remote_name,
                "type": "webdav",
                "parameters": {
                    "url": webdav_url,
                    "vendor": "nextcloud",
                    "user": dest_user,
                    "pass": app_password,
                },
                "opt": {"nonInteractive": True},
            },
        )

    def _delete_remote(self, name: str) -> None:
        try:
            self._call("config/delete", {"name": name})
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to delete remote %s: %s", name, exc)

    # ------------------------------------------------------------------ jobs

    def start_sync(
        self,
        *,
        nc_job_id: int,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        drive_id: str,
        source_path: str = "",
        nextcloud_url: str,
        dest_user: str,
        app_password: str,
        dest_path: str,
        sync_mode: str = "copy",
    ) -> int:
        src = f"ms365_src_{nc_job_id}"
        dst = f"nc_dst_{nc_job_id}"
        try:
            self._create_onedrive_remote(src, tenant_id, client_id, client_secret, drive_id)
            self._create_webdav_remote(dst, nextcloud_url, dest_user, app_password)
            endpoint = "sync/copy" if sync_mode == "copy" else "sync/sync"
            result = self._call(
                endpoint,
                {
                    "srcFs": f"{src}:{source_path}" if source_path else f"{src}:",
                    "dstFs": f"{dst}:{dest_path.rstrip('/')}/{source_path.rsplit('/', 1)[-1]}" if source_path else f"{dst}:{dest_path}",
                    "_async": True,
                    "_group": f"job/{nc_job_id}",
                    "_config": {
                        "Retries": 10,
                        "RetrySleep": "30s",
                        "LowLevelRetries": 10,
                        "CheckSum": True,
                    },
                },
            )
            rclone_jobid = int(result["jobid"])
            self._active[nc_job_id] = {
                "rclone_jobid": rclone_jobid,
                "src_remote": src,
                "dst_remote": dst,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            return rclone_jobid
        except Exception:
            self._delete_remote(src)
            self._delete_remote(dst)
            raise

    def stop_sync(self, nc_job_id: int) -> None:
        info = self._active.get(nc_job_id)
        if not info:
            return
        try:
            self._call("job/stop", {"jobid": info["rclone_jobid"]})
        finally:
            self._delete_remote(info["src_remote"])
            self._delete_remote(info["dst_remote"])
            self._active.pop(nc_job_id, None)

    def status(self, nc_job_id: int) -> dict:
        info = self._active.get(nc_job_id)
        if not info:
            return {"finished": True, "success": False, "error": "unknown job"}
        try:
            st = self._call("job/status", {"jobid": info["rclone_jobid"]})
            try:
                stats = self._call("core/stats", {"group": f"job/{nc_job_id}"})
            except Exception:
                stats = {}
            result = {
                "finished": st.get("finished", False),
                "success": st.get("success", False),
                "error": st.get("error", ""),
                "bytes": stats.get("bytes", 0),
                "files": stats.get("transfers", 0),
                "speed": stats.get("speed", 0),
                "eta": stats.get("eta", 0),
                "total_bytes": stats.get("totalBytes", 0),
                "total_files": stats.get("totalTransfers", 0),
            }
            if result["finished"]:
                self._delete_remote(info["src_remote"])
                self._delete_remote(info["dst_remote"])
                self._active.pop(nc_job_id, None)
            return result
        except Exception as exc:  # noqa: BLE001
            return {"finished": True, "success": False, "error": str(exc)}

    def tail_log(self, lines: int = 100, nc_job_id: int | None = None) -> str:
        if not LOG_FILE.exists():
            return ""
        with LOG_FILE.open("r") as f:
            data = f.readlines()
        # rclone log lines are not tagged with the _group / jobid, so we
        # can't filter by needle. Instead, when a specific job is asked
        # for and is currently active, slice the log by timestamp from
        # when that job started. For finished/unknown jobs we just return
        # the tail of the whole daemon log.
        if nc_job_id is not None:
            info = self._active.get(nc_job_id)
            if info and info.get("started_at"):
                try:
                    started = datetime.fromisoformat(info["started_at"])
                except ValueError:
                    started = None
                if started is not None:
                    filtered: list[str] = []
                    keep = False
                    for line in data:
                        # rclone format: "2024/01/15 12:34:56 INFO  : ..."
                        ts = line[:19]
                        try:
                            line_dt = datetime.strptime(ts, "%Y/%m/%d %H:%M:%S").replace(
                                tzinfo=timezone.utc
                            )
                            keep = line_dt >= started
                        except ValueError:
                            # continuation line — inherit previous decision
                            pass
                        if keep:
                            filtered.append(line)
                    data = filtered
        return "".join(data[-lines:])
