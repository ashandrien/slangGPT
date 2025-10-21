#!/usr/bin/env bash
# deploy-to-server.sh
# Build frontend locally, rsync built files and backend to a remote server,
# and run remote commands to ensure the backend venv is installed and the
# app is started. Edit the CONFIG section below before running.

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

### CONFIG — edit these before running ###
# Remote SSH user and host
REMOTE_USER="root"
REMOTE_HOST="148.230.95.212"
# Remote destination path (repo root on server)
REMOTE_PATH="/home/user/apps/phillygpt"
# SSH port (optional)
SSH_PORT=22
# If you have a systemd service on the server to manage the backend, set to true
USE_SYSTEMD=true
# The systemd service name (only used if USE_SYSTEMD=true)
SYSTEMD_SERVICE_NAME="phillygpt"
##########################################

REMOTE="$REMOTE_USER@$REMOTE_HOST"

echo "Building frontend locally..."
cd "$ROOT_DIR/frontend"
npm ci
npm run build

# Copy optional preview image into dist so it will be deployed and available at /assets/teaser.svg (or .png)
for IMG in teaser.svg teaser.png; do
  if [ -f "$ROOT_DIR/frontend/public/assets/$IMG" ]; then
    mkdir -p "$ROOT_DIR/frontend/dist/assets"
    cp "$ROOT_DIR/frontend/public/assets/$IMG" "$ROOT_DIR/frontend/dist/assets/$IMG"
    echo "Copied $IMG into frontend dist assets"
  fi
done

echo "Syncing frontend build to server: $REMOTE:$REMOTE_PATH/backend/static/"
ssh -p $SSH_PORT $REMOTE "mkdir -p $REMOTE_PATH/backend/static"
rsync -avz --delete "$ROOT_DIR/frontend/dist/" $REMOTE:$REMOTE_PATH/backend/static/

# Also ensure teaser.svg/png is present in backend static assets (local copy)
for IMG in teaser.svg teaser.png; do
  if [ -f "$ROOT_DIR/frontend/public/assets/$IMG" ]; then
    mkdir -p "$ROOT_DIR/backend/static/assets"
    cp "$ROOT_DIR/frontend/public/assets/$IMG" "$ROOT_DIR/backend/static/assets/$IMG"
    echo "Copied $IMG into backend static assets"
  fi
done

echo "Syncing backend code to server (excluding .venv and backend static assets so frontend assets are authoritative)..."
# Exclude backend/static/assets to avoid clobbering the freshly-deployed frontend assets
rsync -avz --delete --exclude '.venv' --exclude 'node_modules' --exclude 'static/assets' "$ROOT_DIR/backend/" $REMOTE:$REMOTE_PATH/backend/

echo "Running remote setup on server"
ssh -p $SSH_PORT $REMOTE bash -s <<EOF
set -euo pipefail
cd $REMOTE_PATH/backend
# Create venv if missing (try python3.11, python3)
if [ ! -d .venv ]; then
  if command -v python3.11 >/dev/null 2>&1; then
    python3.11 -m venv .venv
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv
  else
    echo "No python3 found on remote host. Install Python 3.11 or python3 before proceeding."
    exit 1
  fi
  . .venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
else
  echo ".venv already exists — activating and ensuring required packages are installed."
  . .venv/bin/activate
  # Make sure pip and wheel are up-to-date and install requirements (idempotent)
  pip install --upgrade pip setuptools wheel || true
  pip install -r requirements.txt || true
fi

# Restart the backend using systemd if available, otherwise use nohup
if [ "$USE_SYSTEMD" = "true" ]; then
  echo "Attempting to restart systemd service: $SYSTEMD_SERVICE_NAME"
  # Try restart with sudo if available, otherwise try without sudo
  if command -v sudo >/dev/null 2>&1; then
    sudo systemctl restart $SYSTEMD_SERVICE_NAME || true
    sudo systemctl status $SYSTEMD_SERVICE_NAME --no-pager || true
  else
    systemctl restart $SYSTEMD_SERVICE_NAME || true
    systemctl status $SYSTEMD_SERVICE_NAME --no-pager || true
  fi
else
  echo "Starting uvicorn with nohup (background)"
  # Kill existing uvicorn processes (best-effort)
  pkill -f 'uvicorn main:app' || true
  . .venv/bin/activate
  nohup .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
  sleep 1
  echo "Uvicorn logs (last 10 lines):"
  tail -n 10 uvicorn.log || true
fi

# If nginx is installed, reload it to ensure new static assets and certs are active
if command -v nginx >/dev/null 2>&1; then
  echo "Reloading nginx to pick up new static assets..."
  if command -v sudo >/dev/null 2>&1; then
    sudo systemctl reload nginx || true
  else
    systemctl reload nginx || true
  fi
fi
EOF

echo "Deploy complete. Check your server and logs to verify the app is running."

echo "Reminder: ensure backend/.env on the server includes OPENAI_API_KEY and ALLOWED_ORIGINS as needed."
