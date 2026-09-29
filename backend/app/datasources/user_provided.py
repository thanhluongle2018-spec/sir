from __future__ import annotations

"""
用户明确提供、且自述有权使用的数据接入。

典型场景：用户从自己有权访问的渠道导出/转发商品 JSON，POST 到本系统的受保护入库接口。
系统只做匹配、去重与通知聚合，不替用户抓取平台。
"""


from datetime import datetime, timezone
from typing import Any, Optional

from app.datasources.base import (
    DataSourceCapability,
    DataSourceKind,
    DataSourceStatus,
    items_to_result,
)
from app.platforms.base import ProductItem, SearchQuery, SearchResult


class UserProvidedDataSource:
    """拉取型 fetch 对用户投递数据通常为空；真正入库走 /api/ingest。"""

    id = "multi.user_provided"

    def capability(self) -> DataSourceCapability:
        return DataSourceCapability(
            id=self.id,
            platform="multi",
            kind=DataSourceKind.user_provided,
            name="User-provided ingest",
            name_zh="用户提供的数据入库",
            status=DataSourceStatus.available,
            summary="接受用户主动提交、且声明有权使用的商品 JSON；不主动抓取平台",
            research_notes=[
                "适用于用户已通过合法渠道获得的商品信息（例如自己的导出、自己的提醒转发解析结果）。",
                "调用方必须确认对数据具备使用权；本系统不验证平台侧授权范围。",
            ],
            requirements=[
                "请求头提供 INGEST_API_TOKEN（环境变量配置）",
                "每条商品包含 platform / external_id / title / url",
                "platform 须为本版本目标平台：mercari 或 surugaya",
            ],
            limitations=[
                "不会代替平台搜索；没有用户提交则不会产生新商品",
                "调用方对数据合法性负责",
            ],
            references=[],
        )

    async def fetch(
        self,
        query: SearchQuery,
        *,
        credentials: Optional[dict[str, Any]] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> SearchResult:
        # 用户投递是推模式；调度器拉取时返回空，避免伪造
        return items_to_result([], mode="pull_noop")


def parse_ingest_payload(payload: dict[str, Any]) -> list[ProductItem]:
    raw_items = payload.get("items") or []
    if not isinstance(raw_items, list):
        raise ValueError("items 必须是数组")
    out: list[ProductItem] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        platform = str(raw.get("platform") or "").strip()
        external_id = str(raw.get("external_id") or raw.get("id") or "").strip()
        title = str(raw.get("title") or "").strip()
        url = str(raw.get("url") or "").strip()
        if platform not in {"mercari", "surugaya"}:
            raise ValueError(f"不支持的 platform: {platform}")
        if not external_id or not title or not url:
            raise ValueError("每条商品需要 platform、external_id、title、url")
        price = raw.get("price")
        try:
            price_f = float(price) if price is not None else None
        except (TypeError, ValueError):
            price_f = None
        published_at = None
        if raw.get("published_at"):
            try:
                published_at = datetime.fromisoformat(
                    str(raw["published_at"]).replace("Z", "+00:00")
                )
            except ValueError:
                published_at = None
        out.append(
            ProductItem(
                platform=platform,
                external_id=external_id,
                title=title,
                url=url,
                price=price_f,
                currency=str(raw.get("currency") or "JPY"),
                image_url=raw.get("image_url"),
                seller=raw.get("seller"),
                condition=raw.get("condition"),
                category=raw.get("category"),
                brand=raw.get("brand"),
                published_at=published_at or datetime.now(timezone.utc),
                raw={**raw, "source": "user_provided"},
            )
        )
    return out
