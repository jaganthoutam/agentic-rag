FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libpq-dev \
        poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data & logs directories
RUN mkdir -p data logs

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    AGENTIC_RAG_CONFIG=/app/config.json

# Expose API port
EXPOSE 8000

# Default command
CMD ["python", "api.py", "--host", "0.0.0.0", "--port", "8000"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
