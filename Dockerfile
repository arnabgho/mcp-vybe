FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && export UV_INSTALL_DIR=/usr/local/bin \
 && curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

# Copy requirements.txt (generated from pyproject.toml)
COPY requirements.txt ./

# Install requirements using uv pip install
RUN uv pip install --system -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "server.py"]
