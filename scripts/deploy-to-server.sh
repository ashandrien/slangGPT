#!/usr/bin/env bash
# deploy-to-server.sh
# Build frontend locally, rsync built files and backend to a remote server,
# and run remote commands to ensure the backend venv is installed and the
# app is started. Edit the CONFIG section below before running.

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

### CONFIG — edit these before running ###
# Remote SSH user and host
REMOTE_USER="user"
REMOTE_HOST="example.com"
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

echo "Syncing frontend build to server: $REMOTE:$REMOTE_PATH/backend/static/"
ssh -p $SSH_PORT $REMOTE "mkdir -p $REMOTE_PATH/backend/static"
rsync -avz --delete "$ROOT_DIR/frontend/dist/" $REMOTE:$REMOTE_PATH/backend/static/

echo "Syncing backend code to server (excluding .venv)..."
rsync -avz --delete --exclude '.venv' --exclude 'node_modules' "$ROOT_DIR/backend/" $REMOTE:$REMOTE_PATH/backend/

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
  echo ".venv already exists — skipping venv creation. If you want to recreate it, remove .venv and re-run."
fi

# Restart the backend using systemd if available, otherwise use nohup
if [ "$USE_SYSTEMD" = "true" ]; then
  echo "Attempting to restart systemd service: $SYSTEMD_SERVICE_NAME"
  sudo systemctl restart $SYSTEMD_SERVICE_NAME || true
  sudo systemctl status $SYSTEMD_SERVICE_NAME --no-pager || true
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
EOF

echo "Deploy complete. Check your server and logs to verify the app is running."

echo "Reminder: ensure backend/.env on the server includes OPENAI_API_KEY and ALLOWED_ORIGINS as needed."
