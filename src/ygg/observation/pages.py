"""The fetch service for evidence pages (contract C4; decisions 0.5, 0.6, 1.8).

For a URL wanted as evidence at cutoff tau*:
  1. the Wayback CDX index is asked for the last 200 snapshot at or before tau* (the page as it was then);
  2. if none exists, the latest snapshot is used and marked live_after_cutoff (usable only in P_all);
  3. the raw page (the id_ form, without the Wayback toolbar) is archived in the blob store (D5) and every
     lookup is cached, so replays never call the network again;
  4. first_seen is inherited from Engine 1 when the canonical URL was already a broad record (0.6).
Targeted pages are a separate type and table (A1): they never enter Engine 2.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from ygg.store.blobs import BlobStore

UA = {"User-Agent": "yggdrasil-research/0.1 (+https://github.com/notPhani/Yggdrasil-Research)"}
_TAGS = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")


def html_to_text(raw: bytes) -> str:
    s = raw.decode("utf-8", "replace")
    s = _TAGS.sub(" ", s)
    s = re.sub(r"</(p|div|h[1-6]|li|br|title|article|section)>", "\n", s, flags=re.I)
    s = htmlmod.unescape(_TAG.sub(" ", s))
    return "\n".join(_WS.sub(" ", line).strip() for line in s.split("\n") if line.strip())


class PageFetcher:
    def __init__(self, data_dir: Path, pause_s: float = 1.0, max_bytes: int = 600_000):
        self.store = BlobStore(Path(data_dir) / "blobs")
        self.cache_path = Path(data_dir) / "pages" / "cache.json"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}
        self.pause, self.max_bytes = pause_s, max_bytes

    def _get(self, url: str, timeout: float = 40.0) -> bytes:
        time.sleep(self.pause)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(self.max_bytes)

    def _snapshot(self, url: str, before: str) -> tuple[str | None, bool]:
        q = urllib.parse.urlencode({"url": url, "to": before, "output": "json", "filter": "statuscode:200", "limit": "-1",
                                    "fl": "timestamp"})
        try:
            rows = json.loads(self._get(f"https://web.archive.org/cdx/search/cdx?{q}") or b"[]")
            if len(rows) > 1:
                return rows[-1][0], True
            q2 = urllib.parse.urlencode({"url": url, "output": "json", "filter": "statuscode:200", "limit": "1", "fl": "timestamp"})
            rows = json.loads(self._get(f"https://web.archive.org/cdx/search/cdx?{q2}") or b"[]")
            if len(rows) > 1:
                return rows[1][0], False
        except Exception:
            pass
        return None, False

    def fetch(self, url: str, tau_star: str) -> dict:
        """tau_star as YYYYMMDDhhmmss. Returns {ok, snapshot, before_cutoff, sha256, text_sha256}."""
        key = f"{url}|{tau_star}"
        if key in self.cache:
            return self.cache[key]
        ts, before = self._snapshot(url, tau_star)
        rec = {"url": url, "ok": False, "snapshot": ts, "before_cutoff": before, "sha256": None}
        if ts:
            try:
                raw = self._get(f"https://web.archive.org/web/{ts}id_/{url}")
                rec["sha256"] = self.store.put(raw, ".html")
                rec["ok"] = True
            except Exception as e:
                rec["error"] = repr(e)[:200]
        self.cache[key] = rec
        self.cache_path.write_text(json.dumps(self.cache, indent=0, sort_keys=True))
        return rec

    def text(self, rec: dict) -> str:
        return html_to_text(self.store.get(rec["sha256"], ".html")) if rec.get("ok") else ""
