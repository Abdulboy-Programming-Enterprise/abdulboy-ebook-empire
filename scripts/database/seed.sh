#!/bin/bash
# =============================================================================
# DATABASE SEED SCRIPT - Load initial data
# =============================================================================

set -e

cd apps/api

echo "Seeding database..."

# Run seeds using Python
python -c "
from app.core.database import SessionLocal
from database.seeds import seed_all

db = SessionLocal()
seed_all(db)
db.close()
print('Seeding complete')
"
