# syntax=docker/dockerfile:1.6
#
# ms365sync ExApp — single image:
#   1. Build Vue 3 SPA with Node
#   2. Runtime: Python 3.14 + rclone + nc_py_api/FastAPI, deps managed by uv

FROM node:20-alpine AS ui-build
WORKDIR /ui
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY src ./src
COPY vite.config.js ./
RUN npm run build


# uv-provided image: ships uv + the requested CPython on a slim Debian base.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS runtime

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

# Install Python deps with uv. Use the lockfile for reproducible builds and
# create the venv in a fixed location so we can put it on PATH.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY ms365sync_exapp ./ms365sync_exapp
COPY --from=ui-build /ui/dist ./ms365sync_exapp/ui

# Install the project itself (after the source is copied) so editable/import
# resolution works at runtime.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/opt/venv/bin:$PATH" \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "ms365sync_exapp.main"]
