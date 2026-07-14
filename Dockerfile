FROM python:3.12.1-slim@sha256:ee9a59cfdad294560241c9a8c8e40034f165feb4af7088c1479c2cdd84aafbed

# Install astral/uv from official registry
COPY --from=ghcr.io/astral-sh/uv:0.3.3 /uv /uvx /bin/

# Set up non-root application user
RUN useradd -u 1000 -m appuser

WORKDIR /app
RUN chown appuser:appuser /app

# Switch to non-root user for security
USER appuser

# Copy specification files for caching
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Pre-install dependencies (layer caching optimization)
RUN uv sync --no-install-project --all-extras

# Copy repository contents
COPY --chown=appuser:appuser . .

# Install package
RUN uv sync --all-extras

# Expose FastAPI default port
EXPOSE 8000

# Set Python path to find api app modules
ENV PYTHONPATH=/app

# Healthcheck definition utilizing Python standard library to keep image slim
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/live', timeout=2)" || exit 1

# Run service
CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
