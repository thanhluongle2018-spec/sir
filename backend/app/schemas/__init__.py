from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.models import ChannelType, MatchMode, NotificationStatus, PlatformCode, TaskStatus


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    match_mode: MatchMode = MatchMode.any
    platforms: list[PlatformCode] = Field(default_factory=list)
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    seller: Optional[str] = None
    condition: Optional[str] = None
    currency: str = "JPY"
    interval_seconds: int = Field(default=60, ge=30, le=86400)
    status: TaskStatus = TaskStatus.active
    channel_ids: list[int] = Field(default_factory=list)

    @field_validator("keywords", "exclude_keywords", mode="before")
    @classmethod
    def normalize_keywords(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            parts = [p.strip() for p in v.replace("，", ",").split(",")]
            return [p for p in parts if p]
        return [str(x).strip() for x in v if str(x).strip()]


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    keywords: Optional[list[str]] = None
    exclude_keywords: Optional[list[str]] = None
    match_mode: Optional[MatchMode] = None
    platforms: Optional[list[PlatformCode]] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    seller: Optional[str] = None
    condition: Optional[str] = None
    currency: Optional[str] = None
    interval_seconds: Optional[int] = Field(default=None, ge=30, le=86400)
    status: Optional[TaskStatus] = None
    channel_ids: Optional[list[int]] = None


class TaskOut(BaseModel):
    id: int
    name: str
    keywords: list[str]
    exclude_keywords: list[str]
    match_mode: MatchMode
    platforms: list[str]
    brand: Optional[str]
    model: Optional[str]
    category: Optional[str]
    min_price: Optional[float]
    max_price: Optional[float]
    seller: Optional[str]
    condition: Optional[str]
    currency: str
    interval_seconds: int
    status: TaskStatus
    channel_ids: list[int]
    last_checked_at: Optional[datetime]
    next_check_at: Optional[datetime]
    last_error: Optional[str]
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ItemOut(BaseModel):
    id: int
    platform: PlatformCode
    external_id: str
    title: str
    price: Optional[float]
    currency: str
    image_url: Optional[str]
    url: str
    seller: Optional[str]
    condition: Optional[str]
    category: Optional[str]
    brand: Optional[str]
    published_at: Optional[datetime]
    discovered_at: datetime
    is_read: bool
    matched_keywords: list[str] = Field(default_factory=list)
    task_ids: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ChannelCreate(BaseModel):
    name: str
    channel_type: ChannelType
    enabled: bool = True
    credentials: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    credentials: Optional[dict[str, Any]] = None
    config: Optional[dict[str, Any]] = None


class ChannelOut(BaseModel):
    id: int
    name: str
    channel_type: ChannelType
    enabled: bool
    credentials_masked: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    last_test_at: Optional[datetime] = None
    last_test_ok: Optional[bool] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationLogOut(BaseModel):
    id: int
    channel_id: int
    item_id: Optional[int]
    task_id: Optional[int]
    status: NotificationStatus
    attempts: int
    message: Optional[str]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunLogOut(BaseModel):
    id: int
    task_id: Optional[int]
    platform: Optional[str]
    level: str
    message: str
    detail: Optional[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class PlatformInfo(BaseModel):
    code: str
    name: str
    name_ja: str
    status: str  # supported | partial | stub
    data_source: str
    capabilities: list[str]
    limitations: list[str]
    config_notes: str


class DashboardStats(BaseModel):
    task_total: int
    task_active: int
    task_paused: int
    items_today: int
    items_total: int
    items_by_platform: dict[str, int]
    notifications_success: int
    notifications_failed: int
    notifications_pending: int


class DailyStat(BaseModel):
    date: str
    count: int


class StatsCharts(BaseModel):
    daily: list[DailyStat]
    by_platform: dict[str, int]
    by_keyword: dict[str, int]
