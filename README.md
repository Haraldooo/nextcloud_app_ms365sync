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

## Setup

### 1. Install the Nextcloud App

```bash
cd /path/to/nextcloud/apps
git clone <repo-url> ms365sync
cd ms365sync
make build
```

Enable the app in Nextcloud under **Apps > MS365 Sync**.

### 2. Start the Docker Container

```bash
cd docker
docker-compose up -d
```

### 3. Azure AD App Registration

1. Go to **Azure Portal > App Registrations > New Registration**
2. Add API permissions (Application type):
   - `Sites.Read.All`
   - `Files.Read.All`
   - `User.Read.All`
3. Grant admin consent
4. Create a client secret
5. Note down the Tenant ID, Client ID, and Client Secret

### 4. Configure the App

1. Open **Nextcloud > MS365 Sync > Settings**
2. Enter your Nextcloud external URL and rclone container URL
3. Add your Azure tenant credentials
4. Click **Test Connection** to verify

## Development

```bash
# Frontend
npm install
npm run dev

# PHP
composer install

# Docker
cd docker && docker-compose up --build
```

## License

AGPL-3.0-or-later
