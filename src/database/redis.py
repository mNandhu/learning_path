"""Redis connection management with proper error handling and connection pooling."""

import redis
from redis import Redis, ConnectionPool
from src.logger import get_logger
from src.config import REDIS_HOST, REDIS_PORT, REDIS_DB

logger = get_logger(__name__)

# Global connection pool for Redis
_redis_pool = None


def get_redis_pool() -> ConnectionPool:
    """Get or create a Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = redis.ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=False,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            logger.debug("Redis connection pool created")
        except Exception as e:
            logger.error(f"Failed to create Redis connection pool: {str(e)}")
            raise
    return _redis_pool


def get_redis_client() -> Redis:
    """Get a Redis client using the connection pool with proper error handling."""
    try:
        if REDIS_HOST is None or REDIS_PORT is None:
            # Use FallbackCache if Redis host or port is not set
            logger.warning("Redis host or port not set, using fallback cache")
            return FallbackCache()

        return Redis(connection_pool=get_redis_pool())
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        # Return a dummy Redis client for graceful degradation
        return FallbackCache()


class FallbackCache:
    """Fallback class that mimics Redis but uses an in-memory dict when Redis is unavailable."""

    def __init__(self):
        self.cache = {}
        logger.warning("Using in-memory fallback cache instead of Redis")

    def hgetall(self, key):
        """Get all fields and values in a hash."""
        return self.cache.get(key, {})

    def hset(self, key, mapping=None, **kwargs):
        """Set multiple hash fields to multiple values."""
        if mapping is None:
            mapping = kwargs

        if key not in self.cache:
            self.cache[key] = {}

        for field, value in mapping.items():
            self.cache[key][field] = value
        return len(mapping)

    def set(self, key, value, ex=None):
        """Set the string value of a key with optional expiration."""
        self.cache[key] = value
        return True

    def get(self, key):
        """Get the value of a key."""
        return self.cache.get(key)

    def expire(self, key, time):
        """Set a key's time to live in seconds.

        Note: This fallback implementation does not support actual expiration.
        """
        # Can't actually expire in memory, but pretend it works
        return True
