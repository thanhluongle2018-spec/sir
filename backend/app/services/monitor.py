from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models import (
    Item,
    ItemDiscovery,
    MonitorTask,
    NotificationChannel,
    NotificationLog,
    NotificationStatus,
    PlatformCode,
    RunLog,
    TaskStatus,
)
from app.notifications import send_notification
from app.notifications.base import NotifyPayload
from app.platforms import get_adapter
from app.platforms.base import ProductItem, SearchQuery
from app.services.crypto import decrypt_credentials

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def write_run_log(
    db: Session,
    *,
    message: str,
    level: str = "info",
    task_id: Optional[int] = None,
    platform: Optional[str] = None,
    detail: Optional[dict] = None,
) -> None:
    db.add(
        RunLog(
            task_id=task_id,
            platform=platform,
            level=level,
            message=message,
            detail=detail,
        )
    )


def compute_backoff_seconds(failures: int) -> int:
    settings = get_settings()
    base = settings.retry_base_seconds
    return int(min(3600, base * (2 ** max(0, failures - 1))))


async def run_task_once(db: Session, task: MonitorTask) -> dict:
    """Execute one monitoring cycle for a task."""
    settings = get_settings()
    started = utcnow()
    new_items = 0
    errors: list[str] = []

    platforms = list(task.platforms or [])
    if not platforms:
        errors.append("任务未选择平台")
    if not task.keywords:
        errors.append("任务未配置关键词")

    if errors:
        task.last_error = "; ".join(errors)
        task.consecutive_failures += 1
        task.last_checked_at = started
        task.next_check_at = started + timedelta(
            seconds=max(task.interval_seconds, compute_backoff_seconds(task.consecutive_failures))
        )
        task.status = TaskStatus.error
        write_run_log(db, task_id=task.id, level="error", message=task.last_error)
        db.commit()
        return {"new_items": 0, "errors": errors}

    query = SearchQuery(
        keywords=list(task.keywords or []),
        exclude_keywords=list(task.exclude_keywords or []),
        match_mode=task.match_mode.value if hasattr(task.match_mode, "value") else str(task.match_mode),
        min_price=task.min_price,
        max_price=task.max_price,
        brand=task.brand,
        model=task.model,
        category=task.category,
        seller=task.seller,
        condition=task.condition,
        page_size=settings.max_items_per_search,
    )

    for platform in platforms:
        platform_code = platform if isinstance(platform, str) else str(platform)
        try:
            adapter = get_adapter(platform_code)
            cap = adapter.capability()
            if cap.status == "stub":
                msg = f"平台 {platform_code} 为占位实现，已跳过搜索"
                write_run_log(
                    db,
                    task_id=task.id,
                    platform=platform_code,
                    level="warning",
                    message=msg,
                )
                continue

            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(settings.retry_max_attempts),
                wait=wait_exponential(
                    multiplier=settings.retry_base_seconds, min=1, max=30
                ),
                retry=retry_if_exception_type(Exception),
                reraise=True,
            ):
                with attempt:
                    result = await adapter.search(query)

            for product in result.items:
                created = upsert_item_and_discovery(db, task, product)
                if created:
                    new_items += 1
                    await notify_for_discovery(db, task, product)

            write_run_log(
                db,
                task_id=task.id,
                platform=platform_code,
                level="info",
                message=f"检查完成，返回 {len(result.items)} 条，新增 {new_items} 条（累计）",
                detail={"returned": len(result.items)},
            )
        except NotImplementedError as exc:
            errors.append(str(exc))
            write_run_log(
                db,
                task_id=task.id,
                platform=platform_code,
                level="warning",
                message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            err = f"{platform_code}: {exc}"
            errors.append(err)
            write_run_log(
                db,
                task_id=task.id,
                platform=platform_code,
                level="error",
                message=err,
            )
            logger.exception("platform search failed: %s", platform_code)

    task.last_checked_at = started
    if errors and new_items == 0 and len(errors) >= len(platforms):
        task.consecutive_failures += 1
        task.last_error = "; ".join(errors)[:2000]
        task.status = TaskStatus.error
        delay = max(task.interval_seconds, compute_backoff_seconds(task.consecutive_failures))
    else:
        task.consecutive_failures = 0
        task.last_error = "; ".join(errors)[:2000] if errors else None
        if task.status == TaskStatus.error:
            task.status = TaskStatus.active
        delay = task.interval_seconds

    task.next_check_at = utcnow() + timedelta(seconds=delay)
    db.commit()
    return {"new_items": new_items, "errors": errors}


def upsert_item_and_discovery(db: Session, task: MonitorTask, product: ProductItem) -> bool:
    """Insert item if new; create discovery link. Returns True if newly discovered for this task."""
    try:
        platform_enum = PlatformCode(product.platform)
    except ValueError:
        return False

    existing = db.scalar(
        select(Item).where(
            Item.platform == platform_enum,
            Item.external_id == product.external_id,
        )
    )
    if existing is None:
        existing = Item(
            platform=platform_enum,
            external_id=product.external_id,
            title=product.title,
            price=product.price,
            currency=product.currency,
            image_url=product.image_url,
            url=product.url,
            seller=product.seller,
            condition=product.condition,
            category=product.category,
            brand=product.brand,
            published_at=product.published_at,
            discovered_at=utcnow(),
            raw=product.raw,
            is_read=False,
        )
        db.add(existing)
        db.flush()
    else:
        # Refresh mutable fields
        existing.title = product.title
        existing.price = product.price
        existing.image_url = product.image_url or existing.image_url
        existing.seller = product.seller or existing.seller

    discovery = db.scalar(
        select(ItemDiscovery).where(
            ItemDiscovery.task_id == task.id,
            ItemDiscovery.item_id == existing.id,
        )
    )
    if discovery is not None:
        return False

    matched = _matched_keywords(task, product)
    discovery = ItemDiscovery(
        task_id=task.id,
        item_id=existing.id,
        matched_keywords=matched,
        notified=False,
    )
    db.add(discovery)
    db.flush()
    return True


def _matched_keywords(task: MonitorTask, product: ProductItem) -> list[str]:
    text = (product.title or "").lower()
    hits = []
    for kw in task.keywords or []:
        if kw and kw.lower() in text:
            hits.append(kw)
    return hits or list(task.keywords or [])


async def notify_for_discovery(db: Session, task: MonitorTask, product: ProductItem) -> None:
    item = db.scalar(
        select(Item).where(
            Item.platform == PlatformCode(product.platform),
            Item.external_id == product.external_id,
        )
    )
    if item is None:
        return
    discovery = db.scalar(
        select(ItemDiscovery).where(
            ItemDiscovery.task_id == task.id,
            ItemDiscovery.item_id == item.id,
        )
    )
    channel_ids = list(task.channel_ids or [])
    if not channel_ids:
        if discovery:
            discovery.notified = True
        return

    price_str = f"{int(product.price)} {product.currency}" if product.price is not None else "价格未知"
    payload = NotifyPayload(
        title=f"[{product.platform}] 新商品：{product.title[:80]}",
        body=f"价格：{price_str}\n任务：{task.name}\n卖家：{product.seller or '-'}",
        url=product.url,
        image_url=product.image_url,
        extra={"task_id": task.id, "item_id": item.id},
    )

    any_ok = False
    for cid in channel_ids:
        channel = db.get(NotificationChannel, cid)
        if channel is None or not channel.enabled:
            continue

        # Dedupe: unique constraint on channel+item+task
        existing_log = db.scalar(
            select(NotificationLog).where(
                NotificationLog.channel_id == channel.id,
                NotificationLog.item_id == item.id,
                NotificationLog.task_id == task.id,
            )
        )
        if existing_log and existing_log.status == NotificationStatus.success:
            any_ok = True
            continue

        log = existing_log or NotificationLog(
            channel_id=channel.id,
            item_id=item.id,
            task_id=task.id,
            status=NotificationStatus.pending,
            attempts=0,
            message=payload.title,
        )
        if existing_log is None:
            db.add(log)
            db.flush()

        creds = decrypt_credentials(channel.credentials_encrypted)
        result = None
        settings = get_settings()
        for _ in range(settings.retry_max_attempts):
            log.attempts += 1
            try:
                result = await send_notification(
                    channel.channel_type.value,
                    creds,
                    channel.config or {},
                    payload,
                )
            except Exception as exc:  # noqa: BLE001
                result = type("R", (), {"ok": False, "error": str(exc), "message": ""})()
            if result.ok:
                break
            await asyncio.sleep(1)

        if result and result.ok:
            log.status = NotificationStatus.success
            log.error = None
            any_ok = True
        else:
            log.status = NotificationStatus.failed
            log.error = (result.error if result else "unknown")[:2000]
            channel.last_error = log.error

    if discovery:
        discovery.notified = any_ok or not channel_ids
    db.flush()


async def tick_due_tasks(db: Session) -> int:
    """Find due active tasks and run them sequentially (safe for SQLite)."""
    now = utcnow()
    tasks = db.scalars(
        select(MonitorTask).where(MonitorTask.status.in_([TaskStatus.active, TaskStatus.error]))
    ).all()
    ran = 0
    for task in tasks:
        if task.status == TaskStatus.paused:
            continue
        due = task.next_check_at is None or task.next_check_at <= now
        if not due:
            continue
        try:
            await run_task_once(db, task)
            ran += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception("task %s failed", task.id)
            task.last_error = str(exc)[:2000]
            task.consecutive_failures += 1
            task.next_check_at = utcnow() + timedelta(
                seconds=compute_backoff_seconds(task.consecutive_failures)
            )
            write_run_log(db, task_id=task.id, level="error", message=str(exc))
            db.commit()
    return ran
