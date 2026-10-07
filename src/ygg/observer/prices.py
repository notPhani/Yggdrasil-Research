"""Daily prices from the Yahoo chart API (decision 2.1). Every raw response is archived on first fetch (D5).

Stored in integer 1e-4 $ units (2.7a), plus a corporate-actions table. Yahoo's chart quotes are
split-adjusted at the source, so the stored bars are split-adjusted, not raw. Dividends are adjusted by us
from the action table, never via Yahoo's retroactively recomputed adjclose.
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ygg.store.blobs import BlobStore

CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={p1}&period2={p2}&interval=1d&events=div%2Csplits&includeAdjustedClose=true"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) yggdrasil-research/0.1"}
PRICE_SCHEMA = pa.schema([("symbol", pa.string()), ("date", pa.string()), ("open", pa.int64()), ("high", pa.int64()),
                          ("low", pa.int64()), ("close", pa.int64()), ("volume", pa.int64()), ("raw_ref", pa.string())])
ACTION_SCHEMA = pa.schema([("symbol", pa.string()), ("date", pa.string()), ("kind", pa.string()), ("value", pa.float64())])


def _unix(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def fetch_symbol(sym: str, start: str, end: str, store: BlobStore, ledger: dict, retries: int = 4) -> str:
    key = f"{sym}|{start}|{end}"
    if key in ledger and store.has(ledger[key], ".json"):
        return ledger[key]
    url = CHART.format(sym=sym, p1=_unix(start), p2=_unix(end))
    for attempt in range(retries):
        try:
            body = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
            json.loads(body)["chart"]["result"][0]
            sha = store.put(body, ".json")
            ledger[key] = sha
            return sha
        except Exception:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"price fetch failed for {sym}")


def parse_chart(sym: str, body: bytes, raw_ref: str) -> tuple[list[dict], list[dict]]:
    r = json.loads(body)["chart"]["result"][0]
    ts = r.get("timestamp") or []
    q = r["indicators"]["quote"][0]
    exch_off = r["meta"].get("gmtoffset", 0)
    rows = []
    for i, t in enumerate(ts):
        o, h, l, c, v = (q[k][i] for k in ("open", "high", "low", "close", "volume"))
        if None in (o, h, l, c):
            continue
        day = datetime.fromtimestamp(t + exch_off, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append({"symbol": sym, "date": day, "open": round(o * 1e4), "high": round(h * 1e4), "low": round(l * 1e4),
                     "close": round(c * 1e4), "volume": int(v or 0), "raw_ref": raw_ref})
    acts = []
    ev = r.get("events") or {}
    for d in (ev.get("dividends") or {}).values():
        acts.append({"symbol": sym, "date": datetime.fromtimestamp(d["date"] + exch_off, tz=timezone.utc).strftime("%Y-%m-%d"),
                     "kind": "dividend", "value": float(d["amount"])})
    for s in (ev.get("splits") or {}).values():
        acts.append({"symbol": sym, "date": datetime.fromtimestamp(s["date"] + exch_off, tz=timezone.utc).strftime("%Y-%m-%d"),
                     "kind": "split", "value": float(s["numerator"]) / float(s["denominator"])})
    return rows, acts


def fetch_universe(data_dir: Path, symbols: list[str], start: str, end: str, log=print) -> tuple[pa.Table, pa.Table]:
    store = BlobStore(Path(data_dir) / "blobs")
    ledger_path = Path(data_dir) / "prices" / "ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    rows, acts, failed = [], [], []
    for i, sym in enumerate(symbols):
        try:
            sha = fetch_symbol(sym, start, end, store, ledger)
        except RuntimeError:
            failed.append(sym)
            continue
        ledger_path.write_text(json.dumps(ledger, indent=0, sort_keys=True))
        r, a = parse_chart(sym, store.get(sha, ".json"), sha)
        rows += r
        acts += a
        if (i + 1) % 25 == 0:
            log(f"prices {i + 1}/{len(symbols)}")
    prices = pa.Table.from_pylist(sorted(rows, key=lambda x: (x["symbol"], x["date"])), schema=PRICE_SCHEMA)
    actions = pa.Table.from_pylist(sorted(acts, key=lambda x: (x["symbol"], x["date"], x["kind"])), schema=ACTION_SCHEMA)
    pq.write_table(prices, Path(data_dir) / "prices" / "daily.parquet", compression="zstd")
    pq.write_table(actions, Path(data_dir) / "prices" / "actions.parquet", compression="zstd")
    if failed:
        log(f"price fetch failed for {failed}")
    return prices, actions


def adjusted_closes(dates: list[str], close: np.ndarray, actions: list[dict]) -> np.ndarray:
    """Back-adjust closes for cash dividends (CRSP-style factors) from our own action table.

    Yahoo's chart quotes arrive already split-adjusted (NVDA's 10:1 split of 2024-06-10 is not visible in
    the raw closes), so splits are recorded in the action table but must not be applied a second time.
    The archive (D5) freezes these values, so a later split can never rewrite a replay.
    """
    adj = close.astype(np.float64).copy()
    idx = {d: i for i, d in enumerate(dates)}
    for a in sorted(actions, key=lambda x: x["date"]):
        i = idx.get(a["date"])
        if i is None or i == 0:
            continue
        if a["kind"] == "dividend":
            prev = close[i - 1]
            if prev > 0:
                adj[:i] *= 1.0 - (a["value"] * 1e4) / prev
    return adj
