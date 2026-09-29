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
    煤炉（Mercari / メルカリ）独立适配器。

    接入核查结论：
    - 非官方 search API（api.mercari.jp）当前返回 401，需客户端鉴权
    - 公开搜索页受 Cloudflare 等访问保护
    - 本项目不绕过登录、验证码、Cloudflare 或其他访问控制，也不要求用户提供煤炉账号密码

    因此本版本明确标记为「未接入」。保留 parse_item / make_external_id，
    待出现官方开放 API 或允许的合作数据源后再实现 search()。
    """

    code = "mercari"

    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code=self.code,
            name="Mercari",
            name_ja="メルカリ（煤炉）",
            status="unavailable",
            data_source="暂无允许稳定使用的公开数据源",
            capabilities=[],
            limitations=[
                "未接入：非官方 API 返回 401；公开网页受 Cloudflare 保护",
                "不会绕过登录、验证码、Cloudflare 或其他访问控制",
                "不会使用演示数据冒充真实商品",
            ],
            config_notes=(
                "后续接入条件：官方开放搜索 API，或平台明确允许的合作数据源；"
                "届时在本文件实现 search()，复用 parse_item()/make_external_id()，"
                "并将 status 更新为 supported/partial。"
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

        thumb = None
        thumbs = raw.get("thumbnails") or raw.get("photos") or []
        if isinstance(thumbs, list) and thumbs:
            first = thumbs[0]
            thumb = first if isinstance(first, str) else (first or {}).get("url")
        elif isinstance(raw.get("thumbnail"), str):
            thumb = raw["thumbnail"]

        seller = None
        seller_obj = raw.get("seller") or raw.get("shop") or {}
        if isinstance(seller_obj, dict):
            seller = seller_obj.get("name") or seller_obj.get("shopName")
        elif isinstance(seller_obj, str):
            seller = seller_obj

        created = raw.get("created") or raw.get("updated")
        published_at = None
        if created:
            try:
                published_at = datetime.fromtimestamp(int(created), tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                published_at = None

        return ProductItem(
            platform=self.code,
            external_id=item_id,
            title=str(raw.get("name") or raw.get("title") or ""),
            url=f"https://jp.mercari.com/item/{item_id}" if item_id else "https://jp.mercari.com/",
            price=price_f,
            currency="JPY",
            image_url=thumb,
            seller=seller,
            published_at=published_at,
            raw=raw,
        )

    async def search(self, query: SearchQuery) -> SearchResult:
        raise NotImplementedError(
            "煤炉（Mercari）尚未接入：暂无允许稳定使用的公开数据源"
            "（非官方 API 401 / 公开页受访问保护）。"
            "不会伪造抓取结果。后续需官方或允许的合作接口后再启用。"
            f"关键词={query.keywords}"
        )
