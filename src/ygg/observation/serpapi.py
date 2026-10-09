"""Trigger-gated Google News search via SerpApi with atomic disk cache."""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SerpNewsItem:
    title: str
    link: str
    source: str
    date: str
    snippet: str


class SerpApiGroundedFetcher:
    def __init__(self, cache_dir: Path, api_key: str | None = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key

    def search_news(self, query: str, limit: int = 5) -> list[SerpNewsItem]:
        """Search Google News with atomic disk caching."""
        cache_key = hashlib.sha256(f"{query}::{limit}".encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return [SerpNewsItem(**item) for item in data]

        if not self.api_key:
            return []  # Offline fallback

        url = "https://serpapi.com/search.json?" + urllib.parse.urlencode({
            "engine": "google_news",
            "q": query,
            "api_key": self.api_key,
            "num": limit,
        })

        req = urllib.request.Request(url, headers={"User-Agent": "Yggdrasil/0.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        items = []
        for r in payload.get("news_results", [])[:limit]:
            items.append(SerpNewsItem(
                title=r.get("title", ""),
                link=r.get("link", ""),
                source=r.get("source", {}).get("name", "Unknown"),
                date=r.get("date", ""),
                snippet=r.get("snippet", "")
            ))

        # Atomic write
        tmp = cache_file.with_suffix(".tmp")
        tmp.write_text(json.dumps([item.__dict__ for item in items], indent=1), encoding="utf-8")
        tmp.replace(cache_file)
        return items
