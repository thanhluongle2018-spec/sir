from __future__ import annotations

from typing import Any, Optional

from app.datasources.base import (
    DataSourceCapability,
    DataSourceKind,
    DataSourceStatus,
    SearchQuery,
    SearchResult,
)


class OfficialApiDataSource:
    """
    平台官方 / 合作 API 数据源占位。

    当前煤炉 C2C 无面向个人监控的公开搜索 API；骏合屋亦无公开搜索 API。
    不实现任何绕过访问控制的抓取。
    """

    def __init__(
        self,
        *,
        source_id: str,
        platform: str,
        name: str,
        name_zh: str,
        status: DataSourceStatus,
        summary: str,
        research_notes: list[str],
        requirements: list[str],
        limitations: list[str],
        references: list[str],
    ) -> None:
        self.id = source_id
        self._cap = DataSourceCapability(
            id=source_id,
            platform=platform,
            kind=DataSourceKind.official_api,
            name=name,
            name_zh=name_zh,
            status=status,
            summary=summary,
            research_notes=research_notes,
            requirements=requirements,
            limitations=limitations,
            references=references,
        )

    def capability(self) -> DataSourceCapability:
        return self._cap

    async def fetch(
        self,
        query: SearchQuery,
        *,
        credentials: Optional[dict[str, Any]] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> SearchResult:
        raise NotImplementedError(
            f"数据源 {self.id} 尚未可用：{self._cap.summary}。"
            "不会伪造商品结果。"
        )


def mercari_official_api() -> OfficialApiDataSource:
    return OfficialApiDataSource(
        source_id="mercari.official_api",
        platform="mercari",
        name="Mercari Official / Partner API",
        name_zh="煤炉官方/合作 API",
        status=DataSourceStatus.unavailable,
        summary="jp.mercari.com C2C 暂无面向个人监控的公开搜索 API",
        research_notes=[
            "公开资料表明 Mercari Japan C2C 市场不提供面向外部开发者的通用公开搜索 API。",
            "「メルカリShops API」为店铺卖家的商品/库存/订单 GraphQL API，需店铺与合作合同，"
            "用途是卖家运营而非 C2C 全站关键词监控，不能当作本工具的商品搜索源。",
            "第三方「非官方封装 API」不属于官方或已授权数据服务，本项目不接入。",
        ],
        requirements=[
            "若未来官方开放 C2C 搜索 API，或签署允许「关键词监控」用途的合作协议并取得凭证，"
            "再在本数据源实现 fetch()。",
        ],
        limitations=[
            "当前不可用；不会调用非官方接口绕过 401/Cloudflare。",
        ],
        references=[
            "https://engineering.mercari.com/blog/entry/20221121-mercari-shops-api/",
            "https://api.mercari-shops.com/docs/index.html",
            "https://support.mercari-shops.com/hc/ja/categories/15261095776281",
        ],
    )


def surugaya_official_api() -> OfficialApiDataSource:
    return OfficialApiDataSource(
        source_id="surugaya.official_api",
        platform="surugaya",
        name="Suruga-ya Official API",
        name_zh="骏合屋官方 API",
        status=DataSourceStatus.pending_confirmation,
        summary="未检索到面向第三方的公开商品搜索 API 文档（待确认）",
        research_notes=[
            "官网公开资料可见「入荷お知らせメール」「速報」等用户功能，未见对外开放的商品搜索 API。",
            "在获得官方文档或商务授权前，标为「待确认」，不声称已支持或可抓取。",
        ],
        requirements=[
            "需要骏合屋官方开放 API 文档与授权用途说明，或经授权的数据服务合同。",
        ],
        limitations=[
            "当前不实现 HTML 抓取；公开搜索页在云出口常返回 403。",
        ],
        references=[
            "https://www.suruga-ya.jp/man/rule/mypage.html",
        ],
    )
