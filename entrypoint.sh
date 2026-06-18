#!/bin/sh
set -e

cleanup() {
  kill -TERM $WEB_PID $WORKER_PID $BEAT_PID 2>/dev/null
  wait
}
trap cleanup TERM INT

celery -A app.core.celery worker --loglevel=info &
WORKER_PID=$!

celery -A app.core.celery beat --loglevel=info &
BEAT_PID=$!

uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} &
WEB_PID=$!

wait $WEB_PID $WORKER_PID $BEAT_PID