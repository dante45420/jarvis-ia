# Imagen del backend de Jarvis. Corre migraciones y luego el servidor.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn jarvis.interfaces.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
