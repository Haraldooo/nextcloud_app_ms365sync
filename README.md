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
│  Python 3.12 + nc_py_api + FastAPI + rclone (child process)           │
│   ms365sync_exapp/        ← Python ExApp                              │
│     main.py               ← FastAPI + AppAPI lifecycle                │
│     storage.py            ← state in NC appconfig_ex (stateless app)  │
│     graph.py              ← Microsoft Graph client                    │
│     rclone/manager.py     ← embedded rclone rcd supervisor            │
│     routes/               ← /api/v1 endpoints                         │
│     ui/                   ← built Vue 3 SPA, served at /ui/           │
└───────────────────────────────────────────────────────────────────────┘
```

All persistence (tenants, jobs, config) lives in Nextcloud's app config via `nc_py_api` — the container itself stores nothing on disk. Updates work by `app_api:app:deploy`-ing a new image tag; AppAPI handles the container lifecycle.

## Installation

Prerequisites: Nextcloud with the **AppAPI** app installed and a Deploy Daemon configured.

```bash
# 1. Build & push the image
docker build -t ghcr.io/<org>/ms365sync-exapp:1.0.0 .
docker push ghcr.io/<org>/ms365sync-exapp:1.0.0

# 2. Deploy via AppAPI on the Nextcloud host
occ app_api:app:deploy ms365sync ghcr.io/<org>/ms365sync-exapp:1.0.0
occ app_api:app:enable ms365sync
```

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

```bash
# Frontend dev server (talks to a running ExApp at /api/v1)
npm install
npm run dev

# Build the image locally
docker build -t ms365sync-exapp:dev .
docker run --rm -p 8080:8080 ms365sync-exapp:dev
```

## License

AGPL-3.0-or-later
