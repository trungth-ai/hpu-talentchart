# Dockerfile Template — HPU FastAPI Internal Tools (Jinja2 + SQLite)
# File: ~/hpu-dev/_shared/docker-templates/Dockerfile.fastapi

# Stage 1: Base
FROM python:3.11-slim AS base
WORKDIR /app
RUN adduser --disabled-password --no-create-home --gecos "" appuser
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Application
FROM deps AS app
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/
COPY scripts/ ./scripts/

# Create data directories
RUN mkdir -p /app/data /app/logs /app/uploads \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "src.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log"]
