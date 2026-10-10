"""Live adapter: the world at now - 15 minutes (GDELT's batch cadence) and 5-minute candles from Yahoo.

Live mode never invents state. Engine 1's live ingest runs here (the newest GKG batch, parsed with Engine 1's own
parser); the live world model is reported as COLD because Engine 2 has no warmed live state (it needs a 3-week
blind cold start), and no live trigger runs (the intraday Lee-Mykland test is outside the hackathon cut).
"""
from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ygg.ui.domain import Candle, FeedItem

UA = {"User-Agent": "Mozilla/5.0 (yggdrasil-research terminal)"}
LASTUPDATE = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval={iv}&includePrePost=true"
WATCH = ["BTC-USD", "ETH-USD", "NVDA", "AVGO", "TSM", "ASML", "MU", "AMD", "SMH", "XLK", "VST", "CEG", "NRG", "XLU", "MSFT", "GOOGL", "META", "SPY", "QQQ"]
DEMO_EXTRA = {"BTC-USD", "ETH-USD"}            # 24/7 instrument outside the equity universe, flagged in the UI


def _get(url: str, timeout: float = 20.0) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


@dataclass
class Batch:
    ts: datetime
    url: str
    status: str                     # OK / NOT_YET (listed but 404) / ERROR
    docs: int = 0
    error: str = ""


@dataclass
class LiveWorld:
    feed: list[FeedItem] = field(default_factory=list)
    batches: list[Batch] = field(default_factory=list)
    last_ok: datetime | None = None
    error: str = ""

    def poll(self) -> Batch | None:
        """Fetch the newest GKG batch once. A batch listed before it is served (measured: 404 for a while) is recorded
        as NOT_YET and retried on the next poll, never treated as an empty window."""
        try:
            lines = _get(LASTUPDATE).decode().strip().splitlines()
        except Exception as e:
            self.error = f"lastupdate: {e}"
            return None
        url = next((ln.split()[-1] for ln in lines if ln.endswith(".gkg.csv.zip")), None)
        if url is None:
            self.error = "lastupdate lists no GKG file"
            return None
        ts = datetime.strptime(url.rsplit("/", 1)[1][:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        blob = None
        for back in range(8):                       # newest listed batch first, then up to 7 before it (live lag varies)
            t = ts - timedelta(minutes=15 * back)
            if any(b.ts == t and b.status == "OK" for b in self.batches):
                return None
            u = url.rsplit("/", 1)[0] + "/" + t.strftime("%Y%m%d%H%M%S") + ".gkg.csv.zip"
            try:
                blob = _get(u, timeout=60)
                ts, url = t, u
                break
            except Exception as e:
                if not any(b.ts == t for b in self.batches):
                    self.batches.append(Batch(t, u, "NOT_YET" if "404" in str(e) else "ERROR", error=str(e)[:80]))
        if blob is None:
            return self.batches[-1] if self.batches else None
        from ygg.observation.parse import parse_gkg

        docs, _ = parse_gkg(blob)
        rows = docs.select(["source_name", "title", "record_id"]).to_pylist()
        items = [FeedItem(ts, r["source_name"] or "?", (r["title"] or "").strip(), r["record_id"]) for r in rows if r["title"]]
        self.feed = (items + self.feed)[:2000]
        b = Batch(ts, url, "OK", len(rows))
        self.batches.append(b)
        self.last_ok, self.error = ts, ""
        return b


@dataclass
class Quote:
    symbol: str
    candles: list[Candle]
    last: float | None
    prev_close: float | None
    state: str                      # OPEN / CLOSED / UNAVAILABLE
    error: str = ""
    fetched: float = 0.0

    @property
    def change(self) -> float | None:
        if self.last is None or not self.prev_close:
            return None
        return self.last / self.prev_close - 1.0


def quote(sym: str, rng: str = "1d", iv: str = "1m") -> Quote:
    """1-minute bars (Yahoo keeps 7 days of them); for a closed market the last session's bars are returned."""
    try:
        j = json.loads(_get(CHART.format(sym=sym, rng=rng, iv=iv)))
        r = j["chart"]["result"][0]
        ts = r.get("timestamp") or []
        q = r["indicators"]["quote"][0]
        cs = [Candle(datetime.fromtimestamp(t, tz=timezone.utc), o, h, l, c, v or 0.0)
              for t, o, h, l, c, v in zip(ts, q["open"], q["high"], q["low"], q["close"], q["volume"])
              if None not in (o, h, l, c)]
        meta = r.get("meta", {})
        last = cs[-1].c if cs else meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        fresh = bool(cs) and datetime.now(timezone.utc) - cs[-1].t < timedelta(minutes=10)
        return Quote(sym, cs, last, prev, "OPEN" if fresh else "CLOSED", fetched=time.time())
    except Exception as e:
        return Quote(sym, [], None, None, "UNAVAILABLE", str(e)[:80], time.time())


def world_clock(now: datetime | None = None) -> datetime:
    """Live world time: GDELT publishes 15-minute batches, so the world is observed at now - 15 min."""
    return (now or datetime.now(timezone.utc)) - timedelta(minutes=15)


def params(q: "Quote") -> dict:
    """Descriptive statistics of the bars on screen (not the trigger): session OHLC, VWAP, realized volatility of
    1-minute log returns, and robust z-scores of the last return and the last volume against the bars shown."""
    import math
    import statistics

    cs = q.candles
    if len(cs) < 5:
        return {}
    day = [c for c in cs if c.t.date() == cs[-1].t.date()] or cs
    vol = sum(c.v for c in day)
    vwap = sum((c.h + c.l + c.c) / 3 * c.v for c in day) / vol if vol else None
    rets = [math.log(b.c / a.c) for a, b in zip(cs, cs[1:]) if a.c > 0 and b.c > 0]
    def rz(xs, x):
        med = statistics.median(xs)
        mad = statistics.median(abs(v - med) for v in xs) or 1e-12
        return 0.6745 * (x - med) / mad
    vols = [c.v for c in cs[:-1] if c.v > 0]
    return {"open": day[0].o, "high": max(c.h for c in day), "low": min(c.l for c in day), "vwap": vwap, "volume": vol,
            "bars": len(day), "rv_ann": statistics.pstdev(rets) * math.sqrt(525600) if len(rets) > 2 else None,
            "z_ret": rz(rets[:-1], rets[-1]) if len(rets) > 10 else None,
            "z_vol": rz(vols, cs[-1].v) if len(vols) > 10 and cs[-1].v > 0 else None,
            "first": cs[0].t, "last": cs[-1].t}
