import json
import logging
import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Synchronous Redis client (recommendation service uses sync SQLAlchemy + sync handlers)
_client: redis.Redis | None = None

RECS_TTL = 300   # 5 minutes — buyer recommendations
SCORE_TTL = 600  # 10 minutes — produce avg star scores


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


# ── Recommendations cache ─────────────────────────────────────────────

def get_cached_recommendations(user_id: int) -> dict | None:
    try:
        raw = get_redis().get(f"recs:{user_id}")
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"Redis read error (recs:{user_id}): {e}")
        return None


def set_cached_recommendations(user_id: int, data: dict) -> None:
    try:
        get_redis().setex(f"recs:{user_id}", RECS_TTL, json.dumps(data))
    except Exception as e:
        logger.warning(f"Redis write error (recs:{user_id}): {e}")


def invalidate_recommendations(user_id: int) -> None:
    try:
        get_redis().delete(f"recs:{user_id}")
        logger.info(f"Cache invalidated: recs:{user_id}")
    except Exception as e:
        logger.warning(f"Redis delete error (recs:{user_id}): {e}")


# ── Produce score cache ───────────────────────────────────────────────

def get_cached_score(produce_id: int) -> dict | None:
    try:
        raw = get_redis().get(f"score:{produce_id}")
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"Redis read error (score:{produce_id}): {e}")
        return None


def set_cached_score(produce_id: int, data: dict) -> None:
    try:
        get_redis().setex(f"score:{produce_id}", SCORE_TTL, json.dumps(data))
    except Exception as e:
        logger.warning(f"Redis write error (score:{produce_id}): {e}")


def invalidate_score(produce_id: int) -> None:
    try:
        get_redis().delete(f"score:{produce_id}")
        logger.info(f"Cache invalidated: score:{produce_id}")
    except Exception as e:
        logger.warning(f"Redis delete error (score:{produce_id}): {e}")
