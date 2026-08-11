#!/bin/sh
# sosreport Structure Diagnostic - Podman run script
# Usage: sh run.sh

IMAGE="sosdiag-web"
CONTAINER="sosdiag"
PORT="80"
DATA_DIR="/data/sosdiag-data"

set -u

echo "========================================"
echo "  sosreport Structure Diagnostic"
echo "========================================"

if ! command -v podman >/dev/null 2>&1; then
  echo "Podman is not installed."
  exit 1
fi

if [ ! -f "Containerfile" ]; then
  echo "Containerfile is missing. Run this script from the repository root."
  exit 1
fi

mkdir -p "$DATA_DIR/uploads" "$DATA_DIR/output"

if podman container exists "$CONTAINER" 2>/dev/null; then
  echo "> Removing existing container..."
  podman stop "$CONTAINER" >/dev/null 2>&1 || true
  podman rm "$CONTAINER" >/dev/null 2>&1 || true
fi

echo "> Building image..."
if ! podman build -t "$IMAGE" -f Containerfile .; then
  echo "Image build failed."
  exit 1
fi

echo "> Starting container..."
if podman run -d \
  --name "$CONTAINER" \
  -p "$PORT:8000" \
  -v "$DATA_DIR:/app/data:Z" \
  --restart unless-stopped \
  "$IMAGE" >/dev/null; then
  echo ""
  echo "Server started."
  echo "  URL:     http://localhost:$PORT"
  echo "  Uploads: $DATA_DIR/uploads"
  echo "  Reports: $DATA_DIR/output"
  echo ""
  echo "Commands:"
  echo "  Logs:    podman logs -f $CONTAINER"
  echo "  Status:  podman ps --filter name=$CONTAINER"
  echo "  Stop:    podman stop $CONTAINER"
  echo "  Restart: podman restart $CONTAINER"
  echo "  Remove:  podman rm -f $CONTAINER"
else
  echo "Container start failed."
  exit 1
fi
