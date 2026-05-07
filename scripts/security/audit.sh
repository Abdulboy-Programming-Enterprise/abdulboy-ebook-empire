#!/bin/bash
# =============================================================================
# SECURITY AUDIT SCRIPT - Run security scans
# =============================================================================

set -e

echo "Running security audit..."

# Dependency vulnerabilities
echo "Checking dependencies..."
cd apps/api && safety check -r requirements/base.txt
cd apps/web && npm audit

# Container scanning
echo "Scanning Docker images..."
trivy image abdulboy-api:latest --severity HIGH,CRITICAL
trivy image abdulboy-web:latest --severity HIGH,CRITICAL

# Secret detection
echo "Scanning for secrets..."
gitleaks detect --source . --verbose

echo "Security audit complete"
