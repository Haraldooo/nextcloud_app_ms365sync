#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
NC_CONTAINER="${NC_CONTAINER:-nc_app_sib-io}"
WORKER_CONTAINER="nc_ms365sync_worker"
APP_NAME="ms365sync"

echo "=== MS365 Sync Installer ==="
echo ""

# Check that the NC container is running
if ! docker inspect "$NC_CONTAINER" &>/dev/null; then
    echo "ERROR: Nextcloud container '$NC_CONTAINER' not found."
    echo "Set NC_CONTAINER env var if your container has a different name."
    exit 1
fi

# 1. Copy app into Nextcloud
echo "[1/4] Copying app into Nextcloud container..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
docker cp "$SCRIPT_DIR" "$NC_CONTAINER:/var/www/html/custom_apps/$APP_NAME"
docker exec "$NC_CONTAINER" chown -R www-data:www-data "/var/www/html/custom_apps/$APP_NAME"
echo "      Done."

# 2. Build and start the worker container
echo "[2/4] Starting rclone worker container..."
cd "$SCRIPT_DIR/docker"
docker compose up -d --build
echo "      Done."

# 3. Wait for worker health check
echo "[3/4] Waiting for worker to be healthy..."
for i in $(seq 1 30); do
    if docker exec "$WORKER_CONTAINER" wget -q --spider http://localhost:8080/health 2>/dev/null; then
        echo "      Worker is healthy."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "      WARNING: Worker did not become healthy within 30s. Check logs with:"
        echo "      docker logs $WORKER_CONTAINER"
    fi
    sleep 1
done

# 4. Enable the app in Nextcloud
echo "[4/4] Enabling app in Nextcloud..."
docker exec -u www-data "$NC_CONTAINER" php occ app:enable "$APP_NAME"
echo "      Done."

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Open Nextcloud > MS365 Sync > Settings"
echo "  2. Set Nextcloud URL to your external domain (e.g. https://cloud.example.com)"
echo "  3. Set Container URL to: http://$WORKER_CONTAINER:8080"
echo "  4. Add your Azure AD tenant credentials and test the connection"
echo ""
