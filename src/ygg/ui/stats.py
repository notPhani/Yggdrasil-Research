"""World-model statistics for the control panel, read from the replay's own per-day outputs (never recomputed).

The live world model is cold (no warmed live state), so the panel shows the recorded world model: the latest day
the replay engine has finished, labelled as such.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TopNarrative:
    nid: str
    label: str
    state: str
    mass_day: float
    series: list[float]          # attention per hour over the last 48 h
    bursts: int
    entities: list[str] = field(default_factory=list)


@dataclass
class WorldStats:
    day: str
    alive: int
    dormant: int
    total: int
    born_day: int
    kappa_s: float
    kappa_implied: float | None
    kappa0: float
    pi0: float
    price: float                 # current price of a narrative, nats (log alpha now)
    vol_term: float
    cap_term: float
    omega: float
    r: float
    roots_day: int
    copies_day: int
    none_share: float
    bursts_day: int
    burst_narratives: int
    edges_day: int
    bot_share: float | None
    top: list[TopNarrative]
    days_done: int


def world_stats(data_dir: Path, top_n: int = 8) -> WorldStats | None:
    root = Path(data_dir) / "tables"
    days = sorted(p.stem.split("=", 1)[1] for p in (root / "e2a_narratives").glob("day=*.json"))
    if not days:
        return None
    day = days[-1]
    d = json.loads((root / "e2a_narratives" / f"day={day}.json").read_text())
    diag = d.get("e2a_diag") or {}
    nar = {n["narrative_id"]: n for n in d.get("narratives", [])}
    import duckdb
    import pyarrow.parquet as pq

    led = pq.read_table(root / "e2a_ledger" / f"day={day}" / "part-0.parquet").to_pylist()
    roots = sum(r["roots"] for r in led)
    copies = sum(r["copies"] for r in led)
    none = sum(r["y0_255"] for r in led) / max(1, 255 * roots)
    con = duckdb.connect()
    series_paths = [(root / "e2b_series" / f"day={x}" / "part-0.parquet").as_posix() for x in days[-2:]
                    if (root / "e2b_series" / f"day={x}" / "part-0.parquet").exists()]
    top: list[TopNarrative] = []
    bursts = burst_n = 0
    if series_paths:
        rows = con.execute(f"SELECT narrative_id, \"window\", y, burst FROM read_parquet({series_paths})").fetchall()
        wmax = max(r[1] for r in rows) if rows else 0
        day_rows = [r for r in rows if r[1] > wmax - 96]
        bursts = sum(1 for r in day_rows if r[3])
        burst_n = len({r[0] for r in day_rows if r[3]})
        mass: dict[str, float] = {}
        for n, w, y, b in day_rows:
            mass[n] = mass.get(n, 0.0) + (y or 0.0)
        for n, m in sorted(mass.items(), key=lambda kv: -kv[1])[:top_n]:
            hourly = [0.0] * 48
            nb = 0
            for nn, w, y, b in rows:
                if nn == n and w > wmax - 192:
                    hourly[min(47, (w - (wmax - 191)) // 4)] += y or 0.0
                    nb += bool(b) and w > wmax - 96
            meta = nar.get(n, {})
            top.append(TopNarrative(n, meta.get("label", n), meta.get("state", "?"), m, hourly, nb, meta.get("top_entities", [])[:4]))
    edges, bot = 0, None
    ap = root / "e2b_alpha" / f"day={day}" / "part-0.parquet"
    if ap.exists():
        e, b, tot = con.execute(f"SELECT count(DISTINCT source || '>' || target), sum(CASE WHEN source = 'BOT' THEN alpha ELSE 0 END), sum(alpha) "
                                f"FROM read_parquet('{ap.as_posix()}')").fetchone()
        edges, bot = int(e or 0), (float(b) / float(tot) if tot else None)
    last_h = max((n.get("t_last_h", 0.0) for n in nar.values()), default=0.0)
    born = sum(1 for n in nar.values() if n.get("born_h", -1e9) > last_h - 24)
    return WorldStats(day, int(diag.get("alive", 0)), int(diag.get("dormant", 0)), len(nar), born, float(diag.get("kappa_s", 0.0)),
                      diag.get("kappa_implied_median"), float(diag.get("kappa0", 0.0)), float(diag.get("pi0", 0.0)),
                      float(diag.get("log_alpha_now", 0.0)), float(diag.get("vol_term", 0.0)), float(diag.get("cap_term", 0.0)),
                      float(d.get("omega") or 0.0), float(d.get("r") or 0.0), roots, copies, none, bursts, burst_n, edges, bot, top, len(days))
