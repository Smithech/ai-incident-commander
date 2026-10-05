FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY tests ./tests

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]