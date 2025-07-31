FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY server.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV MCP_TRANSPORT=http
ENV PYTHONUNBUFFERED=1

# Expose port (Render will set PORT env var)
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]