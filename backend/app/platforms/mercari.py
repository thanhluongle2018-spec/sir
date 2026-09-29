from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.platforms.base import (
    PlatformCapability,
    ProductItem,
    SearchQuery,
    SearchResult,
)


class MercariAdapter:
    """
    煤炉（Mercari）平台适配器：保留统一平台接口，商品数据改由可插拔 DataSource 提供。

    当前无可用官方 C2C 搜索数据源；平台层 status=unavailable，界面应明确不能监控。
    """

    code = "mercari"

    def capability(self) -> PlatformCapability:
        from app.datasources import list_datasources_for_platform

        sources = list_datasources_for_platform(self.code)
        source_lines = [f"{s.id}: {s.status.value} — {s.summary}" for s in sources]
        return PlatformCapability(
            code=self.code,
            name="Mercari",
            name_ja="メルカリ（煤炉）",
            status="unavailable",
            data_source="可插拔数据源（官方 API / 邮件提醒 / 用户提供）；当前均未形成可监控链路",
            capabilities=[],
            limitations=[
                "当前不能监控真实煤炉商品：没有已启用的可用数据源",
                "不会绕过 401、Cloudflare、登录或验证码",
                "不会使用演示数据冒充真实结果",
                *source_lines,
            ],
            config_notes=(
                "请查看 /api/datasources 了解各数据源调研结论与接入条件。"
                "监控任务/去重/通知管道已就绪，待数据源 available 后即可生效。"
            ),
        )

    def make_external_id(self, raw: dict[str, Any]) -> str:
        return str(raw.get("id") or raw.get("productId") or "")

    def parse_item(self, raw: dict[str, Any]) -> ProductItem:
        item_id = self.make_external_id(raw)
        price = raw.get("price")
        try:
            price_f = float(price) if price is not None else None
        except (TypeError, ValueError):
            price_f = None
        return ProductItem(
            platform=self.code,
            external_id=item_id,
            title=str(raw.get("name") or raw.get("title") or ""),
            url=f"https://jp.mercari.com/item/{item_id}" if item_id else "https://jp.mercari.com/",
            price=price_f,
            currency="JPY",
            image_url=(raw.get("thumbnails") or [None])[0]
            if isinstance(raw.get("thumbnails"), list)
            else raw.get("image_url"),
            seller=(raw.get("seller") or {}).get("name")
            if isinstance(raw.get("seller"), dict)
            else raw.get("seller"),
            published_at=None,
            raw=raw,
        )

    async def search(self, query: SearchQuery) -> SearchResult:
        raise NotImplementedError(
            "煤炉平台适配器本身不直接抓取。请通过数据源（官方 API / 邮件 / 用户提供）获取商品。"
            "当前无 available 的煤炉搜索数据源，不能监控。"
        )


_ = (datetime, timezone)
