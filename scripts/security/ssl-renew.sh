#!/bin/bash
# =============================================================================
# SSL RENEW SCRIPT - Renew Let's Encrypt certificates
# =============================================================================

set -e

echo "Checking SSL certificates..."

# Renew certificates
certbot renew --quiet

# Reload nginx
docker exec abdulboy-nginx nginx -s reload

echo "SSL renewal complete"
