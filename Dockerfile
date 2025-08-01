FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && export UV_INSTALL_DIR=/usr/local/bin \
 && curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

# Copy project files for uv sync
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
