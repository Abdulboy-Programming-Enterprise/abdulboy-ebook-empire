#!/bin/bash
# =============================================================================
# DATABASE BACKUP SCRIPT - PostgreSQL backup with compression
# =============================================================================

set -e

BACKUP_DIR="/storage/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

mkdir -p ${BACKUP_DIR}

echo "Creating database backup..."

# Backup with pg_dump
PGPASSWORD=${DB_PASSWORD} pg_dump \
    -h ${DB_HOST} \
    -U ${DB_USER} \
    -d ${DB_NAME} \
    -Fc \
    | gzip > ${BACKUP_FILE}

# Upload to S3 if configured
if [ -n "$AWS_BUCKET_NAME" ]; then
    aws s3 cp ${BACKUP_FILE} s3://${AWS_BUCKET_NAME}/backups/
    echo "Backup uploaded to S3"
fi

# Cleanup old backups (keep 30 days)
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete

echo "Backup complete: ${BACKUP_FILE}"
