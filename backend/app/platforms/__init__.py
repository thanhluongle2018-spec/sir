from __future__ import annotations

"""
本版本目标平台：煤炉（Mercari）、骏合屋（Suruga-ya）。

历史平台代码（demo / yahoo_auctions 等）仅保留在 PlatformCode 枚举中，
以便读取旧数据库记录；产品注册表不再暴露它们。
"""

from typing import Dict

from app.platforms.base import PlatformAdapter, PlatformCapability

# Product-facing platforms for this MVP scope
MVP_PLATFORM_CODES = ("mercari", "surugaya")


def build_registry() -> Dict[str, PlatformAdapter]:
    # Lazy imports to avoid circular dependency with datasources
    from app.platforms.mercari import MercariAdapter
    from app.platforms.surugaya import SurugayaAdapter

    return {
        "mercari": MercariAdapter(),
        "surugaya": SurugayaAdapter(),
    }


_REGISTRY: Dict[str, PlatformAdapter] | None = None


def get_registry() -> Dict[str, PlatformAdapter]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = build_registry()
    return _REGISTRY


def get_adapter(code: str) -> PlatformAdapter:
    registry = get_registry()
    if code not in registry:
        raise KeyError(f"本版本未提供平台入口: {code}（仅支持煤炉/骏合屋）")
    return registry[code]


def list_capabilities() -> list[PlatformCapability]:
    return [get_registry()[code].capability() for code in MVP_PLATFORM_CODES]


def is_mvp_platform(code: str) -> bool:
    return code in MVP_PLATFORM_CODES
