# Multi-stage build for WB AutoSlot API
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install playwright==1.54.0
RUN playwright install chromium
RUN playwright install-deps

# Install additional system dependencies for new packages
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY wb-autoslot-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY wb-autoslot-api/ .

# Create necessary directories
RUN mkdir -p logs database static

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/auth/me || exit 1

# Run the application
CMD ["python", "src/main.py"]
