# LIBER - Backend Dockerfile (Production)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create static directory (legacy, not used with Supabase Storage but kept for compatibility)
RUN mkdir -p /app/static/qrcodes

# Expose port (Cloud Run standard)
EXPOSE 8080

# Use Gunicorn for production
# Workers: 2-4 * CPU cores (Cloud Run provides 2 CPUs)
# Threads: 4 per worker for I/O-bound operations (DB, API calls)
# Timeout: 120s (Cloud Run max is 3600s, but we use 300s in deploy)
CMD exec gunicorn --bind :8080 --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - run:app
