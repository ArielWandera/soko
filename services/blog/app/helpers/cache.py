import json
import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

TTL_POSTS    = 300    # 5 min
TTL_POST     = 600    # 10 min
TTL_COMMENTS = 300    # 5 min

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


def _get(key: str) -> dict | list | None:
    try:
        raw = get_redis().get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"Redis read error [{key}]: {e}")
        return None


def _set(key: str, data: dict | list, ttl: int) -> None:
    try:
        get_redis().setex(key, ttl, json.dumps(data))
    except Exception as e:
        logger.warning(f"Redis write error [{key}]: {e}")


def _delete_pattern(pattern: str) -> None:
    try:
        keys = get_redis().keys(pattern)
        if keys:
            get_redis().delete(*keys)
            logger.info(f"Cache invalidated: {len(keys)} key(s) matching '{pattern}'")
    except Exception as e:
        logger.warning(f"Redis delete error [{pattern}]: {e}")


# ── Post list
def _posts_key(category, tag, search, page, limit):
    return f"posts:{category or 'all'}:{tag or 'all'}:{search or ''}:p{page}:l{limit}"


def get_cached_posts(category, tag, search, page, limit):
    return _get(_posts_key(category, tag, search, page, limit))


def set_cached_posts(category, tag, search, page, limit, data):
    _set(_posts_key(category, tag, search, page, limit), data, TTL_POSTS)


def invalidate_posts():
    _delete_pattern("posts:*")


# ── Single post
def _post_key(slug: str):
    return f"post:{slug}"


def get_cached_post(slug):
    return _get(_post_key(slug))


def set_cached_post(slug, data):
    _set(_post_key(slug), data, TTL_POST)


def invalidate_post(slug):
    try:
        get_redis().delete(_post_key(slug))
    except Exception as e:
        logger.warning(f"Redis delete error [post:{slug}]: {e}")


# ── Comments
def _comments_key(post_id, page, limit):
    return f"comments:{post_id}:p{page}:l{limit}"


def get_cached_comments(post_id, page, limit):
    return _get(_comments_key(post_id, page, limit))


def set_cached_comments(post_id, page, limit, data):
    _set(_comments_key(post_id, page, limit), data, TTL_COMMENTS)


def invalidate_comments(post_id):
    _delete_pattern(f"comments:{post_id}:*")