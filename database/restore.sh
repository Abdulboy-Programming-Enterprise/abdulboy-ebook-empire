#!/bin/bash
# =============================================================================
# DATABASE RESTORE SCRIPT
# =============================================================================
# Restores PostgreSQL database from backup
# Usage: ./restore.sh <backup_file> [--drop] [--create]
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================
BACKUP_DIR="/storage/backups"
LOG_FILE="/var/log/database-restore.log"

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-abdulboy_ebook_empire}"
DB_USER="${DB_USER:-abdulboy_admin}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Restore options
DROP_DATABASE=false
CREATE_DATABASE=false
VERIFY_ONLY=false

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

usage() {
    echo "Usage: $0 <backup_file> [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --drop          Drop existing database before restore"
    echo "  --create        Create database if it doesn't exist"
    echo "  --verify-only   Only verify backup integrity, don't restore"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 full_backup_20240101_020000.sql.gz"
    echo "  $0 latest_full_backup.sql.gz --drop --create"
    echo "  $0 backup.custom --verify-only"
    exit 0
}

check_prerequisites() {
    # Check if pg_restore exists
    if ! command -v pg_restore &> /dev/null; then
        error_exit "pg_restore not found. Please install PostgreSQL client tools."
    fi
    
    # Check if psql exists
    if ! command -v psql &> /dev/null; then
        error_exit "psql not found. Please install PostgreSQL client tools."
    fi
}

verify_backup() {
    local backup_file=$1
    log "Verifying backup integrity: $backup_file"
    
    if [[ "$backup_file" == *.gz ]]; then
        if gunzip -c "$backup_file" 2>/dev/null | pg_restore --list &> /dev/null; then
            log "Backup verification PASSED"
            return 0
        else
            log "Backup verification FAILED"
            return 1
        fi
    elif [[ "$backup_file" == *.sql ]] || [[ "$backup_file" == *.custom ]]; then
        if pg_restore --list "$backup_file" &> /dev/null; then
            log "Backup verification PASSED"
            return 0
        else
            log "Backup verification FAILED"
            return 1
        fi
    else
        error_exit "Unknown backup format: $backup_file"
    fi
}

get_backup_format() {
    local backup_file=$1
    if [[ "$backup_file" == *.gz ]]; then
        echo "compressed"
    elif [[ "$backup_file" == *.custom ]]; then
        echo "custom"
    elif [[ "$backup_file" == *.sql ]]; then
        echo "plain"
    else
        echo "unknown"
    fi
}

drop_database() {
    log "Dropping database: $DB_NAME"
    export PGPASSWORD="$DB_PASSWORD"
    
    # Terminate all connections
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME';" \
        >> "$LOG_FILE" 2>&1 || true
    
    # Drop database
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "DROP DATABASE IF EXISTS $DB_NAME;" \
        >> "$LOG_FILE" 2>&1 || error_exit "Failed to drop database"
    
    log "Database dropped successfully"
    unset PGPASSWORD
}

create_database() {
    log "Creating database: $DB_NAME"
    export PGPASSWORD="$DB_PASSWORD"
    
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
        -c "CREATE DATABASE $DB_NAME OWNER $DB_USER ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8' TEMPLATE template0;" \
        >> "$LOG_FILE" 2>&1 || error_exit "Failed to create database"
    
    log "Database created successfully"
    unset PGPASSWORD
}

restore_from_custom() {
    local backup_file=$1
    log "Restoring from custom format backup: $backup_file"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --verbose \
            --no-owner \
            --no-privileges \
            --jobs=4 \
            2>> "$LOG_FILE"
    else
        pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --verbose \
            --no-owner \
            --no-privileges \
            --jobs=4 \
            "$backup_file" \
            2>> "$LOG_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        log "Restore completed successfully"
    else
        error_exit "Restore failed"
    fi
    
    unset PGPASSWORD
}

restore_from_plain() {
    local backup_file=$1
    log "Restoring from plain SQL backup: $backup_file"
    
    export PGPASSWORD="$DB_PASSWORD"
    
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --set ON_ERROR_STOP=on \
            --quiet \
            2>> "$LOG_FILE"
    else
        psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --set ON_ERROR_STOP=on \
            --quiet \
            -f "$backup_file" \
            2>> "$LOG_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        log "Restore completed successfully"
    else
        error_exit "Restore failed"
    fi
    
    unset PGPASSWORD
}

post_restore_tasks() {
    log "Running post-restore maintenance tasks..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # Analyze database to update statistics
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "ANALYZE;" \
        >> "$LOG_FILE" 2>&1
    
    # Reindex database (optional - for large restores)
    # psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    #     -c "REINDEX DATABASE $DB_NAME;" \
    #     >> "$LOG_FILE" 2>&1
    
    # Vacuum database
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "VACUUM ANALYZE;" \
        >> "$LOG_FILE" 2>&1
    
    log "Post-restore tasks completed"
    unset PGPASSWORD
}

# =============================================================================
# Main Execution
# =============================================================================
main() {
    local backup_file=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --drop)
                DROP_DATABASE=true
                shift
                ;;
            --create)
                CREATE_DATABASE=true
                shift
                ;;
            --verify-only)
                VERIFY_ONLY=true
                shift
                ;;
            --help)
                usage
                ;;
            *)
                if [ -z "$backup_file" ]; then
                    backup_file="$1"
                else
                    echo "Unknown option: $1"
                    usage
                fi
                shift
                ;;
        esac
    done
    
    # Check if backup file is provided
    if [ -z "$backup_file" ]; then
        echo "ERROR: Backup file not specified"
        usage
    fi
    
    # Resolve backup file path
    if [[ "$backup_file" != /* ]]; then
        backup_file="$BACKUP_DIR/$backup_file"
    fi
    
    # Check if backup file exists
    if [ ! -f "$backup_file" ]; then
        error_exit "Backup file not found: $backup_file"
    fi
    
    log "=========================================="
    log "Database Restore Started"
    log "Backup file: $backup_file"
    log "=========================================="
    
    check_prerequisites
    
    # Verify backup first
    if ! verify_backup "$backup_file"; then
        error_exit "Backup verification failed. Aborting restore."
    fi
    
    # If verify-only, exit here
    if [ "$VERIFY_ONLY" = true ]; then
        log "Backup verification completed successfully (verify-only mode)"
        exit 0
    fi
    
    # Handle database drop/create
    if [ "$DROP_DATABASE" = true ]; then
        drop_database
        CREATE_DATABASE=true
    fi
    
    if [ "$CREATE_DATABASE" = true ]; then
        create_database
    fi
    
    # Perform restore based on backup format
    backup_format=$(get_backup_format "$backup_file")
    case "$backup_format" in
        custom|compressed)
            restore_from_custom "$backup_file"
            ;;
        plain)
            restore_from_plain "$backup_file"
            ;;
        *)
            error_exit "Unknown backup format. Supported: .sql, .custom, .gz"
            ;;
    esac
    
    # Run post-restore tasks
    post_restore_tasks
    
    log "=========================================="
    log "Database Restore Completed Successfully"
    log "=========================================="
}

# Run main function
main "$@"
