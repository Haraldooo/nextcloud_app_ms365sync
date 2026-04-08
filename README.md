# MS365 Sync — Nextcloud ExApp

A Nextcloud **External App (ExApp)** that syncs Microsoft 365 OneDrive and SharePoint document libraries into Nextcloud.

Built on the Nextcloud AppAPI framework: a single, stateless, versioned Docker image deployed via `occ app_api:app:deploy`. No PHP code in `custom_apps/`, no separate sidecar containers.

## Features

- Connect to Azure AD tenants via App Registration (Client Credentials)
- Browse OneDrive and SharePoint sites/drives
- Configure sync jobs with Nextcloud destination folders
- Resilient file transfers via rclone (handles 100 GB+ overnight)
- Start, pause, and restart jobs
- View rclone transfer logs in the browser
- Uploads via Nextcloud WebDAV API (compatible with S3 backend)

## Architecture

```
┌────── Single Docker image (ghcr.io/<org>/ms365sync-exapp:<ver>) ──────┐
│  Python 3.14 (uv-managed) + nc_py_api + FastAPI + rclone (child proc) │
│   ms365sync_exapp/        ← Python ExApp                              │
│     main.py               ← FastAPI + AppAPI lifecycle                │
│     storage.py            ← state in NC appconfig_ex (stateless app)  │
│     graph.py              ← Microsoft Graph client                    │
│     rclone/manager.py     ← embedded rclone rcd supervisor            │
│     routes/               ← /api/v1 endpoints                         │
│     ui/                   ← built Vue 3 SPA bundle (ms365sync.js/css) │
│                             served at /js/ + /css/, injected into     │
│                             AppAPI's top-menu page via set_script     │
└───────────────────────────────────────────────────────────────────────┘
```

All persistence (tenants, jobs, config) lives in Nextcloud's app config via `nc_py_api` — the container itself stores nothing on disk. Updates work by `app_api:app:deploy`-ing a new image tag; AppAPI handles the container lifecycle.

### Deploy daemons: docker-socket-proxy and HaRP

The image is deploy-daemon-agnostic and works with both AppAPI deploy daemons:

- **docker-socket-proxy** (classic): AppAPI spawns the container via the docker socket proxy and Nextcloud connects **inbound** to the ExApp on `APP_HOST:APP_PORT` (8080 by default).
- **[HaRP](https://github.com/nextcloud/HaRP)** (Nextcloud 30+): a HAProxy + FRP server that ExApp containers reach **outbound**. The traffic path is `NC → HaRP HAProxy → frps → frpc (in this container) → /tmp/exapp.sock → uvicorn`.

To support HaRP the image bundles three pieces:

1. **`frpc`** — the FRP client binary, installed multi-arch with SHA256 verification in [Dockerfile](Dockerfile). The pinned version is exposed via the `FRP_VERSION` build arg; bump it in lockstep with HaRP itself.
2. **[`start.sh`](start.sh)** — vendored from `nextcloud/HaRP/exapps_dev/start.sh`. When `HP_SHARED_KEY` is present in the env it writes `/frpc.toml` (with the `unix_domain_socket` plugin pointed at `/tmp/exapp.sock`), launches `frpc` in the background, and execs the ExApp. When it isn't, it's a transparent passthrough — so the same image still works under docker-socket-proxy.
3. **`ENTRYPOINT ["/start.sh"]`** with the existing `CMD ["python", "-m", "ms365sync_exapp.main"]`.

On the application side nothing else changes:

- `nc_py_api[app] >= 0.21` (see [pyproject.toml](pyproject.toml)) makes [`run_app()`](ms365sync_exapp/main.py#L108) bind uvicorn to `HP_EXAPP_SOCK` (default `/tmp/exapp.sock`) when `HP_SHARED_KEY` is set, so uvicorn meets `frpc` at the same socket.
- HaRP terminates the shared-key check at HAProxy and forwards the standard `EX-APP-ID` / `AUTHORIZATION-APP-API` / `AA-REQUEST-ID` headers, which [`AppAPIAuthMiddleware`](ms365sync_exapp/main.py#L58) already validates the same way as under docker-socket-proxy.
- Route handlers, `appconfig_ex` storage, and the rclone supervisor are identical in both modes.

## Publishing the image to ghcr.io

The image is published to **GitHub Container Registry** at `ghcr.io/haraldooo/ms365sync-exapp`.

### One-time setup (per machine that publishes)

1. **Create a Personal Access Token (classic)** at <https://github.com/settings/tokens> with scope **`write:packages`**.
2. **Login Docker to ghcr.io:**

   ```bash
   export CR_PAT=ghp_xxxxxxxxxxxxxxxxxxxx
   echo "$CR_PAT" | docker login ghcr.io -u haraldooo --password-stdin
   ```

3. **Make the package public** (one-time, after the first push) at <https://github.com/users/haraldooo/packages/container/ms365sync-exapp/settings> → *Change visibility → Public*. Otherwise the Nextcloud host needs to `docker login ghcr.io` too.

### Cut a release

The `Makefile` bumps every version field and builds a multi-arch image (`linux/amd64` + `linux/arm64`) in one shot:

```bash
make release VERSION=1.0.1     # bumps info.xml, pyproject.toml, package.json
git diff                       # review
git commit -am "release 1.0.1"
git tag v1.0.1 && git push --tags

make build VERSION=1.0.1       # buildx multi-arch build + push to ghcr.io
```

`make build` and `make push` are aliases — buildx must push directly because multi-arch images can't be loaded into the local Docker daemon.

### Installation on a Nextcloud host

Prerequisites: Nextcloud with the **AppAPI** app installed and a Deploy Daemon configured.

```bash
occ app_api:app:deploy ms365sync ghcr.io/haraldooo/ms365sync-exapp:1.0.1
occ app_api:app:enable ms365sync
```

If the package is private, run `docker login ghcr.io` on the Nextcloud host first with a token that has `read:packages`.

### Configuration

Open **Nextcloud → Microsoft 365 Sync** in the top navigation, then:

1. Set **Nextcloud URL** (the externally reachable URL the rclone worker should upload to).
2. Add your Azure AD tenant credentials and click **Test Connection**.
3. Set the destination user's app password via the *Container* settings (one-time).

### Azure AD App Registration

1. **Azure Portal → App Registrations → New Registration**
2. API permissions (Application type): `Sites.Read.All`, `Files.Read.All`, `User.Read.All`
3. Grant admin consent
4. Create a client secret
5. Enter Tenant ID, Client ID, and Client Secret in the app settings

### Updating

```bash
docker build -t ghcr.io/<org>/ms365sync-exapp:1.0.1 .
docker push ghcr.io/<org>/ms365sync-exapp:1.0.1
occ app_api:app:deploy ms365sync ghcr.io/<org>/ms365sync-exapp:1.0.1
```

Tenants and jobs survive updates because they live in Nextcloud, not in the container.

## Development

Python deps are managed by [uv](https://docs.astral.sh/uv/) (locked in `uv.lock`, Python 3.14). The Dockerfile uses the same lockfile via `uv sync --frozen`.

```bash
# Python: install/sync the project venv (.venv) from uv.lock
uv sync

# Run the ExApp locally (uses .venv automatically)
uv run python -m ms365sync_exapp.main

# Add / upgrade a dependency
uv add 'somepkg>=1.2'
uv lock --upgrade-package somepkg

# Frontend dev server (talks to a running ExApp at /api/v1)
npm install
npm run dev

# Build the image locally
docker build -t ms365sync-exapp:dev .
docker run --rm -p 8080:8080 ms365sync-exapp:dev
```

## License

AGPL-3.0-or-later
