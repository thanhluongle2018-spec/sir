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
    Mercari (煤炉 / メルカリ) adapter.

    Current access status (2026-09):
    - Unofficial `api.mercari.jp/v2/entities:search` returns HTTP 401 without client auth.
    - Public HTML search is behind Cloudflare / edge protection.
    - This project does NOT bypass login, captcha, or access controls.

    Therefore the adapter is shipped as a **stub** with parsing helpers retained so
    maintainers can re-enable search() when an allowed official/partner API exists.
    """

    code = "mercari"
    # Historical endpoint kept for documentation / future wiring only.
    SEARCH_URL = "https://api.mercari.jp/v2/entities:search"

    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code=self.code,
            name="Mercari",
            name_ja="メルカリ（煤炉）",
            status="stub",
            data_source=(
                "暂无允许稳定使用的公开数据源："
                "非官方 search API 现返回 401；公开搜索页受 Cloudflare 保护"
            ),
            capabilities=[],
            limitations=[
                "未实现稳定搜索：缺少允许使用的官方/合作接口",
                "不会绕过登录、验证码、Cloudflare 或其他访问控制",
                "不要求用户提供煤炉账号密码",
            ],
            config_notes=(
                "接入方法：若获得官方开放 API 或允许的合作数据源，在本文件实现 search()，"
                "复用 parse_item()/make_external_id()，并将 capability.status 改为 supported/partial。"
                "也可通过环境变量预留 MERCARI_API_BASE（未来版本）。"
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
            "煤炉（Mercari）当前无法通过允许的公开数据源稳定接入："
            "非官方 API 返回 401，公开网页受访问保护。"
            "请使用演示平台(demo)验证流程，或待官方开放接口后更新本适配器。"
            f"关键词={query.keywords}"
        )
