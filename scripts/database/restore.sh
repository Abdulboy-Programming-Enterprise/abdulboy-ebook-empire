#!/bin/bash
# =============================================================================
# DATABASE RESTORE SCRIPT - Restore from backup
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Usage: $0 <backup_file>${NC}"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will overwrite the database!${NC}"
read -p "Are you sure? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo "Restoring database from $BACKUP_FILE..."

# Drop and recreate database
PGPASSWORD=${DB_PASSWORD} dropdb -h ${DB_HOST} -U ${DB_USER} ${DB_NAME}
PGPASSWORD=${DB_PASSWORD} createdb -h ${DB_HOST} -U ${DB_USER} ${DB_NAME}

# Restore
gunzip -c ${BACKUP_FILE} | PGPASSWORD=${DB_PASSWORD} pg_restore \
    -h ${DB_HOST} \
    -U ${DB_USER} \
    -d ${DB_NAME} \
    --clean \
    --if-exists

echo -e "${GREEN}Restore complete${NC}"
