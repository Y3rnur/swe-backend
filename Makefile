.PHONY: help install dev start test lint format type-check clean docker-build docker-up docker-down migrate revision upgrade seed

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pre-commit install

dev: ## Run the development server
	uvicorn app.main:app --reload

start: ## Run the production server
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term

lint: ## Run linter
	ruff check .

lint-fix: ## Run linter and fix issues
	ruff check --fix .

format: ## Format code
	ruff format .

type-check: ## Run type checker
	mypy .

check: lint type-check test ## Run all checks

migrate: ## Create a new migration (use MESSAGE="description")
	alembic revision --autogenerate -m "$(MESSAGE)"

revision: migrate ## Alias for migrate (create a new migration)

upgrade: ## Apply database migrations
	alembic upgrade head

downgrade: ## Rollback one migration
	alembic downgrade -1

seed: ## Seed database with initial data
	@echo "Seed command not yet implemented"
	@echo "TODO: Add database seeding script"

clean: ## Clean cache and build files
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	rm -rf htmlcov .coverage
	rm -rf build dist *.egg-info

docker-build: ## Build Docker image
	docker build -t swe-backend .

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## View Docker Compose logs
	docker-compose logs -f

docker-shell: ## Open shell in Docker container
	docker-compose exec app bash

