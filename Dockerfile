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

# Pinned FRP client version (HaRP transport). Bump in lockstep with the
# version HaRP itself ships, and refresh the SHA256s from
# https://github.com/fatedier/frp/releases.
ARG FRP_VERSION=0.61.1
ARG FRP_AMD64_SHA256=bff260b68ca7b1461182a46c4f34e9709ba32764eed30a15dd94ac97f50a2c40
ARG FRP_ARM64_SHA256=af6366f2b43920ebfe6235dba6060770399ed1fb18601e5818552bd46a7621f8

# System packages: ca-certificates + curl (kept around — start.sh and the
# FRP install both need curl) + unzip (rclone tarball is a zip).
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl unzip \
 && rm -rf /var/lib/apt/lists/*

# Official rclone (Debian's apt package is too old — we need >= 1.65 for
# the onedrive backend's client_credentials mode used by app-only auth).
RUN curl -fsSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o /tmp/rclone.zip \
 && unzip -j /tmp/rclone.zip '*/rclone' -d /usr/local/bin/ \
 && chmod +x /usr/local/bin/rclone \
 && rm /tmp/rclone.zip

# FRP client (frpc) — required for HaRP. Multi-arch with SHA256 verification.
RUN set -ex; \
    ARCH=$(uname -m); \
    if [ "$ARCH" = "aarch64" ]; then \
        FRP_ARCH="arm64"; \
        FRP_SHA256="${FRP_ARM64_SHA256}"; \
    else \
        FRP_ARCH="amd64"; \
        FRP_SHA256="${FRP_AMD64_SHA256}"; \
    fi; \
    FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz"; \
    echo "Downloading FRP v${FRP_VERSION} for ${FRP_ARCH}..."; \
    curl -fsSL "${FRP_URL}" -o /tmp/frp.tar.gz; \
    ACTUAL_SHA256=$(sha256sum /tmp/frp.tar.gz | cut -d' ' -f1); \
    if [ "$ACTUAL_SHA256" != "$FRP_SHA256" ]; then \
        echo "Checksum verification failed for FRP v${FRP_VERSION} (${FRP_ARCH})"; \
        echo "Expected: ${FRP_SHA256}"; \
        echo "Got:      ${ACTUAL_SHA256}"; \
        exit 1; \
    fi; \
    tar -C /tmp -xzf /tmp/frp.tar.gz; \
    cp /tmp/frp_${FRP_VERSION}_linux_${FRP_ARCH}/frpc /usr/local/bin/frpc; \
    chmod +x /usr/local/bin/frpc; \
    rm -rf /tmp/frp_${FRP_VERSION}_linux_${FRP_ARCH} /tmp/frp.tar.gz

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

# HaRP launcher: vendored from nextcloud/HaRP exapps_dev/start.sh.
# - Under HaRP (HP_SHARED_KEY set): writes /frpc.toml, starts frpc in the
#   background, then execs the ExApp. nc_py_api's run_app() detects
#   HP_SHARED_KEY and binds uvicorn to /tmp/exapp.sock (matching frpc's
#   unix_domain_socket plugin target).
# - Without HaRP (docker-socket-proxy): no-op passthrough that just
#   execs the ExApp, which then listens on APP_HOST:APP_PORT.
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV PATH="/opt/venv/bin:$PATH" \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

ENTRYPOINT ["/start.sh"]
CMD ["python", "-m", "ms365sync_exapp.main"]
