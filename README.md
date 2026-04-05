# MS365 Sync — Nextcloud App

A Nextcloud app that syncs Microsoft 365 OneDrive and SharePoint document libraries into Nextcloud.
Used Claude opus 4.6 with this.

## Features

- Connect to Azure AD tenants via App Registration (Client Credentials)
- Browse OneDrive and SharePoint sites/drives
- Configure sync jobs with Nextcloud destination folders
- Resilient file transfers via rclone (handles 100GB+ overnight)
- Start, pause, and restart jobs
- View rclone transfer logs in the browser
- Uploads via Nextcloud WebDAV API (compatible with S3 backend)
- Temporary app passwords are generated automatically per job — no manual Nextcloud configuration needed

## Architecture

```
Vue 3 Frontend  <--REST-->  NC PHP Backend  <--HTTP-->  Docker Container (rclone RC + Flask)
```

- **NC PHP Backend** — REST API, database, MS365 credential management, job orchestration
- **Vue 3 Frontend** — Settings, library browser, job management, log viewer
- **Docker Sidecar** — rclone in RC daemon mode with a thin Flask wrapper for job lifecycle

## Installation

The frontend is pre-built and included in the repo. No build tools needed on the server.

### Quick install

```bash
git clone <repo-url> ms365sync
cd ms365sync
./install.sh
```

The script will:
1. Copy the app into your Nextcloud container
2. Build and start the rclone worker container
3. Wait for the worker health check
4. Enable the app in Nextcloud

> **Note:** By default the script looks for a Nextcloud container named `nc_app_sib-io`. If yours is different, run: `NC_CONTAINER=your_container_name ./install.sh`

### After install

1. Open **Nextcloud > MS365 Sync > Settings**
2. Set **Nextcloud URL** to your external domain (e.g. `https://cloud.example.com`)
3. Set **Container URL** to `http://nc_ms365sync_worker:8080`
4. Add your Azure AD tenant credentials (see below) and click **Test Connection**

### Azure AD App Registration

1. Go to **Azure Portal > App Registrations > New Registration**
2. Add API permissions (Application type):
   - `Sites.Read.All`
   - `Files.Read.All`
   - `User.Read.All`
3. Grant admin consent
4. Create a client secret
5. Enter Tenant ID, Client ID, and Client Secret in the app settings

### Updating

```bash
cd ms365sync
git pull
./install.sh
```

## Development

Building the frontend requires Node.js:

```bash
# Frontend (watch mode)
npm install
npm run dev

# One-time production build (commit the output to js/ and css/)
npm run build

# PHP dependencies
composer install

# Docker worker
cd docker && docker compose up --build
```

## License

AGPL-3.0-or-later
