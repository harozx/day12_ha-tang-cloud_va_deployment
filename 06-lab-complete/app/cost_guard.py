import time
import json
import logging
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
        logger.warning(json.dumps({"event": "redis_cost_guard_connection_failed", "error": str(e)}))

_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")

def _fallback_cost_guard(today: str, cost: float):
    global _daily_cost, _cost_reset_day
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today
    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
    _daily_cost += cost

def check_and_record_cost(input_tokens: int, output_tokens: int):
    global _daily_cost, _cost_reset_day
    today = time.strftime("%Y-%m-%d")
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006

    if USE_REDIS and _redis:
        redis_key = f"cost:global:{today}"
        try:
            current = float(_redis.get(redis_key) or 0.0)
            if current >= settings.daily_budget_usd:
                raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
            if cost > 0:
                _redis.incrbyfloat(redis_key, cost)
                _redis.expire(redis_key, 86400)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(json.dumps({"event": "redis_cost_guard_error", "error": str(e)}))
            _fallback_cost_guard(today, cost)
    else:
        _fallback_cost_guard(today, cost)

def get_daily_cost() -> float:
    if USE_REDIS and _redis:
        today = time.strftime("%Y-%m-%d")
        try:
            return float(_redis.get(f"cost:global:{today}") or 0.0)
        except Exception:
            return _daily_cost
    return _daily_cost
