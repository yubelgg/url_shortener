FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy the rest of the project
COPY . .

# Expose port 8080 (DigitalOcean default)
EXPOSE 8080

# Run with gunicorn production server
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8080", "run:app"]
