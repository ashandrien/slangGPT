#!/usr/bin/env bash
# start-dev.sh — start backend and frontend for local development
# Usage: ./scripts/start-dev.sh
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Backend: ensure venv exists and start uvicorn
echo "Starting backend..."
cd backend
if [ ! -d ".venv" ]; then
  echo "No .venv found in backend/. Creating one with python3.11..."
  /opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv
  . .venv/bin/activate
  python -m pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
else
  . .venv/bin/activate
fi

# copy .env.example if .env not present
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example — edit it to set OPENAI_API_KEY if needed"
fi

# Start uvicorn in background, write to uvicorn.log
if pgrep -f "uvicorn.*main:app" > /dev/null 2>&1; then
  echo "uvicorn already running — skipping start"
else
  nohup .venv/bin/uvicorn main:app --reload --port 8000 > uvicorn.log 2>&1 &
  sleep 1
  echo "uvicorn started (logs -> backend/uvicorn.log)"
fi

# Frontend: start vite dev server
cd "$ROOT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

if pgrep -f "node .*node_modules/.bin/vite" > /dev/null 2>&1; then
  echo "Vite already running — skipping start"
else
  nohup ./node_modules/.bin/vite --host 127.0.0.1 --port 5173 </dev/null > vite.log 2>&1 &
  sleep 1
  echo "Vite started (logs -> frontend/vite.log)"
fi

# Print small status summary and tail logs
echo
echo "--- Backend uvicorn log (last 20 lines) ---"
tail -n 20 ../backend/uvicorn.log || true

echo "--- Frontend vite log (last 20 lines) ---"
tail -n 20 vite.log || true

echo
echo "Done. Visit http://127.0.0.1:5173 to open the frontend (Vite). Backend: http://127.0.0.1:8000"
