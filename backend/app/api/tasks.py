from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import MatchMode, MonitorTask, TaskStatus
from app.schemas import TaskCreate, TaskOut, TaskUpdate
from app.services.monitor import run_task_once, utcnow

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _to_out(task: MonitorTask) -> TaskOut:
    return TaskOut(
        id=task.id,
        name=task.name,
        keywords=list(task.keywords or []),
        exclude_keywords=list(task.exclude_keywords or []),
        match_mode=task.match_mode,
        platforms=[str(p) for p in (task.platforms or [])],
        brand=task.brand,
        model=task.model,
        category=task.category,
        min_price=task.min_price,
        max_price=task.max_price,
        seller=task.seller,
        condition=task.condition,
        currency=task.currency,
        interval_seconds=task.interval_seconds,
        status=task.status,
        channel_ids=list(task.channel_ids or []),
        last_checked_at=task.last_checked_at,
        next_check_at=task.next_check_at,
        last_error=task.last_error,
        consecutive_failures=task.consecutive_failures,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)) -> list[TaskOut]:
    tasks = db.scalars(select(MonitorTask).order_by(MonitorTask.id.desc())).all()
    return [_to_out(t) for t in tasks]


@router.post("", response_model=TaskOut)
def create_task(body: TaskCreate, db: Session = Depends(get_db)) -> TaskOut:
    task = MonitorTask(
        name=body.name,
        keywords=body.keywords,
        exclude_keywords=body.exclude_keywords,
        match_mode=body.match_mode,
        platforms=[p.value for p in body.platforms],
        brand=body.brand,
        model=body.model,
        category=body.category,
        min_price=body.min_price,
        max_price=body.max_price,
        seller=body.seller,
        condition=body.condition,
        currency=body.currency,
        interval_seconds=body.interval_seconds,
        status=body.status,
        channel_ids=body.channel_ids,
        next_check_at=utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_out(task)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskOut:
    task = db.get(MonitorTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return _to_out(task)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db)) -> TaskOut:
    task = db.get(MonitorTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    data = body.model_dump(exclude_unset=True)
    if "platforms" in data and data["platforms"] is not None:
        data["platforms"] = [
            p.value if hasattr(p, "value") else str(p) for p in data["platforms"]
        ]
    for k, v in data.items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return _to_out(task)


@router.post("/{task_id}/pause", response_model=TaskOut)
def pause_task(task_id: int, db: Session = Depends(get_db)) -> TaskOut:
    task = db.get(MonitorTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    task.status = TaskStatus.paused
    db.commit()
    db.refresh(task)
    return _to_out(task)


@router.post("/{task_id}/resume", response_model=TaskOut)
def resume_task(task_id: int, db: Session = Depends(get_db)) -> TaskOut:
    task = db.get(MonitorTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    task.status = TaskStatus.active
    task.next_check_at = utcnow()
    task.consecutive_failures = 0
    db.commit()
    db.refresh(task)
    return _to_out(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = db.get(MonitorTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    db.delete(task)
    db.commit()
    return {"ok": True}


@router.post("/{task_id}/run")
async def run_task_now(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = db.get(MonitorTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    result = await run_task_once(db, task)
    return {"ok": True, **result}
