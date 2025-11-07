# ================================
# Crypto Price Alert System - Makefile
# ================================
# Convenience commands for Docker operations
# ================================

.PHONY: help
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Docker Compose files
COMPOSE_FILE := docker-compose.yml
COMPOSE_DEV := docker-compose.dev.yml
COMPOSE_PROD := docker-compose.prod.yml

# Docker Compose commands
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := $(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -f $(COMPOSE_DEV)
DOCKER_COMPOSE_PROD := $(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -f $(COMPOSE_PROD)

# ================================
# Help
# ================================
help: ## Show this help message
	@echo "$(CYAN)Crypto Price Alert System - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  1. Copy environment file:    cp .env.example .env"
	@echo "  2. Edit .env with your values"
	@echo "  3. Run development:          make dev"
	@echo "  4. Run production:           make prod"
	@echo ""

# ================================
# Environment Setup
# ================================
.env: ## Create .env file from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓$(NC) Created .env file from .env.example"; \
		echo "$(YELLOW)⚠$(NC)  Please edit .env and add your configuration"; \
	else \
		echo "$(YELLOW)⚠$(NC)  .env file already exists"; \
	fi

check-env: ## Check if .env file exists
	@if [ ! -f .env ]; then \
		echo "$(RED)✗$(NC) .env file not found. Run 'make .env' first"; \
		exit 1; \
	fi

validate-env: check-env ## Validate required environment variables
	@echo "$(CYAN)Validating environment variables...$(NC)"
	@bash -c 'source .env && \
		if [ -z "$$TELEGRAM_BOT_TOKEN" ]; then echo "$(RED)✗$(NC) TELEGRAM_BOT_TOKEN is not set"; exit 1; fi && \
		if [ -z "$$AUTH_TOKEN" ]; then echo "$(RED)✗$(NC) AUTH_TOKEN is not set"; exit 1; fi && \
		if [ "$${#AUTH_TOKEN}" -lt 32 ]; then echo "$(RED)✗$(NC) AUTH_TOKEN must be at least 32 characters"; exit 1; fi && \
		echo "$(GREEN)✓$(NC) Environment variables are valid"'

# ================================
# Development Commands
# ================================
dev: check-env ## Start services in development mode
	@echo "$(CYAN)Starting services in development mode...$(NC)"
	$(DOCKER_COMPOSE_DEV) up --build

dev-daemon: check-env ## Start services in development mode (background)
	@echo "$(CYAN)Starting services in development mode (background)...$(NC)"
	$(DOCKER_COMPOSE_DEV) up --build -d
	@echo "$(GREEN)✓$(NC) Services started in background"
	@echo "$(YELLOW)Run 'make logs' to view logs$(NC)"

dev-down: ## Stop development services
	@echo "$(CYAN)Stopping development services...$(NC)"
	$(DOCKER_COMPOSE_DEV) down
	@echo "$(GREEN)✓$(NC) Development services stopped"

# ================================
# Production Commands
# ================================
prod: check-env validate-env ## Start services in production mode
	@echo "$(CYAN)Starting services in production mode...$(NC)"
	$(DOCKER_COMPOSE_PROD) up -d
	@echo "$(GREEN)✓$(NC) Services started in production mode"
	@$(MAKE) status

prod-build: check-env ## Build production images
	@echo "$(CYAN)Building production images...$(NC)"
	$(DOCKER_COMPOSE_PROD) build --no-cache
	@echo "$(GREEN)✓$(NC) Production images built"

prod-down: ## Stop production services
	@echo "$(CYAN)Stopping production services...$(NC)"
	$(DOCKER_COMPOSE_PROD) down
	@echo "$(GREEN)✓$(NC) Production services stopped"

prod-restart: ## Restart production services
	@$(MAKE) prod-down
	@$(MAKE) prod

# ================================
# Monitoring Stack
# ================================
monitoring-up: check-env ## Start with monitoring stack (Prometheus + Grafana)
	@echo "$(CYAN)Starting services with monitoring stack...$(NC)"
	$(DOCKER_COMPOSE_PROD) --profile monitoring up -d
	@echo "$(GREEN)✓$(NC) Services with monitoring started"
	@echo "$(YELLOW)Grafana:$(NC)    http://localhost:3000"
	@echo "$(YELLOW)Prometheus:$(NC) http://localhost:9090"

monitoring-down: ## Stop monitoring stack
	@echo "$(CYAN)Stopping monitoring stack...$(NC)"
	$(DOCKER_COMPOSE_PROD) --profile monitoring down
	@echo "$(GREEN)✓$(NC) Monitoring stack stopped"

# ================================
# Common Commands
# ================================
build: ## Build all services
	@echo "$(CYAN)Building all services...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓$(NC) All services built"

up: check-env ## Start all services (foreground)
	@echo "$(CYAN)Starting all services...$(NC)"
	$(DOCKER_COMPOSE) up

up-daemon: check-env ## Start all services (background)
	@echo "$(CYAN)Starting all services (background)...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓$(NC) Services started"
	@$(MAKE) status

down: ## Stop all services
	@echo "$(CYAN)Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓$(NC) All services stopped"

restart: ## Restart all services
	@$(MAKE) down
	@$(MAKE) up-daemon

# ================================
# Status and Logs
# ================================
status: ## Show status of all services
	@echo "$(CYAN)Service Status:$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(CYAN)Health Status:$(NC)"
	@docker ps --filter "name=crypto-" --format "table {{.Names}}\t{{.Status}}"

ps: status ## Alias for status

logs: ## Tail logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-crypto: ## Tail logs from crypto service
	$(DOCKER_COMPOSE) logs -f crypto-service

logs-telegram: ## Tail logs from telegram service
	$(DOCKER_COMPOSE) logs -f telegram-service

logs-postgres: ## Tail logs from postgres
	$(DOCKER_COMPOSE) logs -f postgres

# ================================
# Health Checks
# ================================
health: ## Check health of all services
	@echo "$(CYAN)Checking service health...$(NC)"
	@echo ""
	@echo "$(YELLOW)Crypto Service:$(NC)"
	@curl -f http://localhost:52000/health 2>/dev/null && echo " $(GREEN)✓$(NC)" || echo " $(RED)✗$(NC)"
	@echo ""
	@echo "$(YELLOW)Telegram Service:$(NC)"
	@curl -f http://localhost:52001/health 2>/dev/null && echo " $(GREEN)✓$(NC)" || echo " $(RED)✗$(NC)"
	@echo ""

ping: health ## Alias for health

# ================================
# Database Operations
# ================================
db-migrate: ## Run database migrations
	@echo "$(CYAN)Running database migrations...$(NC)"
	$(DOCKER_COMPOSE) exec crypto-service alembic upgrade head
	@echo "$(GREEN)✓$(NC) Migrations completed"

db-shell: ## Open PostgreSQL shell
	@echo "$(CYAN)Opening PostgreSQL shell...$(NC)"
	$(DOCKER_COMPOSE) exec postgres psql -U crypto_user -d crypto_alerts

db-backup: ## Backup PostgreSQL database
	@echo "$(CYAN)Backing up database...$(NC)"
	@mkdir -p backups
	@docker exec crypto-postgres pg_dump -U crypto_user crypto_alerts > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓$(NC) Database backed up to backups/"

db-restore: ## Restore PostgreSQL database from latest backup
	@echo "$(CYAN)Restoring database from latest backup...$(NC)"
	@latest_backup=$$(ls -t backups/*.sql 2>/dev/null | head -1); \
	if [ -z "$$latest_backup" ]; then \
		echo "$(RED)✗$(NC) No backup files found in backups/"; \
		exit 1; \
	fi; \
	echo "$(YELLOW)Restoring from:$(NC) $$latest_backup"; \
	cat "$$latest_backup" | docker exec -i crypto-postgres psql -U crypto_user crypto_alerts && \
	echo "$(GREEN)✓$(NC) Database restored"

# ================================
# Testing
# ================================
test: ## Run tests in crypto service
	@echo "$(CYAN)Running tests...$(NC)"
	$(DOCKER_COMPOSE) exec crypto-service pytest -v
	@echo "$(GREEN)✓$(NC) Tests completed"

test-integration: ## Run integration tests
	@echo "$(CYAN)Running integration tests...$(NC)"
	$(DOCKER_COMPOSE) exec crypto-service pytest -v -m integration
	@echo "$(GREEN)✓$(NC) Integration tests completed"

# ================================
# Shell Access
# ================================
shell-crypto: ## Open shell in crypto service container
	$(DOCKER_COMPOSE) exec crypto-service /bin/bash

shell-telegram: ## Open shell in telegram service container
	$(DOCKER_COMPOSE) exec telegram-service /bin/bash

shell-postgres: ## Open shell in postgres container
	$(DOCKER_COMPOSE) exec postgres /bin/bash

# ================================
# Cleanup Commands
# ================================
clean: ## Stop services and remove volumes (data will be lost!)
	@echo "$(RED)⚠  WARNING: This will delete all data!$(NC)"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@echo "$(CYAN)Stopping services and removing volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✓$(NC) Services stopped and volumes removed"

clean-all: clean ## Clean everything including images
	@echo "$(CYAN)Removing Docker images...$(NC)"
	docker images "crypto-alert/*" -q | xargs -r docker rmi -f
	@echo "$(GREEN)✓$(NC) All cleaned up"

prune: ## Remove unused Docker resources
	@echo "$(CYAN)Pruning unused Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓$(NC) Unused resources removed"

# ================================
# Image Management
# ================================
pull: ## Pull latest base images
	@echo "$(CYAN)Pulling latest base images...$(NC)"
	docker pull python:3.11-slim
	docker pull postgres:16-alpine
	docker pull prom/prometheus:latest
	docker pull grafana/grafana:latest
	@echo "$(GREEN)✓$(NC) Base images pulled"

images: ## List all crypto-alert images
	@echo "$(CYAN)Crypto Alert Images:$(NC)"
	@docker images "crypto-alert/*"

# ================================
# Development Utilities
# ================================
format: ## Format code (if tools are available)
	@echo "$(CYAN)Formatting code...$(NC)"
	@docker run --rm -v $(PWD)/src:/src -w /src python:3.11-slim sh -c "pip install black isort && black . && isort ."
	@echo "$(GREEN)✓$(NC) Code formatted"

lint: ## Lint code (if tools are available)
	@echo "$(CYAN)Linting code...$(NC)"
	@docker run --rm -v $(PWD)/src:/src -w /src python:3.11-slim sh -c "pip install flake8 && flake8 ."

# ================================
# Information
# ================================
info: ## Show system information
	@echo "$(CYAN)System Information:$(NC)"
	@echo ""
	@echo "$(YELLOW)Docker Version:$(NC)"
	@docker --version
	@echo ""
	@echo "$(YELLOW)Docker Compose Version:$(NC)"
	@docker-compose --version
	@echo ""
	@echo "$(YELLOW)Available Compose Files:$(NC)"
	@ls -1 docker-compose*.yml
	@echo ""
	@echo "$(YELLOW)Environment File:$(NC)"
	@if [ -f .env ]; then echo "$(GREEN)✓$(NC) .env exists"; else echo "$(RED)✗$(NC) .env not found"; fi
	@echo ""

ports: ## Show exposed ports
	@echo "$(CYAN)Service Ports:$(NC)"
	@echo "  $(YELLOW)Crypto Service:$(NC)    http://localhost:52000"
	@echo "  $(YELLOW)Telegram Service:$(NC)  http://localhost:52001 (internal)"
	@echo "  $(YELLOW)PostgreSQL:$(NC)        localhost:5432 (internal)"
	@echo "  $(YELLOW)Prometheus:$(NC)        http://localhost:9090 (with --profile monitoring)"
	@echo "  $(YELLOW)Grafana:$(NC)           http://localhost:3000 (with --profile monitoring)"
	@echo ""

# ================================
# Documentation
# ================================
docs: ## Open documentation
	@echo "$(CYAN)Documentation:$(NC)"
	@echo "  Main Guide:       docs/deployment/DOCKER_GUIDE.md"
	@echo "  Telegram Setup:   src/telegram_service/README.md"
	@echo "  Crypto Service:   src/crypto_service/README.md"
	@echo ""

# ================================
# Quick Commands
# ================================
init: .env ## Initialize project (create .env and setup directories)
	@echo "$(CYAN)Initializing project...$(NC)"
	@mkdir -p data backups config/prometheus config/grafana
	@echo "$(GREEN)✓$(NC) Project initialized"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env file with your configuration"
	@echo "  2. Run 'make dev' for development"
	@echo "  3. Run 'make prod' for production"
	@echo ""

start: up-daemon ## Alias for up-daemon

stop: down ## Alias for down
