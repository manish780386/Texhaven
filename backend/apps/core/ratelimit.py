from django.core.cache import cache


def hit(key: str, limit: int, window_seconds: int) -> bool:
    """Fixed-window counter. Returns True while the caller is still within the limit.
    cache.incr is atomic on Redis (and under a lock on locmem)."""
    cache.add(key, 0, timeout=window_seconds)
    try:
        count = cache.incr(key)
    except ValueError:  # key expired between add and incr
        cache.set(key, 1, timeout=window_seconds)
        count = 1
    return count <= limit
