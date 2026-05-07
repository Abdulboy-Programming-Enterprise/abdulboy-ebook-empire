#!/bin/bash
# =============================================================================
# CLEANUP TEMP SCRIPT - Remove temporary files
# =============================================================================

set -e

TEMP_DIR="/storage/uploads/temp"
CUTOFF_HOURS=24

echo "Cleaning up temporary files older than ${CUTOFF_HOURS} hours..."

find ${TEMP_DIR} -type f -mtime +${CUTOFF_HOURS} -delete
find ${TEMP_DIR} -type d -empty -delete

echo "Cleanup complete"
