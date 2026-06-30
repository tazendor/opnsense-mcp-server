# syntax=docker/dockerfile:1
# ── builder ──────────────────────────────────────────────────────────────────
# ghcr.io/astral-sh/uv:python3.14-bookworm-slim
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim@sha256:7cf77f594be8042dab6daa9fe326f90962252268b4f120a7f5dccce4d947e6c1 AS builder

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
# python:3.14-slim-bookworm
FROM python:3.14-slim-bookworm@sha256:4ff4b92a68355dbdb52584ab3391dff8d371a61d4e063468bfd0130e3189c6d9

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
