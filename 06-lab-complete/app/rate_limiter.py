import time
import json
import logging
from collections import defaultdict, deque
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

USE_REDIS = False
_redis = None

if settings.redis_url:
    try:
        import redis
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
        _redis.ping()
        USE_REDIS = True
    except Exception as e:
        logger.warning(json.dumps({"event": "redis_rate_limit_connection_failed", "error": str(e)}))

_rate_windows: dict[str, deque] = defaultdict(deque)

def _fallback_rate_limit(key: str):
    now = time.time()
    window = _rate_windows[key]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
    window.append(now)

def check_rate_limit(key: str):
    if USE_REDIS and _redis:
        now = time.time()
        redis_key = f"rate_limit:{key}"
        try:
            pipe = _redis.pipeline()
            pipe.zremrangebyscore(redis_key, 0, now - 60)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, 60)
            res = pipe.execute()
            count = res[1]
            if count >= settings.rate_limit_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                    headers={"Retry-After": "60"},
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(json.dumps({"event": "redis_rate_limit_error", "error": str(e)}))
            _fallback_rate_limit(key)
    else:
        _fallback_rate_limit(key)
