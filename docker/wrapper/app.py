"""Flask wrapper for rclone RC API — job orchestration layer."""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify

import rclone_manager as rc

app = Flask(__name__)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# In-memory mapping: nc_job_id -> { rclone_jobid, src_remote, dst_remote, log_file }
active_jobs = {}


@app.route("/health", methods=["GET"])
def health():
    result = rc.check_health()
    status_code = 200 if result["status"] == "ok" else 503
    return jsonify(result), status_code


@app.route("/jobs/start", methods=["POST"])
def start_job():
    """Start a new sync job.

    Expected JSON body:
    {
        "job_id": 123,           # NC sync job ID
        "tenant_id": "...",       # Azure tenant ID
        "client_id": "...",       # Azure client ID
        "client_secret": "...",   # Azure client secret
        "drive_id": "...",        # MS Graph drive ID
        "source_type": "onedrive|sharepoint",
        "dest_path": "/path",     # Destination path in Nextcloud
        "dest_user": "admin",     # Nextcloud user
        "sync_mode": "copy|sync",
        "nextcloud_url": "https://cloud.example.com",
        "nextcloud_app_password": "xxxxx"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id required"}), 400

    src_remote = f"ms365_src_{job_id}"
    dst_remote = f"nc_dst_{job_id}"

    try:
        # Create source remote (OneDrive/SharePoint)
        rc.create_onedrive_remote(
            remote_name=src_remote,
            tenant_id=data["tenant_id"],
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            drive_id=data["drive_id"],
        )

        # Create destination remote (Nextcloud WebDAV)
        rc.create_webdav_remote(
            remote_name=dst_remote,
            nextcloud_url=data["nextcloud_url"],
            dest_user=data["dest_user"],
            app_password=data.get("nextcloud_app_password", ""),
        )

        # Start async sync
        rclone_jobid = rc.start_sync(
            src_remote=src_remote,
            dst_remote=dst_remote,
            dst_path=data.get("dest_path", ""),
            sync_mode=data.get("sync_mode", "copy"),
            job_id=job_id,
        )

        # Track active job
        active_jobs[job_id] = {
            "rclone_jobid": rclone_jobid,
            "src_remote": src_remote,
            "dst_remote": dst_remote,
            "started_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Job {job_id} started with rclone job {rclone_jobid}")
        return jsonify({"jobid": rclone_jobid, "status": "started"})

    except Exception as e:
        # Cleanup remotes on failure
        rc.delete_remote(src_remote)
        rc.delete_remote(dst_remote)
        logger.error(f"Failed to start job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/jobs/stop", methods=["POST"])
def stop_job():
    data = request.get_json()
    rclone_jobid = data.get("jobid")
    if not rclone_jobid:
        return jsonify({"error": "jobid required"}), 400

    try:
        rc.stop_job(rclone_jobid)

        # Cleanup remotes for this job
        for jid, info in list(active_jobs.items()):
            if info["rclone_jobid"] == rclone_jobid:
                rc.delete_remote(info["src_remote"])
                rc.delete_remote(info["dst_remote"])
                del active_jobs[jid]
                break

        return jsonify({"status": "stopped"})
    except Exception as e:
        logger.error(f"Failed to stop job {rclone_jobid}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/jobs/<int:rclone_job_id>/status", methods=["GET"])
def job_status(rclone_job_id):
    try:
        status = rc.get_job_status(rclone_job_id)

        # Try to get stats for this job group
        nc_job_id = None
        for jid, info in active_jobs.items():
            if info["rclone_jobid"] == rclone_job_id:
                nc_job_id = jid
                break

        stats = {}
        if nc_job_id is not None:
            try:
                stats = rc.get_stats(group=f"job/{nc_job_id}")
            except Exception:
                stats = rc.get_stats()

        result = {
            "finished": status.get("finished", False),
            "success": status.get("success", False),
            "error": status.get("error", ""),
            "bytes": stats.get("bytes", 0),
            "files": stats.get("transfers", 0),
            "speed": stats.get("speed", 0),
            "eta": stats.get("eta", 0),
            "total_bytes": stats.get("totalBytes", 0),
            "total_files": stats.get("totalTransfers", 0),
        }

        # Cleanup if finished
        if status.get("finished"):
            if nc_job_id in active_jobs:
                info = active_jobs[nc_job_id]
                rc.delete_remote(info["src_remote"])
                rc.delete_remote(info["dst_remote"])
                del active_jobs[nc_job_id]

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/jobs/<int:job_id>/log", methods=["GET"])
def job_log(job_id):
    """Return log file contents for a job."""
    log_file = f"/logs/rclone-daemon.log"
    lines = request.args.get("lines", 100, type=int)

    try:
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return "".join(tail), 200, {"Content-Type": "text/plain"}
    except FileNotFoundError:
        return "No log file found", 404


@app.route("/rclone/version", methods=["GET"])
def rclone_version():
    try:
        result = rc.rc_call("core/version")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
