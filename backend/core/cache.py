from typing import Any, Optional
from datetime import datetime, timedelta
import json

class InMemoryCache:
    """
    Simple in-memory cache (FREE alternative to Redis)
    Good for development and small-scale production
    """
    
    def __init__(self):
        self._cache: dict = {}
        self._expiry: dict = {}
        print("✅ In-memory cache initialized")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Check if key exists and hasn't expired
        if key in self._cache:
            if key in self._expiry:
                if datetime.now() > self._expiry[key]:
                    # Expired - remove it
                    del self._cache[key]
                    del self._expiry[key]
                    return None
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any, expire_seconds: int = 3600):
        """Set value in cache with expiration"""
        self._cache[key] = value
        if expire_seconds > 0:
            self._expiry[key] = datetime.now() + timedelta(seconds=expire_seconds)
    
    def delete(self, key: str):
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._expiry.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_keys = len(self._cache)
        expired_keys = sum(
            1 for key in self._expiry 
            if datetime.now() > self._expiry[key]
        )
        return {
            'total_keys': total_keys,
            'expired_keys': expired_keys,
            'active_keys': total_keys - expired_keys
        }

# Global cache instance
cache = InMemoryCache()