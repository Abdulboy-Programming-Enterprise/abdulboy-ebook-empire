#!/bin/bash
# =============================================================================
# DEPLOYMENT SCRIPT - Production Deployment
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting deployment...${NC}"

# Load environment
source .env.production

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker required${NC}" >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI required${NC}" >&2; exit 1; }

# Build images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker build -t abdulboy-api:latest -f infra/docker/Dockerfile .
docker build -t abdulboy-web:latest -f infra/docker/Dockerfile.nginx

# Tag for ECR
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
docker tag abdulboy-api:latest ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/abdulboy-api:latest
docker tag abdulboy-web:latest ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/abdulboy-web:latest

# Push to ECR
echo -e "${YELLOW}📤 Pushing to ECR...${NC}"
aws ecr get-login-password | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/abdulboy-api:latest
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/abdulboy-web:latest

# Update ECS services
echo -e "${YELLOW}🔄 Updating ECS services...${NC}"
aws ecs update-service --cluster abdulboy-prod --service backend-api --force-new-deployment
aws ecs update-service --cluster abdulboy-prod --service frontend-web --force-new-deployment
aws ecs update-service --cluster abdulboy-prod --service worker --force-new-deployment

# Run migrations
echo -e "${YELLOW}🗄️ Running database migrations...${NC}"
aws ecs run-task --cluster abdulboy-prod --task-definition migrate --overrides '{"containerOverrides":[{"name":"migrate","command":["alembic","upgrade","head"]}]}'

# Wait for deployments
echo -e "${YELLOW}⏳ Waiting for deployments to stabilize...${NC}"
sleep 30

# Health check
echo -e "${YELLOW}🏥 Running health checks...${NC}"
curl -f https://api.abdulboy-ebook.com/api/v1/health || { echo -e "${RED}Health check failed${NC}"; exit 1; }
curl -f https://abdulboy-ebook.com || { echo -e "${RED}Frontend check failed${NC}"; exit 1; }

# Clear CDN cache
echo -e "${YELLOW}🗑️ Clearing CDN cache...${NC}"
aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_DIST_ID} --paths "/*"

echo -e "${GREEN}✅ Deployment complete!${NC}"
