from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    Item,
    ItemDiscovery,
    MonitorTask,
    NotificationLog,
    NotificationStatus,
    RunLog,
    TaskStatus,
)
from app.platforms import list_capabilities
from app.schemas import (
    DailyStat,
    DashboardStats,
    NotificationLogOut,
    PlatformInfo,
    RunLogOut,
    StatsCharts,
)

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "jp-monitor"}


def _platform_status_label(status: str) -> str:
    return {
        "supported": "已接入",
        "partial": "部分接入",
        "unavailable": "当前不能监控",
        "stub": "未接入",
        "pending_confirmation": "待确认",
    }.get(status, status)


@router.get("/platforms", response_model=list[PlatformInfo])
def platforms() -> list[PlatformInfo]:
    return [
        PlatformInfo(
            code=c.code,
            name=c.name,
            name_ja=c.name_ja,
            status=c.status,
            data_source=c.data_source,
            capabilities=c.capabilities,
            limitations=c.limitations,
            config_notes=c.config_notes,
            can_monitor=c.status in ("supported", "partial"),
            status_label=_platform_status_label(c.status),
        )
        for c in list_capabilities()
    ]


@router.get("/stats/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)) -> DashboardStats:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    task_total = db.scalar(select(func.count()).select_from(MonitorTask)) or 0
    task_active = (
        db.scalar(
            select(func.count()).select_from(MonitorTask).where(MonitorTask.status == TaskStatus.active)
        )
        or 0
    )
    task_paused = (
        db.scalar(
            select(func.count())
            .select_from(MonitorTask)
            .where(MonitorTask.status == TaskStatus.paused)
        )
        or 0
    )
    items_today = (
        db.scalar(select(func.count()).select_from(Item).where(Item.discovered_at >= start)) or 0
    )
    items_total = db.scalar(select(func.count()).select_from(Item)) or 0

    by_platform_rows = db.execute(
        select(Item.platform, func.count()).group_by(Item.platform)
    ).all()
    items_by_platform = {str(p.value if hasattr(p, "value") else p): c for p, c in by_platform_rows}

    n_ok = (
        db.scalar(
            select(func.count())
            .select_from(NotificationLog)
            .where(NotificationLog.status == NotificationStatus.success)
        )
        or 0
    )
    n_fail = (
        db.scalar(
            select(func.count())
            .select_from(NotificationLog)
            .where(NotificationLog.status == NotificationStatus.failed)
        )
        or 0
    )
    n_pending = (
        db.scalar(
            select(func.count())
            .select_from(NotificationLog)
            .where(NotificationLog.status == NotificationStatus.pending)
        )
        or 0
    )

    return DashboardStats(
        task_total=task_total,
        task_active=task_active,
        task_paused=task_paused,
        items_today=items_today,
        items_total=items_total,
        items_by_platform=items_by_platform,
        notifications_success=n_ok,
        notifications_failed=n_fail,
        notifications_pending=n_pending,
    )


@router.get("/stats/charts", response_model=StatsCharts)
def charts(days: int = Query(default=14, ge=1, le=90), db: Session = Depends(get_db)) -> StatsCharts:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    items = db.scalars(select(Item).where(Item.discovered_at >= start)).all()
    daily_map: dict[str, int] = {}
    by_platform: dict[str, int] = {}
    for item in items:
        d = (item.discovered_at or now).astimezone(timezone.utc).strftime("%Y-%m-%d")
        daily_map[d] = daily_map.get(d, 0) + 1
        key = item.platform.value if hasattr(item.platform, "value") else str(item.platform)
        by_platform[key] = by_platform.get(key, 0) + 1

    daily = [DailyStat(date=k, count=daily_map[k]) for k in sorted(daily_map.keys())]

    by_keyword: dict[str, int] = {}
    discoveries = db.scalars(
        select(ItemDiscovery).where(ItemDiscovery.created_at >= start)
    ).all()
    for disc in discoveries:
        for kw in disc.matched_keywords or []:
            by_keyword[kw] = by_keyword.get(kw, 0) + 1

    return StatsCharts(daily=daily, by_platform=by_platform, by_keyword=by_keyword)


@router.get("/logs/runs", response_model=list[RunLogOut])
def run_logs(
    limit: int = Query(default=100, ge=1, le=500),
    task_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[RunLogOut]:
    stmt = select(RunLog).order_by(RunLog.id.desc()).limit(limit)
    if task_id is not None:
        stmt = stmt.where(RunLog.task_id == task_id)
    rows = db.scalars(stmt).all()
    return [RunLogOut.model_validate(r) for r in rows]


@router.get("/logs/notifications", response_model=list[NotificationLogOut])
def notification_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[NotificationLogOut]:
    rows = db.scalars(
        select(NotificationLog).order_by(NotificationLog.id.desc()).limit(limit)
    ).all()
    return [NotificationLogOut.model_validate(r) for r in rows]
