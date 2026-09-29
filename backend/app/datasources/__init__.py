from __future__ import annotations

from typing import Dict

from app.datasources.base import DataSource, DataSourceCapability
from app.datasources.email_alert import mercari_email_alert, surugaya_email_alert
from app.datasources.official_api import mercari_official_api, surugaya_official_api
from app.datasources.user_provided import UserProvidedDataSource


def build_datasource_registry() -> Dict[str, DataSource]:
    sources: list[DataSource] = [
        mercari_official_api(),
        surugaya_official_api(),
        mercari_email_alert(),
        surugaya_email_alert(),
        UserProvidedDataSource(),
    ]
    return {s.id: s for s in sources}


_REGISTRY: Dict[str, DataSource] | None = None


def get_datasource_registry() -> Dict[str, DataSource]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = build_datasource_registry()
    return _REGISTRY


def get_datasource(source_id: str) -> DataSource:
    reg = get_datasource_registry()
    if source_id not in reg:
        raise KeyError(f"未知数据源: {source_id}")
    return reg[source_id]


def list_datasource_capabilities() -> list[DataSourceCapability]:
    return [s.capability() for s in get_datasource_registry().values()]


def list_datasources_for_platform(platform: str) -> list[DataSourceCapability]:
    return [
        c
        for c in list_datasource_capabilities()
        if c.platform in (platform, "multi")
    ]


def default_source_ids_for_platform(platform: str) -> list[str]:
    """任务未指定数据源时的默认尝试顺序（仍可能全部 unavailable）。"""
    mapping = {
        "mercari": ["mercari.official_api", "mercari.email_alert", "multi.user_provided"],
        "surugaya": [
            "surugaya.official_api",
            "surugaya.email_alert",
            "multi.user_provided",
        ],
    }
    return list(mapping.get(platform, []))
