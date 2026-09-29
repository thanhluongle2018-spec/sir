from __future__ import annotations

from typing import Any

from app.platforms.base import (
    PlatformCapability,
    ProductItem,
    SearchQuery,
    SearchResult,
)


class StubAdapter:
    """Placeholder for platforms that cannot be stably accessed without accounts/bypass."""

    def __init__(
        self,
        code: str,
        name: str,
        name_ja: str,
        data_source: str,
        limitations: list[str],
        config_notes: str,
        status: str = "stub",
    ) -> None:
        self.code = code
        self._name = name
        self._name_ja = name_ja
        self._data_source = data_source
        self._limitations = limitations
        self._config_notes = config_notes
        self._status = status

    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code=self.code,
            name=self._name,
            name_ja=self._name_ja,
            status=self._status,
            data_source=self._data_source,
            capabilities=[],
            limitations=self._limitations,
            config_notes=self._config_notes,
        )

    def make_external_id(self, raw: dict[str, Any]) -> str:
        return str(raw.get("id") or "")

    def parse_item(self, raw: dict[str, Any]) -> ProductItem:
        return ProductItem(
            platform=self.code,
            external_id=self.make_external_id(raw),
            title=str(raw.get("title") or ""),
            url=str(raw.get("url") or ""),
            raw=raw,
        )

    async def search(self, query: SearchQuery) -> SearchResult:
        raise NotImplementedError(
            f"平台「{self._name_ja}」尚未提供允许的稳定公开数据源。"
            f"请参阅 README 接入说明后再启用。关键词={query.keywords}"
        )


def paypay_fleamarket_adapter() -> StubAdapter:
    return StubAdapter(
        code="paypay_fleamarket",
        name="PayPay Fleamarket",
        name_ja="PayPayフリマ（闪电市场）",
        data_source="无稳定公开官方搜索 API（页面多依赖客户端/登录态）",
        limitations=[
            "未实现：缺少允许使用的稳定公开接口",
            "不会实现绕过登录、验证码或客户端签名校验",
            "雅虎闲置业务已并入 PayPayフリマ，请勿重复配置",
        ],
        config_notes=(
            "接入思路：若平台日后提供开放 API 或官方合作接口，实现 search()/parse_item() 即可。"
            "可参考 backend/app/platforms/base.py 与 mercari.py。"
        ),
    )


def rakuma_adapter() -> StubAdapter:
    return StubAdapter(
        code="rakuma",
        name="Rakuma",
        name_ja="ラクマ（乐天二手）",
        data_source="无稳定公开官方搜索 API",
        limitations=[
            "未实现：公开网页搜索不稳定且常有反爬/登录限制",
            "不会抓取需登录或付费墙内容",
        ],
        config_notes="未来可在获得官方允许的数据源后替换本占位适配器。",
    )


def yahoo_fleamarket_adapter() -> StubAdapter:
    return StubAdapter(
        code="yahoo_fleamarket",
        name="Yahoo Fleamarket",
        name_ja="ヤフオク!フリマ / 雅虎闲置（历史）",
        data_source="业务已并入 PayPayフリマ，独立闲置站已不可用",
        limitations=[
            "占位：原雅虎闲置已迁移，请改用 paypay_fleamarket（待接入）或雅虎日拍",
        ],
        config_notes="保留枚举以便历史任务兼容；请勿期望返回商品。",
        status="stub",
    )
