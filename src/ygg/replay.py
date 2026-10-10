"""The replay loop (decision 0.4): one process, window by window, Engine 2a then Engine 2b.

Engine 1 has already written its day tables (obs_doc, window_ledger) and the embedding cache. For every
window t: 2a assigns this window's objects -> memberships and y/m; 2b consumes y(t), the root count V(t),
the missing-batch flag and 2a's lineage events. At each day boundary 2b gets fresh content neighbours
K(i) from 2a's narrative centroids before its refit. At requested snapshot windows (a case cutoff tau* and
the placebo cutoffs) the full state of both engines is pickled under a content-addressed SnapshotManifest
(C2), so Engine 3 reads S_tau* and the run can be resumed bit-identically (T1).
"""
from __future__ import annotations

import json
import pickle
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from ygg.attention.engine2b import B2Config, Engine2b
from ygg.contracts import SnapshotManifest
from ygg.determinism import WindowClock, stable_hash
from ygg.observation import embed as emb
from ygg.narratives.learned import LearnedConfig
from ygg.narratives.engine2a import (LEDGER_SCHEMA, LINEAGE_SCHEMA, MEMBERSHIP_SCHEMA, SERIES_SCHEMA, Engine2a, read_day)

E2B_SERIES = pa.schema([("narrative_id", pa.string()), ("window", pa.int32()), ("y", pa.float64()), ("lam", pa.float64()),
                        ("pit", pa.float64()), ("burst", pa.bool_())])
E2B_ALPHA = pa.schema([("target", pa.string()), ("source", pa.string()), ("window", pa.int32()), ("alpha", pa.float64())])


def _write(root: Path, name: str, day: str, rows: list[dict], schema: pa.Schema) -> None:
    out = root / name / f"day={day}" / "part-0.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), out, compression="zstd")


def snapshot(data_dir: Path, t: int, cfg_hash: str, e2a: Engine2a, e2b: Engine2b, parent: str) -> SnapshotManifest:
    """What Engine 3 reads at a cutoff: the narrative layer and the attention engine. The online event-cluster
    index (hundreds of thousands of centroids) is not needed downstream and is left out to keep snapshots small.
    Full-state resume (T1) is tested separately."""
    blob = pickle.dumps({"narratives": e2a.model.narratives, "kappa": e2a.model.kappa, "log_pi": getattr(e2a.model, "log_pi", {}),
                         "lineage": e2a.model.lineage, "e2b": e2b}, protocol=5)
    state_hash = stable_hash(e2a.state_hash(), json.dumps(sorted((n, float(v)) for n, v in e2b.lam_next.items())))
    m = SnapshotManifest(t=t, cfg_hash=cfg_hash, parent_snapshot_id=parent, inputs_hash=state_hash,
                         tables=(("engines.pkl", stable_hash(blob)),))
    out = Path(data_dir) / "snapshots" / f"t={t}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "engines.pkl").write_bytes(blob)
    (out / "manifest.json").write_text(json.dumps({"snapshot_id": m.snapshot_id, "t": t, "cfg_hash": cfg_hash,
                                                   "parent": parent, "inputs_hash": state_hash, "tables": m.tables}, indent=1))
    return m


def run_replay(data_dir: Path, clock: WindowClock, start_day: str, end_day: str, embed_model: str, cfg_hash: str,
               snapshot_windows: set[int] = frozenset(), log=print, e2a: Engine2a | None = None,
               e2b: Engine2b | None = None, lr_cfg: LearnedConfig | None = None) -> dict:
    data_dir = Path(data_dir)
    root = data_dir / "tables"
    e2a = e2a or Engine2a(clock, emb.cached_dim(data_dir, embed_model), lr_cfg=lr_cfg or LearnedConfig())
    e2b = e2b or Engine2b(clock, B2Config(cfg_hash=cfg_hash))
    led_tab = pq.read_table(root / "window_ledger").to_pylist() if (root / "window_ledger").exists() else []
    missing = {r["window"]: r["missing_batch"] for r in led_tab}
    d0, d1 = datetime.fromisoformat(start_day), datetime.fromisoformat(end_day)
    days = [(d0 + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((d1 - d0).days)]
    parent, made, t_start = "", [], time.monotonic()
    for day in days:
        by_w, vecs = read_day(data_dir, day, embed_model)
        acc = defaultdict(list)
        day_start = clock.window_of(datetime.fromisoformat(day + "T00:00:00+00:00"))
        for t in range(day_start, day_start + 96):
            if t == day_start:
                alive = {n.nid: n.mu for n in e2a.model.narratives.values() if n.state == "alive"}
                e2b.set_neighbors(alive)
            ra = e2a.step(t, by_w.get(t, []), vecs)
            y = {r["narrative_id"]: r["y255"] / 255.0 for r in ra["series"]}
            rb = e2b.step(t, y, float(ra["ledger"]["roots"]), bool(missing.get(t, False)), ra["lineage"])
            for k in ("memberships", "series", "lineage"):
                acc[k] += ra[k]
            acc["ledger"].append(ra["ledger"])
            acc["e2b_series"] += rb["series"]
            acc["e2b_alpha"] += rb["alpha"]
            if t in snapshot_windows:
                m = snapshot(data_dir, t, cfg_hash, e2a, e2b, parent)
                parent = m.snapshot_id
                made.append({"t": t, "snapshot_id": m.snapshot_id})
        for name, schema, key in (("e2a_memberships", MEMBERSHIP_SCHEMA, "memberships"), ("e2a_series", SERIES_SCHEMA, "series"),
                                  ("e2a_ledger", LEDGER_SCHEMA, "ledger"), ("e2a_lineage", LINEAGE_SCHEMA, "lineage"),
                                  ("e2b_series", E2B_SERIES, "e2b_series"), ("e2b_alpha", E2B_ALPHA, "e2b_alpha")):
            _write(root, name, day, acc[key], schema)
        nar = [{"narrative_id": n.nid, "state": n.state, "label": n.label, "born_h": n.born_h, "t_last_h": n.t_last_h,
                "mass_total": n.mass_total, "top_entities": [e for e, _ in sorted(n.ents.items(), key=lambda kv: (-kv[1], kv[0]))[:8]]}
               for n in sorted(e2a.model.narratives.values(), key=lambda n: n.nid)]
        snapd = root / "e2a_narratives" / f"day={day}.json"
        snapd.parent.mkdir(parents=True, exist_ok=True)
        diag = e2a.model.diagnostics(e2a.hours(day_start + 95)) if e2a.learned else None
        snapd.write_text(json.dumps({"day": day, "kappa": e2a.model.kappa, "omega": e2b.omega, "r": e2b.r, "e2a_diag": diag,
                                     "refit": e2b.refits[-1] if e2b.refits else None, "narratives": nar}, indent=0))
        led = acc["ledger"]
        roots = sum(x["roots"] for x in led)
        bursts = sum(1 for r in acc["e2b_series"] if r["burst"])
        log(f"replay {day}: roots {roots}  alive {led[-1]['alive']}  dormant {led[-1]['dormant']}  "
            f"none {sum(x['y0_255'] for x in led) / max(1, 255 * roots):.2f}  kappa {e2a.model.kappa:.0f}  "
            f"omega {e2b.omega}  burst-windows {bursts}  {time.monotonic() - t_start:.0f}s")
    return {"snapshots": made, "refits_2a": e2a.refits, "refits_2b": e2b.refits}
