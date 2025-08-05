FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache --no-dev

COPY . .

RUN mkdir -p logs

EXPOSE 8000

ENV UV_PROJECT_ENVIRONMENT=/app/.venv

CMD ["uv", "run", "uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8000"]