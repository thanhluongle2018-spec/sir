from __future__ import annotations

from typing import Any

import httpx

from app.notifications.base import NotifyPayload, NotifyResult


class TelegramAdapter:
    channel_type = "telegram"

    async def send(
        self, credentials: dict[str, Any], config: dict[str, Any], payload: NotifyPayload
    ) -> NotifyResult:
        token = credentials.get("bot_token") or credentials.get("token")
        chat_id = credentials.get("chat_id")
        if not token or not chat_id:
            return NotifyResult(ok=False, error="缺少 bot_token 或 chat_id")

        text = f"<b>{_escape(payload.title)}</b>\n{_escape(payload.body)}"
        if payload.url:
            text += f'\n<a href="{payload.url}">打开商品</a>'

        api = f"https://api.telegram.org/bot{token}/sendMessage"
        data: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(api, json=data)
            if resp.status_code >= 400:
                return NotifyResult(ok=False, error=f"Telegram HTTP {resp.status_code}: {resp.text[:300]}")
            body = resp.json()
            if not body.get("ok"):
                return NotifyResult(ok=False, error=str(body)[:300])
        return NotifyResult(ok=True, message="sent")


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
