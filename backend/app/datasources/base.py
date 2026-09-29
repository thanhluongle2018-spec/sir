from __future__ import annotations

"""
可插拔数据源抽象。

监控系统（任务 / 匹配 / 去重 / 通知）与「商品从哪里来」解耦。
未来可接入：平台官方 API、经授权的第三方 API、用户有权使用的自有数据、
或用户授权后的官方邮件提醒（OAuth，不保存邮箱密码）。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Protocol

from app.platforms.base import ProductItem, SearchQuery, SearchResult


class DataSourceKind(str, Enum):
    official_api = "official_api"
    authorized_third_party = "authorized_third_party"
    user_provided = "user_provided"
    email_alert = "email_alert"


class DataSourceStatus(str, Enum):
    available = "available"  # 已实现且可运行
    unavailable = "unavailable"  # 明确当前不可用
    pending_confirmation = "pending_confirmation"  # 信息不足，待确认
    disabled = "disabled"  # 用户关闭或未配置


@dataclass
class DataSourceCapability:
    id: str
    platform: str  # mercari | surugaya | multi
    kind: DataSourceKind
    name: str
    name_zh: str
    status: DataSourceStatus
    summary: str
    research_notes: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


class DataSource(Protocol):
    """统一数据源接口：调度器只依赖 fetch / capability。"""

    id: str

    def capability(self) -> DataSourceCapability: ...

    async def fetch(
        self,
        query: SearchQuery,
        *,
        credentials: Optional[dict[str, Any]] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> SearchResult: ...


def items_to_result(items: list[ProductItem], **meta: Any) -> SearchResult:
    return SearchResult(items=items, has_more=False, raw_meta=dict(meta))
