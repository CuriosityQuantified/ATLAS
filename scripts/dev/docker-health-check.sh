#!/bin/bash

# Docker Health Check Script for ATLAS MLflow
# This script checks the status of all Docker services and provides diagnostic information

echo "🔍 ATLAS Docker Services Health Check"
echo "======================================"

# Function to check if Docker is running
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Docker daemon is not running"
        exit 1
    fi
    
    echo "✅ Docker is running"
}

# Function to check Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    echo "✅ Docker Compose is available"
}

# Function to check service status
check_service_status() {
    echo -e "\n📊 Service Status:"
    echo "=================="
    
    services=("atlas-mlflow-server" "atlas-postgres" "atlas-minio" "atlas-redis" "atlas-chromadb" "atlas-neo4j")
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service"; then
            status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$service" | awk '{print $2, $3, $4}')
            echo "✅ $service: $status"
        else
            echo "❌ $service: Not running"
        fi
    done
}

# Function to check specific ports
check_ports() {
    echo -e "\n🔌 Port Accessibility:"
    echo "======================"
    
    ports=("5001:MLflow" "5432:PostgreSQL" "9000:MinIO API" "9001:MinIO Console" "6379:Redis" "8000:ChromaDB" "7474:Neo4j HTTP" "7687:Neo4j Bolt")
    
    for port_info in "${ports[@]}"; do
        port=$(echo "$port_info" | cut -d: -f1)
        service=$(echo "$port_info" | cut -d: -f2)
        
        if nc -z localhost "$port" 2>/dev/null; then
            echo "✅ $service (port $port): Accessible"
        else
            echo "❌ $service (port $port): Not accessible"
        fi
    done
}

# Function to show MLflow specific diagnostics
check_mlflow_diagnostics() {
    echo -e "\n🔍 MLflow Diagnostics:"
    echo "======================"
    
    # Check if MLflow container is running
    if docker ps | grep -q "atlas-mlflow-server"; then
        echo "✅ MLflow container is running"
        
        # Show recent logs
        echo -e "\n📋 Recent MLflow Logs:"
        echo "----------------------"
        docker logs atlas-mlflow-server --tail=10
        
        # Test internal connectivity
        echo -e "\n🔗 Testing Internal Connectivity:"
        echo "--------------------------------"
        if docker exec atlas-mlflow-server curl -s -f http://localhost:5001/health > /dev/null 2>&1; then
            echo "✅ MLflow internal health check passed"
        else
            echo "❌ MLflow internal health check failed"
        fi
        
    else
        echo "❌ MLflow container is not running"
        echo -e "\n📋 MLflow Container Logs (if available):"
        echo "----------------------------------------"
        docker logs atlas-mlflow-server --tail=20 2>/dev/null || echo "No logs available"
    fi
}

# Function to show network information
check_network_info() {
    echo -e "\n🌐 Network Information:"
    echo "======================="
    
    # Check if atlas-network exists
    if docker network ls | grep -q "atlas-network"; then
        echo "✅ atlas-network exists"
        
        # Show network details
        echo -e "\n📊 Network Details:"
        echo "-------------------"
        docker network inspect atlas-network --format "{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{println}}{{end}}" 2>/dev/null || echo "Network inspection failed"
    else
        echo "❌ atlas-network does not exist"
    fi
}

# Function to provide recommendations
provide_recommendations() {
    echo -e "\n💡 Troubleshooting Steps:"
    echo "========================="
    echo "1. If services are not running:"
    echo "   docker-compose up -d"
    echo ""
    echo "2. If MLflow port is not accessible:"
    echo "   docker-compose restart mlflow-server"
    echo ""
    echo "3. Check specific service logs:"
    echo "   docker-compose logs mlflow-server"
    echo "   docker-compose logs postgres"
    echo ""
    echo "4. Rebuild services if needed:"
    echo "   docker-compose down"
    echo "   docker-compose up -d --build"
    echo ""
    echo "5. Test MLflow connectivity:"
    echo "   python scripts/dev/test-mlflow-networking.py"
}

# Main execution
main() {
    check_docker
    check_docker_compose
    check_service_status
    check_ports
    check_mlflow_diagnostics
    check_network_info
    provide_recommendations
}

# Run the main function
main