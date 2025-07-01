#!/usr/bin/env python3
"""
ATLAS Redis Connection and Operation Testing
Tests Redis functionality including caching, pub/sub, and metrics
"""

import asyncio
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
import time

from redis_config import (
    redis_manager, redis_cache, redis_pubsub, redis_metrics, 
    check_redis_health, REDIS_DATABASES
)

async def test_basic_connections():
    """Test basic Redis connections across all databases"""
    print("\n🔧 Testing Redis connections...")
    
    success_count = 0
    total_tests = len(REDIS_DATABASES)
    
    for db_name, db_num in REDIS_DATABASES.items():
        try:
            conn = await redis_manager.get_connection(db_name)
            result = await conn.ping()
            
            if result:
                print(f"✅ Redis {db_name} (db {db_num}): Connection successful")
                success_count += 1
            else:
                print(f"❌ Redis {db_name} (db {db_num}): Ping failed")
        
        except Exception as e:
            print(f"❌ Redis {db_name} (db {db_num}): Connection failed - {e}")
    
    return success_count == total_tests

async def test_cache_operations():
    """Test Redis caching functionality"""
    print("\n🔧 Testing Redis cache operations...")
    
    try:
        # Test 1: Set and get string value
        test_key = f"test:string:{uuid.uuid4()}"
        test_value = "Hello Redis!"
        
        await redis_cache.set(test_key, test_value, ttl=60)
        retrieved_value = await redis_cache.get(test_key)
        
        if retrieved_value != test_value:
            print(f"❌ Cache string test failed: expected {test_value}, got {retrieved_value}")
            return False
        
        # Test 2: Set and get JSON value
        test_json_key = f"test:json:{uuid.uuid4()}"
        test_json_value = {
            "task_id": str(uuid.uuid4()),
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "metrics": {"tokens": 150, "cost": 0.003}
        }
        
        await redis_cache.set(test_json_key, test_json_value, ttl=60)
        retrieved_json = await redis_cache.get(test_json_key)
        
        if retrieved_json != test_json_value:
            print(f"❌ Cache JSON test failed: values don't match")
            return False
        
        # Test 3: Check exists
        exists = await redis_cache.exists(test_key)
        if not exists:
            print(f"❌ Cache exists test failed: key should exist")
            return False
        
        # Test 4: Delete and verify
        deleted = await redis_cache.delete(test_key)
        if not deleted:
            print(f"❌ Cache delete test failed: deletion unsuccessful")
            return False
        
        exists_after_delete = await redis_cache.exists(test_key)
        if exists_after_delete:
            print(f"❌ Cache delete verification failed: key still exists")
            return False
        
        # Clean up JSON test key
        await redis_cache.delete(test_json_key)
        
        print(f"✅ Redis cache: All operations successful")
        return True
    
    except Exception as e:
        print(f"❌ Redis cache operations failed: {e}")
        return False

async def test_pubsub_operations():
    """Test Redis pub/sub messaging"""
    print("\n🔧 Testing Redis pub/sub operations...")
    
    try:
        test_channel = f"test_channel_{uuid.uuid4().hex[:8]}"
        test_message = {
            "event_type": "agent_status_change",
            "agent_id": str(uuid.uuid4()),
            "old_status": "idle",
            "new_status": "processing",
            "task_id": str(uuid.uuid4())
        }
        
        # Subscribe to test channel
        pubsub = await redis_pubsub.subscribe([test_channel])
        if not pubsub:
            print("❌ Pub/sub subscribe failed")
            return False
        
        # Publish a message
        published_count = await redis_pubsub.publish(test_channel, test_message)
        if published_count == 0:
            print("❌ Pub/sub publish failed: no subscribers")
            await redis_pubsub.unsubscribe()
            return False
        
        # Wait for and receive the message
        message_received = False
        timeout_seconds = 5
        start_time = time.time()
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    received_data = json.loads(message['data'])
                    if received_data['data'] == test_message:
                        message_received = True
                        break
                except json.JSONDecodeError:
                    pass
            
            # Timeout check
            if time.time() - start_time > timeout_seconds:
                break
        
        await redis_pubsub.unsubscribe()
        
        if not message_received:
            print("❌ Pub/sub message not received within timeout")
            return False
        
        print(f"✅ Redis pub/sub: Message published and received successfully")
        return True
    
    except Exception as e:
        print(f"❌ Redis pub/sub operations failed: {e}")
        return False

async def test_metrics_operations():
    """Test Redis metrics functionality"""
    print("\n🔧 Testing Redis metrics operations...")
    
    try:
        test_prefix = f"test_{uuid.uuid4().hex[:8]}"
        
        # Test 1: Counter operations
        counter_name = f"{test_prefix}_requests"
        
        # Increment counter multiple times
        for i in range(5):
            await redis_metrics.increment_counter(counter_name, 1)
        
        # Get final counter value
        conn = await redis_manager.get_connection('metrics')
        final_count = await conn.get(f"counter:{counter_name}")
        
        if int(final_count) != 5:
            print(f"❌ Metrics counter test failed: expected 5, got {final_count}")
            return False
        
        # Test 2: Gauge operations
        gauge_name = f"{test_prefix}_cpu_usage"
        test_gauge_value = 75.5
        
        await redis_metrics.set_gauge(gauge_name, test_gauge_value)
        stored_gauge = await conn.get(f"gauge:{gauge_name}")
        
        if float(stored_gauge) != test_gauge_value:
            print(f"❌ Metrics gauge test failed: expected {test_gauge_value}, got {stored_gauge}")
            return False
        
        # Test 3: Histogram operations
        histogram_name = f"{test_prefix}_response_time"
        test_values = [0.1, 0.15, 0.2, 0.25, 0.3]
        
        for value in test_values:
            await redis_metrics.add_to_histogram(histogram_name, value)
        
        # Get histogram stats
        stats = await redis_metrics.get_histogram_stats(histogram_name, since_minutes=1)
        
        if stats['count'] != len(test_values):
            print(f"❌ Metrics histogram test failed: expected {len(test_values)} values, got {stats['count']}")
            return False
        
        expected_avg = sum(test_values) / len(test_values)
        if abs(stats['avg'] - expected_avg) > 0.001:
            print(f"❌ Metrics histogram average test failed: expected {expected_avg}, got {stats['avg']}")
            return False
        
        # Clean up test metrics
        await conn.delete(f"counter:{counter_name}")
        await conn.delete(f"gauge:{gauge_name}")
        await conn.delete(f"histogram:{histogram_name}")
        
        print(f"✅ Redis metrics: All operations successful")
        print(f"  • Counter: {final_count} increments")
        print(f"  • Gauge: {test_gauge_value} stored/retrieved")
        print(f"  • Histogram: {stats['count']} values, avg={stats['avg']:.3f}")
        return True
    
    except Exception as e:
        print(f"❌ Redis metrics operations failed: {e}")
        return False

async def test_redis_health():
    """Test Redis health check function"""
    print("\n🔧 Testing Redis health check...")
    
    try:
        health = await check_redis_health()
        
        if not health['redis_available']:
            print("❌ Redis health check failed: Redis not available")
            return False
        
        # Check that all databases are healthy
        for db_name, is_healthy in health['databases'].items():
            if not is_healthy:
                print(f"❌ Redis health check failed: {db_name} database unhealthy")
                return False
        
        print(f"✅ Redis health check: All systems operational")
        print(f"  • Memory usage: {health['memory_usage']}")
        print(f"  • Connected clients: {health['connected_clients']}")
        print(f"  • Healthy databases: {list(health['databases'].keys())}")
        return True
    
    except Exception as e:
        print(f"❌ Redis health check failed: {e}")
        return False

async def test_concurrent_operations():
    """Test Redis under concurrent load"""
    print("\n🔧 Testing Redis concurrent operations...")
    
    try:
        # Create multiple concurrent tasks
        async def cache_worker(worker_id: int):
            for i in range(10):
                key = f"concurrent_test_{worker_id}_{i}"
                value = f"worker_{worker_id}_value_{i}"
                await redis_cache.set(key, value, ttl=30)
                retrieved = await redis_cache.get(key)
                if retrieved != value:
                    raise Exception(f"Worker {worker_id} cache mismatch")
                await redis_cache.delete(key)
        
        # Run 5 workers concurrently
        workers = [cache_worker(i) for i in range(5)]
        await asyncio.gather(*workers)
        
        print(f"✅ Redis concurrent operations: 5 workers × 10 operations each completed successfully")
        return True
    
    except Exception as e:
        print(f"❌ Redis concurrent operations failed: {e}")
        return False

async def main():
    """Run all Redis tests"""
    print("🔍 ATLAS Redis Testing")
    print("=" * 40)
    
    success_count = 0
    total_tests = 0
    
    # Test functions to run
    test_functions = [
        ("Basic Connections", test_basic_connections),
        ("Cache Operations", test_cache_operations),
        ("Pub/Sub Operations", test_pubsub_operations),
        ("Metrics Operations", test_metrics_operations),
        ("Health Check", test_redis_health),
        ("Concurrent Operations", test_concurrent_operations)
    ]
    
    for test_name, test_func in test_functions:
        total_tests += 1
        try:
            if await test_func():
                success_count += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    # Close all connections
    await redis_manager.close_connections()
    
    # Summary
    print("\n" + "=" * 40)
    print(f"📊 Redis Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All Redis tests passed! Redis is ready for ATLAS.")
        return 0
    else:
        print("❌ Some Redis tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)