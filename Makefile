# Makefile for ChannelWright Discord Bot

.PHONY: help build deploy clean test lint format install-deps

# Default environment
ENV ?= dev

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)ChannelWright Discord Bot$(NC)"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install-deps: ## Install Python dependencies
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	pip install -r requirements.txt

build: ## Build the deployment package
	@echo "$(YELLOW)Building deployment package...$(NC)"
	chmod +x scripts/build.sh
	./scripts/build.sh

deploy: build ## Deploy to AWS (usage: make deploy ENV=dev)
	@echo "$(YELLOW)Deploying to $(ENV) environment...$(NC)"
	@if [ -z "$$DISCORD_BOT_TOKEN" ]; then \
		echo "$(RED)Error: DISCORD_BOT_TOKEN environment variable is required$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$$DISCORD_APPLICATION_ID" ]; then \
		echo "$(RED)Error: DISCORD_APPLICATION_ID environment variable is required$(NC)"; \
		exit 1; \
	fi
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh $(ENV)

register-commands: ## Register Discord slash commands
	@echo "$(YELLOW)Registering Discord commands...$(NC)"
	chmod +x scripts/register-commands.py
	python3 scripts/register-commands.py

destroy: ## Destroy AWS infrastructure (usage: make destroy ENV=dev)
	@echo "$(RED)Destroying $(ENV) environment...$(NC)"
	@read -p "Are you sure you want to destroy the $(ENV) environment? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		cd terraform && terraform destroy \
			-var="environment=$(ENV)" \
			-var="discord_bot_token=dummy" \
			-var="discord_application_id=dummy"; \
	else \
		echo "$(YELLOW)Destruction cancelled$(NC)"; \
	fi

clean: ## Clean build artifacts
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf dist/
	rm -rf src/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

test: ## Run tests (placeholder)
	@echo "$(YELLOW)Running tests...$(NC)"
	@echo "$(BLUE)No tests implemented yet$(NC)"

lint: ## Run code linting
	@echo "$(YELLOW)Running linting...$(NC)"
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 src/ --max-line-length=120; \
	else \
		echo "$(YELLOW)flake8 not installed, skipping linting$(NC)"; \
	fi

format: ## Format code
	@echo "$(YELLOW)Formatting code...$(NC)"
	@if command -v black >/dev/null 2>&1; then \
		black src/ --line-length=120; \
	else \
		echo "$(YELLOW)black not installed, skipping formatting$(NC)"; \
	fi

logs: ## View Lambda function logs (usage: make logs ENV=dev)
	@echo "$(YELLOW)Viewing logs for $(ENV) environment...$(NC)"
	aws logs tail /aws/lambda/channelwright-bot-$(ENV) --follow

status: ## Check deployment status
	@echo "$(YELLOW)Checking deployment status...$(NC)"
	cd terraform && terraform show

plan: ## Plan Terraform changes (usage: make plan ENV=dev)
	@echo "$(YELLOW)Planning changes for $(ENV) environment...$(NC)"
	@if [ -z "$$DISCORD_BOT_TOKEN" ]; then \
		echo "$(RED)Error: DISCORD_BOT_TOKEN environment variable is required$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$$DISCORD_APPLICATION_ID" ]; then \
		echo "$(RED)Error: DISCORD_APPLICATION_ID environment variable is required$(NC)"; \
		exit 1; \
	fi
	cd terraform && terraform plan \
		-var="environment=$(ENV)" \
		-var="discord_bot_token=$$DISCORD_BOT_TOKEN" \
		-var="discord_application_id=$$DISCORD_APPLICATION_ID"

init: ## Initialize Terraform
	@echo "$(YELLOW)Initializing Terraform...$(NC)"
	cd terraform && terraform init

validate: ## Validate Terraform configuration
	@echo "$(YELLOW)Validating Terraform configuration...$(NC)"
	cd terraform && terraform validate

setup-env: ## Setup environment file
	@echo "$(YELLOW)Setting up environment file...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file from template$(NC)"; \
		echo "$(YELLOW)Please edit .env with your Discord bot credentials$(NC)"; \
	else \
		echo "$(BLUE).env file already exists$(NC)"; \
	fi

all: install-deps build deploy register-commands ## Complete setup and deployment
