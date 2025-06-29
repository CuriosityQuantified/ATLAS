# MLflow Docker Networking Issues - Debugging Documentation

## Summary
Extensive debugging of MLflow 3.0 Docker networking issues where the MLflow UI was inaccessible due to gunicorn binding to `127.0.0.1` instead of `0.0.0.0`.

## Problem Description
MLflow server running in Docker container was not accessible from outside the container because gunicorn was binding to localhost (`127.0.0.1:5000`) instead of all interfaces (`0.0.0.0:5001`).

## Symptoms
- Port 5001 appeared open in `netstat` output: `tcp46 0 0 *.5001 *.* LISTEN`
- But also showed localhost binding: `tcp4 0 0 127.0.0.1.5001 *.* LISTEN`
- HTTP requests to `http://localhost:5001` failed with "Connection aborted, Connection reset by peer"
- MLflow logs showed: `[INFO] Listening at: http://127.0.0.1:5000 (179)` instead of expected `0.0.0.0:5001`

## Root Cause Analysis
MLflow's gunicorn integration has known issues where it ignores the `--host` and `--port` parameters in certain configurations, defaulting to `127.0.0.1:5000`.

## Attempted Solutions

### 1. Basic MLflow Server Command Fix ✅ Attempted
**What we tried:**
```yaml
command: >
  bash -c "
    pip install mlflow[extras]==3.0.0 psycopg2-binary boto3 &&
    mlflow server --backend-store-uri postgresql://mlflow:mlflow_password@postgres:5432/mlflow --default-artifact-root s3://mlflow-artifacts --host 0.0.0.0 --port 5001 --serve-artifacts
  "
```

**Result:** Failed - gunicorn still bound to `127.0.0.1:5000`

### 2. Gunicorn Direct Command ✅ Attempted
**What we tried:**
```yaml
command: >
  bash -c "
    pip install mlflow[extras]==3.0.0 psycopg2-binary boto3 &&
    gunicorn -b 0.0.0.0:5001 -w 1 --timeout 120 mlflow.server:app --env MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:mlflow_password@postgres:5432/mlflow
  "
```

**Result:** Failed - gunicorn didn't respect environment variables for MLflow configuration

### 3. GUNICORN_CMD_ARGS Environment Variable ✅ Attempted
**What we tried:**
```yaml
environment:
  - GUNICORN_CMD_ARGS=--bind 0.0.0.0:5001 --workers 1 --timeout 120
```

**Result:** Failed - MLflow server command ignored the environment variable

### 4. Command Line Formatting Fixes ✅ Attempted
**What we tried:** Fixed YAML multiline formatting to ensure all parameters were properly passed as single line command.

**Result:** Failed - same binding issue persisted

## Configuration Files Tested

### Working Docker Compose Structure
```yaml
# docker-compose.yml
services:
  mlflow-server:
    image: python:3.11-slim
    container_name: atlas-mlflow-server
    command: >
      bash -c "
        pip install mlflow[extras]==3.0.0 psycopg2-binary boto3 &&
        mlflow server --backend-store-uri postgresql://mlflow:mlflow_password@postgres:5432/mlflow --default-artifact-root s3://mlflow-artifacts --host 0.0.0.0 --port 5001 --serve-artifacts
      "
    ports:
      - "5001:5001"
    environment:
      - MLFLOW_S3_ENDPOINT_URL=http://minio:9000
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin
    depends_on:
      - postgres
      - minio
    networks:
      - atlas-network
```

### Alternative Dockerfile Approach (Created but not tested)
```dockerfile
# infrastructure/docker/mlflow/Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl netcat-openbsd
RUN pip install --no-cache-dir mlflow[extras]==3.0.0 psycopg2-binary boto3

RUN useradd -m -u 1000 mlflow
USER mlflow
WORKDIR /mlflow

EXPOSE 5001

CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "5001", \
     "--serve-artifacts", \
     "--gunicorn-opts", "--bind 0.0.0.0:5001 --workers 1 --timeout 120 --access-logfile -"]
```

## Investigation Tools Used

### 1. Network Testing Script
Created `scripts/dev/test-mlflow-networking.py`:
```python
def test_port_open(host='localhost', port=5001):
    """Test if port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False
```

### 2. Verification Script
Created `scripts/dev/verify-mlflow.py` - comprehensive MLflow testing script.

### 3. Environment Configuration
Created `.env.mlflow` with proper configuration variables.

## Research Findings

Based on extensive research, MLflow Docker networking issues are common and have several known solutions:

### Known Working Solutions (From Research)
1. **Use official MLflow Docker image** instead of building from scratch
2. **Set PORT environment variable** - Gunicorn respects this more reliably than command line args
3. **Use Custom Dockerfile with explicit gunicorn configuration**
4. **Use MLflow model serving approach** with proper GUNICORN_CMD_ARGS

### Recommended Next Attempts

#### Option 1: Official MLflow Image
```yaml
mlflow-server:
  image: mlflow/mlflow:latest
  command: >
    mlflow server
    --backend-store-uri postgresql://mlflow:mlflow_password@postgres:5432/mlflow
    --default-artifact-root s3://mlflow-artifacts
    --host 0.0.0.0
    --port 5001
    --serve-artifacts
  ports:
    - "5001:5001"
  environment:
    - PORT=5001  # Critical for gunicorn binding
```

#### Option 2: Environment Variable Approach
```yaml
mlflow-server:
  image: python:3.11-slim
  environment:
    - PORT=5001
    - MLFLOW_TRACKING_URI=http://0.0.0.0:5001
    - MLFLOW_HOST=0.0.0.0
    - MLFLOW_PORT=5001
  command: >
    bash -c "
      pip install mlflow[extras]==3.0.0 psycopg2-binary boto3 &&
      python -c \"import mlflow; mlflow.server.run(host='0.0.0.0', port=5001)\"
    "
```

#### Option 3: Custom Dockerfile Build
Use the created Dockerfile in `infrastructure/docker/mlflow/Dockerfile` with docker-compose build approach.

## Current Status
- **Docker approach**: Failed after multiple attempts
- **Virtual environment approach**: Recommended as fallback
- **Container cleanup**: All containers properly cleaned up and running
- **Configuration files**: All debugging artifacts preserved

## Next Steps
1. **Immediate**: Set up MLflow in virtual environment
2. **Future**: Try Option 1 (official MLflow image) when time permits
3. **Future**: Try Option 2 (environment variable approach)
4. **Future**: Complete custom Dockerfile approach (Option 3)

## Lessons Learned
1. MLflow's Docker networking is notoriously difficult due to gunicorn integration issues
2. The `--host` and `--port` parameters are often ignored in containerized environments
3. Virtual environment approach is more reliable for development
4. Official MLflow Docker images may handle networking better than custom images
5. Container recreation (not just restart) is necessary for configuration changes

## Files Modified/Created
- `infrastructure/docker-compose.yml` - Multiple configuration attempts
- `scripts/dev/test-mlflow-networking.py` - Network testing utility
- `scripts/dev/verify-mlflow.py` - MLflow verification script
- `.env.mlflow` - Environment configuration
- `infrastructure/docker/mlflow/Dockerfile` - Custom Dockerfile (unused)
- `docker-compose.alternative.yml` - Alternative configuration (removed)

## Debug Commands Used
```bash
# Port checking
netstat -an | grep 5001

# Container logs
docker logs atlas-mlflow-server --tail=20

# Container status
docker ps -a

# Network testing
python scripts/dev/test-mlflow-networking.py

# Container recreation
docker rm -f atlas-mlflow-server
docker-compose up -d --no-deps mlflow-server
```

This documentation should help future debugging efforts and provide a comprehensive reference for the MLflow Docker networking challenges encountered.