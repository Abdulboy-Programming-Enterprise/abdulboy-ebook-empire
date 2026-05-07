#!/bin/bash
# =============================================================================
# DEVELOPMENT SETUP SCRIPT - Initialize dev environment
# =============================================================================

set -e

echo "Setting up development environment..."

# Install dependencies
echo "Installing backend dependencies..."
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt

echo "Installing frontend dependencies..."
cd ../web
npm install

# Configure environment
echo "Configuring environment..."
cp .env.example .env
cp .env.example .env.local

# Start Docker services
echo "Starting Docker services..."
cd ../../
docker-compose -f infra/docker/docker-compose.yml up -d

# Wait for database
sleep 10

# Run migrations
echo "Running migrations..."
cd apps/api
alembic upgrade head

# Seed database
echo "Seeding database..."
python scripts/seed.py

echo -e "\n✅ Development environment ready!"
echo "API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
