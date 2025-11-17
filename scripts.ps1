# PowerShell scripts similar to npm scripts

param(
    [Parameter(Position=0)]
    [string]$Command,
    [Parameter(Position=1)]
    [string]$MESSAGE = ""
)

switch ($Command) {
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Green
        pip install -r requirements.txt
        pre-commit install
    }
    "dev" {
        Write-Host "Starting development server..." -ForegroundColor Green
        uvicorn app.main:app --reload
    }
    "start" {
        Write-Host "Starting production server..." -ForegroundColor Green
        uvicorn app.main:app --host 0.0.0.0 --port 8000
    }
    "test" {
        Write-Host "Running tests..." -ForegroundColor Green
        pytest
    }
    "test-cov" {
        Write-Host "Running tests with coverage..." -ForegroundColor Green
        pytest --cov=. --cov-report=html --cov-report=term
    }
    "lint" {
        Write-Host "Running linter..." -ForegroundColor Green
        ruff check .
    }
    "lint-fix" {
        Write-Host "Running linter and fixing issues..." -ForegroundColor Green
        ruff check --fix .
    }
    "format" {
        Write-Host "Formatting code..." -ForegroundColor Green
        ruff format .
    }
    "type-check" {
        Write-Host "Running type checker..." -ForegroundColor Green
        mypy .
    }
    "check" {
        Write-Host "Running all checks..." -ForegroundColor Green
        ruff check .
        mypy .
        pytest
    }
    "migrate" {
        if ($MESSAGE -eq "") {
            Write-Host "Error: MESSAGE parameter required" -ForegroundColor Red
            Write-Host "Usage: .\scripts.ps1 migrate -MESSAGE 'description'" -ForegroundColor Yellow
            break
        }
        Write-Host "Creating migration..." -ForegroundColor Green
        alembic revision --autogenerate -m "$MESSAGE"
    }
    "revision" {
        if ($MESSAGE -eq "") {
            Write-Host "Error: MESSAGE parameter required" -ForegroundColor Red
            Write-Host "Usage: .\scripts.ps1 revision -MESSAGE 'description'" -ForegroundColor Yellow
            break
        }
        Write-Host "Creating migration..." -ForegroundColor Green
        alembic revision --autogenerate -m "$MESSAGE"
    }
    "upgrade" {
        Write-Host "Applying migrations..." -ForegroundColor Green
        alembic upgrade head
    }
    "downgrade" {
        Write-Host "Rolling back one migration..." -ForegroundColor Green
        alembic downgrade -1
    }
    "seed" {
        Write-Host "Seed command not yet implemented" -ForegroundColor Yellow
        Write-Host "TODO: Add database seeding script" -ForegroundColor Yellow
    }
    "clean" {
        Write-Host "Cleaning cache and build files..." -ForegroundColor Green
        Get-ChildItem -Path . -Include __pycache__,*.pyc,.pytest_cache,.mypy_cache,.ruff_cache -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path htmlcov) { Remove-Item -Recurse -Force htmlcov }
        if (Test-Path .coverage) { Remove-Item -Force .coverage }
        if (Test-Path build) { Remove-Item -Recurse -Force build }
        if (Test-Path dist) { Remove-Item -Recurse -Force dist }
        Get-ChildItem -Path . -Filter *.egg-info -Directory | Remove-Item -Recurse -Force
        Write-Host "Cleanup complete" -ForegroundColor Green
    }
    "docker-build" {
        Write-Host "Building Docker image..." -ForegroundColor Green
        docker build -t swe-backend .
    }
    "docker-up" {
        Write-Host "Starting Docker Compose services..." -ForegroundColor Green
        docker-compose up -d
    }
    "docker-down" {
        Write-Host "Stopping Docker Compose services..." -ForegroundColor Green
        docker-compose down
    }
    "docker-logs" {
        Write-Host "Viewing Docker Compose logs..." -ForegroundColor Green
        docker-compose logs -f
    }
    "docker-shell" {
        Write-Host "Opening shell in Docker container..." -ForegroundColor Green
        docker-compose exec app bash
    }
    default {
        Write-Host "Available commands:" -ForegroundColor Yellow
        Write-Host "  .\scripts.ps1 install       - Install dependencies" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 dev           - Run development server" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 start         - Run production server" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 test          - Run tests" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 test-cov      - Run tests with coverage" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 lint          - Run linter" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 lint-fix      - Run linter and fix issues" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 format        - Format code" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 type-check    - Run type checker" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 check         - Run all checks" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 migrate -MESSAGE 'description'  - Create migration" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 revision -MESSAGE 'description' - Alias for migrate" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 upgrade       - Apply migrations" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 downgrade     - Rollback one migration" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 seed          - Seed database" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 clean         - Clean cache and build files" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 docker-build  - Build Docker image" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 docker-up     - Start Docker Compose services" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 docker-down   - Stop Docker Compose services" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 docker-logs   - View Docker Compose logs" -ForegroundColor Cyan
        Write-Host "  .\scripts.ps1 docker-shell  - Open shell in Docker container" -ForegroundColor Cyan
    }
}

