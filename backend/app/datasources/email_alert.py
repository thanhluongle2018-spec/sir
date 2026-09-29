from __future__ import annotations

"""
官方邮件提醒数据源（评估与脚手架）。

煤炉：官方提供「保存した検索条件の新着」邮件/推送/LINE 通知（有帮助中心依据）。
骏合屋：官方提供「入荷お知らせメール」（针对入荷待ちリスト的到货提醒，不是关键词全站监控）。

实现原则：
- 仅通过用户 OAuth 授权读取邮箱（Gmail / Microsoft Graph 等），不读取、不保存邮箱密码
- 复用现有关键词匹配、去重与通知推送
- 在 OAuth 客户端与用户授权未配置前，状态为 unavailable，不伪造邮件解析结果
"""


import re
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse

from app.config import get_settings
from app.datasources.base import (
    DataSourceCapability,
    DataSourceKind,
    DataSourceStatus,
)
from app.platforms.base import ProductItem, SearchQuery, SearchResult


class EmailAlertDataSource:
    def __init__(
        self,
        *,
        source_id: str,
        platform: str,
        name_zh: str,
        research_notes: list[str],
        requirements: list[str],
        limitations: list[str],
        references: list[str],
        summary: str,
        sender_hints: list[str],
        subject_hints: list[str],
        url_patterns: list[str],
    ) -> None:
        self.id = source_id
        self.platform = platform
        self.sender_hints = sender_hints
        self.subject_hints = subject_hints
        self.url_patterns = [re.compile(p) for p in url_patterns]
        self._name_zh = name_zh
        self._summary = summary
        self._research_notes = research_notes
        self._requirements = requirements
        self._limitations = limitations
        self._references = references

    def capability(self) -> DataSourceCapability:
        settings = get_settings()
        oauth_ready = bool(
            (settings.email_oauth_client_id or "").strip()
            and (settings.email_oauth_client_secret or "").strip()
            and (settings.email_oauth_provider or "").strip()
        )
        summary = self._summary
        if oauth_ready:
            summary += "（已检测到 OAuth 环境变量，但仍需用户完成授权并验证邮件模板解析后才能启用）"
        else:
            summary += "（未配置邮箱 OAuth，当前不能读取邮件）"
        return DataSourceCapability(
            id=self.id,
            platform=self.platform,
            kind=DataSourceKind.email_alert,
            name=f"{self.platform} email alerts",
            name_zh=self._name_zh,
            status=DataSourceStatus.unavailable,
            summary=summary,
            research_notes=self._research_notes,
            requirements=self._requirements,
            limitations=self._limitations,
            references=self._references,
        )

    async def fetch(
        self,
        query: SearchQuery,
        *,
        credentials: Optional[dict[str, Any]] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> SearchResult:
        """
        credentials 期望字段（OAuth，绝非密码）：
          - refresh_token / access_token（由用户授权流程写入，加密存储）
          - mailbox（可选，邮箱地址仅作标识）
        """
        creds = credentials or {}
        if creds.get("password") or creds.get("smtp_password") or creds.get("imap_password"):
            raise ValueError("禁止使用邮箱密码。请使用 OAuth 授权（refresh_token）。")

        if not creds.get("refresh_token") and not creds.get("access_token"):
            raise NotImplementedError(
                f"数据源 {self.id} 需要用户 OAuth 授权后的 token，当前未配置。"
                "不会读取或保存邮箱密码，也不会伪造邮件结果。"
            )

        raise NotImplementedError(
            f"数据源 {self.id} 的邮箱读取与模板解析尚未完成生产验证。"
            "架构已预留 OAuth token 路径；请勿使用密码登录 IMAP。"
        )

    def parse_email_to_items(
        self,
        *,
        subject: str,
        body_text: str,
        body_html: str = "",
        message_id: str = "",
        received_at: Optional[datetime] = None,
    ) -> list[ProductItem]:
        """从单封提醒邮件中提取商品链接（启发式，需真实样本校准）。"""
        text = f"{subject}\n{body_text}\n{body_html}"
        urls = re.findall(r"https?://[^\s\"'<>]+", text)
        items: list[ProductItem] = []
        seen: set[str] = set()
        for url in urls:
            url = url.rstrip(").,]>\"'")
            if not any(p.search(url) for p in self.url_patterns):
                continue
            external_id = self._id_from_url(url)
            if not external_id or external_id in seen:
                continue
            seen.add(external_id)
            items.append(
                ProductItem(
                    platform=self.platform,
                    external_id=external_id,
                    title=subject.strip() or f"{self.platform} alert {external_id}",
                    url=url,
                    published_at=received_at,
                    raw={
                        "source": self.id,
                        "message_id": message_id,
                        "subject": subject,
                    },
                )
            )
        return items

    def _id_from_url(self, url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        if not path:
            return ""
        return path.split("/")[-1]


def mercari_email_alert() -> EmailAlertDataSource:
    return EmailAlertDataSource(
        source_id="mercari.email_alert",
        platform="mercari",
        name_zh="煤炉官方「保存搜索」新着邮件",
        summary="煤炉官方支持保存搜索条件的新着邮件提醒；本工具可经用户 OAuth 读取该类邮件（尚未启用）",
        research_notes=[
            "官方帮助中心确认：可对「保存した検索条件の新着」开启邮件通知（频率如 1 日 2 回等）。",
            "这是平台官方提醒渠道，不是抓取网站。",
            "接入方式评估：用户将煤炉提醒发到自己的邮箱，再通过 Gmail/Microsoft OAuth "
            "授权本工具只读相关邮件；禁止保存邮箱密码。",
            "邮件 HTML/文案模板可能变更，解析器需用真实样本校准后才能标为 available。",
        ],
        requirements=[
            "配置 EMAIL_OAUTH_PROVIDER / CLIENT_ID / CLIENT_SECRET",
            "用户完成 OAuth 授权并仅授予只读邮件权限",
            "用户在煤炉 App 中开启「保存した検索条件の新着」邮件通知",
            "使用真实提醒邮件样本完成解析校验",
        ],
        limitations=[
            "当前未启用，不会读取邮箱",
            "邮件频率由煤炉决定，可能低于实时监控预期",
            "不解析或存储与监控无关的私人邮件内容（实现时应按发件人/主题过滤）",
        ],
        references=[
            "https://help.jp.mercari.com/guide/articles/239/",
            "https://jp-news.mercari.com/info/40559",
        ],
        sender_hints=["mercari", "メルカリ"],
        subject_hints=["検索", "新着", "保存"],
        url_patterns=[
            r"https?://(?:jp\.)?mercari\.com/item/[A-Za-z0-9]+",
            r"https?://(?:www\.)?mercari\.com/.*/item/[A-Za-z0-9]+",
        ],
    )


def surugaya_email_alert() -> EmailAlertDataSource:
    return EmailAlertDataSource(
        source_id="surugaya.email_alert",
        platform="surugaya",
        name_zh="骏合屋官方「入荷お知らせ」邮件",
        summary="骏合屋官方提供入荷待ちリスト到货邮件；适用于已登记缺货商品，不是关键词全站监控",
        research_notes=[
            "官方マイページ说明：将品切れ商品加入入荷待ちリスト后，可收到入荷お知らせメール。",
            "该能力覆盖「指定商品到货」，与「任意关键词上新」模型不同，仅作可选补充数据源。",
            "是否允许第三方工具代读此类邮件：待确认（需用户自身邮箱授权，且遵守邮件服务 ToS）。",
        ],
        requirements=[
            "用户 OAuth 授权只读邮箱（不存密码）",
            "用户在骏合屋登记入荷待ち并开启入荷お知らせメール",
            "确认邮件模板与发件人后完成解析校验",
        ],
        limitations=[
            "不能替代关键词搜索监控",
            "当前未启用",
            "合规代读范围：待确认",
        ],
        references=[
            "https://www.suruga-ya.jp/man/rule/mypage.html",
        ],
        sender_hints=["suruga-ya", "駿河屋"],
        subject_hints=["入荷", "お知らせ"],
        url_patterns=[
            r"https?://(?:www\.)?suruga-ya\.jp/product/[^\s\"'<>]+",
        ],
    )
