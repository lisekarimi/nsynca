# Dockerfile
FROM python:3.11-slim
RUN pip install uv

WORKDIR /app

# Copy dependency files first (changes rarely)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code (changes frequently)
COPY . .
CMD ["uv", "run", "main.py"]
# CMD ["uv", "run", "gui.py"]
