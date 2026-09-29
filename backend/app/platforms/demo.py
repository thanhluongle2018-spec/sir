from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime, timezone
from typing import Any

from app.platforms.base import (
    PlatformCapability,
    ProductItem,
    SearchQuery,
    SearchResult,
)


class DemoAdapter:
    """
    Offline demo platform that synthesizes items from keywords.
    Used to verify scheduling, dedupe, notifications, and UI without hitting real sites.
    """

    code = "demo"

    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code=self.code,
            name="Demo",
            name_ja="演示平台",
            status="supported",
            data_source="本地合成数据（不访问外网）",
            capabilities=[
                "keyword_search",
                "price_filter",
                "item_image",
                "seller",
            ],
            limitations=["仅用于联调与演示，不会出现真实可购商品"],
            config_notes="通过 ENABLE_DEMO_PLATFORM=true 启用（默认开启）。",
        )

    def make_external_id(self, raw: dict[str, Any]) -> str:
        return str(raw.get("id") or "")

    def parse_item(self, raw: dict[str, Any]) -> ProductItem:
        return ProductItem(
            platform=self.code,
            external_id=str(raw["id"]),
            title=str(raw["title"]),
            url=str(raw["url"]),
            price=float(raw["price"]),
            currency="JPY",
            image_url=raw.get("image_url"),
            seller=raw.get("seller"),
            condition=raw.get("condition"),
            published_at=datetime.fromtimestamp(raw["published_ts"], tz=timezone.utc),
            raw=raw,
        )

    async def search(self, query: SearchQuery) -> SearchResult:
        keyword = " / ".join(query.keywords) or "demo"
        # Bucket by minute so re-checks within the same minute mostly dedupe,
        # while a new minute yields fresh "new" items for notification testing.
        bucket = int(time.time() // 60)
        items: list[ProductItem] = []
        for i in range(3):
            seed = f"{keyword}|{bucket}|{i}"
            digest = hashlib.sha1(seed.encode()).hexdigest()
            rng = random.Random(digest)
            price = rng.randint(500, 80000)
            if query.min_price is not None and price < query.min_price:
                price = int(query.min_price) + rng.randint(0, 1000)
            if query.max_price is not None and price > query.max_price:
                price = max(int(query.min_price or 0), int(query.max_price) - rng.randint(0, 500))
            title = f"[DEMO] {keyword} サンプル商品 #{i + 1} ({bucket})"
            if query.match_mode == "all" and len(query.keywords) > 1:
                title = f"[DEMO] {' '.join(query.keywords)} #{i + 1}"
            for ex in query.exclude_keywords:
                if ex and ex.lower() in title.lower():
                    break
            else:
                raw = {
                    "id": digest[:12],
                    "title": title,
                    "url": f"https://example.local/demo/{digest[:12]}",
                    "price": price,
                    "image_url": f"https://picsum.photos/seed/{digest[:8]}/400/400",
                    "seller": f"demo_seller_{rng.randint(1, 99)}",
                    "condition": rng.choice(["new", "used_a", "used_b"]),
                    "published_ts": time.time() - rng.randint(0, 3600),
                }
                items.append(self.parse_item(raw))
        return SearchResult(items=items, has_more=False)
