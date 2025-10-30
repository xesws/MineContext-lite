# MineContext-v2 Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data screenshots

# Expose port (can be overridden at runtime)
EXPOSE 8000

# Environment variables (can be overridden)
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${SERVER_PORT}/health')" || exit 1

# Run the application
CMD ["python", "run.py", "-H", "0.0.0.0"]
