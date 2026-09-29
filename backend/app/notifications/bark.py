from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.notifications.base import NotifyPayload, NotifyResult


class BarkAdapter:
    channel_type = "bark"

    async def send(
        self, credentials: dict[str, Any], config: dict[str, Any], payload: NotifyPayload
    ) -> NotifyResult:
        server = (credentials.get("server") or "https://api.day.app").rstrip("/")
        key = credentials.get("device_key") or credentials.get("key")
        if not key:
            return NotifyResult(ok=False, error="缺少 Bark device_key")

        title = quote(payload.title[:100])
        body = quote(payload.body[:500])
        url = f"{server}/{key}/{title}/{body}"
        params = {}
        if payload.url:
            params["url"] = payload.url
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            if resp.status_code >= 400:
                return NotifyResult(ok=False, error=f"Bark HTTP {resp.status_code}: {resp.text[:300]}")
        return NotifyResult(ok=True, message="sent")
