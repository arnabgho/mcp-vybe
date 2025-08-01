FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml README.md ./
COPY server.py ./

# Install Python dependencies using uv sync
RUN uv sync --frozen --no-dev

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (Render will set PORT env var)
EXPOSE 8000

# Run the server
CMD ["uv", "run", "python", "server.py"]