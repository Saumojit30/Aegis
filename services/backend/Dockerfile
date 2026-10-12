FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml .
COPY aegis/ aegis/
COPY configs/ configs/
COPY data/ data/
COPY artifacts/ artifacts/
COPY services/ services/

# Sync virtualenv dependencies
RUN uv venv && uv pip install -e .

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "services.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
