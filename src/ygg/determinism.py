"""Determinism rules D1-D7. Every stage uses these helpers instead of clocks, ad hoc RNGs or ad hoc sums.

D1  no wall clock in replay: ingested_time = observed_time + lag
D2  every random draw comes from Philox keyed by (cfg_hash, record ids)
D3  floating-point reductions are order-independent (math.fsum) or run in a fixed order
D4  ties are broken by key(x) = (observed_time, source_rank, url_key, record_id)
D5  nondeterministic calls are archived (see ygg.store) and replayed from the archive
D6  artifacts are stamped with cfg_hash (see ygg.config)
D7  no stage reads an input timed after the window it computes; parameters fitted through day D-1 apply on day D
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

import numpy as np

UTC = timezone.utc


def parse_utc(text: str) -> datetime:
    """'YYYY-MM-DD', 'YYYYMMDDHHMMSS' or ISO 8601 -> aware UTC datetime."""
    if len(text) == 14 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    dt = datetime.fromisoformat(text)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


class WindowClock:
    """The replay clock: window t covers [t0 + t*delta, t0 + (t+1)*delta). Nothing here reads the wall clock (D1)."""

    def __init__(self, t0: datetime, delta_s: int = 900, ingest_lag_s: int = 900):
        if t0.tzinfo is None:
            raise ValueError("t0 must be timezone-aware UTC")
        self.t0, self.delta, self.lag = t0, timedelta(seconds=delta_s), timedelta(seconds=ingest_lag_s)

    def window_of(self, ts: datetime) -> int:
        return math.floor((ts - self.t0) / self.delta)

    def start(self, t: int) -> datetime:
        return self.t0 + t * self.delta

    def end(self, t: int) -> datetime:
        return self.t0 + (t + 1) * self.delta

    def ingested_time(self, observed_time: datetime) -> datetime:
        """D1: in replay, a record is ingested one lag after the batch that carried it."""
        return observed_time + self.lag

    def day_of(self, t: int) -> datetime:
        s = self.start(t)
        return datetime(s.year, s.month, s.day, tzinfo=UTC)

    def fit_cutoff(self, t: int) -> datetime:
        """D7: parameters used in window t were fitted on data strictly before the start of t's UTC day."""
        return self.day_of(t)


def keyed_rng(cfg_hash: str, *ids: str) -> np.random.Generator:
    """D2: a Philox generator whose 128-bit key is derived from the config hash and record ids."""
    digest = hashlib.sha256("\x1f".join((cfg_hash, *ids)).encode()).digest()
    key = int.from_bytes(digest[:16], "big")
    return np.random.Generator(np.random.Philox(key=key))


def exact_sum(values: Iterable[float]) -> float:
    """D3: correctly rounded sum, independent of iteration order."""
    return math.fsum(values)


def tie_key(observed_time: datetime, source_rank: int, url_key: str, record_id: str) -> tuple:
    """D4: the total order used for every tie in the system."""
    return (observed_time, source_rank, url_key, record_id)


def stable_hash(*parts: str | bytes) -> str:
    """sha256 over length-prefixed parts, so ('ab','c') and ('a','bc') never collide."""
    h = hashlib.sha256()
    for p in parts:
        b = p.encode() if isinstance(p, str) else p
        h.update(len(b).to_bytes(8, "big"))
        h.update(b)
    return h.hexdigest()
