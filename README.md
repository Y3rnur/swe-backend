# FastAPI Backend Server

Minimal FastAPI server with PostgreSQL, async SQLAlchemy, and Alembic.

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your DATABASE_URL

# Run migrations
alembic upgrade head

# Start server (development)
make dev
# Or: scripts.ps1 dev  (Windows PowerShell)
# Or: scripts.bat dev  (Windows CMD)
```

Server: http://localhost:8000 Docs: http://localhost:8000/docs

## Docker

```bash
docker-compose up -d
```

## Development Commands

```bash
make dev           # Run development server with hot reload
make start         # Run production server
make test          # Run tests
make lint          # Run linter
make format        # Format code
make type-check    # Type check
make migrate       # Create migration (use MESSAGE="description")
make upgrade       # Apply migrations
```
