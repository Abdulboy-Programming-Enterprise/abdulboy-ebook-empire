# =============================================================================
# ABDULBOY EBOOK EMPIRE - MAKEFILE
# =============================================================================
# Usage: make [command]
# Commands help you manage the entire project from setup to deployment
# =============================================================================

.PHONY: help setup dev build test lint clean docker-up docker-down deploy

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Project variables
PROJECT_NAME := abdulboy-ebook-empire
DOCKER_COMPOSE := docker-compose -f infra/docker/docker-compose.yml
DOCKER_COMPOSE_DEV := docker-compose -f infra/docker/docker-compose.dev.yml
DOCKER_COMPOSE_PROD := docker-compose -f infra/docker/docker-compose.prod.yml

# Help command
help: ## Show this help message
	@printf "\n${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}\n"
	@printf "${BLUE}║${NC}     ${GREEN}ABDULBOY EBOOK EMPIRE - MAKE COMMANDS${NC}                         ${BLUE}║${NC}\n"
	@printf "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}\n\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@printf "\n"

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

setup: ## Complete project setup (install deps, docker, migrate, seed)
	@printf "\n${YELLOW}🚀 Setting up ${PROJECT_NAME}...${NC}\n"
	@make install-deps
	@make docker-up
	@printf "${YELLOW}⏳ Waiting for databases to be ready...${NC}\n"
	@sleep 10
	@make db-migrate
	@make db-seed
	@printf "\n${GREEN}✅ Setup complete! Run 'make dev' to start development${NC}\n\n"

install-deps: ## Install all dependencies (Node.js + Python)
	@printf "${YELLOW}📦 Installing dependencies...${NC}\n"
	@pnpm install
	@cd apps/api && python -m venv venv && source venv/bin/activate && pip install -r requirements/base.txt
	@printf "${GREEN}✅ Dependencies installed${NC}\n"

# =============================================================================
# DEVELOPMENT
# =============================================================================

dev: ## Start all development servers (frontend + backend + worker)
	@printf "${YELLOW}🚀 Starting development servers...${NC}\n"
	@pnpm dev

dev-web: ## Start only frontend development server
	@pnpm dev --filter=@abdulboy/web

dev-api: ## Start only backend API server
	@pnpm dev --filter=@abdulboy/api

dev-worker: ## Start only background worker
	@pnpm dev --filter=@abdulboy/worker

# =============================================================================
# DOCKER
# =============================================================================

docker-up: ## Start all Docker containers (PostgreSQL, Redis, MongoDB, etc.)
	@printf "${YELLOW}🐳 Starting Docker containers...${NC}\n"
	@$(DOCKER_COMPOSE) up -d
	@printf "${GREEN}✅ Docker containers started${NC}\n"

docker-down: ## Stop all Docker containers
	@printf "${YELLOW}🛑 Stopping Docker containers...${NC}\n"
	@$(DOCKER_COMPOSE) down
	@printf "${GREEN}✅ Docker containers stopped${NC}\n"

docker-down-volumes: ## Stop Docker containers and remove volumes (WARNING: deletes all data)
	@printf "${RED}⚠️  WARNING: This will delete all database data!${NC}\n"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(DOCKER_COMPOSE) down -v; \
		printf "${GREEN}✅ Docker containers and volumes removed${NC}\n"; \
	else \
		printf "${YELLOW}Cancelled${NC}\n"; \
	fi

docker-logs: ## View Docker container logs
	@$(DOCKER_COMPOSE) logs -f

docker-build: ## Build Docker images
	@$(DOCKER_COMPOSE) build

docker-dev-up: ## Start development Docker containers with hot reload
	@$(DOCKER_COMPOSE_DEV) up -d

docker-prod-up: ## Start production Docker containers
	@$(DOCKER_COMPOSE_PROD) up -d

# =============================================================================
# DATABASE
# =============================================================================

db-migrate: ## Run database migrations
	@printf "${YELLOW}📊 Running database migrations...${NC}\n"
	@cd apps/api && alembic upgrade head
	@printf "${GREEN}✅ Migrations complete${NC}\n"

db-migrate-create: ## Create a new migration (usage: make db-migrate-create name=add_users_table)
	@printf "${YELLOW}📝 Creating migration: $(name)...${NC}\n"
	@cd apps/api && alembic revision --autogenerate -m "$(name)"
	@printf "${GREEN}✅ Migration created${NC}\n"

db-rollback: ## Rollback last migration
	@printf "${YELLOW}⏪ Rolling back last migration...${NC}\n"
	@cd apps/api && alembic downgrade -1
	@printf "${GREEN}✅ Rollback complete${NC}\n"

db-seed: ## Seed database with initial data
	@printf "${YELLOW}🌱 Seeding database...${NC}\n"
	@psql -h localhost -U abdulboy_admin -d abdulboy_ebook_empire -f database/seeds/admin_user.sql
	@psql -h localhost -U abdulboy_admin -d abdulboy_ebook_empire -f database/seeds/subscription_plans.sql
	@psql -h localhost -U abdulboy_admin -d abdulboy_ebook_empire -f database/seeds/badges_seed.sql
	@psql -h localhost -U abdulboy_admin -d abdulboy_ebook_empire -f database/seeds/sample_books.sql
	@printf "${GREEN}✅ Seeding complete${NC}\n"

db-reset: docker-down-volumes docker-up db-migrate db-seed ## Reset database (WARNING: deletes all data)
	@printf "${GREEN}✅ Database reset complete${NC}\n"

db-backup: ## Backup database
	@printf "${YELLOW}💾 Backing up database...${NC}\n"
	@mkdir -p storage/backups
	@pg_dump -h localhost -U abdulboy_admin abdulboy_ebook_empire > storage/backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@printf "${GREEN}✅ Backup complete${NC}\n"

db-restore: ## Restore database from backup (usage: make db-restore file=backup.sql)
	@printf "${YELLOW}🔄 Restoring database from $(file)...${NC}\n"
	@psql -h localhost -U abdulboy_admin -d abdulboy_ebook_empire < storage/backups/$(file)
	@printf "${GREEN}✅ Restore complete${NC}\n"

# =============================================================================
# TESTING
# =============================================================================

test: ## Run all tests
	@printf "${YELLOW}🧪 Running all tests...${NC}\n"
	@pnpm test

test-unit: ## Run unit tests only
	@pnpm test:unit

test-integration: ## Run integration tests only
	@pnpm test:integration

test-e2e: ## Run end-to-end tests only
	@pnpm test:e2e

test-coverage: ## Generate test coverage report
	@pnpm test:coverage

test-watch: ## Run tests in watch mode
	@pnpm test -- --watch

test-load: ## Run load testing with Locust
	@locust -f tests/performance/load_test.py --host=http://localhost:8000

# =============================================================================
# BUILD & DEPLOY
# =============================================================================

build: ## Build all applications for production
	@printf "${YELLOW}🔨 Building applications...${NC}\n"
	@pnpm build
	@printf "${GREEN}✅ Build complete${NC}\n"

build-web: ## Build only frontend
	@pnpm build --filter=@abdulboy/web

build-api: ## Build only backend API
	@pnpm build --filter=@abdulboy/api

deploy-staging: ## Deploy to staging environment
	@printf "${YELLOW}🚀 Deploying to staging...${NC}\n"
	@git push origin develop
	@gh workflow run deploy-staging.yml
	@printf "${GREEN}✅ Staging deployment initiated${NC}\n"

deploy-production: ## Deploy to production environment
	@printf "${RED}⚠️  WARNING: Deploying to PRODUCTION!${NC}\n"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		git push origin main; \
		gh workflow run deploy-production.yml; \
		printf "${GREEN}✅ Production deployment initiated${NC}\n"; \
	else \
		printf "${YELLOW}Cancelled${NC}\n"; \
	fi

rollback: ## Rollback last production deployment
	@printf "${RED}⚠️  Rolling back production...${NC}\n"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		gh workflow run rollback.yml; \
		printf "${GREEN}✅ Rollback initiated${NC}\n"; \
	else \
		printf "${YELLOW}Cancelled${NC}\n"; \
	fi

# =============================================================================
# CODE QUALITY
# =============================================================================

lint: ## Run linters on all code
	@printf "${YELLOW}🔍 Running linters...${NC}\n"
	@pnpm lint
	@printf "${GREEN}✅ Linting complete${NC}\n"

lint-fix: ## Fix linting issues automatically
	@pnpm lint:fix

format: ## Format code with Prettier
	@pnpm format

type-check: ## Run TypeScript type checking
	@pnpm type-check

security-scan: ## Run security vulnerability scan
	@printf "${YELLOW}🔒 Scanning for security vulnerabilities...${NC}\n"
	@pnpm audit
	@snyk test
	@printf "${GREEN}✅ Security scan complete${NC}\n"

# =============================================================================
# CLEANUP
# =============================================================================

clean: ## Clean build artifacts and dependencies
	@printf "${YELLOW}🧹 Cleaning project...${NC}\n"
	@rm -rf node_modules
	@rm -rf apps/**/node_modules
	@rm -rf apps/**/dist
	@rm -rf apps/**/build
	@rm -rf packages/**/node_modules
	@rm -rf packages/**/dist
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete
	@printf "${GREEN}✅ Clean complete${NC}\n"

clean-cache: ## Clear all cache directories
	@printf "${YELLOW}🗑️  Clearing cache...${NC}\n"
	@rm -rf storage/cache/*
	@rm -rf .turbo
	@rm -rf **/.turbo
	@docker exec abdulboy-ebook-redis redis-cli FLUSHALL
	@printf "${GREEN}✅ Cache cleared${NC}\n"

# =============================================================================
# MONITORING
# =============================================================================

monitor-up: ## Start monitoring stack (Prometheus + Grafana)
	@docker-compose -f infra/monitoring/docker-compose.yml up -d

monitor-down: ## Stop monitoring stack
	@docker-compose -f infra/monitoring/docker-compose.yml down

grafana: ## Open Grafana dashboard
	@open http://localhost:3000

prometheus: ## Open Prometheus dashboard
	@open http://localhost:9090

# =============================================================================
# UTILITY
# =============================================================================

logs: ## View all logs
	@$(DOCKER_COMPOSE) logs -f

status: ## Check status of all services
	@$(DOCKER_COMPOSE) ps
	@printf "\n"
	@git status --short

info: ## Display project information
	@printf "\n${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}\n"
	@printf "${BLUE}║${NC}              ${GREEN}ABDULBOY EBOOK EMPIRE INFO${NC}                         ${BLUE}║${NC}\n"
	@printf "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}\n"
	@printf "${YELLOW}Project Name:${NC}     ${PROJECT_NAME}\n"
	@printf "${YELLOW}Version:${NC}           $(shell node -p "require('./package.json').version")\n"
	@printf "${YELLOW}Node Version:${NC}      $(shell node --version)\n"
	@printf "${YELLOW}pnpm Version:${NC}      $(shell pnpm --version)\n"
	@printf "${YELLOW}Python Version:${NC}    $(shell python3 --version 2>/dev/null || echo 'Not installed')\n"
	@printf "${YELLOW}Docker Version:${NC}    $(shell docker --version)\n"
	@printf "${YELLOW}Total Files:${NC}       508\n"
	@printf "${YELLOW}Total Lines:${NC}       $(shell find . -name "*.py" -o -name "*.js" -o -name "*.html" -o -name "*.css" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $$1}')\n"
	@printf "\n"

# =============================================================================
# SHELL ACCESS
# =============================================================================

shell-api: ## Open a shell in the API container
	@docker exec -it abdulboy-ebook-api /bin/bash

shell-web: ## Open a shell in the Web container
	@docker exec -it abdulboy-ebook-web /bin/sh

shell-db: ## Open PostgreSQL shell
	@docker exec -it abdulboy-ebook-postgres psql -U abdulboy_admin -d abdulboy_ebook_empire

shell-redis: ## Open Redis CLI
	@docker exec -it abdulboy-ebook-redis redis-cli

# =============================================================================
# MAINTENANCE
# =============================================================================

update-deps: ## Update all dependencies to latest versions
	@pnpm update --latest
	@cd apps/api && pip install --upgrade -r requirements/base.txt

ssl-renew: ## Renew SSL certificates
	@sudo certbot renew --nginx

health-check: ## Check application health
	@curl -s http://localhost:8000/api/v1/health | jq .
	@curl -s http://localhost:3000/health | jq .
