from __future__ import annotations

import asyncio
import time
from typing import Optional

import httpx

from app.config import get_settings


class RateLimiter:
    """Simple per-key minimum-interval limiter."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self._locks: dict[str, asyncio.Lock] = {}
        self._last: dict[str, float] = {}

    def _lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def wait(self, key: str) -> None:
        async with self._lock(key):
            now = time.monotonic()
            last = self._last.get(key, 0.0)
            delay = self.min_interval - (now - last)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last[key] = time.monotonic()


_rate_limiter: Optional[RateLimiter] = None
_client: Optional[httpx.AsyncClient] = None
_sem: Optional[asyncio.Semaphore] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(get_settings().platform_min_interval_seconds)
    return _rate_limiter


def get_semaphore() -> asyncio.Semaphore:
    global _sem
    if _sem is None:
        _sem = asyncio.Semaphore(get_settings().max_concurrent_platform_requests)
    return _sem


async def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        settings = get_settings()
        _client = httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            headers={"User-Agent": settings.http_user_agent},
            follow_redirects=True,
        )
    return _client


async def close_http_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
