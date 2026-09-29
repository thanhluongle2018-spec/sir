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
    骏合屋（Suruga-ya / 駿河屋）独立适配器。

    接入核查结论：
    - 公开 HTML 搜索在多数云 / 数据中心出口返回 403
    - 无官方开放搜索 API
    - 本项目不绕过 WAF / 访问控制，也不要求用户提供站点账号密码

    因此本版本明确标记为「未接入」。保留 parse_item / make_external_id，
    待出现允许且稳定的数据源后再实现 search()。
    """

    code = "surugaya"

    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code=self.code,
            name="Suruga-ya",
            name_ja="駿河屋（骏合屋）",
            status="unavailable",
            data_source="暂无允许稳定使用的公开数据源（公开 HTML 常被 403）",
            capabilities=[],
            limitations=[
                "未接入：公开搜索在多数自动化出口返回 403",
                "不会绕过 WAF / 访问控制",
                "不会使用演示数据冒充真实商品",
            ],
            config_notes=(
                "后续接入条件：官方开放 API，或在合规前提下可稳定访问的允许数据源；"
                "届时在本文件实现 search() 并更新 status。"
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
            "骏合屋（駿河屋）尚未接入：暂无允许稳定使用的公开数据源"
            "（公开搜索常返回 403）。不会伪造抓取结果。"
            f"关键词={query.keywords}"
        )
