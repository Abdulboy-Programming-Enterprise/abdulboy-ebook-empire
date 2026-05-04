#!/bin/bash
# =============================================================================
# DATABASE BACKUP SCRIPT
# =============================================================================
# Performs full/incremental backup of PostgreSQL database
# Usage: ./backup.sh [full|incremental|schema]
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================
BACKUP_DIR="/storage/backups"
DATE=$(date +%Y%m%d_%H%M%S)
TIMESTAMP=$(date +%Y%m%d)
LOG_FILE="/var/log/database-backup.log"
RETENTION_DAYS=30

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-abdulboy_ebook_empire}"
DB_USER="${DB_USER:-abdulboy_admin}"
DB_PASSWORD="${DB_PASSWORD:-}"

# AWS S3 configuration (optional)
S3_BUCKET="${S3_BUCKET:-abdulboy-ebook-backups}"
S3_PATH="database"
ENABLE_S3_UPLOAD="${ENABLE_S3_UPLOAD:-false}"

# =============================================================================
# Helper Functions
# =============================================================================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

check_prerequisites() {
    # Check if pg_dump exists
    if ! command -v pg_dump &> /dev/null; then
        error_exit "pg_dump not found. Please install PostgreSQL client tools."
    fi
    
    # Check if backup directory exists
    if [ ! -d "$BACKUP_DIR" ]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
    
    # Check database connection
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &> /dev/null; then
        error_exit "Cannot connect to database. Please check connection parameters."
    fi
}

upload_to_s3() {
    local file=$1
    if [ "$ENABLE_S3_UPLOAD" = "true" ]; then
        if command -v aws &> /dev/null; then
            log "Uploading to S3: $file"
            aws s3 cp "$file" "s3://$S3_BUCKET/$S3_PATH/$DATE/" --storage-class STANDARD_IA
        else
            log "WARNING: AWS CLI not found. Skipping S3 upload."
        fi
    fi
}

cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days"
    find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sql" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.custom" -type f -mtime +$RETENTION_DAYS -delete
}

# =============================================================================
# Backup Functions
# =============================================================================
full_backup() {
    log "Starting FULL database backup..."
    BACKUP_FILE="$BACKUP_DIR/full_backup_${DB_NAME}_${DATE}.sql.gz"
    
    # Export password for pg_dump
    export PGPASSWORD="$DB_PASSWORD"
    
    # Perform backup with compression
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=custom \
        --verbose \
        --file="$BACKUP_FILE.tmp" \
        2>> "$LOG_FILE"
    
    # Compress the backup
    gzip -c "$BACKUP_FILE.tmp" > "$BACKUP_FILE"
    rm -f "$BACKUP_FILE.tmp"
    
    # Check if backup was successful
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log "Full backup completed successfully: $BACKUP_FILE (Size: $BACKUP_SIZE)"
        
        # Upload to S3
        upload_to_s3 "$BACKUP_FILE"
        
        # Create symlink to latest backup
        ln -sf "$BACKUP_FILE" "$BACKUP_DIR/latest_full_backup.sql.gz"
    else
        error_exit "Full backup failed"
    fi
    
    unset PGPASSWORD
}

schema_backup() {
    log "Starting SCHEMA ONLY backup..."
    SCHEMA_FILE="$BACKUP_DIR/schema_backup_${DB_NAME}_${DATE}.sql"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # Backup only schema (no data)
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --schema-only \
        --format=plain \
        --verbose \
        --file="$SCHEMA_FILE" \
        2>> "$LOG_FILE"
    
    if [ -f "$SCHEMA_FILE" ] && [ -s "$SCHEMA_FILE" ]; then
        # Compress schema file
        gzip -f "$SCHEMA_FILE"
        log "Schema backup completed: ${SCHEMA_FILE}.gz"
        upload_to_s3 "${SCHEMA_FILE}.gz"
    else
        error_exit "Schema backup failed"
    fi
    
    unset PGPASSWORD
}

data_backup() {
    log "Starting DATA ONLY backup..."
    DATA_FILE="$BACKUP_DIR/data_backup_${DB_NAME}_${DATE}.sql.gz"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # Backup only data (no schema)
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --data-only \
        --format=custom \
        --verbose \
        --file="$DATA_FILE.tmp" \
        2>> "$LOG_FILE"
    
    gzip -c "$DATA_FILE.tmp" > "$DATA_FILE"
    rm -f "$DATA_FILE.tmp"
    
    if [ -f "$DATA_FILE" ] && [ -s "$DATA_FILE" ]; then
        log "Data backup completed: $DATA_FILE"
        upload_to_s3 "$DATA_FILE"
    else
        error_exit "Data backup failed"
    fi
    
    unset PGPASSWORD
}

incremental_backup() {
    log "Starting INCREMENTAL backup (using WAL archiving)..."
    
    # Enable WAL archiving if not already enabled
    export PGPASSWORD="$DB_PASSWORD"
    
    # Force a log switch to archive current WAL
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "SELECT pg_switch_wal();" \
        >> "$LOG_FILE" 2>&1
    
    # Backup WAL files from archive
    if [ -d "/var/lib/postgresql/wal_archive" ]; then
        WAL_BACKUP="$BACKUP_DIR/wal_backup_${DATE}.tar.gz"
        tar -czf "$WAL_BACKUP" /var/lib/postgresql/wal_archive/* 2>/dev/null || true
        
        if [ -f "$WAL_BACKUP" ]; then
            log "WAL backup completed: $WAL_BACKUP"
            upload_to_s3 "$WAL_BACKUP"
        fi
    fi
    
    unset PGPASSWORD
}

verify_backup() {
    log "Verifying backup integrity..."
    
    LATEST_BACKUP="$BACKUP_DIR/latest_full_backup.sql.gz"
    
    if [ -f "$LATEST_BACKUP" ]; then
        # Test restore (to /dev/null)
        if gunzip -c "$LATEST_BACKUP" 2>/dev/null | pg_restore --list &> /dev/null; then
            log "Backup verification PASSED"
        else
            log "ERROR: Backup verification FAILED"
            return 1
        fi
    else
        log "No latest backup found to verify"
        return 1
    fi
    
    return 0
}

# =============================================================================
# Main Execution
# =============================================================================
main() {
    BACKUP_TYPE="${1:-full}"
    
    log "=========================================="
    log "Database Backup Started - Type: $BACKUP_TYPE"
    log "=========================================="
    
    check_prerequisites
    
    case "$BACKUP_TYPE" in
        full)
            full_backup
            verify_backup
            ;;
        schema)
            schema_backup
            ;;
        data)
            data_backup
            ;;
        incremental)
            incremental_backup
            ;;
        all)
            full_backup
            schema_backup
            data_backup
            incremental_backup
            verify_backup
            ;;
        *)
            error_exit "Invalid backup type. Use: full, schema, data, incremental, or all"
            ;;
    esac
    
    cleanup_old_backups
    
    log "=========================================="
    log "Database Backup Completed Successfully"
    log "=========================================="
}

# Run main function
main "$@"
