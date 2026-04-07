"""FastAPI entry point for the ms365sync ExApp.

Wires up the AppAPI lifecycle (handled by nc_py_api), serves the static
Vue UI under /ui, exposes the JSON API under /api/v1, and starts the
embedded rclone daemon as a child process for the lifetime of the app.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from nc_py_api.ex_app import (
    AppAPIAuthMiddleware,
    LogLvl,
    nc_app,
    run_app,
    set_handlers,
)

from .rclone.manager import RcloneManager
from .routes import jobs, libraries, logs, settings

UI_DIR = Path(__file__).parent / "ui"

rclone = RcloneManager()


@asynccontextmanager
async def lifespan(_: FastAPI):
    rclone.start()
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


def _enabled_handler(enabled: bool, nc) -> str:
    """AppAPI calls this on enable/disable. Return "" on success."""
    try:
        if enabled:
            nc.log(LogLvl.INFO, "ms365sync enabled")
            # Register the top-menu entry that opens the embedded SPA.
            nc.ui.resources.set_script("top_menu", "ms365sync", "ui/")
            nc.ui.top_menu.register(
                name="ms365sync",
                display_name="Microsoft 365 Sync",
                admin_required=True,
            )
        else:
            nc.log(LogLvl.INFO, "ms365sync disabled")
            nc.ui.top_menu.unregister("ms365sync")
        return ""
    except Exception as exc:  # noqa: BLE001
        return str(exc)


set_handlers(APP, _enabled_handler)


@APP.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/")


if UI_DIR.exists():
    APP.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


# Expose the rclone manager to route modules via app.state
APP.state.rclone = rclone
APP.state.nc_app = nc_app


if __name__ == "__main__":
    run_app("ms365sync_exapp.main:APP", log_level="info")
