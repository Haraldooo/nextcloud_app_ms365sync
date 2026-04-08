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

# rclone + ca-certs (for HTTPS to Graph + WebDAV)
RUN apt-get update \
 && apt-get install -y --no-install-recommends rclone ca-certificates \
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
