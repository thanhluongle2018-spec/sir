from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.datasources import list_datasource_capabilities
from app.datasources.user_provided import parse_ingest_payload
from app.models import MonitorTask
from app.schemas import DataSourceOut
from app.services.monitor import notify_for_discovery, upsert_item_and_discovery, write_run_log

router = APIRouter(prefix="/api", tags=["datasources"])


def _ds_status_label(status: str) -> str:
    return {
        "available": "可用",
        "unavailable": "不可用",
        "pending_confirmation": "待确认",
        "disabled": "已禁用",
    }.get(status, status)


@router.get("/datasources", response_model=list[DataSourceOut])
def list_datasources() -> list[DataSourceOut]:
    return [
        DataSourceOut(
            id=c.id,
            platform=c.platform,
            kind=c.kind.value,
            name=c.name,
            name_zh=c.name_zh,
            status=c.status.value,
            summary=c.summary,
            research_notes=c.research_notes,
            requirements=c.requirements,
            limitations=c.limitations,
            references=c.references,
            status_label=_ds_status_label(c.status.value),
        )
        for c in list_datasource_capabilities()
    ]


class IngestBody(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    task_id: Optional[int] = None
    note: Optional[str] = None


@router.post("/ingest")
async def ingest_items(
    body: IngestBody,
    db: Session = Depends(get_db),
    x_ingest_token: Optional[str] = Header(default=None, alias="X-Ingest-Token"),
) -> dict:
    """
    用户主动提交有权使用的商品数据。需要环境变量 INGEST_API_TOKEN。
    不抓取平台；提交后走去重与（可选）任务通知。
    """
    settings = get_settings()
    expected = (settings.ingest_api_token or "").strip()
    if not expected:
        raise HTTPException(
            503,
            "入库接口未启用：请先在环境变量设置 INGEST_API_TOKEN",
        )
    if not x_ingest_token or x_ingest_token != expected:
        raise HTTPException(401, "无效的 X-Ingest-Token")

    try:
        products = parse_ingest_payload({"items": body.items})
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    task: MonitorTask | None = None
    if body.task_id is not None:
        task = db.get(MonitorTask, body.task_id)
        if task is None:
            raise HTTPException(404, "任务不存在")

    created = 0
    for product in products:
        if task is None:
            # 无任务时只入库去重，不发通知
            from app.models import Item, PlatformCode

            existing = db.scalar(
                select(Item).where(
                    Item.platform == PlatformCode(product.platform),
                    Item.external_id == product.external_id,
                )
            )
            if existing is None:
                db.add(
                    Item(
                        platform=PlatformCode(product.platform),
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
                        raw=product.raw,
                        is_read=False,
                    )
                )
                created += 1
        else:
            if upsert_item_and_discovery(db, task, product):
                created += 1
                await notify_for_discovery(db, task, product)

    write_run_log(
        db,
        task_id=body.task_id,
        level="info",
        message=f"用户入库 {len(products)} 条，新增 {created} 条",
        detail={"note": body.note, "source": "user_provided"},
    )
    db.commit()
    return {
        "ok": True,
        "received": len(products),
        "created": created,
        "task_id": body.task_id,
    }
