from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import NotificationChannel
from app.notifications import send_notification
from app.notifications.base import NotifyPayload
from app.schemas import ChannelCreate, ChannelOut, ChannelUpdate
from app.services.crypto import decrypt_credentials, encrypt_credentials, mask_credentials
from app.services.monitor import utcnow

router = APIRouter(prefix="/api/channels", tags=["channels"])


def _to_out(ch: NotificationChannel) -> ChannelOut:
    creds = decrypt_credentials(ch.credentials_encrypted)
    return ChannelOut(
        id=ch.id,
        name=ch.name,
        channel_type=ch.channel_type,
        enabled=ch.enabled,
        credentials_masked=mask_credentials(creds),
        config=ch.config or {},
        last_test_at=ch.last_test_at,
        last_test_ok=ch.last_test_ok,
        last_error=ch.last_error,
        created_at=ch.created_at,
        updated_at=ch.updated_at,
    )


@router.get("", response_model=list[ChannelOut])
def list_channels(db: Session = Depends(get_db)) -> list[ChannelOut]:
    rows = db.scalars(select(NotificationChannel).order_by(NotificationChannel.id.desc())).all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=ChannelOut)
def create_channel(body: ChannelCreate, db: Session = Depends(get_db)) -> ChannelOut:
    ch = NotificationChannel(
        name=body.name,
        channel_type=body.channel_type,
        enabled=body.enabled,
        credentials_encrypted=encrypt_credentials(body.credentials or {}),
        config=body.config or {},
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return _to_out(ch)


@router.patch("/{channel_id}", response_model=ChannelOut)
def update_channel(
    channel_id: int, body: ChannelUpdate, db: Session = Depends(get_db)
) -> ChannelOut:
    ch = db.get(NotificationChannel, channel_id)
    if not ch:
        raise HTTPException(404, "渠道不存在")
    data = body.model_dump(exclude_unset=True)
    if "credentials" in data:
        creds = data.pop("credentials") or {}
        # Merge with existing so partial updates don't wipe secrets
        existing = decrypt_credentials(ch.credentials_encrypted)
        for k, v in creds.items():
            if v is None or v == "" or (isinstance(v, str) and "****" in v):
                continue
            existing[k] = v
        ch.credentials_encrypted = encrypt_credentials(existing)
    for k, v in data.items():
        setattr(ch, k, v)
    db.commit()
    db.refresh(ch)
    return _to_out(ch)


@router.delete("/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)) -> dict:
    ch = db.get(NotificationChannel, channel_id)
    if not ch:
        raise HTTPException(404, "渠道不存在")
    db.delete(ch)
    db.commit()
    return {"ok": True}


@router.post("/{channel_id}/test")
async def test_channel(channel_id: int, db: Session = Depends(get_db)) -> dict:
    ch = db.get(NotificationChannel, channel_id)
    if not ch:
        raise HTTPException(404, "渠道不存在")
    creds = decrypt_credentials(ch.credentials_encrypted)
    payload = NotifyPayload(
        title="日本二手监控 · 测试通知",
        body="这是一条测试消息。若你收到，说明渠道配置正确。",
        url="https://example.com",
    )
    result = await send_notification(ch.channel_type.value, creds, ch.config or {}, payload)
    ch.last_test_at = utcnow()
    ch.last_test_ok = result.ok
    ch.last_error = None if result.ok else (result.error or "failed")
    db.commit()
    return {"ok": result.ok, "message": result.message, "error": result.error}
