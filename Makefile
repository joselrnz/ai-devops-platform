.PHONY: help install test lint build up down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Development
# ============================================

install: ## Install all dependencies
	cd mcp-aws-server && pip install -e ".[dev]"
	cd llm-security-gateway && pip install -e ".[dev]"
	cd nl-automation-hub && pip install -e ".[dev]"

test: ## Run all tests
	cd mcp-aws-server && pytest
	cd llm-security-gateway && pytest
	cd nl-automation-hub && pytest

lint: ## Run linters on all projects
	cd mcp-aws-server && ruff check . && mypy .
	cd llm-security-gateway && ruff check . && mypy .
	cd nl-automation-hub && ruff check . && mypy .

# ============================================
# Docker
# ============================================

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

# ============================================
# Individual Services
# ============================================

aws-server: ## Run MCP AWS Server locally
	cd mcp-aws-server && uvicorn src.main:app --reload --port 8001

gateway: ## Run LLM Security Gateway locally
	cd llm-security-gateway && uvicorn src.main:app --reload --port 8002

hub: ## Run NL Automation Hub locally
	cd nl-automation-hub && uvicorn src.main:app --reload --port 8000

# ============================================
# Cleanup
# ============================================

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
