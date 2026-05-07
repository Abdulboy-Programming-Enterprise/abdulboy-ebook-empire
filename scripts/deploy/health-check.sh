#!/bin/bash
# =============================================================================
# HEALTH CHECK SCRIPT - Verify all services are healthy
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🏥 Running health checks...${NC}"

FAILED=0

# API Health
echo -n "API Health... "
if curl -s -f https://api.abdulboy-ebook.com/api/v1/health > /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=1
fi

# Frontend
echo -n "Frontend... "
if curl -s -f https://abdulboy-ebook.com > /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=1
fi

# Database
echo -n "Database... "
if curl -s -f https://api.abdulboy-ebook.com/api/v1/health/db > /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=1
fi

# Redis
echo -n "Redis... "
if curl -s -f https://api.abdulboy-ebook.com/api/v1/health/redis > /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=1
fi

# Worker
echo -n "Worker... "
if curl -s -f https://api.abdulboy-ebook.com/api/v1/health/worker > /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=1
fi

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All services healthy${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some services unhealthy${NC}"
    exit 1
fi
