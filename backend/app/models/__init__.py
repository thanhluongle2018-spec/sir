from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TaskStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    error = "error"


class MatchMode(str, enum.Enum):
    any = "any"  # 任意关键词命中
    all = "all"  # 全部命中


class PlatformCode(str, enum.Enum):
    mercari = "mercari"
    paypay_fleamarket = "paypay_fleamarket"  # 闪电市场 / PayPayフリマ
    rakuma = "rakuma"  # 乐天二手 / ラクマ
    yahoo_fleamarket = "yahoo_fleamarket"  # 雅虎闲置（已并入 PayPayフリマ）
    yahoo_auctions = "yahoo_auctions"  # 雅虎日拍
    surugaya = "surugaya"  # 骏合屋 / 駿河屋
    demo = "demo"  # 离线演示平台


class ChannelType(str, enum.Enum):
    telegram = "telegram"
    bark = "bark"
    wecom = "wecom"  # 企业微信机器人
    dingtalk = "dingtalk"
    feishu = "feishu"
    email = "email"
    webhook = "webhook"
    wechat_mp = "wechat_mp"  # 微信公众号 / 第三方推送


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
    skipped = "skipped"


class MonitorTask(Base):
    __tablename__ = "monitor_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    keywords: Mapped[list[Any]] = mapped_column(JSON, default=list)  # include keywords
    exclude_keywords: Mapped[list[Any]] = mapped_column(JSON, default=list)
    match_mode: Mapped[MatchMode] = mapped_column(
        Enum(MatchMode), default=MatchMode.any, nullable=False
    )
    platforms: Mapped[list[Any]] = mapped_column(JSON, default=list)
    brand: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    min_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    seller: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="JPY")
    interval_seconds: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.active, nullable=False
    )
    channel_ids: Mapped[list[Any]] = mapped_column(JSON, default=list)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    discoveries: Mapped[list["ItemDiscovery"]] = relationship(back_populates="task")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_item_platform_external"),
        Index("ix_items_platform_discovered", "platform", "discovered_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[PlatformCode] = mapped_column(Enum(PlatformCode), nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="JPY")
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    seller: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    raw: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    discoveries: Mapped[list["ItemDiscovery"]] = relationship(back_populates="item")


class ItemDiscovery(Base):
    """Links an item to the task/keywords that matched it (dedupe notifications per task+item)."""

    __tablename__ = "item_discoveries"
    __table_args__ = (
        UniqueConstraint("task_id", "item_id", name="uq_discovery_task_item"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("monitor_tasks.id", ondelete="CASCADE"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    matched_keywords: Mapped[list[Any]] = mapped_column(JSON, default=list)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    task: Mapped[MonitorTask] = relationship(back_populates="discoveries")
    item: Mapped[Item] = relationship(back_populates="discoveries")


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    channel_type: Mapped[ChannelType] = mapped_column(Enum(ChannelType), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Encrypted JSON blob of credentials (or plain JSON if fernet key unset in dev)
    credentials_encrypted: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)  # non-secret options
    last_test_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_test_ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    __table_args__ = (
        UniqueConstraint(
            "channel_id", "item_id", "task_id", name="uq_notif_channel_item_task"
        ),
        Index("ix_notif_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("notification_channels.id", ondelete="CASCADE")
    )
    item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("monitor_tasks.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), default=NotificationStatus.pending
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RunLog(Base):
    __tablename__ = "run_logs"
    __table_args__ = (Index("ix_run_logs_created", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("monitor_tasks.id", ondelete="SET NULL"), nullable=True
    )
    platform: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    level: Mapped[str] = mapped_column(String(20), default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
