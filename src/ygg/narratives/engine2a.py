"""Engine 2a: Engine 1 objects -> event clusters -> narratives -> memberships and attention series.

Per window (D4 order):
  roots (copy-group roots) are clustered into events; every touched event cluster gets a narrative
  membership (top 3 + none, uint8); roots inherit their cluster's membership; copies inherit their
  root's cluster's membership.
  y[n][t] = sum of root shares (unweighted attention, Session 1: no weighting)
  m[n][t] = sum of root and copy shares (reach)
Shares are integers out of 255, so Lemma 5.1 holds exactly: sum_n y[n][t] + y[0][t] = 255 * roots[t].
Narrative layer: the learned model (2a-L, ygg.narratives.learned; default since 2026-10-07): routing is
MAP, births / merges / splits are Bayes-factor decisions, statistics update online. The gated model of
the first real run (ygg.narratives.narratives: corpus-vMF background, join gate, m_emerge) stays available
as the fallback ("gated"). Every 6 hours the lineage checks run (dormancy, merge, split). The state can be
pickled at any window boundary and resumed bit-identically (test T1).
"""
from __future__ import annotations

import hashlib
import json
import pickle
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ygg.determinism import WindowClock
from ygg.narratives.events import EventClusterer, EventConfig
from ygg.narratives.features import CausalIDF, entities
from ygg.narratives.learned import LearnedConfig, LearnedNarrativeModel
from ygg.narratives.narratives import NarrativeConfig, NarrativeModel
from ygg.observation import embed as emb

MEMBERSHIP_SCHEMA = pa.schema([
    ("observation_id", pa.string()), ("window", pa.int32()), ("is_root", pa.bool_()), ("event_cluster", pa.int64()),
    ("n1", pa.string()), ("n2", pa.string()), ("n3", pa.string()),
    ("p1", pa.uint8()), ("p2", pa.uint8()), ("p3", pa.uint8()), ("p0", pa.uint8()),
])
SERIES_SCHEMA = pa.schema([("narrative_id", pa.string()), ("window", pa.int32()), ("y255", pa.int64()), ("m255", pa.int64())])
LEDGER_SCHEMA = pa.schema([("window", pa.int32()), ("roots", pa.int32()), ("copies", pa.int32()), ("y0_255", pa.int64()),
                           ("m0_255", pa.int64()), ("alive", pa.int32()), ("dormant", pa.int32()), ("new_events", pa.int32())])
LINEAGE_SCHEMA = pa.schema([("window", pa.int32()), ("kind", pa.string()), ("parents", pa.list_(pa.string())),
                            ("children", pa.list_(pa.string())), ("shares", pa.list_(pa.float64()))])
NONE = "~none"


@dataclass
class Engine2a:
    clock: WindowClock
    dim: int = 256
    ev_cfg: EventConfig = field(default_factory=EventConfig)
    nr_cfg: NarrativeConfig = field(default_factory=NarrativeConfig)
    lr_cfg: LearnedConfig | None = field(default_factory=LearnedConfig)     # None selects the gated fallback

    def __post_init__(self):
        self.events = EventClusterer(self.dim, self.ev_cfg)
        self.learned = self.lr_cfg is not None
        self.model = LearnedNarrativeModel(self.dim, self.lr_cfg) if self.learned else NarrativeModel(self.dim, self.nr_cfg)
        self.idf = CausalIDF()
        self.cluster_mass: Counter = Counter()
        self.cluster_title: dict[int, str] = {}
        self.cluster_members: dict[int, tuple] = {}          # cid -> (ids, shares) latest membership
        self.root_cluster: dict[str, tuple[int, float]] = {}  # root oid -> (cid, t_h), kept 72 h for copies
        self.last_day: str | None = None
        self.refits: list[dict] = []

    def hours(self, t: int) -> float:
        return (self.clock.start(t) - self.clock.t0).total_seconds() / 3600.0

    def step(self, t: int, docs: list[dict], vecs: dict[str, np.ndarray]) -> dict:
        t_h = self.hours(t)
        day = self.clock.start(t).strftime("%Y-%m-%d")
        if day != self.last_day:
            if self.last_day is not None and not self.learned:
                self.refits.append({"day": day, **self.model.refit(t_h)})
            self.last_day = day
        roots = [d for d in docs if d["copy_group"] == d["observation_id"]]
        copies = [d for d in docs if d["copy_group"] != d["observation_id"]]
        touched: dict[int, int] = defaultdict(int)
        root_ents = []
        new_events = 0
        new_cids = set()
        rows = []
        for d in roots:
            v = vecs.get(d["observation_id"])
            if v is None:
                continue
            ents = entities(d)
            root_ents.append(ents)
            cid, is_new = self.events.assign(v, ents, self.idf, t_h, t)
            new_events += int(is_new)
            if is_new:
                new_cids.add(cid)
                self.cluster_title[cid] = d["title"]
            self.cluster_mass[cid] += 1
            touched[cid] += 1
            self.root_cluster[d["observation_id"]] = (cid, t_h)
        if self.learned:
            self._narrate_learned(t, t_h, touched, new_cids)
        for cid in ([] if self.learned else sorted(touched)):
            cl = self.events.clusters[cid]
            ids, shares, routed = self.model.membership(cl.centroid, cl.ents, t_h)
            if routed is not None:
                self.model.absorb(routed, cl.centroid, cl.ents, touched[cid], t_h, t)
            elif self.cluster_mass[cid] >= self.nr_cfg.m_emerge and cid not in self.model.emerged_from:
                self.model.emerge(cid, cl.centroid, cl.ents, t_h, t, self.cluster_title.get(cid, ""))
                ids, shares, routed = self.model.membership(cl.centroid, cl.ents, t_h)
            self.model.record(t_h, cid, cl.centroid, cl.ents, float(touched[cid]))
            self.cluster_members[cid] = (ids, shares)
        y: Counter = Counter()
        mreach: Counter = Counter()

        def emit(d, cid, is_root):
            ids, shares = self.cluster_members.get(cid, ([], np.array([255], np.uint8)))
            padded = list(ids) + [""] * (3 - len(ids))
            sh = list(int(s) for s in shares[:-1]) + [0] * (3 - len(ids))
            for nid, s in zip(ids, shares[:-1]):
                if is_root:
                    y[nid] += int(s)
                mreach[nid] += int(s)
            if is_root:
                y[NONE] += int(shares[-1])
            mreach[NONE] += int(shares[-1])
            rows.append({"observation_id": d["observation_id"], "window": t, "is_root": is_root, "event_cluster": cid,
                         "n1": padded[0], "n2": padded[1], "n3": padded[2], "p1": sh[0], "p2": sh[1], "p3": sh[2], "p0": int(shares[-1])})
        for d in roots:
            rc = self.root_cluster.get(d["observation_id"])
            if rc:
                emit(d, rc[0], True)
        for d in copies:
            rc = self.root_cluster.get(d["copy_group"])
            if rc:
                emit(d, rc[0], False)
        cutoff = t_h - 72.0
        if t % 96 == 0:
            for k in [k for k, (_, th) in self.root_cluster.items() if th < cutoff]:
                del self.root_cluster[k]
            # memory: per-cluster side tables of clusters the clusterer has expired (7 days without an update) are never
            # read again (copies resolve through root_cluster, 72 h; births use live pool clusters), so drop them
            live = self.events.clusters
            for d in (self.cluster_mass, self.cluster_title, self.cluster_members):
                for k in [k for k in d if k not in live]:
                    del d[k]
        self.idf.close_window(t, root_ents)
        every = self.lr_cfg.check_every_windows if self.learned else self.nr_cfg.check_every_windows
        if (t + 1) % every != 0:
            lineage = []
        elif self.learned:
            lineage = self.model.lineage_check(t_h, t, self.events.clusters)
        else:
            lineage = self.model.lineage_check(t_h, t)
        states = Counter(n.state for n in self.model.narratives.values())
        n_roots = sum(1 for r in rows if r["is_root"])
        return {
            "memberships": rows,
            "series": [{"narrative_id": n, "window": t, "y255": y[n], "m255": mreach[n]} for n in sorted(set(y) | set(mreach)) if n != NONE],
            "ledger": {"window": t, "roots": n_roots, "copies": len(rows) - n_roots, "y0_255": y[NONE], "m0_255": mreach[NONE],
                       "alive": states.get("alive", 0), "dormant": states.get("dormant", 0), "new_events": new_events},
            "lineage": lineage,
        }

    def _narrate_learned(self, t: int, t_h: float, touched: dict, new_cids: set) -> None:
        narrate_learned(self.model, self.idf, self.events.clusters, touched, new_cids, self.cluster_title, self.cluster_members, t, t_h)

    def state_hash(self) -> str:
        """Canonical digest of the full state (sorted, so set/dict insertion order cannot leak in). The learned
        path hashes repr(), not pickle bytes: pickle memoizes shared objects, so equal states could differ."""
        evs = ((c.cid, c.vsum.tobytes(), c.n, c.t_mean, c.t_last, sorted(c.ents.items()), sorted(c.cnt.items()))
               for c in sorted(self.events.clusters.values(), key=lambda c: c.cid))
        if self.learned:
            # Streamed: the same bytes as sha256(repr(canon)) with the event list fed one cluster at a time. Building
            # repr(canon) in one string took ~5 GB at 500k live event clusters (the replay was OOM-killed on Jan 13).
            h = hashlib.sha256()
            parts = (self.model.canon(), _Seq(evs, "[]"), sorted(self.idf.df.items()), self.idf.n_docs, sorted(self.root_cluster.items()),
                     sorted(self.cluster_mass.items()), self.events.next_id)
            _feed_repr(h, parts)
            return h.hexdigest()
        evs = list(evs)
        nar = [(n.nid, n.mu.tobytes(), n.state, n.born_h, n.t_last_h, n.mass_total, sorted(n.ents.items()))
               for n in sorted(self.model.narratives.values(), key=lambda n: n.nid)]
        canon = (nar, evs, self.model.kappa, sorted(self.model.log_pi.items()), self.model.log_pi0,
                 sorted(self.idf.df.items()), self.idf.n_docs, sorted(self.root_cluster.items()),
                 sorted(self.cluster_mass.items()), self.events.next_id, len(self.model.lineage))
        return hashlib.sha256(pickle.dumps(canon, protocol=5)).hexdigest()


class _Seq:
    """A lazily produced list or tuple for _feed_repr."""

    def __init__(self, it, brackets: str):
        self.it, self.brackets = it, brackets


def _feed_repr(h, x) -> None:
    """Feed repr(x) into hash h piece by piece, for nested tuples and lists, without building the string.
    repr(list) = '[' + ', '.join(reprs) + ']' and repr(tuple) the same with '(' ')' and a trailing comma for one item."""
    if isinstance(x, _Seq) or type(x) in (list, tuple):
        if isinstance(x, _Seq):
            items, (lo, hi) = x.it, x.brackets
        else:
            items, (lo, hi) = x, ("[]" if type(x) is list else "()")
        h.update(lo.encode())
        n = 0
        for item in items:
            if n:
                h.update(b", ")
            _feed_repr(h, item)
            n += 1
        if hi == ")" and n == 1:
            h.update(b",")
        h.update(hi.encode())
    else:
        h.update(repr(x).encode())


def narrate_learned(m: LearnedNarrativeModel, idf: CausalIDF, clusters: dict, touched: dict, new_cids: set, titles: dict,
                    members: dict, t: int, t_h: float) -> None:
    """2a-L for one window's touched event clusters (D4 order: by cluster id). Shared by Engine2a and the
    warmup fit (ygg.narratives.fit), so both run exactly the same decisions."""
    m.set_background_counts(idf.df, len(idf.df), idf.total)
    for cid in sorted(touched):
        cl = clusters[cid]
        w = {e: c / cl.n for e, c in cl.cnt.items()}
        ids, shares, routed = m.membership(cl.centroid, w, t_h, idf, score=cid in new_cids)
        if routed is not None:
            m.route(cid, routed, cl.centroid, w, float(touched[cid]), t_h, t)
        else:
            nid = m.try_birth(cid, cl.centroid, w, clusters, t_h, t, titles) if cl.n >= 2 and cid not in m.emerged_from else None
            if nid is not None:
                m.narratives[nid].mass_total += touched[cid]
                ids, shares, routed = m.membership(cl.centroid, w, t_h, idf)
            else:
                m.background_add(cid, cl.centroid, t_h)
                if cl.n >= 2:
                    m.pool_upsert(cid, cl.centroid, t_h)
        members[cid] = (ids, shares)
    m.record_volume(sum(touched.values()))                # after the decisions: the price terms stay predictable


def read_day(data_dir: Path, day: str, model: str) -> tuple[dict[int, list[dict]], dict[str, np.ndarray]]:
    tab = pq.read_table(Path(data_dir) / "tables" / "obs_doc" / f"day={day}" / "part-0.parquet",
                        columns=["observation_id", "window", "copy_group", "title", "persons", "orgs", "all_names", "url_key"])
    by_w: dict[int, list[dict]] = defaultdict(list)
    for r in tab.to_pylist():
        by_w[r["window"]].append(r)
    return by_w, emb.read_day(emb.cache_path(data_dir, model, day))


def run_engine2a(data_dir: Path, clock: WindowClock, days: list[str], model: str, log=print,
                 ev_cfg: EventConfig | None = None, nr_cfg: NarrativeConfig | None = None, out_name: str = "e2a") -> dict:
    eng = Engine2a(clock, emb.cached_dim(data_dir, model), ev_cfg or EventConfig(), nr_cfg or NarrativeConfig())
    out_root = Path(data_dir) / "tables"
    t0 = time.monotonic()
    for day in days:
        by_w, vecs = read_day(data_dir, day, model)
        acc = defaultdict(list)
        day_start = clock.window_of(datetime.fromisoformat(day + "T00:00:00+00:00"))
        for t in range(day_start, day_start + 96):
            r = eng.step(t, by_w.get(t, []), vecs)
            acc["memberships"] += r["memberships"]
            acc["series"] += r["series"]
            acc["ledger"].append(r["ledger"])
            acc["lineage"] += r["lineage"]
        for name, schema in (("memberships", MEMBERSHIP_SCHEMA), ("series", SERIES_SCHEMA), ("ledger", LEDGER_SCHEMA), ("lineage", LINEAGE_SCHEMA)):
            out = out_root / f"{out_name}_{name}" / f"day={day}" / "part-0.parquet"
            out.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(pa.Table.from_pylist(acc[name], schema=schema), out, compression="zstd")
        nar = [{"narrative_id": n.nid, "state": n.state, "label": n.label, "born_h": n.born_h, "t_last_h": n.t_last_h,
                "mass_total": n.mass_total, "top_entities": [e for e, _ in sorted(n.ents.items(), key=lambda kv: (-kv[1], kv[0]))[:8]]}
               for n in sorted(eng.model.narratives.values(), key=lambda n: n.nid)]
        snap = out_root / f"{out_name}_narratives" / f"day={day}.json"
        snap.parent.mkdir(parents=True, exist_ok=True)
        snap.write_text(json.dumps({"day": day, "kappa": eng.model.kappa, "narratives": nar}, indent=0))
        led = acc["ledger"]
        log(f"2a {day}: roots {sum(l['roots'] for l in led)}  alive {led[-1]['alive']}  dormant {led[-1]['dormant']}  "
            f"none share {sum(l['y0_255'] for l in led) / max(1, 255 * sum(l['roots'] for l in led)):.2f}  "
            f"kappa {eng.model.kappa:.0f}  {time.monotonic() - t0:.0f}s")
    return {"refits": eng.refits, "state_hash": eng.state_hash()}
