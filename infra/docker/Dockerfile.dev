# =============================================================================
# ABDULBOY EBOOK EMPIRE - PRODUCTION DOCKERFILE
# =============================================================================
# Multi-stage build for optimized production image
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder - Build dependencies and compile assets
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY apps/api/pyproject.toml apps/api/poetry.lock* ./

# Install dependencies (including dev for building)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# -----------------------------------------------------------------------------
# STAGE 2: Frontend Builder - Build static assets
# -----------------------------------------------------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy frontend source
COPY apps/web/package*.json ./
COPY apps/web/ ./

# Install dependencies and build
RUN npm ci --only=production \
    && npm run build

# -----------------------------------------------------------------------------
# STAGE 3: Runtime - Production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

# Create non-root user
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 appuser

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libmagic1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY apps/api/ .

# Copy frontend static files
COPY --from=frontend-builder /app/dist /app/static

# Copy entrypoint script
COPY apps/api/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/storage \
    && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

# Start command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app.app:app"]
