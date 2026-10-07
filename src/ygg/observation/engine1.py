"""Engine 1: raw GDELT batches -> canonical, exact-deduplicated, time-stamped observation tables.

Two stages:
  1. parse (parallel, pure): each raw blob -> a cached Parquet keyed by (parser version, blob sha256),
     with url_key computed once here.
  2. sequential pass (window loop, D4 order): exact-key dedup (L1: native_id, then url_key), the
     clocks, first_seen, the missing-batch flag (4.8) and day-partitioned output tables.

Semantic dedup (L2) plugs into the sequential pass, because merges must be decided in time order.
Engine 1 never interprets meaning and never filters by stock relevance.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ygg.contracts import OBSERVATION_SCHEMA
from ygg.determinism import WindowClock, parse_utc, stable_hash
from ygg.observation import embed as emb
from ygg.observation.canon import CANON_VERSION, url_key
from ygg.observation.dedup_l2 import L2Config, L2Dedup
from ygg.observation.gdelt_fetch import Ledger, load_manifest, plan
from ygg.observation.parse import PARSERS
from ygg.store.blobs import BlobStore

PARSE_VERSION = f"parse-1+{CANON_VERSION}"
WINDOW_LEDGER_SCHEMA = pa.schema([
    ("window", pa.int32()), ("batch_ts", pa.timestamp("us", tz="UTC")), ("gkg_status", pa.string()),
    ("export_status", pa.string()), ("mentions_status", pa.string()), ("missing_batch", pa.bool_()),
    ("rows", pa.int32()), ("new_objects", pa.int32()), ("l1_dups", pa.int32()), ("l2_merges", pa.int32()),
    ("roots", pa.int32()), ("quarantined", pa.int32()),
])
DUP_SCHEMA = pa.schema([("observation_id", pa.string()), ("canonical_id", pa.string()), ("matched_on", pa.string()),
                        ("window", pa.int32())])


# ---------------------------------------------------------------- stage 1: parse (pure, cached)
def parsed_path(data_dir: Path, kind: str, sha: str) -> Path:
    return data_dir / "parsed" / PARSE_VERSION / kind / sha[:2] / f"{sha}.parquet"


def _parse_job(args: tuple[str, str, str]) -> tuple[str, str, int, int]:
    data_dir, kind, sha = args
    out = parsed_path(Path(data_dir), kind, sha)
    if out.exists():
        return kind, sha, -1, -1
    tab, bad = PARSERS[kind](BlobStore(Path(data_dir) / "blobs").get(sha, ".zip"))
    col = "source_url" if kind == "export" else "url"
    tab = tab.append_column("url_key", pa.array([url_key(u) if u else "" for u in tab.column(col).to_pylist()], pa.string()))
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    pq.write_table(tab, tmp, compression="zstd")
    tmp.replace(out)
    if bad.num_rows:
        qp = out.with_suffix(".quarantine.parquet")
        pq.write_table(bad, qp)
    return kind, sha, tab.num_rows, bad.num_rows


# ---------------------------------------------------------------- stage 2: sequential pass
class Engine1:
    def __init__(self, data_dir: Path, clock: WindowClock, fetch_status: dict[tuple[str, str], tuple[str, str]],
                 l2: L2Config | None = None, embed_model: str | None = emb.DEFAULT_MODEL):
        self.data_dir, self.clock, self.fetch_status = data_dir, clock, fetch_status
        self.l2 = L2Dedup(l2 or L2Config())
        self.embed_model = embed_model
        self.day_vecs: dict[str, list] = defaultdict(list)
        self.tables = data_dir / "tables"
        self.by_native: dict[str, str] = {}
        self.by_url: dict[bytes, str] = {}
        self.day_rows: dict[str, list] = defaultdict(list)
        self.current_day: str | None = None

    def _status(self, ts: str, kind: str) -> tuple[str, str]:
        return self.fetch_status.get((ts, kind), ("absent", ""))

    def step(self, t: int) -> tuple[list[dict], dict]:
        start = self.clock.start(t)
        ts = start.strftime("%Y%m%d%H%M%S")
        day = start.strftime("%Y-%m-%d")
        if self.current_day and day != self.current_day:
            self.flush_day(self.current_day)
        self.current_day = day
        observed = start
        ingested = self.clock.ingested_time(observed)
        gkg_status, gkg_sha = self._status(ts, "gkg")
        new, dups, rows_n, quar = [], [], 0, 0
        if gkg_status == "ok":
            path = parsed_path(self.data_dir, "gkg", gkg_sha)
            tab = pq.read_table(path)
            qp = path.with_suffix(".quarantine.parquet")
            quar = pq.read_metadata(qp).num_rows if qp.exists() else 0
            rows = tab.to_pylist()
            rows.sort(key=lambda r: (r["url_key"], r["record_id"]))       # D4 within one batch time
            rows_n = len(rows)
            for r in rows:
                oid = stable_hash("gdelt_gkg", r["record_id"], r["url_key"], "")
                if r["record_id"] in self.by_native:
                    dups.append({"observation_id": oid, "canonical_id": self.by_native[r["record_id"]], "matched_on": "native_id", "window": t})
                    continue
                uk = bytes.fromhex(r["url_key"])[:16] if r["url_key"] else b""
                if uk and uk in self.by_url:
                    dups.append({"observation_id": oid, "canonical_id": self.by_url[uk], "matched_on": "url_key", "window": t})
                    continue
                self.by_native[r["record_id"]] = oid
                if uk:
                    self.by_url[uk] = oid
                new.append({
                    "observation_id": oid, "source_type": "gdelt_gkg", "source_name": r["source_name"], "url": r["url"],
                    "url_key": r["url_key"], "native_id": r["record_id"], "observed_time": observed, "ingested_time": ingested,
                    "first_seen": ingested, "window": t, "title": r["title"], "published_time": r["published_time"],
                    "event_time": None, "authors": r["authors"], "persons": r["persons"], "orgs": r["orgs"],
                    "all_names": r["all_names"], "countries": r["countries"], "themes": r["themes"], "tone": r["tone"],
                    "word_count": r["word_count"], "sharing_image": r["sharing_image"], "quotations": r["quotations"],
                    "amounts": r["amounts"], "copy_group": oid, "member_count": 1, "member_ids": [oid],
                    "merge_evidence": "", "content_hash": "", "raw_ref": gkg_sha, "origin": "broad",
                })
            vecs = emb.encode([r["title"] for r in new], self.embed_model) if (self.embed_model and new) else None
            for i, r in enumerate(new):
                v = vecs[i] if vecs is not None else None
                root, evidence = self.l2.assign(r, v)
                r["copy_group"], r["merge_evidence"] = root, evidence
            if vecs is not None:
                self.day_vecs[day].append(([r["observation_id"] for r in new], vecs))
        ledger = {
            "window": t, "batch_ts": observed, "gkg_status": gkg_status, "export_status": self._status(ts, "export")[0],
            "mentions_status": self._status(ts, "mentions")[0], "missing_batch": gkg_status != "ok",
            "rows": rows_n, "new_objects": len(new), "l1_dups": len(dups),
            "l2_merges": sum(1 for r in new if r["merge_evidence"].startswith("L2")),
            "roots": sum(1 for r in new if r["copy_group"] == r["observation_id"]), "quarantined": quar,
        }
        bucket = self.day_rows[day]
        bucket.append(("obs_doc", new))
        bucket.append(("dup_links", dups))
        bucket.append(("window_ledger", [ledger]))
        for kind, table in (("export", "obs_event"), ("mentions", "obs_mention")):
            st, sha = self._status(ts, kind)
            if st == "ok":
                tab = pq.read_table(parsed_path(self.data_dir, kind, sha))
                tab = tab.append_column("window", pa.array([t] * tab.num_rows, pa.int32()))
                tab = tab.append_column("raw_ref", pa.array([sha] * tab.num_rows, pa.string()))
                bucket.append((table, tab))
        return new, ledger

    def flush_day(self, day: str) -> None:
        parts = self.day_vecs.pop(day, [])
        if parts and self.embed_model:
            ids = [i for p in parts for i in p[0]]
            emb.write_day(emb.cache_path(self.data_dir, self.embed_model, day), ids, np.concatenate([p[1] for p in parts]))
        groups: dict[str, list] = defaultdict(list)
        for name, payload in self.day_rows.pop(day, []):
            groups[name].append(payload)
        schemas = {"obs_doc": OBSERVATION_SCHEMA, "dup_links": DUP_SCHEMA, "window_ledger": WINDOW_LEDGER_SCHEMA}
        for name, parts in groups.items():
            if name in schemas:
                rows = [r for p in parts for r in p]
                tab = pa.Table.from_pylist(rows, schema=schemas[name])
            else:
                tab = pa.concat_tables(parts)
            out = self.tables / name / f"day={day}" / "part-0.parquet"
            out.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(tab, out, compression="zstd")

    def finish(self) -> None:
        if self.current_day:
            self.flush_day(self.current_day)


# ---------------------------------------------------------------- orchestration
def fetch_status_map(data_dir: Path) -> dict[tuple[str, str], tuple[str, str]]:
    latest = Ledger(data_dir / "fetch" / "ledger.jsonl").load()
    return {(r["batch_ts"], r["kind"]): (r["status"], r.get("sha256") or "") for r in latest.values()}


def complete_days(data_dir: Path, start: str, end: str) -> list[str]:
    """Days in [start, end) whose every planned file has a terminal fetch status (ok or missing)."""
    entries, _ = load_manifest(data_dir)
    status = fetch_status_map(data_dir)
    by_day: dict[str, list[str]] = defaultdict(list)
    for e in plan(entries, start, end):
        by_day[e.batch_ts[:8]].append(status.get((e.batch_ts, e.kind), ("pending", ""))[0])
    return sorted(d for d, sts in by_day.items() if all(s in ("ok", "missing") for s in sts))


def run_ingest(data_dir: Path, start_day: str, end_day: str, delta_s: int, lag_s: int, workers: int = 4,
               log=print, l2: L2Config | None = None, embed_model: str | None = emb.DEFAULT_MODEL) -> dict:
    start, end = start_day.replace("-", "") + "000000", end_day.replace("-", "") + "000000"
    days = complete_days(data_dir, start, end)
    if not days:
        log("no fully downloaded days in range yet")
        return {"days": 0}
    # contiguous prefix only: the sequential pass must not skip a day
    first = datetime.strptime(start[:8], "%Y%m%d")
    prefix = []
    for i, d in enumerate(days):
        if d != (first + timedelta(days=i)).strftime("%Y%m%d"):
            break
        prefix.append(d)
    last = prefix[-1]
    status = fetch_status_map(data_dir)
    jobs = sorted({(str(data_dir), k, sha) for (ts, k), (st, sha) in status.items()
                   if st == "ok" and start[:8] <= ts[:8] <= last})
    t0 = time.monotonic()
    parsed = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, _ in enumerate(pool.map(_parse_job, jobs, chunksize=8)):
            parsed += 1
            if parsed % 500 == 0:
                log(f"parse {parsed}/{len(jobs)} files  {time.monotonic() - t0:.0f}s")
    log(f"parse done: {len(jobs)} files in {time.monotonic() - t0:.0f}s")
    clock = WindowClock(parse_utc(start_day), delta_s, lag_s)
    eng = Engine1(data_dir, clock, status, l2=l2, embed_model=embed_model)
    end_t = clock.window_of(datetime.strptime(last, "%Y%m%d").replace(tzinfo=timezone.utc) + timedelta(days=1))
    totals = defaultdict(int)
    t1 = time.monotonic()
    for t in range(0, end_t):
        new, led = eng.step(t)
        totals["windows"] += 1
        totals["rows"] += led["rows"]
        totals["objects"] += led["new_objects"]
        totals["l1_dups"] += led["l1_dups"]
        totals["l2_merges"] += led["l2_merges"]
        totals["roots"] += led["roots"]
        totals["missing"] += int(led["missing_batch"])
        if (t + 1) % 96 == 0:
            log(f"day {clock.start(t).strftime('%Y-%m-%d')} done: {dict(totals)}  {time.monotonic() - t1:.0f}s")
    eng.finish()
    summary = {"days": len(prefix), "through": last, **totals, "seconds": round(time.monotonic() - t0)}
    (data_dir / "tables").mkdir(parents=True, exist_ok=True)
    (data_dir / "tables" / "ingest_summary.json").write_text(json.dumps(summary, indent=1))
    return summary
