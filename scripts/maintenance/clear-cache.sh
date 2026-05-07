#!/bin/bash
# =============================================================================
# CLEAR CACHE SCRIPT - Flush Redis cache
# =============================================================================

set -e

echo "Clearing Redis cache..."

# Flush all Redis databases
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} -a ${REDIS_PASSWORD} FLUSHALL

echo "Cache cleared"

# Clear CloudFront cache if configured
if [ -n "$CLOUDFRONT_DIST_ID" ]; then
    echo "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_DIST_ID} --paths "/*"
fi
