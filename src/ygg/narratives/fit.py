"""Fit the three learned settings of 2a-L (kappa_s, alpha, entity temperature T) on the warmup only.

Objective: the prequential score. Each brand-new event is scored before any update by
log p(x | entities) under the model as it stands (ygg.narratives.learned, score_new). Days 1-7 of the
warmup are burn-in; days 8 to the end of the warmup are scored. The score never sees the case period,
needs no labels, and is comparable across settings because it is a normalized density of the direction x.

Stage 1 (event clustering) does not depend on these settings, so it runs once and is cached per day:
  data/narratives_fit/cache/day=D.pkl  {window: (root entity sets, touches)}
  touch = (cid, is_new, centroid f32, |vsum|, n, entity counts, new stories, title or None)
Stage 2 replays only the narrative layer for each setting, with the same code path as Engine 2a
(engine2a.narrate_learned).
"""
from __future__ import annotations

import json
import pickle
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from ygg.narratives.events import EventClusterer, EventConfig
from ygg.narratives.features import CausalIDF, entities


@dataclass
class EventState:
    """What the narrative layer reads from an event cluster."""
    cid: int
    centroid: np.ndarray
    vsum: np.ndarray
    n: int
    cnt: dict
    t_last: float


def _days(start: str, end_exclusive: str) -> list[str]:
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end_exclusive)
    return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days)]


def build_cache(data_dir: Path, clock, start: str, end_exclusive: str, model: str, log=print) -> Path:
    from ygg.narratives.engine2a import read_day

    out = Path(data_dir) / "narratives_fit" / "cache"
    out.mkdir(parents=True, exist_ok=True)
    from ygg.observation import embed as emb

    events = EventClusterer(emb.cached_dim(data_dir, model), EventConfig())
    idf = CausalIDF()
    t0 = time.monotonic()
    for day in _days(start, end_exclusive):
        path = out / f"day={day}.pkl"
        by_w, vecs = read_day(data_dir, day, model)
        day_start = clock.window_of(datetime.fromisoformat(day + "T00:00:00+00:00"))
        rec = {}
        for t in range(day_start, day_start + 96):
            t_h = (clock.start(t) - clock.t0).total_seconds() / 3600.0
            touched, new, first_title, root_ents = defaultdict(int), set(), {}, []
            for d in by_w.get(t, []):
                if d["copy_group"] != d["observation_id"]:
                    continue
                v = vecs.get(d["observation_id"])
                if v is None:
                    continue
                ents = entities(d)
                root_ents.append(ents)
                cid, is_new = events.assign(v, ents, idf, t_h, t)
                touched[cid] += 1
                if is_new:
                    new.add(cid)
                    first_title[cid] = d["title"]
            touches = []
            for cid in sorted(touched):
                cl = events.clusters[cid]
                touches.append((cid, cid in new, cl.centroid.astype(np.float32), float(np.linalg.norm(cl.vsum)), cl.n,
                                dict(cl.cnt), touched[cid], first_title.get(cid)))
            idf.close_window(t, root_ents)
            rec[t] = (root_ents, touches)
        path.write_bytes(pickle.dumps(rec, protocol=5))
        log(f"fit-cache {day}: {sum(len(v[1]) for v in rec.values())} touches  {time.monotonic() - t0:.0f}s")
    return out


def run_setting(data_dir: Path, clock, days: list[str], burn_in_days: int, cfg, dim: int) -> dict:
    """Stage 2 for one setting: the narrative layer over the cached warmup; returns the score and diagnostics."""
    from ygg.narratives.engine2a import narrate_learned
    from ygg.narratives.learned import LearnedNarrativeModel

    cache = Path(data_dir) / "narratives_fit" / "cache"
    m = LearnedNarrativeModel(dim, cfg)
    idf = CausalIDF()
    clusters: dict[int, EventState] = {}
    titles, members = {}, {}
    per_day, base = [], None
    t_start = time.monotonic()
    for i, day in enumerate(days):
        if i == burn_in_days:
            base = dict(m.preq)
        rec = pickle.loads((cache / f"day={day}.pkl").read_bytes())
        births = 0
        for t in sorted(rec):
            root_ents, touches = rec[t]
            t_h = (clock.start(t) - clock.t0).total_seconds() / 3600.0
            touched, new = {}, set()
            for cid, is_new, c, vnorm, n, cnt, k, title in touches:
                clusters[cid] = EventState(cid, c.astype(np.float64), c.astype(np.float64) * vnorm, n, cnt, t_h)
                touched[cid] = k
                if is_new:
                    new.add(cid)
                if title is not None:
                    titles[cid] = title
            before = len(m.emerged_from)
            narrate_learned(m, idf, clusters, touched, new, titles, members, t, t_h)
            births += len(m.emerged_from) - before
            idf.close_window(t, root_ents)
            if (t + 1) % cfg.check_every_windows == 0:
                m.lineage_check(t_h, t, clusters)
            if t % 96 == 95:
                for cid in [c for c, s in clusters.items() if s.t_last < t_h - 168.0]:
                    del clusters[cid]
                    titles.pop(cid, None)
                    members.pop(cid, None)
        diag = m.diagnostics((clock.start(max(rec)) - clock.t0).total_seconds() / 3600.0)
        per_day.append({"day": day, "births": births, **{k: diag[k] for k in ("alive", "dormant", "kappa_implied_median", "pi0", "kappa0")}})
    base = base or {"sum": 0.0, "n": 0}
    n = m.preq["n"] - base["n"]
    kinds = defaultdict(int)
    for ev in m.lineage:
        kinds[ev["kind"]] += 1
    return {"kappa_s": cfg.kappa_s, "log_alpha": cfg.log_alpha, "temp": cfg.temp,
            "score_mean": (m.preq["sum"] - base["sum"]) / max(n, 1), "scored_events": n,
            "lineage": dict(kinds), "per_day": per_day, "seconds": round(time.monotonic() - t_start, 1)}


def grid(data_dir: Path, clock, days: list[str], burn_in_days: int, dim: int, kappas, log_alphas, temps, log=print) -> list[dict]:
    from ygg.narratives.learned import LearnedConfig

    out_path = Path(data_dir) / "narratives_fit" / "results.jsonl"
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            r = json.loads(line)
            done.add((r["kappa_s"], r["log_alpha"], r["temp"]))
    res = []
    for k in kappas:
        for a in log_alphas:
            for T in temps:
                if (k, a, T) in done:
                    continue
                r = run_setting(data_dir, clock, days, burn_in_days, LearnedConfig(kappa_s=k, log_alpha=a, temp=T), dim)
                with out_path.open("a") as f:
                    f.write(json.dumps(r) + "\n")
                last = r["per_day"][-1]
                log(f"fit kappa_s {k:g} log_alpha {a:g} T {T:g}: score {r['score_mean']:.3f} nats/event  alive {last['alive']}  "
                    f"births/day {np.mean([d['births'] for d in r['per_day']]):.0f}  kappa_implied {last['kappa_implied_median']}  "
                    f"lineage {r['lineage']}  {r['seconds']}s")
                res.append(r)
    return res
