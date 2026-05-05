#!/bin/sh
# =============================================================================
# DOCKER ENTRYPOINT SCRIPT
# =============================================================================

set -e

echo "Starting Abdulboy Ebook Empire API..."

# Wait for database to be ready
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    while ! nc -z ${DB_HOST:-postgres} ${DB_PORT:-5432}; do
        sleep 1
    done
    echo "Database is ready!"
fi

# Wait for Redis
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
        sleep 1
    done
    echo "Redis is ready!"
fi

# Run database migrations
if [ "$APP_ENV" != "development" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Execute the main command
exec "$@"
