from __future__ import annotations

import hashlib
import hmac
import base64
import time
from typing import Any

import httpx

from app.notifications.base import NotifyPayload, NotifyResult


class WebhookAdapter:
    channel_type = "webhook"

    async def send(
        self, credentials: dict[str, Any], config: dict[str, Any], payload: NotifyPayload
    ) -> NotifyResult:
        url = credentials.get("url") or config.get("url")
        if not url:
            return NotifyResult(ok=False, error="缺少 webhook url")
        body = {
            "title": payload.title,
            "body": payload.body,
            "url": payload.url,
            "image_url": payload.image_url,
            "extra": payload.extra or {},
        }
        headers = {"Content-Type": "application/json"}
        if credentials.get("auth_header"):
            headers["Authorization"] = credentials["auth_header"]
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, json=body, headers=headers)
            if resp.status_code >= 400:
                return NotifyResult(ok=False, error=f"Webhook HTTP {resp.status_code}: {resp.text[:300]}")
        return NotifyResult(ok=True, message="sent")


class WecomAdapter:
    """企业微信群机器人."""

    channel_type = "wecom"

    async def send(
        self, credentials: dict[str, Any], config: dict[str, Any], payload: NotifyPayload
    ) -> NotifyResult:
        webhook = credentials.get("webhook_url")
        if not webhook:
            return NotifyResult(ok=False, error="缺少企业微信 webhook_url")
        content = f"{payload.title}\n{payload.body}"
        if payload.url:
            content += f"\n{payload.url}"
        data = {"msgtype": "text", "text": {"content": content}}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(webhook, json=data)
            if resp.status_code >= 400:
                return NotifyResult(ok=False, error=f"WeCom HTTP {resp.status_code}: {resp.text[:300]}")
            j = resp.json()
            if j.get("errcode", 0) != 0:
                return NotifyResult(ok=False, error=str(j)[:300])
        return NotifyResult(ok=True, message="sent")


class DingtalkAdapter:
    channel_type = "dingtalk"

    async def send(
        self, credentials: dict[str, Any], config: dict[str, Any], payload: NotifyPayload
    ) -> NotifyResult:
        webhook = credentials.get("webhook_url")
        if not webhook:
            return NotifyResult(ok=False, error="缺少钉钉 webhook_url")
        secret = credentials.get("secret")
        url = webhook
        if secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{secret}"
            h = hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
            sign = quote_base64(h)
            url = f"{webhook}&timestamp={timestamp}&sign={sign}"

        text = f"{payload.title}\n{payload.body}"
        if payload.url:
            text += f"\n{payload.url}"
        data = {"msgtype": "text", "text": {"content": text}}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, json=data)
            if resp.status_code >= 400:
                return NotifyResult(ok=False, error=f"DingTalk HTTP {resp.status_code}: {resp.text[:300]}")
            j = resp.json()
            if j.get("errcode", 0) != 0:
                return NotifyResult(ok=False, error=str(j)[:300])
        return NotifyResult(ok=True, message="sent")


def quote_base64(digest: bytes) -> str:
    from urllib.parse import quote_plus

    return quote_plus(base64.b64encode(digest))


class FeishuAdapter:
    channel_type = "feishu"

    async def send(
        self, credentials: dict[str, Any], config: dict[str, Any], payload: NotifyPayload
    ) -> NotifyResult:
        webhook = credentials.get("webhook_url")
        if not webhook:
            return NotifyResult(ok=False, error="缺少飞书 webhook_url")
        text = f"{payload.title}\n{payload.body}"
        if payload.url:
            text += f"\n{payload.url}"
        data = {"msg_type": "text", "content": {"text": text}}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(webhook, json=data)
            if resp.status_code >= 400:
                return NotifyResult(ok=False, error=f"Feishu HTTP {resp.status_code}: {resp.text[:300]}")
            j = resp.json()
            if j.get("code", 0) not in (0, None) and j.get("StatusCode", 0) not in (0, None):
                # Feishu returns StatusCode 0 on success for some bots
                if j.get("code") not in (0, None):
                    return NotifyResult(ok=False, error=str(j)[:300])
        return NotifyResult(ok=True, message="sent")


class EmailAdapter:
    channel_type = "email"

    async def send(
        self, credentials: dict[str, Any], config: dict[str, Any], payload: NotifyPayload
    ) -> NotifyResult:
        import aiosmtplib
        from email.message import EmailMessage

        host = credentials.get("smtp_host")
        port = int(credentials.get("smtp_port") or 587)
        user = credentials.get("smtp_user")
        password = credentials.get("smtp_password")
        mail_from = credentials.get("from") or user
        mail_to = credentials.get("to") or config.get("to")
        if not all([host, mail_from, mail_to]):
            return NotifyResult(ok=False, error="缺少 smtp_host / from / to")

        msg = EmailMessage()
        msg["From"] = mail_from
        msg["To"] = mail_to
        msg["Subject"] = payload.title
        body = payload.body
        if payload.url:
            body += f"\n\n{payload.url}"
        msg.set_content(body)

        try:
            await aiosmtplib.send(
                msg,
                hostname=host,
                port=port,
                username=user,
                password=password,
                start_tls=bool(credentials.get("start_tls", True)),
            )
        except Exception as exc:  # noqa: BLE001
            return NotifyResult(ok=False, error=str(exc)[:300])
        return NotifyResult(ok=True, message="sent")


class WechatMpAdapter:
    """
    微信公众号 / 微信推送：MVP 通过通用第三方 HTTP 推送（如 Server酱、PushPlus 风格）实现，
    不内置公众号明文 appsecret 硬编码；凭证由用户配置。
    """

    channel_type = "wechat_mp"

    async def send(
        self, credentials: dict[str, Any], config: dict[str, Any], payload: NotifyPayload
    ) -> NotifyResult:
        # Support PushPlus-style or custom endpoint
        endpoint = credentials.get("endpoint") or "http://www.pushplus.plus/send"
        token = credentials.get("token")
        if not token:
            return NotifyResult(ok=False, error="缺少 token（如 PushPlus token）")
        data = {
            "token": token,
            "title": payload.title,
            "content": f"{payload.body}<br/>{payload.url or ''}",
            "template": config.get("template", "html"),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(endpoint, json=data)
            if resp.status_code >= 400:
                return NotifyResult(ok=False, error=f"WeChatMP HTTP {resp.status_code}: {resp.text[:300]}")
        return NotifyResult(ok=True, message="sent")
