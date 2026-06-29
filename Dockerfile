# syntax=docker/dockerfile:1
# ── builder ──────────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Copy manifest files first so the dependency layer is cached independently
# of source changes.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ── runtime ───────────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

RUN useradd --create-home --uid 1000 --shell /bin/sh appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

# HTTP transport defaults; override via environment variables.
ENV OPNSENSE_TRANSPORT=http \
    OPNSENSE_HTTP_HOST=0.0.0.0 \
    OPNSENSE_HTTP_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python3 -c "import socket; socket.create_connection(('localhost', 8000), timeout=2)"

CMD ["opnsense-mcp"]
