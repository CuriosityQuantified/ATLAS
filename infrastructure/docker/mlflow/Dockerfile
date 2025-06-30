# Custom MLflow Dockerfile for better networking control
FROM python:3.11-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install MLflow and dependencies
RUN pip install --no-cache-dir mlflow[extras]==3.0.0 psycopg2-binary boto3

# Create MLflow user
RUN useradd -m -u 1000 mlflow && \
    mkdir -p /mlflow && \
    chown -R mlflow:mlflow /mlflow

USER mlflow
WORKDIR /mlflow

# Expose the port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Default command with explicit gunicorn configuration
CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "5001", \
     "--serve-artifacts", \
     "--gunicorn-opts", "--bind 0.0.0.0:5001 --workers 1 --timeout 120 --access-logfile -"]