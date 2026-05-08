# MediScan AI Backend - Dockerfile
# For deployment to Google Cloud Run or any container platform

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY extractor.py .
COPY analyst.py .
COPY validator.py .
COPY .env .

# Copy static files and credentials
COPY static/ ./static/
COPY credentials/ ./credentials/

# Expose port (Cloud Run uses PORT env var, default to 8080)
ENV PORT=8080
ENV FLASK_PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run the application
CMD ["python", "app.py"]

# Made with Bob
