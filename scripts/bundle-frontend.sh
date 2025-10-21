#!/usr/bin/env bash
# Build frontend and copy to backend/static/
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Building frontend..."
cd frontend
if [ ! -d node_modules ]; then
  echo "node_modules missing — run npm install first on this host"
fi
npm run build

BUILD_DIR="$ROOT_DIR/frontend/dist"
TARGET_DIR="$ROOT_DIR/backend/static"

if [ ! -d "$BUILD_DIR" ]; then
  echo "Build output not found: $BUILD_DIR"
  exit 1
fi

rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"
cp -R "$BUILD_DIR/"* "$TARGET_DIR/"

echo "Copied frontend build to backend/static/"
