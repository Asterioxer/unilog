FROM python:3.12-slim

# Install astral/uv
COPY --from=astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy specification files for caching
COPY pyproject.toml uv.lock ./

# Pre-install dependencies
RUN uv sync --no-install-project --all-extras

# Copy repository contents
COPY . .

# Install package
RUN uv sync --all-extras

# Expose FastAPI default port
EXPOSE 8000

# Set Python path to find api app modules
ENV PYTHONPATH=/app

# Run service
CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
