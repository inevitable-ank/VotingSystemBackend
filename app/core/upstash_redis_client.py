import httpx
import json
from typing import Optional, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class UpstashRedisClient:
    """Upstash Redis REST API client."""
    
    def __init__(self):
        self.base_url = settings.upstash_redis_rest_url
        self.token = settings.upstash_redis_rest_token
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            timeout=10.0
        )
    
    async def ping(self) -> bool:
        """Test connection."""
        try:
            response = await self.client.get(f"{self.base_url}/ping")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a key-value pair using Upstash REST semantics."""
        try:
            url = f"{self.base_url}/set/{key}/{value}"
            params = {"EX": ex} if ex else None
            response = await self.client.post(url, params=params)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        try:
            response = await self.client.get(f"{self.base_url}/get/{key}")
            if response.status_code == 200:
                result = response.json()
                return result.get("result")
            return None
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        try:
            response = await self.client.post(f"{self.base_url}/del", json={"key": key})
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")
            return False
    
    async def incr(self, key: str) -> Optional[int]:
        """Increment a counter."""
        try:
            response = await self.client.post(f"{self.base_url}/incr", json={"key": key})
            if response.status_code == 200:
                result = response.json()
                return result.get("result")
            return None
        except Exception as e:
            logger.error(f"Redis incr failed: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key."""
        try:
            response = await self.client.post(f"{self.base_url}/expire", json={"key": key, "seconds": seconds})
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Redis expire failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global Upstash client instance
_upstash_client: Optional[UpstashRedisClient] = None


async def get_upstash_client() -> Optional[UpstashRedisClient]:
    """Get Upstash Redis client instance."""
    global _upstash_client
    
    if _upstash_client is None and settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
        try:
            _upstash_client = UpstashRedisClient()
            if await _upstash_client.ping():
                logger.info("Upstash Redis client connected successfully")
            else:
                logger.error("Upstash Redis ping failed")
                _upstash_client = None
        except Exception as e:
            logger.error(f"Failed to create Upstash Redis client: {e}")
            _upstash_client = None
    
    return _upstash_client


async def close_upstash_client():
    """Close Upstash Redis client."""
    global _upstash_client
    
    if _upstash_client:
        await _upstash_client.close()
        _upstash_client = None
        logger.info("Upstash Redis client closed")

