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
    骏合屋（Suruga-ya）平台适配器：保留统一平台接口，商品数据改由可插拔 DataSource 提供。

    官方公开搜索 API：待确认；入荷邮件不是关键词全站监控。status=unavailable。
    """

    code = "surugaya"

    def capability(self) -> PlatformCapability:
        from app.datasources import list_datasources_for_platform

        sources = list_datasources_for_platform(self.code)
        source_lines = [f"{s.id}: {s.status.value} — {s.summary}" for s in sources]
        return PlatformCapability(
            code=self.code,
            name="Suruga-ya",
            name_ja="駿河屋（骏合屋）",
            status="unavailable",
            data_source="可插拔数据源（官方 API 待确认 / 入荷邮件 / 用户提供）；当前不能关键词监控",
            capabilities=[],
            limitations=[
                "当前不能监控真实骏合屋关键词上新：没有已启用的可用搜索数据源",
                "不会绕过 403/WAF 或登录验证",
                "不会使用演示数据冒充真实结果",
                *source_lines,
            ],
            config_notes=(
                "请查看 /api/datasources。"
                "入荷お知らせ邮件仅覆盖入荷待ちリスト，不能替代关键词搜索。"
            ),
        )

    def make_external_id(self, raw: dict[str, Any]) -> str:
        if raw.get("product_id"):
            return str(raw["product_id"])
        link = str(raw.get("link") or raw.get("url") or "")
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
            url=str(raw.get("link") or raw.get("url") or ""),
            price=price_f,
            currency="JPY",
            image_url=raw.get("image") or raw.get("image_url"),
            condition=raw.get("condition"),
            raw=raw,
        )

    async def search(self, query: SearchQuery) -> SearchResult:
        raise NotImplementedError(
            "骏合屋平台适配器本身不直接抓取。请通过数据源获取商品。"
            "当前无 available 的关键词搜索数据源，不能监控。"
        )
