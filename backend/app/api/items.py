from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Item, ItemDiscovery, PlatformCode
from app.schemas import ItemOut

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=list[ItemOut])
def list_items(
    q: Optional[str] = None,
    platform: Optional[PlatformCode] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_read: Optional[bool] = None,
    task_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ItemOut]:
    stmt = select(Item).order_by(Item.discovered_at.desc())
    if platform:
        stmt = stmt.where(Item.platform == platform)
    if min_price is not None:
        stmt = stmt.where(Item.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Item.price <= max_price)
    if is_read is not None:
        stmt = stmt.where(Item.is_read == is_read)
    if q:
        stmt = stmt.where(Item.title.contains(q))
    if task_id is not None:
        stmt = stmt.join(ItemDiscovery).where(ItemDiscovery.task_id == task_id)

    items = db.scalars(stmt.offset(offset).limit(limit)).unique().all()
    out: list[ItemOut] = []
    for item in items:
        discoveries = db.scalars(
            select(ItemDiscovery).where(ItemDiscovery.item_id == item.id)
        ).all()
        matched: list[str] = []
        task_ids: list[int] = []
        for d in discoveries:
            matched.extend(d.matched_keywords or [])
            task_ids.append(d.task_id)
        out.append(
            ItemOut(
                id=item.id,
                platform=item.platform,
                external_id=item.external_id,
                title=item.title,
                price=item.price,
                currency=item.currency,
                image_url=item.image_url,
                url=item.url,
                seller=item.seller,
                condition=item.condition,
                category=item.category,
                brand=item.brand,
                published_at=item.published_at,
                discovered_at=item.discovered_at,
                is_read=item.is_read,
                matched_keywords=list(dict.fromkeys(matched)),
                task_ids=task_ids,
            )
        )
    return out


@router.post("/{item_id}/read", response_model=ItemOut)
def mark_read(item_id: int, db: Session = Depends(get_db)) -> ItemOut:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "商品不存在")
    item.is_read = True
    db.commit()
    db.refresh(item)
    return ItemOut(
        id=item.id,
        platform=item.platform,
        external_id=item.external_id,
        title=item.title,
        price=item.price,
        currency=item.currency,
        image_url=item.image_url,
        url=item.url,
        seller=item.seller,
        condition=item.condition,
        category=item.category,
        brand=item.brand,
        published_at=item.published_at,
        discovered_at=item.discovered_at,
        is_read=item.is_read,
        matched_keywords=[],
        task_ids=[],
    )
