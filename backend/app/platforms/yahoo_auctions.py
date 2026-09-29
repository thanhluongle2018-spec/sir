from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus, urlencode

from bs4 import BeautifulSoup

from app.config import get_settings
from app.platforms.base import (
    PlatformCapability,
    ProductItem,
    SearchQuery,
    SearchResult,
)
from app.platforms.http_util import get_http_client, get_rate_limiter, get_semaphore


class YahooAuctionsAdapter:
    """
    Yahoo! Auctions (雅虎日拍 / ヤフオク!) via public HTML search results.

    Uses the publicly accessible search page only — no login, no captcha bypass,
    no official paid API keys required. HTML structure may change over time.
    """

    code = "yahoo_auctions"
    SEARCH_URL = "https://auctions.yahoo.co.jp/search/search"

    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code=self.code,
            name="Yahoo Auctions",
            name_ja="ヤフオク!（雅虎日拍）",
            status="partial",
            data_source="Public HTML search https://auctions.yahoo.co.jp/search/search",
            capabilities=[
                "keyword_search",
                "price_filter",
                "item_image",
                "item_link",
            ],
            limitations=[
                "依赖公开 HTML，页面改版需更新解析器",
                "卖家/成色等字段可能缺失",
                "官方 Web API 需开发者凭证且已收紧，本适配器不使用",
                "请控制请求频率，遵守站点条款",
            ],
            config_notes="无需平台账号。建议检查间隔 ≥ 60 秒。",
        )

    def make_external_id(self, raw: dict[str, Any]) -> str:
        if raw.get("auction_id"):
            return str(raw["auction_id"])
        link = str(raw.get("link") or "")
        m = re.search(r"/auction/([a-zA-Z0-9]+)", link)
        if m:
            return m.group(1)
        return link.rstrip("/").split("/")[-1]

    def parse_item(self, raw: dict[str, Any]) -> ProductItem:
        external_id = self.make_external_id(raw)
        price = raw.get("price")
        try:
            price_f = float(price) if price is not None else None
        except (TypeError, ValueError):
            price_f = None
        return ProductItem(
            platform=self.code,
            external_id=external_id,
            title=str(raw.get("title") or ""),
            url=str(raw.get("link") or f"https://auctions.yahoo.co.jp/jp/auction/{external_id}"),
            price=price_f,
            currency="JPY",
            image_url=raw.get("image"),
            seller=raw.get("seller"),
            published_at=None,
            raw=raw,
        )

    async def search(self, query: SearchQuery) -> SearchResult:
        keyword = " ".join(query.keywords)
        if query.brand:
            keyword = f"{keyword} {query.brand}".strip()
        if query.model:
            keyword = f"{keyword} {query.model}".strip()
        if not keyword:
            return SearchResult(items=[])

        params: dict[str, Any] = {
            "p": keyword,
            "va": keyword,
            "b": 1,
            "n": min(query.page_size, get_settings().max_items_per_search),
        }
        if query.min_price is not None:
            params["min"] = int(query.min_price)
        if query.max_price is not None:
            params["max"] = int(query.max_price)
        if query.exclude_keywords:
            params["ex"] = " ".join(query.exclude_keywords)

        await get_rate_limiter().wait(self.code)
        async with get_semaphore():
            client = await get_http_client()
            resp = await client.get(
                self.SEARCH_URL,
                params=params,
                headers={"Accept": "text/html,application/xhtml+xml"},
            )
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "lxml")
        items: list[ProductItem] = []
        seen: set[str] = set()
        for li in soup.select("li.Product"):
            title_a = li.select_one("a.Product__titleLink")
            if not title_a or not title_a.get("href"):
                continue
            href = title_a["href"]
            title = title_a.get_text(strip=True)
            if not title:
                continue
            price_el = li.select_one(
                ".Product__priceValue, .Product__price .u-textRed, .Product__price"
            )
            price = self._extract_price(price_el.get_text() if price_el else "")
            img_el = li.select_one("img")
            image = None
            if img_el:
                image = img_el.get("src") or img_el.get("data-src")
            raw = {
                "title": title,
                "link": href,
                "price": price,
                "image": image,
                "auction_id": self.make_external_id({"link": href}),
            }
            item = self.parse_item(raw)
            if item.external_id in seen:
                continue
            seen.add(item.external_id)
            if not self._match(item, query):
                continue
            items.append(item)
            if len(items) >= get_settings().max_items_per_search:
                break

        return SearchResult(items=items, has_more=False, raw_meta={"parsed": len(items)})

    def _extract_price(self, text: str) -> float | None:
        m = re.search(r"([0-9][0-9,]*)\s*円", text)
        if not m:
            m = re.search(r"([0-9][0-9,]*)", text.replace(",", ""))
            if not m:
                return None
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                return None
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            return None

    def _match(self, item: ProductItem, query: SearchQuery) -> bool:
        text = (item.title or "").lower()
        includes = [k.lower() for k in query.keywords if k]
        if includes:
            if query.match_mode == "all":
                if not all(k in text for k in includes):
                    return False
            elif not any(k in text for k in includes):
                return False
        for ex in query.exclude_keywords:
            if ex and ex.lower() in text:
                return False
        if query.min_price is not None and item.price is not None and item.price < query.min_price:
            return False
        if query.max_price is not None and item.price is not None and item.price > query.max_price:
            return False
        return True


_ = (datetime, quote_plus, urlencode)
