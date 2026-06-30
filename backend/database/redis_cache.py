"""
MyAgent - Redis Cache Layer (Alibaba Cloud Tair)
Provides session caching, rate limiting, and response caching.
Falls back to in-memory if Redis is unavailable.
"""

import json
import time
from typing import Any, Dict, Optional
from config import get_settings

try:
    import redis
    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False

_redis_client = None
_redis_available = None


def _get_redis_client():
    """Get or create Redis connection."""
    global _redis_client, _redis_available

    if _redis_available is False:
        return None

    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    redis_url = getattr(settings, "redis_url", "")

    if not redis_url or not _HAS_REDIS:
        _redis_available = False
        return None

    try:
        _redis_client = redis.from_url(redis_url, decode_responses=True, socket_timeout=3)
        _redis_client.ping()
        _redis_available = True
        print("✅ Redis: Connected (Alibaba Cloud Tair)")
        return _redis_client
    except Exception as e:
        print(f"⚠️ Redis: Not available ({str(e)[:50]}). Using in-memory fallback.")
        _redis_available = False
        return None


def is_redis_available() -> bool:
    """Check if Redis is connected."""
    _get_redis_client()
    return _redis_available is True


# ============================================
# RATE LIMITING (using Redis INCR + TTL)
# ============================================

def check_rate_limit_redis(client_id: str, limit_per_minute: int) -> tuple:
    """
    Redis-based rate limiting with sliding window.
    Returns (allowed: bool, retry_after: int, current: int)
    """
    client = _get_redis_client()
    if not client:
        return True, 0, 0  # Fallback: allow all

    key = f"ratelimit:{client_id}:{int(time.time()) // 60}"
    try:
        current = client.incr(key)
        if current == 1:
            client.expire(key, 60)

        if current > limit_per_minute:
            ttl = client.ttl(key)
            return False, max(ttl, 1), current

        return True, 0, current
    except Exception:
        return True, 0, 0


# ============================================
# SESSION CACHE
# ============================================

def cache_session_data(session_id: str, data: Dict, ttl_seconds: int = 7200) -> bool:
    """Cache session data in Redis with TTL."""
    client = _get_redis_client()
    if not client:
        return False
    try:
        client.setex(f"session:{session_id}", ttl_seconds, json.dumps(data, default=str))
        return True
    except Exception:
        return False


def get_cached_session(session_id: str) -> Optional[Dict]:
    """Retrieve cached session data."""
    client = _get_redis_client()
    if not client:
        return None
    try:
        data = client.get(f"session:{session_id}")
        return json.loads(data) if data else None
    except Exception:
        return None


# ============================================
# RESPONSE CACHE (for frequent queries)
# ============================================

def cache_response(key: str, response: str, ttl_seconds: int = 300) -> bool:
    """Cache an agent response for repeated queries."""
    client = _get_redis_client()
    if not client:
        return False
    try:
        client.setex(f"response:{key}", ttl_seconds, response)
        return True
    except Exception:
        return False


def get_cached_response(key: str) -> Optional[str]:
    """Get a cached response."""
    client = _get_redis_client()
    if not client:
        return None
    try:
        return client.get(f"response:{key}")
    except Exception:
        return None


# ============================================
# METRICS COUNTER
# ============================================

def increment_metric(metric_name: str, amount: int = 1) -> int:
    """Increment a metric counter in Redis."""
    client = _get_redis_client()
    if not client:
        return 0
    try:
        return client.incrby(f"metric:{metric_name}", amount)
    except Exception:
        return 0


def get_metric(metric_name: str) -> int:
    """Get current metric value."""
    client = _get_redis_client()
    if not client:
        return 0
    try:
        val = client.get(f"metric:{metric_name}")
        return int(val) if val else 0
    except Exception:
        return 0
