#!/bin/bash
# =============================================================================
# DATABASE MIGRATE SCRIPT - Run Alembic migrations
# =============================================================================

set -e

cd apps/api

echo "Running database migrations..."

# Run migrations
alembic upgrade head

echo "Migrations complete"

# Create new migration if requested
if [ "$1" == "--create" ]; then
    MESSAGE=$2
    if [ -z "$MESSAGE" ]; then
        echo "Usage: $0 --create <migration_message>"
        exit 1
    fi
    alembic revision --autogenerate -m "$MESSAGE"
    echo "Migration created"
fi
