FROM python:3.11-slim

# Install uv package manager from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Configure Python virtual environment location
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
ENV PYTHONPATH=/app

WORKDIR /app

# Copy dependency files first (changes rarely)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code (changes frequently)
COPY . .
CMD ["uv", "run", "main.py"]
