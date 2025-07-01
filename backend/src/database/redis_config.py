#!/usr/bin/env python3
"""
ATLAS Redis Configuration and Connection Management
Handles Redis setup for caching and pub/sub messaging
"""

import redis.asyncio as redis
import redis as sync_redis
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

# Redis configuration
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30
}

# Redis database assignments for different use cases
REDIS_DATABASES = {
    'cache': 0,        # General caching
    'sessions': 1,     # Agent session data
    'pubsub': 2,       # Pub/sub messaging
    'metrics': 3       # Performance metrics
}

class RedisManager:
    """Redis connection and operation manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or REDIS_CONFIG.copy()
        self.connections: Dict[str, redis.Redis] = {}
        self.sync_connections: Dict[str, sync_redis.Redis] = {}
        
    async def get_connection(self, db_name: str = 'cache') -> redis.Redis:
        """Get or create Redis connection for specific database"""
        if db_name not in self.connections:
            db_num = REDIS_DATABASES.get(db_name, 0)
            config = self.config.copy()
            config['db'] = db_num
            
            self.connections[db_name] = redis.Redis(**config)
        
        return self.connections[db_name]
    
    def get_sync_connection(self, db_name: str = 'cache') -> sync_redis.Redis:
        """Get or create synchronous Redis connection"""
        if db_name not in self.sync_connections:
            db_num = REDIS_DATABASES.get(db_name, 0)
            config = self.config.copy()
            config['db'] = db_num
            
            self.sync_connections[db_name] = sync_redis.Redis(**config)
        
        return self.sync_connections[db_name]
    
    async def close_connections(self):
        """Close all Redis connections"""
        for conn in self.connections.values():
            await conn.close()
        
        for conn in self.sync_connections.values():
            conn.close()
        
        self.connections.clear()
        self.sync_connections.clear()

class RedisCache:
    """Redis caching utilities"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache value with TTL"""
        try:
            conn = await self.redis_manager.get_connection('cache')
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            return await conn.setex(key, ttl, serialized_value)
        except Exception as e:
            logging.error(f"Redis cache set error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            conn = await self.redis_manager.get_connection('cache')
            value = await conn.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logging.error(f"Redis cache get error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete cache key"""
        try:
            conn = await self.redis_manager.get_connection('cache')
            return await conn.delete(key) > 0
        except Exception as e:
            logging.error(f"Redis cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            conn = await self.redis_manager.get_connection('cache')
            return await conn.exists(key) > 0
        except Exception as e:
            logging.error(f"Redis cache exists error: {e}")
            return False

class RedisPubSub:
    """Redis pub/sub messaging utilities"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        self.pubsub = None
    
    async def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish message to channel"""
        try:
            conn = await self.redis_manager.get_connection('pubsub')
            serialized_message = json.dumps({
                'timestamp': datetime.now().isoformat(),
                'data': message
            })
            return await conn.publish(channel, serialized_message)
        except Exception as e:
            logging.error(f"Redis publish error: {e}")
            return 0
    
    async def subscribe(self, channels: List[str]) -> redis.client.PubSub:
        """Subscribe to channels"""
        try:
            conn = await self.redis_manager.get_connection('pubsub')
            self.pubsub = conn.pubsub()
            await self.pubsub.subscribe(*channels)
            return self.pubsub
        except Exception as e:
            logging.error(f"Redis subscribe error: {e}")
            return None
    
    async def unsubscribe(self):
        """Unsubscribe from all channels"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
            self.pubsub = None

class RedisMetrics:
    """Redis metrics tracking utilities"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
    
    async def increment_counter(self, metric_name: str, value: int = 1) -> int:
        """Increment a counter metric"""
        try:
            conn = await self.redis_manager.get_connection('metrics')
            return await conn.incrby(f"counter:{metric_name}", value)
        except Exception as e:
            logging.error(f"Redis counter increment error: {e}")
            return 0
    
    async def set_gauge(self, metric_name: str, value: float) -> bool:
        """Set a gauge metric"""
        try:
            conn = await self.redis_manager.get_connection('metrics')
            return await conn.set(f"gauge:{metric_name}", value)
        except Exception as e:
            logging.error(f"Redis gauge set error: {e}")
            return False
    
    async def add_to_histogram(self, metric_name: str, value: float) -> bool:
        """Add value to histogram (using sorted set)"""
        try:
            conn = await self.redis_manager.get_connection('metrics')
            timestamp = datetime.now().timestamp()
            # Use the value as the score and timestamp as member for proper sorting
            return await conn.zadd(f"histogram:{metric_name}", {str(timestamp): value}) > 0
        except Exception as e:
            logging.error(f"Redis histogram add error: {e}")
            return False
    
    async def get_histogram_stats(self, metric_name: str, since_minutes: int = 60) -> Dict[str, float]:
        """Get histogram statistics for recent time period"""
        try:
            conn = await self.redis_manager.get_connection('metrics')
            cutoff_time = (datetime.now() - timedelta(minutes=since_minutes)).timestamp()
            
            # Get all values and filter by timestamp (member names)
            all_values = await conn.zrange(f"histogram:{metric_name}", 0, -1, withscores=True)
            
            if not all_values:
                return {'count': 0, 'avg': 0, 'min': 0, 'max': 0}
            
            # Filter by timestamp and extract scores (the actual values)
            recent_values = []
            for member, score in all_values:
                try:
                    timestamp = float(member)
                    if timestamp >= cutoff_time:
                        recent_values.append(score)
                except (ValueError, TypeError):
                    continue
            
            if not recent_values:
                return {'count': 0, 'avg': 0, 'min': 0, 'max': 0}
            
            return {
                'count': len(recent_values),
                'avg': sum(recent_values) / len(recent_values),
                'min': min(recent_values),
                'max': max(recent_values)
            }
        except Exception as e:
            logging.error(f"Redis histogram stats error: {e}")
            return {'count': 0, 'avg': 0, 'min': 0, 'max': 0}

# Global Redis manager instance
redis_manager = RedisManager()
redis_cache = RedisCache(redis_manager)
redis_pubsub = RedisPubSub(redis_manager)
redis_metrics = RedisMetrics(redis_manager)

# Health check function
async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health across all databases"""
    health_status = {
        'redis_available': False,
        'databases': {},
        'memory_usage': None,
        'connected_clients': None
    }
    
    try:
        # Test each database
        for db_name in REDIS_DATABASES.keys():
            try:
                conn = await redis_manager.get_connection(db_name)
                await conn.ping()
                health_status['databases'][db_name] = True
            except Exception as e:
                health_status['databases'][db_name] = False
                logging.error(f"Redis {db_name} database health check failed: {e}")
        
        # Get Redis info if any database is working
        if any(health_status['databases'].values()):
            health_status['redis_available'] = True
            conn = await redis_manager.get_connection('cache')
            info = await conn.info()
            health_status['memory_usage'] = info.get('used_memory_human')
            health_status['connected_clients'] = info.get('connected_clients')
    
    except Exception as e:
        logging.error(f"Redis health check failed: {e}")
    
    return health_status