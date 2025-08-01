FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && export UV_INSTALL_DIR=/usr/local/bin \
 && curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

# Copy requirements.txt
COPY requirements.txt ./

# Install requirements
RUN uv pip sync requirements.txt --system
COPY . .
# RUN uv pip install --system -e .

EXPOSE 8000
CMD ["python", "server.py"]