@echo off
REM Windows batch scripts similar to npm scripts

if "%1"=="install" (
    pip install -r requirements.txt
    pre-commit install
    goto :eof
)

if "%1"=="dev" (
    uvicorn app.main:app --reload
    goto :eof
)

if "%1"=="start" (
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    goto :eof
)

if "%1"=="test" (
    pytest
    goto :eof
)

if "%1"=="test-cov" (
    pytest --cov=. --cov-report=html --cov-report=term
    goto :eof
)

if "%1"=="lint" (
    ruff check .
    goto :eof
)

if "%1"=="lint-fix" (
    ruff check --fix .
    goto :eof
)

if "%1"=="format" (
    ruff format .
    goto :eof
)

if "%1"=="type-check" (
    mypy .
    goto :eof
)

if "%1"=="check" (
    ruff check .
    mypy .
    pytest
    goto :eof
)

if "%1"=="migrate" (
    if "%2"=="" (
        echo Error: MESSAGE parameter required
        echo Usage: scripts.bat migrate "description"
        goto :eof
    )
    alembic revision --autogenerate -m "%2"
    goto :eof
)

if "%1"=="revision" (
    if "%2"=="" (
        echo Error: MESSAGE parameter required
        echo Usage: scripts.bat revision "description"
        goto :eof
    )
    alembic revision --autogenerate -m "%2"
    goto :eof
)

if "%1"=="upgrade" (
    alembic upgrade head
    goto :eof
)

if "%1"=="downgrade" (
    alembic downgrade -1
    goto :eof
)

if "%1"=="seed" (
    echo Seed command not yet implemented
    echo TODO: Add database seeding script
    goto :eof
)

if "%1"=="clean" (
    if exist __pycache__ rmdir /s /q __pycache__
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
    for /r . %%f in (*.pyc) do @del /q "%%f"
    if exist .pytest_cache rmdir /s /q .pytest_cache
    if exist .mypy_cache rmdir /s /q .mypy_cache
    if exist .ruff_cache rmdir /s /q .ruff_cache
    if exist htmlcov rmdir /s /q htmlcov
    if exist .coverage del /q .coverage
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    if exist *.egg-info rmdir /s /q *.egg-info
    goto :eof
)

if "%1"=="docker-build" (
    docker build -t swe-backend .
    goto :eof
)

if "%1"=="docker-up" (
    docker-compose up -d
    goto :eof
)

if "%1"=="docker-down" (
    docker-compose down
    goto :eof
)

if "%1"=="docker-logs" (
    docker-compose logs -f
    goto :eof
)

if "%1"=="docker-shell" (
    docker-compose exec app bash
    goto :eof
)

echo Available commands:
echo   scripts.bat install      - Install dependencies
echo   scripts.bat dev          - Run development server
echo   scripts.bat start        - Run production server
echo   scripts.bat test         - Run tests
echo   scripts.bat test-cov     - Run tests with coverage
echo   scripts.bat lint         - Run linter
echo   scripts.bat lint-fix     - Run linter and fix issues
echo   scripts.bat format       - Format code
echo   scripts.bat type-check   - Run type checker
echo   scripts.bat check        - Run all checks
echo   scripts.bat migrate "description"  - Create migration
echo   scripts.bat revision "description" - Alias for migrate
echo   scripts.bat upgrade      - Apply migrations
echo   scripts.bat downgrade    - Rollback one migration
echo   scripts.bat seed         - Seed database
echo   scripts.bat clean        - Clean cache and build files
echo   scripts.bat docker-build - Build Docker image
echo   scripts.bat docker-up    - Start Docker Compose services
echo   scripts.bat docker-down  - Stop Docker Compose services
echo   scripts.bat docker-logs  - View Docker Compose logs
echo   scripts.bat docker-shell - Open shell in Docker container

