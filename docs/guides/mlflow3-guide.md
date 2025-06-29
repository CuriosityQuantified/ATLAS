# MLflow3 Comprehensive Guide for ATLAS (2025)

## Overview

MLflow 3 (2025) fundamentally expands multi-agent AI observability and deployment capabilities. This guide covers Docker deployment, multi-agent monitoring, and production-ready configuration for the ATLAS system.

## Key MLflow 3 Features for Multi-Agent Systems

### Multi-Agent Monitoring and Support
- **OpenAI Agent SDK Support**: Native support for multi-agent frameworks
- **Enhanced Agent Tracking**: Organization and comparison of GenAI agents, deep learning checkpoints, and model variants
- **Real-time Monitoring**: Monitor GenAI quality in real time with dashboards, trace explorers, and automated alerts
- **Agent Version Management**: Version prompts, agents, and application code with full lifecycle lineage

### Production Deployment Enhancements
- **FastAPI Migration**: ASGI-based scalable inference for improved performance
- **MLServer Integration**: Alternative deployment option for Kubernetes-native frameworks
- **Enhanced Docker Support**: Optimized container images with improved performance
- **Streaming API**: Real-time streaming capabilities for GenAI applications

## Docker Setup for ATLAS

### 1. MLflow3 Docker Compose Configuration

```yaml
# docker-compose.mlflow.yml
version: '3.8'

services:
  # MLflow Tracking Server
  mlflow-server:
    image: python:3.11-slim
    container_name: atlas-mlflow-server
    command: >
      bash -c "
        pip install mlflow[extras]==3.0.0 psycopg2-binary &&
        mlflow server
        --backend-store-uri postgresql://mlflow:mlflow_password@postgres:5432/mlflow
        --default-artifact-root s3://mlflow-artifacts
        --host 0.0.0.0
        --port 5000
        --default-artifact-root s3://mlflow-artifacts
      "
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_TRACKING_URI=http://localhost:5000
      - MLFLOW_S3_ENDPOINT_URL=http://minio:9000
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin
    volumes:
      - mlflow_data:/mlflow
    depends_on:
      - postgres
      - minio
    networks:
      - atlas-network
    restart: unless-stopped

  # PostgreSQL for MLflow Backend
  postgres:
    image: postgres:15-alpine
    container_name: atlas-postgres
    environment:
      POSTGRES_DB: mlflow
      POSTGRES_USER: mlflow
      POSTGRES_PASSWORD: mlflow_password
      POSTGRES_MULTIPLE_DATABASES: atlas_main,atlas_agents,atlas_memory
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-multiple-dbs.sh:/docker-entrypoint-initdb.d/init-multiple-dbs.sh
    ports:
      - "5432:5432"
    networks:
      - atlas-network
    restart: unless-stopped

  # MinIO for Artifact Storage
  minio:
    image: minio/minio:latest
    container_name: atlas-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - atlas-network
    restart: unless-stopped

  # Redis for Caching
  redis:
    image: redis:7-alpine
    container_name: atlas-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - atlas-network
    restart: unless-stopped

  # ChromaDB for Vector Storage
  chromadb:
    image: chromadb/chroma:latest
    container_name: atlas-chromadb
    ports:
      - "8000:8000"
    volumes:
      - chromadb_data:/chroma/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
    networks:
      - atlas-network
    restart: unless-stopped

  # Neo4j for Knowledge Graph
  neo4j:
    image: neo4j:5-community
    container_name: atlas-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/atlas_password
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_apoc_export_file_enabled: true
      NEO4J_apoc_import_file_enabled: true
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - atlas-network
    restart: unless-stopped

volumes:
  mlflow_data:
  postgres_data:
  minio_data:
  redis_data:
  chromadb_data:
  neo4j_data:
  neo4j_logs:

networks:
  atlas-network:
    driver: bridge
```

### 2. Database Initialization Script

```bash
#!/bin/bash
# scripts/init-multiple-dbs.sh

set -e
set -u

function create_user_and_database() {
    local database=$1
    echo "Creating user and database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE USER ${database}_user WITH PASSWORD '${database}_password';
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO ${database}_user;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_user_and_database $db
    done
    echo "Multiple databases created"
fi
```

## MLflow3 ATLAS Integration

### 1. Enhanced Multi-Agent Tracking System

```python
import mlflow
from mlflow.tracking import MlflowClient
# Note: MLflow 3.0 agent tracking is handled through mlflow.openai.autolog() for OpenAI agents
from typing import Dict, Any, List, Optional
import asyncio
import time
import json
from datetime import datetime
import uuid

class ATLASMLflowIntegration:
    """MLflow 3 integration optimized for ATLAS multi-agent system"""
    
    def __init__(self, tracking_uri: str = "http://localhost:5000"):
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()
        self.current_experiment = None
        self.current_run = None
        self.agent_runs = {}
        self.coordination_traces = {}
        
    async def start_atlas_experiment(
        self,
        task_id: str,
        task_metadata: Dict[str, Any],
        experiment_tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Start comprehensive ATLAS task experiment with MLflow 3 features"""
        
        experiment_name = f"atlas_task_{task_id}"
        
        # Create or get experiment
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    experiment_name,
                    tags=experiment_tags or {}
                )
            else:
                experiment_id = experiment.experiment_id
        except Exception:
            experiment_id = mlflow.create_experiment(experiment_name)
        
        mlflow.set_experiment(experiment_name)
        
        # Start main task run with enhanced metadata
        with mlflow.start_run(run_name=f"atlas_task_{task_id}") as run:
            self.current_run = run
            
            # Log comprehensive task metadata
            mlflow.log_params({
                "task_id": task_id,
                "task_type": task_metadata.get("type", "unknown"),
                "task_complexity": task_metadata.get("complexity", "medium"),
                "user_id": task_metadata.get("user_id"),
                "priority": task_metadata.get("priority", "normal"),
                "expected_duration": task_metadata.get("expected_duration"),
                "teams_involved": ",".join(task_metadata.get("teams", [])),
                "start_timestamp": datetime.now().isoformat()
            })
            
            # Set comprehensive tags for organization
            mlflow.set_tags({
                "atlas.task_type": task_metadata.get("type", "unknown"),
                "atlas.complexity": task_metadata.get("complexity", "medium"),
                "atlas.version": "3.0",
                "atlas.experiment_type": "multi_agent",
                "mlflow.runName": f"atlas_task_{task_id}"
            })
            
            return run.info.run_id
    
    async def track_agent_execution(
        self,
        agent_id: str,
        agent_type: str,
        team: str,
        task_data: Dict[str, Any],
        execution_start: float,
        parent_run_id: Optional[str] = None
    ) -> str:
        """Enhanced agent execution tracking with MLflow 3 agent support"""
        
        # Create nested run for agent
        with mlflow.start_run(
            nested=True, 
            run_name=f"{team}_{agent_type}_{agent_id}",
            parent_run_id=parent_run_id
        ) as agent_run:
            self.agent_runs[agent_id] = agent_run
            
            # Log comprehensive agent configuration
            mlflow.log_params({
                "agent_id": agent_id,
                "agent_type": agent_type,
                "team": team,
                "model_provider": task_data.get("model_provider", "unknown"),
                "model_name": task_data.get("model", "unknown"),
                "tools_available": len(task_data.get("tools", [])),
                "task_complexity": task_data.get("complexity", "medium"),
                "memory_context_size": task_data.get("memory_context_size", 0),
                "fresh_agent": task_data.get("fresh_agent", True),
                "persona_version": task_data.get("persona_version", "1.0")
            })
            
            # Set agent-specific tags
            mlflow.set_tags({
                "atlas.agent_type": agent_type,
                "atlas.team": team,
                "atlas.execution_mode": task_data.get("execution_mode", "standard"),
                "atlas.coordination_level": task_data.get("coordination_level", "worker")
            })
            
            # Log execution start metrics
            mlflow.log_metrics({
                "execution_start_time": execution_start,
                "context_tokens": task_data.get("context_tokens", 0),
                "available_tools_count": len(task_data.get("tools", []))
            })
            
            return agent_run.info.run_id
    
    async def log_agent_performance(
        self,
        agent_id: str,
        performance_data: Dict[str, Any],
        step: int = 0
    ):
        """Log comprehensive agent performance with MLflow 3 enhancements"""
        
        if agent_id not in self.agent_runs:
            return
        
        run_id = self.agent_runs[agent_id].info.run_id
        
        with mlflow.start_run(run_id=run_id):
            # Core performance metrics
            metrics = {
                "execution_time": performance_data.get("execution_time", 0),
                "tokens_used": performance_data.get("tokens_used", 0),
                "input_tokens": performance_data.get("input_tokens", 0),
                "output_tokens": performance_data.get("output_tokens", 0),
                "cost_usd": performance_data.get("cost", 0),
                "quality_score": performance_data.get("quality_score", 0),
                "error_count": performance_data.get("error_count", 0),
                "memory_usage_mb": performance_data.get("memory_usage", 0),
                "tool_calls_count": performance_data.get("tool_calls", 0),
                "coordination_calls": performance_data.get("coordination_calls", 0),
                "retry_count": performance_data.get("retry_count", 0)
            }
            
            # Log with step for time series analysis
            for metric_name, value in metrics.items():
                mlflow.log_metric(metric_name, value, step=step)
            
            # Enhanced MLflow 3 features
            if "reasoning_trace" in performance_data:
                # Use MLflow 3 tracing for reasoning paths
                with mlflow.start_trace(name=f"agent_reasoning_{agent_id}") as trace:
                    trace.log_input(performance_data.get("input_context", {}))
                    trace.log_output(performance_data.get("output_result", {}))
                    
                    # Log reasoning steps
                    reasoning_steps = performance_data["reasoning_trace"]
                    for i, step_data in enumerate(reasoning_steps):
                        with trace.span(f"reasoning_step_{i}") as span:
                            span.log_input(step_data.get("input", {}))
                            span.log_output(step_data.get("output", {}))
                            span.set_attributes({
                                "step_type": step_data.get("type", "unknown"),
                                "confidence": step_data.get("confidence", 0),
                                "duration": step_data.get("duration", 0)
                            })
            
            # Log artifacts with enhanced metadata
            if "output_text" in performance_data:
                output_file = f"agent_{agent_id}_output_{step}.txt"
                with open(output_file, "w") as f:
                    f.write(performance_data["output_text"])
                mlflow.log_artifact(output_file, artifact_path="outputs")
                
            if "tool_usage" in performance_data:
                tool_usage_file = f"agent_{agent_id}_tools_{step}.json"
                with open(tool_usage_file, "w") as f:
                    json.dump(performance_data["tool_usage"], f, indent=2)
                mlflow.log_artifact(tool_usage_file, artifact_path="tool_usage")
    
    async def track_coordination_patterns(
        self,
        supervisor_id: str,
        coordination_data: Dict[str, Any],
        step: int = 0
    ):
        """Track agent coordination with MLflow 3 multi-agent features"""
        
        coordination_id = f"coordination_{supervisor_id}_{step}"
        
        with mlflow.start_run(
            nested=True, 
            run_name=coordination_id
        ) as coordination_run:
            
            # Log coordination parameters
            mlflow.log_params({
                "supervisor_id": supervisor_id,
                "coordination_type": coordination_data.get("type", "unknown"),
                "agents_involved": len(coordination_data.get("agents", [])),
                "tool_calls_made": len(coordination_data.get("tool_calls", [])),
                "coordination_strategy": coordination_data.get("strategy", "sequential"),
                "parallel_execution": coordination_data.get("parallel", False)
            })
            
            # Log coordination metrics
            mlflow.log_metrics({
                "coordination_latency": coordination_data.get("latency", 0),
                "parallel_efficiency": coordination_data.get("parallel_efficiency", 0),
                "task_completion_rate": coordination_data.get("completion_rate", 0),
                "communication_overhead": coordination_data.get("communication_overhead", 0),
                "decision_time": coordination_data.get("decision_time", 0),
                "agents_active": len(coordination_data.get("active_agents", []))
            }, step=step)
            
            # Enhanced MLflow 3 tracing for coordination flows
            if "coordination_flow" in coordination_data:
                with mlflow.start_trace(name=f"coordination_flow_{supervisor_id}") as trace:
                    flow_data = coordination_data["coordination_flow"]
                    
                    trace.log_input({
                        "task_decomposition": flow_data.get("task_breakdown", {}),
                        "agent_assignments": flow_data.get("assignments", {})
                    })
                    
                    # Track each coordination step
                    for i, flow_step in enumerate(flow_data.get("steps", [])):
                        with trace.span(f"coordination_step_{i}") as span:
                            span.log_input(flow_step.get("input", {}))
                            span.log_output(flow_step.get("output", {}))
                            span.set_attributes({
                                "step_type": flow_step.get("type", "unknown"),
                                "agents_involved": flow_step.get("agents", []),
                                "duration": flow_step.get("duration", 0),
                                "success": flow_step.get("success", True)
                            })
            
            # Log coordination artifacts
            if "tool_call_sequence" in coordination_data:
                sequence_file = f"coordination_sequence_{supervisor_id}_{step}.json"
                with open(sequence_file, "w") as f:
                    json.dump(coordination_data["tool_call_sequence"], f, indent=2)
                mlflow.log_artifact(sequence_file, artifact_path="coordination")
            
            return coordination_run.info.run_id
    
    async def track_memory_operations(
        self,
        operation_type: str,
        database_type: str,
        operation_data: Dict[str, Any],
        step: int = 0
    ):
        """Track memory system operations with MLflow 3"""
        
        with mlflow.start_run(
            nested=True, 
            run_name=f"memory_{operation_type}_{database_type}"
        ) as memory_run:
            
            mlflow.log_params({
                "operation_type": operation_type,
                "database_type": database_type,
                "data_size_bytes": operation_data.get("size", 0),
                "memory_type": operation_data.get("memory_type", "unknown"),
                "persistence_level": operation_data.get("persistence", "temporary")
            })
            
            mlflow.log_metrics({
                "operation_latency": operation_data.get("latency", 0),
                "throughput_ops_sec": operation_data.get("throughput", 0),
                "cache_hit_rate": operation_data.get("cache_hit_rate", 0),
                "storage_efficiency": operation_data.get("storage_efficiency", 0),
                "retrieval_accuracy": operation_data.get("retrieval_accuracy", 0)
            }, step=step)
            
            return memory_run.info.run_id
    
    async def generate_system_report(self, experiment_name: str) -> Dict[str, Any]:
        """Generate comprehensive system performance report using MLflow 3 features"""
        
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            return {"error": "Experiment not found"}
        
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="",
            order_by=["start_time DESC"]
        )
        
        # Analyze performance trends
        performance_summary = {
            "total_runs": len(runs),
            "avg_execution_time": runs["metrics.execution_time"].mean() if not runs.empty else 0,
            "avg_quality_score": runs["metrics.quality_score"].mean() if not runs.empty else 0,
            "total_cost": runs["metrics.cost_usd"].sum() if not runs.empty else 0,
            "error_rate": (runs["metrics.error_count"].sum() / len(runs)) if not runs.empty else 0,
            "agent_types": runs["tags.atlas.agent_type"].value_counts().to_dict() if not runs.empty else {},
            "coordination_efficiency": runs["metrics.parallel_efficiency"].mean() if not runs.empty else 0
        }
        
        return performance_summary

class ATLASDebugger:
    """Enhanced debugging with MLflow 3 real-time capabilities"""
    
    def __init__(self, mlflow_integration: ATLASMLflowIntegration):
        self.mlflow = mlflow_integration
        self.debug_traces = {}
        self.performance_alerts = []
        
    async def debug_agent_reasoning(
        self,
        agent_id: str,
        reasoning_step: str,
        context: Dict[str, Any],
        decision: Dict[str, Any],
        step: int = 0
    ):
        """Enhanced debugging with MLflow 3 tracing capabilities"""
        
        debug_data = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "reasoning_step": reasoning_step,
            "context_size": len(str(context)),
            "decision_confidence": decision.get("confidence", 0),
            "tools_considered": decision.get("tools_considered", []),
            "final_choice": decision.get("choice"),
            "reasoning_time": decision.get("reasoning_time", 0)
        }
        
        # Store for analysis
        if agent_id not in self.debug_traces:
            self.debug_traces[agent_id] = []
        self.debug_traces[agent_id].append(debug_data)
        
        # Enhanced MLflow 3 logging
        with mlflow.start_trace(name=f"debug_reasoning_{agent_id}_{step}") as trace:
            trace.log_input(context)
            trace.log_output(decision)
            trace.set_attributes({
                "reasoning_step": reasoning_step,
                "confidence": decision.get("confidence", 0),
                "tools_available": len(decision.get("tools_considered", [])),
                "decision_time": decision.get("reasoning_time", 0)
            })
        
        # Real-time performance monitoring
        if decision.get("confidence", 0) < 0.3:
            alert = {
                "type": "low_confidence_decision",
                "agent_id": agent_id,
                "confidence": decision.get("confidence", 0),
                "timestamp": datetime.now().isoformat()
            }
            self.performance_alerts.append(alert)
            
            # Log alert to MLflow
            mlflow.log_metric(f"alert_low_confidence_{agent_id}", 1, step=step)

# Performance monitoring setup
class ATLASPerformanceMonitor:
    """Real-time performance monitoring with MLflow 3 alerts"""
    
    def __init__(self, mlflow_integration: ATLASMLflowIntegration):
        self.mlflow = mlflow_integration
        self.thresholds = {
            "max_execution_time": 300,  # 5 minutes
            "max_cost_per_task": 5.0,   # $5 per task
            "min_quality_score": 3.5,   # Minimum acceptable quality
            "max_error_rate": 0.1       # 10% error rate
        }
        self.alert_history = []
    
    async def check_performance_alerts(
        self, 
        metrics: Dict[str, Any],
        agent_id: str,
        step: int = 0
    ) -> List[str]:
        """Check for performance issues with MLflow 3 real-time alerts"""
        
        alerts = []
        
        # Check execution time
        if metrics.get("execution_time", 0) > self.thresholds["max_execution_time"]:
            alert = f"SLOW_EXECUTION: {metrics['execution_time']}s > {self.thresholds['max_execution_time']}s"
            alerts.append(alert)
            mlflow.log_metric("alert_slow_execution", 1, step=step)
        
        # Check cost
        if metrics.get("cost", 0) > self.thresholds["max_cost_per_task"]:
            alert = f"HIGH_COST: ${metrics['cost']} > ${self.thresholds['max_cost_per_task']}"
            alerts.append(alert)
            mlflow.log_metric("alert_high_cost", 1, step=step)
        
        # Check quality
        if metrics.get("quality_score", 0) < self.thresholds["min_quality_score"]:
            alert = f"LOW_QUALITY: {metrics['quality_score']} < {self.thresholds['min_quality_score']}"
            alerts.append(alert)
            mlflow.log_metric("alert_low_quality", 1, step=step)
        
        # Log all alerts
        for alert in alerts:
            self.alert_history.append({
                "alert": alert,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            })
            
            # Use MLflow 3 enhanced logging
            mlflow.log_param(f"performance_alert_{agent_id}", alert)
        
        return alerts
```

### 2. MLflow3 Configuration for ATLAS

```python
# config/mlflow_config.py

import os
from typing import Dict, Any

class MLflowConfig:
    """MLflow 3 configuration for ATLAS multi-agent system"""
    
    def __init__(self):
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        self.artifact_uri = os.getenv("MLFLOW_ARTIFACT_URI", "s3://mlflow-artifacts")
        self.backend_store_uri = os.getenv(
            "MLFLOW_BACKEND_STORE_URI", 
            "postgresql://mlflow:mlflow_password@localhost:5432/mlflow"
        )
        
    def get_server_config(self) -> Dict[str, Any]:
        """Get MLflow server configuration"""
        return {
            "host": "0.0.0.0",
            "port": 5000,
            "backend_store_uri": self.backend_store_uri,
            "default_artifact_root": self.artifact_uri,
            "serve_artifacts": True,
            "artifacts_destination": self.artifact_uri,
            "workers": 4  # For production scaling
        }
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get MLflow client configuration"""
        return {
            "tracking_uri": self.tracking_uri,
            "registry_uri": self.tracking_uri
        }
    
    def get_experiment_config(self) -> Dict[str, Any]:
        """Get default experiment configuration"""
        return {
            "experiment_tags": {
                "project": "ATLAS",
                "version": "3.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "mlflow_version": "3.0.0"
            },
            "run_tags": {
                "atlas.version": "3.0",
                "atlas.mode": "multi_agent"
            }
        }

# Environment configuration
MLFLOW_ENV_CONFIG = {
    "development": {
        "MLFLOW_TRACKING_URI": "http://localhost:5000",
        "MLFLOW_BACKEND_STORE_URI": "postgresql://mlflow:mlflow_password@localhost:5432/mlflow",
        "MLFLOW_ARTIFACT_URI": "s3://mlflow-artifacts",
        "MLFLOW_S3_ENDPOINT_URL": "http://localhost:9000",
        "AWS_ACCESS_KEY_ID": "minioadmin",
        "AWS_SECRET_ACCESS_KEY": "minioadmin"
    },
    "production": {
        "MLFLOW_TRACKING_URI": "https://mlflow.atlas.com",
        "MLFLOW_BACKEND_STORE_URI": "postgresql://mlflow:secure_password@prod-db:5432/mlflow",
        "MLFLOW_ARTIFACT_URI": "s3://atlas-mlflow-artifacts-prod",
        "AWS_ACCESS_KEY_ID": "PROD_ACCESS_KEY",
        "AWS_SECRET_ACCESS_KEY": "PROD_SECRET_KEY"
    }
}
```

## Production Deployment

### 1. Kubernetes Deployment (MLflow 3)

```yaml
# k8s/mlflow-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-server
  namespace: atlas
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mlflow-server
  template:
    metadata:
      labels:
        app: mlflow-server
    spec:
      containers:
      - name: mlflow-server
        image: python:3.11-slim
        command:
          - bash
          - -c
          - |
            pip install mlflow[extras]==3.0.0 psycopg2-binary boto3 &&
            mlflow server \
              --host 0.0.0.0 \
              --port 5000 \
              --backend-store-uri postgresql://mlflow:${POSTGRES_PASSWORD}@postgres:5432/mlflow \
              --default-artifact-root s3://mlflow-artifacts \
              --serve-artifacts \
              --workers 4
        ports:
        - containerPort: 5000
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: s3-secret
              key: access-key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: s3-secret
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /api/2.0/mlflow/experiments/list
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/2.0/mlflow/experiments/list
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-service
  namespace: atlas
spec:
  selector:
    app: mlflow-server
  ports:
  - protocol: TCP
    port: 5000
    targetPort: 5000
  type: LoadBalancer
```

### 2. MLflow3 Startup Script

```bash
#!/bin/bash
# scripts/start-mlflow.sh

set -e

echo "Starting ATLAS MLflow 3 Setup..."

# Create necessary directories
mkdir -p logs artifacts

# Set environment variables
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:mlflow_password@localhost:5432/mlflow
export MLFLOW_ARTIFACT_URI=s3://mlflow-artifacts
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin

# Wait for dependencies
echo "Waiting for PostgreSQL..."
while ! nc -z localhost 5432; do
  sleep 1
done

echo "Waiting for MinIO..."
while ! nc -z localhost 9000; do
  sleep 1
done

# Create MLflow bucket in MinIO
echo "Creating MLflow bucket..."
python -c "
import boto3
from botocore.client import Config

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    config=Config(signature_version='s3v4')
)

try:
    s3.create_bucket(Bucket='mlflow-artifacts')
    print('Bucket created successfully')
except Exception as e:
    print(f'Bucket may already exist: {e}')
"

# Start MLflow server
echo "Starting MLflow 3 server..."
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri $MLFLOW_BACKEND_STORE_URI \
  --default-artifact-root $MLFLOW_ARTIFACT_URI \
  --default-artifact-root $MLFLOW_ARTIFACT_URI \
  --workers 4 &

MLFLOW_PID=$!

echo "MLflow server started with PID: $MLFLOW_PID"
echo "MLflow UI available at: http://localhost:5000"
echo "Logs available in: logs/mlflow.log"

# Wait for MLflow to be ready
echo "Waiting for MLflow server to be ready..."
until curl -f http://localhost:5000/api/2.0/mlflow/experiments/list; do
  sleep 2
done

echo "MLflow 3 is ready for ATLAS!"

# Keep script running
wait $MLFLOW_PID
```

## Usage Examples

### 1. Basic ATLAS Integration

```python
# example/atlas_mlflow_example.py

import asyncio
from mlflow_integration import ATLASMLflowIntegration, ATLASDebugger

async def main():
    # Initialize MLflow integration
    mlflow_integration = ATLASMLflowIntegration()
    debugger = ATLASDebugger(mlflow_integration)
    
    # Start ATLAS experiment
    task_metadata = {
        "type": "strategic_analysis",
        "complexity": "high",
        "user_id": "user_123",
        "priority": "high",
        "teams": ["research", "analysis", "writing"],
        "expected_duration": 1800  # 30 minutes
    }
    
    experiment_run_id = await mlflow_integration.start_atlas_experiment(
        task_id="task_001",
        task_metadata=task_metadata
    )
    
    print(f"Started ATLAS experiment: {experiment_run_id}")
    
    # Track agent execution
    agent_run_id = await mlflow_integration.track_agent_execution(
        agent_id="research_supervisor_001",
        agent_type="supervisor",
        team="research",
        task_data={
            "model": "claude-3-opus",
            "tools": ["web_search", "worker_coordination"],
            "complexity": "high",
            "fresh_agent": True
        },
        execution_start=time.time()
    )
    
    # Log performance
    await mlflow_integration.log_agent_performance(
        agent_id="research_supervisor_001",
        performance_data={
            "execution_time": 45.2,
            "tokens_used": 1250,
            "cost": 0.15,
            "quality_score": 4.2,
            "tool_calls": 3,
            "reasoning_trace": [
                {"step": "task_analysis", "confidence": 0.9, "duration": 5.2},
                {"step": "worker_assignment", "confidence": 0.85, "duration": 8.1},
                {"step": "result_synthesis", "confidence": 0.92, "duration": 12.3}
            ]
        }
    )
    
    # Generate report
    report = await mlflow_integration.generate_system_report("atlas_task_task_001")
    print(f"System Report: {report}")

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive MLflow 3 guide provides the foundation for monitoring and observability in the ATLAS multi-agent system, leveraging the latest 2025 features for enhanced agent tracking, coordination monitoring, and production deployment.