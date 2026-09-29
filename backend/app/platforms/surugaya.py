from __future__ import annotations

from typing import Any

from app.platforms.base import (
    PlatformCapability,
    ProductItem,
    SearchQuery,
    SearchResult,
)


class SurugayaAdapter:
    """
    Suruga-ya (骏合屋 / 駿河屋) adapter.

    Public HTML search frequently returns 403 from datacenter / cloud egress IPs
    and may require residential access. This project will not bypass that protection.
    Parsing helpers are retained for future enablement when an allowed source exists
    or when the site is reachable without circumventing controls.
    """

    code = "surugaya"
    SEARCH_URL = "https://www.suruga-ya.jp/search"

    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code=self.code,
            name="Suruga-ya",
            name_ja="駿河屋（骏合屋）",
            status="stub",
            data_source="公开 HTML 搜索在多数云出口返回 403；无官方开放搜索 API",
            capabilities=[],
            limitations=[
                "未实现稳定接入：站点对自动化出口常返回 403",
                "不会绕过 WAF / 访问控制",
                "页面结构变更时需单独维护解析器",
            ],
            config_notes=(
                "若你在可正常访问的网络环境中维护本项目，可参考历史 HTML 解析思路恢复 search()，"
                "并更新 capability.status。请遵守 robots 与服务条款，控制频率。"
            ),
        )

    def make_external_id(self, raw: dict[str, Any]) -> str:
        if raw.get("product_id"):
            return str(raw["product_id"])
        link = str(raw.get("link") or "")
        return link.rstrip("/").split("/")[-1] if link else ""

    def parse_item(self, raw: dict[str, Any]) -> ProductItem:
        external_id = self.make_external_id(raw)
        price = raw.get("price")
        try:
            price_f = float(price) if price is not None else None
        except (TypeError, ValueError):
            price_f = None
        return ProductItem(
            platform=self.code,
            external_id=external_id,
            title=str(raw.get("title") or ""),
            url=str(raw.get("link") or ""),
            price=price_f,
            currency="JPY",
            image_url=raw.get("image"),
            condition=raw.get("condition"),
            raw=raw,
        )

    async def search(self, query: SearchQuery) -> SearchResult:
        raise NotImplementedError(
            "骏合屋（駿河屋）当前无法从本部署环境通过允许方式稳定访问（公开搜索常返回 403）。"
            "不会绕过访问控制。请使用 demo / yahoo_auctions 验证流程。"
            f"关键词={query.keywords}"
        )
