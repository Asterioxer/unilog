# Production Multi-Stage Dockerfile for unilog Platform API
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS builder

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c /uv /uv/bin/uv

# Copy project manifests
COPY pyproject.toml README.md ./
COPY unilog ./unilog
COPY api ./api

# Build wheel and install production dependencies
RUN /uv/bin/uv pip install --system --no-cache .

FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS runner

WORKDIR /app

# Copy installed site-packages and app code from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY unilog ./unilog
COPY api ./api

EXPOSE 8002

ENV PORT=8002 \
    PYTHONUNBUFFERED=1 \
    UNILOG_ENV=production

# Non-root security user
RUN useradd -m -u 1000 unilog && chown -R unilog:unilog /app
USER unilog

HEALTHCHECK --interval=5s --timeout=5s --start-period=15s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/health')"


CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8002"]

