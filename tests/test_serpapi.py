import hashlib
import json
from pathlib import Path
from ygg.observation.serpapi import SerpApiGroundedFetcher, SerpNewsItem

def test_serpapi_cache_read(tmp_path):
    fetcher = SerpApiGroundedFetcher(tmp_path)
    query = "DeepSeek Nvidia AI"
    
    # Pre-populate cache directly
    key = hashlib.sha256(f"{query}::3".encode()).hexdigest()
    cache_file = tmp_path / f"{key}.json"
    cache_file.write_text(json.dumps([{
        "title": "DeepSeek R1 Shakes AI Chip Market",
        "link": "https://example.com/deepseek",
        "source": "Reuters",
        "date": "2025-01-27",
        "snippet": "Nvidia shares dropped sharply following DeepSeek announcement."
    }]), encoding="utf-8")
    
    results = fetcher.search_news(query, limit=3)
    assert len(results) == 1
    assert results[0].title == "DeepSeek R1 Shakes AI Chip Market"
    assert results[0].source == "Reuters"
