#!/bin/sh
# sosreport Structure Diagnostic - Podman run script
# Usage: sh run.sh

set -eu

IMAGE="${IMAGE:-sosdiag-web}"
CONTAINER="${CONTAINER:-sosdiag}"
PORT="${PORT:-8080}"
DATA_DIR="${DATA_DIR:-/data/sosdiag-data}"
CONTAINER_DATA_DIR="/data"

printf '%s\n' "========================================"
printf '%s\n' "  sosreport Structure Diagnostic"
printf '%s\n' "========================================"

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
  podman rm -f "$CONTAINER" >/dev/null 2>&1 || true
fi

echo "> Building image: $IMAGE"
podman build -t "$IMAGE" -f Containerfile .

echo "> Starting container: $CONTAINER"
podman run -d \
  --name "$CONTAINER" \
  -p "$PORT:8000" \
  -e SOSDIAG_DATA_DIR="$CONTAINER_DATA_DIR" \
  -v "$DATA_DIR:$CONTAINER_DATA_DIR:Z" \
  --restart unless-stopped \
  "$IMAGE" >/dev/null

echo "> Waiting for health endpoint..."
ATTEMPT=0
while [ "$ATTEMPT" -lt 30 ]; do
  STATUS="$(podman inspect --format '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || true)"
  if [ "$STATUS" = "healthy" ]; then
    echo ""
    echo "Server started and healthy."
    echo "  URL:     http://localhost:$PORT"
    echo "  Health:  http://localhost:$PORT/health"
    echo "  Uploads: $DATA_DIR/uploads"
    echo "  Reports: $DATA_DIR/output"
    echo ""
    echo "Commands:"
    echo "  Logs:    podman logs -f $CONTAINER"
    echo "  Status:  podman ps --filter name=$CONTAINER"
    echo "  Health:  podman inspect --format '{{.State.Health.Status}}' $CONTAINER"
    echo "  Stop:    podman stop $CONTAINER"
    echo "  Restart: podman restart $CONTAINER"
    echo "  Remove:  podman rm -f $CONTAINER"
    exit 0
  fi

  RUNNING="$(podman inspect --format '{{.State.Running}}' "$CONTAINER" 2>/dev/null || true)"
  if [ "$RUNNING" != "true" ]; then
    echo "Container stopped before becoming healthy."
    podman logs "$CONTAINER" || true
    exit 1
  fi

  ATTEMPT=$((ATTEMPT + 1))
  sleep 2
done

echo "Container did not become healthy within 60 seconds."
podman logs "$CONTAINER" || true
exit 1
