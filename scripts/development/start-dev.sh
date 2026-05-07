#!/bin/bash
# =============================================================================
# DEVELOPMENT START SCRIPT - Start all services
# =============================================================================

set -e

echo "Starting development environment..."

# Ensure Docker is running
docker-compose -f infra/docker/docker-compose.yml up -d

# Start backend
cd apps/api
source venv/bin/activate
uvicorn app.app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd ../web
npm run dev &
FRONTEND_PID=$!

# Start worker
cd ../api
celery -A app.tasks worker --loglevel=info &
WORKER_PID=$!

echo "All services started"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Worker PID: $WORKER_PID"

# Wait for interrupts
wait
