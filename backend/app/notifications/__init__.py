from __future__ import annotations

from typing import Any, Dict

from app.notifications.bark import BarkAdapter
from app.notifications.base import NotifyPayload, NotifyResult
from app.notifications.channels import (
    DingtalkAdapter,
    EmailAdapter,
    FeishuAdapter,
    WebhookAdapter,
    WechatMpAdapter,
    WecomAdapter,
)
from app.notifications.telegram import TelegramAdapter


def build_adapters() -> Dict[str, Any]:
    return {
        "telegram": TelegramAdapter(),
        "bark": BarkAdapter(),
        "wecom": WecomAdapter(),
        "dingtalk": DingtalkAdapter(),
        "feishu": FeishuAdapter(),
        "email": EmailAdapter(),
        "webhook": WebhookAdapter(),
        "wechat_mp": WechatMpAdapter(),
    }


_ADAPTERS: Dict[str, Any] | None = None


def get_notification_adapter(channel_type: str):
    global _ADAPTERS
    if _ADAPTERS is None:
        _ADAPTERS = build_adapters()
    if channel_type not in _ADAPTERS:
        raise KeyError(f"未知通知渠道: {channel_type}")
    return _ADAPTERS[channel_type]


async def send_notification(
    channel_type: str,
    credentials: dict[str, Any],
    config: dict[str, Any],
    payload: NotifyPayload,
) -> NotifyResult:
    adapter = get_notification_adapter(channel_type)
    return await adapter.send(credentials, config, payload)
