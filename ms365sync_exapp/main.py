"""FastAPI entry point for the ms365sync ExApp.

Wires up the AppAPI lifecycle (handled by nc_py_api), serves the Vue
SPA bundle under /js and /css (loaded into Nextcloud's top-menu page
via nc.ui.resources.set_script/set_style), exposes the JSON API under
/api/v1, and starts the embedded rclone daemon as a child process for
the lifetime of the app.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from nc_py_api import AsyncNextcloudApp
from nc_py_api.ex_app import (
    AppAPIAuthMiddleware,
    LogLvl,
    nc_app,
    run_app,
    set_handlers,
)

from . import storage
from .rclone.manager import RcloneManager
from .routes import destinations, jobs, libraries, logs, settings

UI_DIR = Path(__file__).parent / "ui"

rclone = RcloneManager()


@asynccontextmanager
async def lifespan(_: FastAPI):
    rclone.start()
    # Reconcile persisted job state with the freshly-started rclone daemon.
    # The in-memory _active map is empty after a container restart, so any
    # job persisted as "running" would otherwise be unkillable and report
    # "unknown job" forever. Mark them as errored so the operator can
    # restart them explicitly.
    try:
        for j in storage.list_jobs():
            if j.status == "running":
                j.status = "error"
                j.last_error = "container restarted while job was running"
                j.rclone_job_id = None
                storage.save_job(j)
    except Exception:  # noqa: BLE001
        # Storage may not be reachable yet on first boot; non-fatal.
        pass
    try:
        yield
    finally:
        rclone.stop()


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(AppAPIAuthMiddleware)

APP.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
APP.include_router(libraries.router, prefix="/api/v1/libraries", tags=["libraries"])
APP.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
APP.include_router(logs.router, prefix="/api/v1/logs", tags=["logs"])
APP.include_router(destinations.router, prefix="/api/v1/destinations", tags=["destinations"])


async def _enabled_handler(enabled: bool, nc: AsyncNextcloudApp) -> str:
    """AppAPI calls this on enable/disable. Return "" on success.

    Must be async — sync handlers are deprecated in nc_py_api 0.30 and
    removed in 0.31. The async path passes an AsyncNextcloudApp, so the
    nc.log / nc.ui.* calls below are awaitable HTTP roundtrips.
    """
    try:
        if enabled:
            await nc.log(LogLvl.INFO, "ms365sync enabled")
            # Register the self-mounting SPA bundle + its stylesheet.
            # AppAPI injects these into the Nextcloud-rendered top-menu page.
            # NB: AppAPI appends ".js"/".css" to these paths automatically,
            # so do NOT include the extension here.
            await nc.ui.resources.set_script("top_menu", "ms365sync", "js/ms365sync")
            await nc.ui.resources.set_style("top_menu", "ms365sync", "css/ms365sync")
            await nc.ui.top_menu.register(
                name="ms365sync",
                display_name="Microsoft 365 Sync",
                admin_required=True,
            )
        else:
            await nc.log(LogLvl.INFO, "ms365sync disabled")
            await nc.ui.top_menu.unregister("ms365sync")
        return ""
    except Exception as exc:  # noqa: BLE001
        return str(exc)


set_handlers(APP, _enabled_handler)


# Serve the bundle + stylesheet at stable URLs that AppAPI's set_script /
# set_style point at. The Dockerfile drops dist/ms365sync.js and
# dist/ms365sync.css into UI_DIR at image build time.
if UI_DIR.exists():
    APP.mount("/js", StaticFiles(directory=str(UI_DIR)), name="js")
    APP.mount("/css", StaticFiles(directory=str(UI_DIR)), name="css")


# Expose the rclone manager to route modules via app.state
APP.state.rclone = rclone
APP.state.nc_app = nc_app


if __name__ == "__main__":
    run_app("ms365sync_exapp.main:APP", log_level="info")
