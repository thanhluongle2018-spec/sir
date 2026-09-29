from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol


@dataclass
class SearchQuery:
    keywords: list[str]
    exclude_keywords: list[str] = field(default_factory=list)
    match_mode: str = "any"
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    seller: Optional[str] = None
    condition: Optional[str] = None
    page: int = 1
    page_size: int = 30
    cursor: Optional[str] = None


@dataclass
class ProductItem:
    platform: str
    external_id: str
    title: str
    url: str
    price: Optional[float] = None
    currency: str = "JPY"
    image_url: Optional[str] = None
    seller: Optional[str] = None
    condition: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    published_at: Optional[datetime] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def stable_id(self) -> str:
        return f"{self.platform}:{self.external_id}"


@dataclass
class SearchResult:
    items: list[ProductItem]
    next_cursor: Optional[str] = None
    has_more: bool = False
    raw_meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformCapability:
    code: str
    name: str
    name_ja: str
    status: str  # supported | partial | stub
    data_source: str
    capabilities: list[str]
    limitations: list[str]
    config_notes: str


class PlatformAdapter(Protocol):
    code: str

    def capability(self) -> PlatformCapability: ...

    async def search(self, query: SearchQuery) -> SearchResult: ...

    def parse_item(self, raw: dict[str, Any]) -> ProductItem: ...

    def make_external_id(self, raw: dict[str, Any]) -> str: ...
