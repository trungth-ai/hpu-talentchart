# Dockerfile — TalentChart backend (FastAPI + uv, port 8003)

FROM python:3.12-slim AS base
WORKDIR /app
RUN adduser --disabled-password --no-create-home --gecos "" appuser \
    && apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# uv — package manager (thay pip, theo chuẩn hpu-dev v2.0)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Cài dependencies trước để tận dụng layer cache
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project || uv sync --no-dev --no-install-project --no-cache

# ★ Venv vào PATH — runtime gọi thẳng uvicorn/celery/alembic, KHÔNG qua `uv run`
# (appuser không có home dir → uv run lúc runtime sẽ lỗi Permission denied khi tạo cache)
ENV PATH="/app/.venv/bin:$PATH" \
    UV_CACHE_DIR=/tmp/uv-cache

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/ ./scripts/

RUN mkdir -p /app/logs /app/uploads && chown -R appuser:appuser /app

USER appuser
EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8003", "--workers", "2"]
