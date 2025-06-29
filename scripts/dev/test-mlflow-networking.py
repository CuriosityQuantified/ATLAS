#!/usr/bin/env python3
"""
Quick MLflow networking test
Tests basic connectivity to MLflow server
"""

import requests
import socket
import time

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

def test_http_response(url='http://localhost:5001'):
    """Test HTTP response"""
    try:
        response = requests.get(url, timeout=10)
        return response.status_code, len(response.text)
    except Exception as e:
        return None, str(e)

def main():
    print("🔍 MLflow Networking Test")
    print("=" * 30)
    
    # Test 1: Port connectivity
    print("1. Testing port 5001...")
    if test_port_open():
        print("   ✅ Port 5001 is open")
    else:
        print("   ❌ Port 5001 is not accessible")
        return
    
    # Test 2: HTTP response
    print("2. Testing HTTP response...")
    status, content = test_http_response()
    if status:
        print(f"   ✅ HTTP {status}, content length: {content}")
    else:
        print(f"   ❌ HTTP request failed: {content}")
        return
    
    # Test 3: MLflow specific endpoint
    print("3. Testing MLflow API...")
    status, content = test_http_response('http://localhost:5001/api/2.0/mlflow/experiments/search')
    if status and status < 500:
        print(f"   ✅ MLflow API responding: HTTP {status}")
    else:
        print(f"   ❌ MLflow API issue: {status} - {content}")
    
    print("\n🎉 MLflow networking test complete!")

if __name__ == "__main__":
    main()