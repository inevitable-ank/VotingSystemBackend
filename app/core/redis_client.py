import redis.asyncio as redis
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client instance.
    
    Returns:
        Optional[redis.Redis]: Redis client or None if connection fails
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await _redis_client.ping()
            logger.info("Redis client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            _redis_client = None
    
    return _redis_client


async def close_redis_client():
    """Close Redis client connection."""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client connection closed")


async def publish_message(channel: str, message: dict) -> bool:
    """
    Publish a message to a Redis channel.
    
    Args:
        channel: Redis channel name
        message: Message to publish
        
    Returns:
        bool: True if published successfully, False otherwise
    """
    try:
        client = await get_redis_client()
        if client:
            await client.publish(channel, str(message))
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to publish message to {channel}: {e}")
        return False


async def subscribe_to_channel(channel: str):
    """
    Subscribe to a Redis channel.
    
    Args:
        channel: Redis channel name
        
    Yields:
        dict: Messages from the channel
    """
    try:
        client = await get_redis_client()
        if client:
            pubsub = client.pubsub()
            await pubsub.subscribe(channel)
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    yield message['data']
    except Exception as e:
        logger.error(f"Failed to subscribe to {channel}: {e}")


async def set_cache(key: str, value: str, expire: int = 3600) -> bool:
    """
    Set a value in Redis cache.
    
    Args:
        key: Cache key
        value: Value to cache
        expire: Expiration time in seconds
        
    Returns:
        bool: True if set successfully, False otherwise
    """
    try:
        client = await get_redis_client()
        if client:
            await client.setex(key, expire, value)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to set cache key {key}: {e}")
        return False


async def get_cache(key: str) -> Optional[str]:
    """
    Get a value from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        Optional[str]: Cached value or None if not found
    """
    try:
        client = await get_redis_client()
        if client:
            return await client.get(key)
        return None
    except Exception as e:
        logger.error(f"Failed to get cache key {key}: {e}")
        return None


async def delete_cache(key: str) -> bool:
    """
    Delete a value from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        client = await get_redis_client()
        if client:
            await client.delete(key)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete cache key {key}: {e}")
        return False


async def increment_counter(key: str, expire: int = 3600) -> Optional[int]:
    """
    Increment a counter in Redis.
    
    Args:
        key: Counter key
        expire: Expiration time in seconds
        
    Returns:
        Optional[int]: New counter value or None if failed
    """
    try:
        client = await get_redis_client()
        if client:
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, expire)
            results = await pipe.execute()
            return results[0]
        return None
    except Exception as e:
        logger.error(f"Failed to increment counter {key}: {e}")
        return None
