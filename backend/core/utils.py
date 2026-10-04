from django.core.cache import cache


def get_cached_or_set(key, callback, timeout=300):
    data = cache.get(key)
    if data is None:
        data = callback()
        cache.set(key, data, timeout)
    return data
