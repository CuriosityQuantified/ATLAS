#!/usr/bin/env python3
"""
Script to start Letta server and verify setup
"""

import subprocess
import time
import requests
import sys

print("🚀 Starting Letta Server Setup")
print("=" * 60)

# Check if Letta is installed
try:
    import letta
    print("✅ Letta is installed")
    print(f"   Version: {letta.__version__ if hasattr(letta, '__version__') else 'Unknown'}")
except ImportError:
    print("❌ Letta is not installed. Please run: pip install letta")
    sys.exit(1)

print("\n📋 Starting Letta server...")
print("   This will run: letta server")
print("   Server will be available at: http://localhost:8283")
print("\nPress Ctrl+C to stop the server")
print("-" * 60)

try:
    # Start Letta server
    process = subprocess.Popen(
        ["letta", "server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("⏳ Waiting for server to start...")
    time.sleep(5)  # Give server time to start
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8283/v1/health")
        if response.status_code == 200:
            print("✅ Letta server is running!")
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Letta server")
        print("   The server may still be starting up...")
    
    print("\nServer logs:")
    print("-" * 60)
    
    # Show server output
    while True:
        output = process.stdout.readline()
        if output:
            print(output.strip())
        
        # Check if process has terminated
        retcode = process.poll()
        if retcode is not None:
            print(f"\nServer exited with code: {retcode}")
            break
            
except KeyboardInterrupt:
    print("\n\n🛑 Stopping Letta server...")
    process.terminate()
    process.wait()
    print("✅ Server stopped")
except Exception as e:
    print(f"\n❌ Error: {e}")
    if 'process' in locals():
        process.terminate()