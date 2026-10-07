"""Layer 1: online event clusters (decision 3.1/3.2): one specific happening, hard assignment, in D4 order.

  score(o, c) = (w_txt * cos(e_o, mu_c) + w_ent * J_idf(ents_o, ents_c)) * exp(-(t_o - t_c)^2 / (2 * sigma^2))
  assign(o)   = argmax_c score if >= tau_event, else a new cluster
Candidates: clusters seen in the last 7 days that share a rare entity with o or an embedding LSH bucket.
The LSH hyperplanes come from a keyed Philox stream (D2), so buckets are identical across runs.
"""
from __future__ import annotations

import heapq
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field

import numpy as np

from ygg.determinism import keyed_rng
from ygg.narratives.features import CausalIDF, weighted_jaccard


@dataclass
class EventConfig:
    w_txt: float = 0.7
    w_ent: float = 0.3
    tau_event: float = 0.55
    sigma_h: float = 72.0          # locked (3.2)
    horizon_h: float = 168.0       # candidate clusters seen in the last 7 days
    lsh_tables: int = 6
    lsh_bits: int = 12
    rare_idf: float = 5.0          # an entity counts as rare above this IDF
    max_candidates: int = 64
    ent_top: int = 8               # entity term computed for the 8 candidates with the highest cosine


@dataclass
class EventCluster:
    cid: int
    centroid: np.ndarray            # running mean of member embeddings (unnormalized sum kept separately)
    vsum: np.ndarray
    ents: dict                      # entity -> accumulated IDF weight
    t_mean: float                   # mean member time (hours since t0)
    t_last: float
    n: int
    first_window: int
    last_window: int
    ents_sum: float = 0.0
    slot: int = -1
    cnt: dict = field(default_factory=dict)      # entity -> number of member stories that mention it (2a-L)


@dataclass
class EventClusterer:
    dim: int
    cfg: EventConfig = field(default_factory=EventConfig)
    seed_key: str = "event-lsh-v1"
    clusters: dict = field(default_factory=dict)
    buckets: list = field(default_factory=list)
    by_entity: dict = field(default_factory=lambda: defaultdict(set))
    recent: deque = field(default_factory=deque)          # (t_last_hours, cid) for expiry
    next_id: int = 0

    def __post_init__(self):
        self.C = np.zeros((1024, self.dim), np.float32)     # centroid matrix; rows reused through a free list
        self.free: list[int] = []
        self.next_slot = 0
        rng = keyed_rng(self.seed_key, str(self.dim))
        self.planes = rng.standard_normal((self.cfg.lsh_tables, self.cfg.lsh_bits, self.dim)).astype(np.float32)
        self.buckets = [defaultdict(set) for _ in range(self.cfg.lsh_tables)]
        self.pow2 = (1 << np.arange(self.cfg.lsh_bits)).astype(np.int64)

    def _keys(self, v: np.ndarray) -> list[int]:
        bits = (self.planes @ v > 0).astype(np.int64)        # tables x bits
        return [int(k) for k in bits @ self.pow2]

    def _expire(self, now_h: float) -> None:
        cutoff = now_h - self.cfg.horizon_h
        while self.recent and self.recent[0][0] < cutoff:
            t_last, cid = self.recent.popleft()
            c = self.clusters.get(cid)
            if c is None or c.t_last != t_last:
                continue                                     # stale entry; a newer one exists
            for i, k in enumerate(self._keys(c.centroid)):
                self.buckets[i][k].discard(cid)
            self.free.append(c.slot)
            for e in c.ents:
                s = self.by_entity.get(e)
                if s is not None:
                    s.discard(cid)
                    if not s:
                        del self.by_entity[e]
            del self.clusters[cid]

    def assign(self, v: np.ndarray, ents: frozenset[str], idf: CausalIDF, t_h: float, window: int) -> tuple[int, bool]:
        """Return (cluster id, is_new)."""
        self._expire(t_h)
        w = idf.weights(ents)
        cand = set()
        for i, k in enumerate(self._keys(v)):
            cand |= self.buckets[i].get(k, set())
        for e, wt in w.items():
            if wt >= self.cfg.rare_idf:
                cand |= self.by_entity.get(e, set())
        best, best_s = None, -1.0
        if cand:
            ids = sorted(heapq.nlargest(self.cfg.max_candidates, cand)) if len(cand) > self.cfg.max_candidates else sorted(cand)
            cos = self.C[[self.clusters[c].slot for c in ids]] @ v
            top = set(np.argsort(-cos, kind="stable")[: self.cfg.ent_top].tolist())
            w_sum = sum(w.values())
            for pos, (c, cs) in enumerate(zip(ids, cos)):
                cl = self.clusters[c]
                dt = t_h - cl.t_mean
                k = math.exp(-dt * dt / (2.0 * self.cfg.sigma_h ** 2))
                jac = weighted_jaccard(w, cl.ents, w_sum, cl.ents_sum) if pos in top else 0.0
                s = (self.cfg.w_txt * float(cs) + self.cfg.w_ent * jac) * k
                if s > best_s or (s == best_s and best is not None and c < best):
                    best, best_s = c, s
        if best is not None and best_s >= self.cfg.tau_event:
            cl = self.clusters[best]
            old_keys = self._keys(cl.centroid)
            cl.vsum = cl.vsum + v
            cl.centroid = cl.vsum / max(np.linalg.norm(cl.vsum), 1e-12)
            self.C[cl.slot] = cl.centroid
            for e, wt in w.items():
                cl.cnt[e] = cl.cnt.get(e, 0) + 1
                cl.ents[e] = cl.ents.get(e, 0.0) + wt
                cl.ents_sum += wt
                if wt >= self.cfg.rare_idf:
                    self.by_entity[e].add(best)
            cl.t_mean = (cl.t_mean * cl.n + t_h) / (cl.n + 1)
            cl.n += 1
            cl.t_last, cl.last_window = t_h, window
            new_keys = self._keys(cl.centroid)
            for i, (ko, kn) in enumerate(zip(old_keys, new_keys)):
                if ko != kn:
                    self.buckets[i][ko].discard(best)
                    self.buckets[i][kn].add(best)
            self.recent.append((t_h, best))
            return best, False
        cid = self.next_id
        self.next_id += 1
        cl = EventCluster(cid, v.copy(), v.copy(), dict(w), t_h, t_h, 1, window, window, sum(w.values()), cnt={e: 1 for e in w})
        if self.free:
            cl.slot = self.free.pop()
        else:
            if self.next_slot >= len(self.C):
                self.C = np.concatenate([self.C, np.zeros_like(self.C)])
            cl.slot = self.next_slot
            self.next_slot += 1
        self.C[cl.slot] = v
        self.clusters[cid] = cl
        for i, k in enumerate(self._keys(v)):
            self.buckets[i][k].add(cid)
        for e, wt in w.items():
            if wt >= self.cfg.rare_idf:
                self.by_entity[e].add(cid)
        self.recent.append((t_h, cid))
        return cid, True
