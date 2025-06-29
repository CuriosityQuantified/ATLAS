# MLflow Virtual Environment Setup - Success Documentation

## Summary
Successfully set up MLflow 3.0 monitoring for ATLAS using Python virtual environment after Docker networking issues. MLflow UI is accessible at `http://localhost:5002`.

## Key Learnings

### 1. Virtual Environment is Critical
- **Issue**: Initial attempts used system Python instead of virtual environment
- **Solution**: Always activate virtual environment with `source .venv/bin/activate` before any Python operations
- **Root Cause**: System Python conflicts and dependency management issues

### 2. Requirements.txt Management
- **Challenge**: Complex dependency conflicts with full requirements.txt
- **Solution**: Simplified to essential MLflow dependencies only:
  ```
  # Monitoring & Observability
  mlflow[extras]
  
  # Database & Storage
  boto3
  
  # Utilities
  python-dotenv
  requests
  ```
- **Key Dependencies**: `mlflow[extras]` includes all necessary MLflow UI components

### 3. Port Management
- **Issue**: Port 5001 was already in use by another application
- **Solution**: Changed to port 5002 - always check port availability
- **Command**: `netstat -an | grep [PORT]` to check port usage

### 4. Virtual Environment vs Docker
- **Docker Issues**: Multiple networking and binding problems (documented in mlflow-docker-debugging.md)
- **Virtual Environment Success**: Direct MLflow installation works reliably for development
- **Recommendation**: Use virtual environment for development, Docker for production deployment

## Working Setup Commands

### Initial Setup (One-time)
```bash
# Create virtual environment (if not exists)
uv venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Daily Usage
```bash
# Always activate virtual environment first
source .venv/bin/activate

# Start MLflow server
nohup mlflow server --host 0.0.0.0 --port 5002 > mlflow.log 2>&1 &

# Verify server is running
ps aux | grep mlflow
netstat -an | grep 5002

# Access UI at: http://localhost:5002
```

### Stopping MLflow
```bash
# Find and kill MLflow processes
pkill -f "mlflow server"

# Or kill specific process ID
ps aux | grep mlflow
kill [PID]
```

## MLflow 3.0 Built-in UI Features

### Dashboard Capabilities
- **Experiments View**: Hierarchical run organization and comparison
- **Models Registry**: Version management and staging
- **Metrics Visualization**: Charts, graphs, and performance tracking
- **Artifact Storage**: Model files, plots, and data artifacts
- **Run Comparison**: Side-by-side analysis of different experiments

### Integration Points for ATLAS
- **Agent Tracking**: Each agent team can log runs and metrics
- **Cost Monitoring**: Track LLM API costs per run
- **Performance Metrics**: Measure response times and quality scores
- **Experiment Management**: Compare different agent configurations
- **Model Versioning**: Track prompt versions and agent improvements

## Technical Details

### Successful Configuration
- **MLflow Version**: 3.0.0
- **Server Host**: 0.0.0.0 (all interfaces)
- **Server Port**: 5002
- **Backend**: File-based storage (development)
- **UI Access**: http://localhost:5002

### Process Management
- **Background Process**: Uses `nohup` for persistent operation
- **Logging**: Output redirected to `mlflow.log`
- **Process Monitoring**: `ps aux | grep mlflow` to check status

### Network Verification
- **Port Check**: `netstat -an | grep 5002`
- **HTTP Test**: `curl http://localhost:5002` returns 200 OK
- **UI Response**: Full React application HTML served correctly

## Troubleshooting Guide

### Server Won't Start
1. Check virtual environment activation
2. Verify port availability
3. Check Python path: `which python` should show `.venv/bin/python`
4. Review `mlflow.log` for error messages

### UI Not Accessible
1. Confirm server is running: `ps aux | grep mlflow`
2. Test port binding: `netstat -an | grep 5002`
3. Try HTTP request: `curl http://localhost:5002`
4. Check firewall settings
5. Try different browser or incognito mode

### Dependency Issues
1. Always activate virtual environment first
2. Use simplified requirements.txt for MLflow essentials
3. Install with `pip install -r backend/requirements.txt`
4. Verify installation: `mlflow --version`

## Integration with ATLAS Development

### Next Steps
1. **Agent Tracking Implementation**: Add MLflow logging to agent classes
2. **Cost Monitoring**: Integrate with cost calculator utility
3. **Dashboard Customization**: Create ATLAS-specific MLflow dashboards
4. **Automated Startup**: Add MLflow server to development startup scripts

### File Locations
- **Requirements**: `/backend/requirements.txt`
- **Logs**: `/mlflow.log`
- **Test Scripts**: `/scripts/dev/test-mlflow-networking.py`
- **Documentation**: `/docs/guides/` (this file)

## Best Practices Established

1. **Always use virtual environment** - Critical for dependency management
2. **Check port availability** - Prevents binding conflicts
3. **Use background processes** - Allows continued development work
4. **Log output** - Essential for debugging
5. **Verify connectivity** - Test HTTP responses before UI access
6. **Document working commands** - Enables reliable reproduction

This setup provides a solid foundation for ATLAS multi-agent monitoring and establishes reliable patterns for ongoing development.