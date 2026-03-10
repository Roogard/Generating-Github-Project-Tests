FROM python:3.12-slim

# Install uv and git
RUN pip install --no-cache-dir uv && \
    apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies (cached layer)
COPY pyproject.toml ./
RUN uv sync --no-dev

# Copy source
COPY src/ ./src/

# Default output directory (override via -v mount)
RUN mkdir -p /output

ENTRYPOINT ["uv", "run", "python", "-m", "src.main", "--output", "/output"]
