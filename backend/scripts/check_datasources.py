"""Lightweight checks for pluggable datasources (no network bypass)."""

from __future__ import annotations

from app.datasources import list_datasource_capabilities
from app.datasources.email_alert import mercari_email_alert
from app.datasources.base import DataSourceStatus
from app.platforms import list_capabilities


def test_platform_cannot_monitor() -> None:
    caps = list_capabilities()
    assert {c.code for c in caps} == {"mercari", "surugaya"}
    for c in caps:
        assert c.status == "unavailable"


def test_datasource_statuses() -> None:
    caps = {c.id: c for c in list_datasource_capabilities()}
    assert caps["mercari.official_api"].status == DataSourceStatus.unavailable
    assert caps["surugaya.official_api"].status == DataSourceStatus.pending_confirmation
    assert caps["mercari.email_alert"].status == DataSourceStatus.unavailable
    assert caps["multi.user_provided"].status == DataSourceStatus.available


def test_email_parser_extracts_mercari_link() -> None:
    ds = mercari_email_alert()
    items = ds.parse_email_to_items(
        subject="保存した検索条件の新着",
        body_text="新着です https://jp.mercari.com/item/m123456789 をご確認ください",
        message_id="mid-1",
    )
    assert len(items) == 1
    assert items[0].external_id == "m123456789"
    assert items[0].platform == "mercari"


def test_email_fetch_rejects_password() -> None:
    import asyncio

    ds = mercari_email_alert()

    async def run() -> None:
        try:
            await ds.fetch(
                __import__("app.platforms.base", fromlist=["SearchQuery"]).SearchQuery(
                    keywords=["x"]
                ),
                credentials={"password": "secret"},
            )
            raise AssertionError("should reject password")
        except ValueError as exc:
            assert "禁止使用邮箱密码" in str(exc)

    asyncio.run(run())


if __name__ == "__main__":
    test_platform_cannot_monitor()
    test_datasource_statuses()
    test_email_parser_extracts_mercari_link()
    test_email_fetch_rejects_password()
    print("ok")
