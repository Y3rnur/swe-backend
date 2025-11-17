# Dockerfile for B2B Supplier-Wholesale Exchange Platform
#
# This Dockerfile creates a production-ready image for the FastAPI application.
# It uses a multi-stage build to optimize image size and security.
#
# Build:
#   docker build -t swe-backend:latest .
#
# Run:
#   docker run -p 8000:8000 -e DATABASE_URL=... swe-backend:latest
#
# Multi-stage build:
#   - Stage 1 (builder): Install dependencies and build artifacts
#   - Stage 2 (runtime): Copy only necessary files for runtime

# ==============================================================================
# Stage 1: Builder
# ==============================================================================
# This stage installs dependencies and prepares the build environment
FROM python:3.13.5-slim AS builder

# Set build arguments
ARG BUILDPLATFORM
ARG TARGETPLATFORM

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies required for building Python packages
# gcc: Required for compiling some Python packages (e.g., asyncpg, bcrypt)
# postgresql-client: Optional, useful for database migrations and debugging
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements file first for better layer caching
# This allows Docker to cache the dependency installation layer
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir to reduce image size
# Using --user to install packages in user directory (optional, can be removed)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Runtime
# ==============================================================================
# This stage creates the final production image with only runtime dependencies
FROM python:3.13.5-slim AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.local/bin:$PATH"

# Install runtime system dependencies only
# postgresql-client: For database migrations (alembic) and debugging
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user for security
# Running as root in containers is a security risk
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create application directory and set ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Copy Python packages from builder stage
# Copy the entire Python installation (site-packages and binaries)
# This ensures all dependencies are available in the runtime image
COPY --from=builder /usr/local/lib/python3.13 /usr/local/lib/python3.13
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
# This is done after dependency installation for better caching
# If code changes, only this layer needs to be rebuilt
COPY --chown=appuser:appuser . .

# Create logs directory with proper permissions
RUN mkdir -p logs && \
    chown -R appuser:appuser logs && \
    chmod 755 logs

# Switch to non-root user
USER appuser

# Expose the application port
# This is informational and doesn't actually publish the port
EXPOSE 8000

# Health check configuration
# This allows Docker to monitor the container's health
# The endpoint should return 200 OK if the service is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command to run the application
# Using uvicorn as the ASGI server
# --host 0.0.0.0: Listen on all network interfaces
# --port 8000: Listen on port 8000
# Note: In production, consider using a process manager like gunicorn with uvicorn workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==============================================================================
# Development Stage (Optional)
# ==============================================================================
# Uncomment the section below to create a development image with hot reload
# This stage includes development dependencies and mounts code as volumes

# FROM runtime AS development
# USER root
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     git \
#     vim \
#     && rm -rf /var/lib/apt/lists/*
# USER appuser
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
