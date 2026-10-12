FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml .
COPY aegis/ aegis/
COPY configs/ configs/
COPY data/ data/
COPY artifacts/ artifacts/
COPY services/ services/

RUN uv venv && uv pip install -e .

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["uv", "run", "uvicorn", "services.inference.main:app", "--host", "0.0.0.0", "--port", "8001"]
