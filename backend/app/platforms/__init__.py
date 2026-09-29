from __future__ import annotations

from typing import Dict

from app.config import get_settings
from app.platforms.base import PlatformAdapter, PlatformCapability
from app.platforms.demo import DemoAdapter
from app.platforms.mercari import MercariAdapter
from app.platforms.stubs import (
    paypay_fleamarket_adapter,
    rakuma_adapter,
    yahoo_fleamarket_adapter,
)
from app.platforms.surugaya import SurugayaAdapter
from app.platforms.yahoo_auctions import YahooAuctionsAdapter


def build_registry() -> Dict[str, PlatformAdapter]:
    registry: Dict[str, PlatformAdapter] = {
        "mercari": MercariAdapter(),
        "yahoo_auctions": YahooAuctionsAdapter(),
        "surugaya": SurugayaAdapter(),
        "paypay_fleamarket": paypay_fleamarket_adapter(),
        "rakuma": rakuma_adapter(),
        "yahoo_fleamarket": yahoo_fleamarket_adapter(),
    }
    if get_settings().enable_demo_platform:
        registry["demo"] = DemoAdapter()
    return registry


_REGISTRY: Dict[str, PlatformAdapter] | None = None


def get_registry() -> Dict[str, PlatformAdapter]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = build_registry()
    return _REGISTRY


def get_adapter(code: str) -> PlatformAdapter:
    registry = get_registry()
    if code not in registry:
        raise KeyError(f"未知平台: {code}")
    return registry[code]


def list_capabilities() -> list[PlatformCapability]:
    return [a.capability() for a in get_registry().values()]
