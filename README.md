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

## Deployment (Nextcloud in Docker)

This assumes Nextcloud runs in Docker with a named volume for `/var/www/html` (the standard `nextcloud:xx-apache` setup).

### Step 1: Build the app

On your server (or locally, then `scp` the folder):

```bash
git clone <repo-url> ms365sync
cd ms365sync
npm install && npm run build
```

### Step 2: Copy the app into the Nextcloud container

```bash
# From the parent directory of ms365sync/
docker cp ms365sync nc_app_sib-io:/var/www/html/custom_apps/ms365sync
docker exec nc_app_sib-io chown -R www-data:www-data /var/www/html/custom_apps/ms365sync
```

### Step 3: Add the sync worker to your docker-compose

Add this service block to your existing `docker-compose.yml`:

```yaml
  # --- MS365 Sync Worker (rclone) ---
  ms365sync-worker:
    build: ./ms365sync/docker
    container_name: nc_ms365sync_worker
    restart: unless-stopped
    volumes:
      - ms365sync_logs:/logs
    networks:
      - internal
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

And add the volume:

```yaml
volumes:
  # ... your existing volumes ...
  ms365sync_logs:
```

Then start it:

```bash
docker-compose up -d ms365sync-worker
```

### Step 4: Enable the app and configure

```bash
docker exec -u www-data nc_app_sib-io php occ app:enable ms365sync
```

Then open **Nextcloud > MS365 Sync > Settings** and configure:

- **Nextcloud URL**: Your external URL (e.g. `https://cloud.example.com`) — used for WebDAV uploads
- **Container URL**: `http://ms365sync-worker:8080` — since both containers share the `internal` network

### Step 5: Azure AD App Registration

1. Go to **Azure Portal > App Registrations > New Registration**
2. Add API permissions (Application type):
   - `Sites.Read.All`
   - `Files.Read.All`
   - `User.Read.All`
3. Grant admin consent
4. Create a client secret
5. Enter Tenant ID, Client ID, and Client Secret in the app settings
6. Click **Test Connection** to verify

### Updating the app

```bash
cd ms365sync
git pull
npm run build
docker cp . nc_app_sib-io:/var/www/html/custom_apps/ms365sync
docker exec nc_app_sib-io chown -R www-data:www-data /var/www/html/custom_apps/ms365sync
docker exec -u www-data nc_app_sib-io php occ upgrade
```

## Development

```bash
# Frontend (watch mode)
npm install
npm run dev

# PHP dependencies
composer install

# Docker worker
cd docker && docker-compose up --build
```

## License

AGPL-3.0-or-later
