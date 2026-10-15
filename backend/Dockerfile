# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Install dependencies first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source code and entry points
COPY src/ ./src/
COPY server.py main.py README.md ./

# Install the application into the virtual environment
RUN uv sync --frozen --no-dev

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create directories for persistent resume storage
RUN mkdir -p /app/data/resumes /app/qdrant_storage

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
