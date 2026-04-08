# syntax=docker/dockerfile:1.6
#
# ms365sync ExApp — single image:
#   1. Build Vue 3 SPA with Node
#   2. Runtime: Python 3.12 + rclone + nc_py_api/FastAPI

FROM node:20-alpine AS ui-build
WORKDIR /ui
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY src ./src
COPY vite.config.js ./
RUN npm run build


FROM python:3.12-slim AS runtime

# Official rclone (Debian's apt package is too old — we need >= 1.65 for
# the onedrive backend's client_credentials mode used by app-only auth).
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl unzip \
 && curl -fsSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o /tmp/rclone.zip \
 && unzip -j /tmp/rclone.zip '*/rclone' -d /usr/local/bin/ \
 && chmod +x /usr/local/bin/rclone \
 && rm /tmp/rclone.zip \
 && apt-get purge -y curl unzip \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY ms365sync_exapp ./ms365sync_exapp
COPY --from=ui-build /ui/dist ./ms365sync_exapp/ui

ENV APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "ms365sync_exapp.main"]
