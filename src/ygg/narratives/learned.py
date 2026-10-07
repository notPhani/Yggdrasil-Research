"""Layer 2, learned ("2a-L", locked 2026-10-07): soft narratives where every structural decision is a
likelihood comparison in nats, replacing the hand gates of the first real run (join gate, m_emerge, entity
weight, merge and split thresholds).

Model. Each event cluster c is one draw of a narrative: its mean title direction x_c (unit, MiniLM) and its
entity profile w_c(e) = share of its stories that mention e.
  narrative k:  vMF(x; mu_k, kappa_s) * prod_e phi_k(e)^(w(e)/T)
  background:   vMF(x; mu_0, kappa_0) * prod_e phi_0(e)^(w(e)/T)
  phi_k(e) = (n_k(e) + beta * phi_0(e)) / (N_k + beta)          Dirichlet-smoothed toward the corpus
  phi_0(e) = trailing 7-day document frequency (causal IDF counts), add-half smoothed
Gain of k over the background (nats):
  g_k = log pi_k - log pi_0 + [log C(kappa_s) + kappa_s mu_k.x] - [log C(kappa_0) + kappa_0 mu_0.x]
        + (1/T) sum_e w(e) log(phi_k(e) / phi_0(e)) - (t - t_k)^2 / (2 sigma^2)
A story's soft membership is the posterior over the top 3 gains plus the background (uint8, sums to 255).
The event's own statistics go to its MAP narrative once (routing = MAP; no tau_alive / tau_dormant).

Structure (each narrative costs -log alpha nats, i.e. prior P(K) proportional to alpha^K):
  birth   a group G of >= 2 distinct events (an unrouted event plus its nearest recent background events)
          becomes a narrative iff
            log alpha + log Z_vMF(G) - sum_{e in G} log p_0(x_e) + (DM entity evidence of G)/T > 0
          with the exact conjugate evidence (vMF prior on the direction centred on the background):
            log Z_vMF(S, n) = n log C(kappa_s) + log C(kappa_0) - log C(|kappa_s S + kappa_0 mu_0|)
          G is grown greedily from the 8 nearest pool events while the evidence rises (proposal only).
          Unit: events. The first real run counted stories instead and was wrong: the stories of one event
          are near-copies (median within-cluster cosine 0.83), each added ~65 nats, and 99.8% of the 11,906
          multi-story events of Dec 18 would have started a narrative even at zero cost. Copies are one
          observation, not many (pseudo-replication), so a narrative needs several events.
  merge   narratives a, b (each one's nearest neighbour is the proposal) merge iff
            log Z(a + b) - log Z(a) - log Z(b) - log alpha + (DM entity terms)/T > 0
  split   a deterministic 2-means proposal over the narrative's events of the last 7 days is accepted iff
            log Z(A) + log Z(B) - log Z(A + B) + log alpha + (DM entity terms)/T > 0
          Unit for merge and split: events, so kappa_s (the spread of event directions inside a narrative)
          sets the scale at which narratives live.
Statistics decay with the locked narrative time scale sigma (336 h), stored in exp(t / sigma) units.

Fitted, not set: alpha, kappa_s, T (prequential score on the warmup only; ygg.narratives.fit).
Hand-set and disclosed: beta, dormancy after 7 days, sigma = 336 h, the event clusterer (proposals only).

Prequential score. When an event cluster is first seen (one story), before any update:
  log p(x | w) = log sum_k r_k(w) vMF(x; mu_k, kappa_k),  r_k(w) proportional to pi_k phi_k(w)^(1/T) * time prior
A proper score for the direction given the entities, comparable across alpha, kappa_s and T. Brand-new
events only: narratives that are just yesterday's events do not help predict new ones.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
from scipy.special import gammaln, ive

from ygg.determinism import stable_hash
from ygg.narratives.narratives import largest_remainder_uint8


# ---------------------------------------------------------------- vMF normalizer in high dimension
def log_iv(nu: float, x: float) -> float:
    """log I_nu(x). nu >= 30: uniform asymptotic (Debye) expansion with two correction terms (relative error
    ~ nu^-3, below 1e-7 at d = 384); smaller nu: scipy, with Debye as the fallback when it underflows."""
    if x <= 0:
        return 0.0 if nu == 0 else -math.inf
    if nu < 30:
        v = ive(nu, x)
        if v > 0 and math.isfinite(v):
            return math.log(v) + x
    z = x / nu
    s = math.sqrt(1.0 + z * z)
    eta = s + math.log(z / (1.0 + s))
    t = 1.0 / s
    u1 = (3 * t - 5 * t ** 3) / 24.0
    u2 = (81 * t ** 2 - 462 * t ** 4 + 385 * t ** 6) / 1152.0
    return nu * eta - 0.5 * math.log(2 * math.pi * nu) - 0.5 * math.log(s) + math.log1p(u1 / nu + u2 / nu ** 2)


def log_cd(kappa: float, d: int) -> float:
    """log C_d(kappa), the vMF normalizer on the unit sphere in R^d (kappa -> 0: one over the surface area)."""
    if kappa <= 1e-9:
        return float(gammaln(d / 2.0)) - math.log(2.0) - (d / 2.0) * math.log(math.pi)
    nu = d / 2.0 - 1.0
    return nu * math.log(kappa) - (d / 2.0) * math.log(2 * math.pi) - log_iv(nu, kappa)


def kappa_mle(rbar: float, d: int, rbar_max: float = 0.98) -> float:
    """Banerjee et al. (2005) approximation, with rbar clipped so kappa stays finite."""
    r = min(max(rbar, 1e-6), rbar_max)
    return max(r * (d - r * r) / (1 - r * r), 1e-6)


@dataclass
class LearnedConfig:
    kappa_s: float = 250.0              # fitted: spread of event directions inside a narrative
    log_alpha: float = -15.0            # fitted: each narrative costs -log alpha nats
    temp: float = 2.0                   # fitted: entity temperature (correlated entities are not independent evidence)
    beta: float = 10.0                  # hand-set, disclosed: Dirichlet smoothing toward the corpus
    sigma_h: float = 14 * 24.0          # locked (3.9'): narrative time scale (decay and time prior)
    dormant_after_h: float = 7 * 24.0   # hand-set, disclosed
    top_m: int = 3
    n_cand: int = 16                    # scored exactly: the 16 most similar narratives + those holding a rare entity
    rare_idf: float = 5.0
    ent_keep: int = 300                 # entity profile size per narrative (pruned to the heaviest)
    check_every_windows: int = 24       # merge / split / dormancy checks every 6 hours
    split_min_events: int = 4
    rbar_max: float = 0.98


@dataclass
class LNarrative:
    nid: str
    slot: int
    S: np.ndarray                       # decayed sum of event directions (stored in exp(t / sigma) units)
    N: float                            # decayed event count (same units)
    ents: dict                          # entity -> decayed weight (same units)
    E: float                            # decayed entity total (same units)
    state: str
    born_h: float
    t_last_h: float
    mass_total: float = 0.0
    label: str = ""
    events: list = field(default_factory=list)      # (t_h, cid) routed in the last 7 days (split proposals)

    @property
    def mu(self) -> np.ndarray:
        n = np.linalg.norm(self.S)
        return self.S / n if n > 0 else self.S


@dataclass
class LearnedNarrativeModel:
    dim: int
    cfg: LearnedConfig = field(default_factory=LearnedConfig)
    narratives: dict = field(default_factory=dict)
    lineage: list = field(default_factory=list)

    def __post_init__(self):
        self.MU = np.zeros((256, self.dim), np.float32)   # per slot: direction, N, E (stored units), t_last
        self.Nv = np.zeros(256)
        self.Ev = np.zeros(256)
        self.Tv = np.zeros(256)
        self.Ntot = 0.0                                   # sum of N over narratives (stored units)
        self._active = None                               # (nids sorted, slots, position map); None = stale
        self.slots_free: list[int] = []
        self.next_slot = 0
        self.by_entity: dict = defaultdict(set)          # entity -> narratives whose profile holds it
        self.S0 = np.zeros(self.dim)                      # background: decayed sum of event directions
        self.N0 = 0.0
        self.mu0 = np.zeros(self.dim)
        self.kappa0 = 1e-6
        self.assigned: dict = {}                          # event cid -> ("~bg" or "nar", t_h): statistics added once
        self.emerged_from: set = set()
        self.preq = {"sum": 0.0, "n": 0}
        self.df, self.df_vocab, self.df_total = {}, 0, 0.0
        self.P = np.zeros((1024, self.dim), np.float32)     # birth pool: recent background events with >= 2 stories
        self.P_cid = np.full(1024, -1, dtype=np.int64)
        self.P_t = np.zeros(1024)
        self.pool: dict = {}                                # cid -> slot
        self.P_free: list[int] = []
        self.P_next = 0
        self._lc_s = log_cd(self.cfg.kappa_s, self.dim)
        self._lc_0 = log_cd(self.kappa0, self.dim)

    # ------------------------------------------------------------ helpers
    @property
    def kappa(self) -> float:
        return self.cfg.kappa_s

    def _u(self, t_h: float) -> float:
        """Weight of an observation at t_h in exp(t / sigma) units, so decay needs no per-step rescaling."""
        return math.exp(t_h / self.cfg.sigma_h)

    def set_background_counts(self, df: dict, n_vocab: int, total: float) -> None:
        self.df, self.df_vocab, self.df_total = df, n_vocab, total

    def phi0(self, e: str) -> float:
        return (self.df.get(e, 0) + 0.5) / (self.df_total + 0.5 * (self.df_vocab + 1))

    def _ids(self, states=("alive", "dormant")) -> list[str]:
        return sorted(n for n, v in self.narratives.items() if v.state in states)

    def active(self) -> tuple[list[str], np.ndarray, dict]:
        if self._active is None:
            ids = sorted(self.narratives)
            self._active = (ids, np.array([self.narratives[n].slot for n in ids], dtype=np.int64),
                            {n: i for i, n in enumerate(ids)})
        return self._active

    def _refresh_bg(self) -> None:
        if self.N0 > 0:
            nrm = float(np.linalg.norm(self.S0))
            if nrm > 0:
                self.mu0 = self.S0 / nrm
                self.kappa0 = kappa_mle(nrm / self.N0, self.dim, self.cfg.rbar_max)
                self._lc_0 = log_cd(self.kappa0, self.dim)

    def _set_row(self, n: LNarrative) -> None:
        while n.slot >= len(self.MU):
            self.MU = np.concatenate([self.MU, np.zeros_like(self.MU)])
            self.Nv, self.Ev, self.Tv = (np.concatenate([a, np.zeros_like(a)]) for a in (self.Nv, self.Ev, self.Tv))
        self.MU[n.slot] = n.mu
        self.Nv[n.slot], self.Ev[n.slot], self.Tv[n.slot] = n.N, n.E, n.t_last_h

    def _new_slot(self) -> int:
        if self.slots_free:
            return self.slots_free.pop()
        self.next_slot += 1
        return self.next_slot - 1

    def _log_pi0(self) -> float:
        tot = self.N0 + self.Ntot
        return math.log(self.N0 / tot) if tot > 0 and self.N0 > 0 else 0.0

    def diagnostics(self, t_h: float) -> dict:
        """kappa implied by the data (event-level mean resultant, narratives with >= 3 events) vs the fitted kappa_s."""
        u = self._u(t_h)
        ks = [kappa_mle(float(np.linalg.norm(n.S) / n.N), self.dim, self.cfg.rbar_max)
              for n in self.narratives.values() if n.N / u >= 3]
        return {"kappa_s": self.cfg.kappa_s, "kappa_implied_median": float(np.median(ks)) if ks else None,
                "kappa0": self.kappa0, "pi0": math.exp(self._log_pi0()), "alive": len(self._ids(("alive",))),
                "dormant": len(self._ids(("dormant",))), "preq_mean": self.preq["sum"] / max(self.preq["n"], 1)}

    # ------------------------------------------------------------ scoring
    def gains(self, x: np.ndarray, w: dict, t_h: float, idf=None, with_cos: bool = False):
        """Exact gains over the background for the candidates: the n_cand most similar narratives plus any
        narrative whose profile holds one of the event's rare entities."""
        ids, slots, pos = self.active()
        if not ids:
            return ([], np.zeros(0), np.zeros(0)) if with_cos else ([], np.zeros(0))
        cos_all = self.MU[slots] @ x.astype(np.float32)
        k = min(self.cfg.n_cand, len(ids))
        cand = set(np.argpartition(-cos_all, k - 1)[:k].tolist()) if k < len(ids) else set(range(len(ids)))
        if idf is not None:
            for e in w:
                owners = self.by_entity.get(e)
                if owners and idf.idf(e) >= self.cfg.rare_idf:
                    cand |= {pos[o] for o in owners}
        ci = np.array(sorted(cand), dtype=np.int64)
        sl = slots[ci]
        u_now = self._u(t_h)
        b, T = self.cfg.beta, self.cfg.temp
        bg = self._lc_0 + self.kappa0 * float(self.mu0 @ x)
        dt = t_h - self.Tv[sl]
        g = (np.log(np.maximum(self.Nv[sl], 1e-300) / (self.N0 + self.Ntot)) - self._log_pi0() + self._lc_s
             + self.cfg.kappa_s * cos_all[ci].astype(float) - bg
             + sum(w.values()) * (math.log(b) - np.log(self.Ev[sl] / u_now + b)) / T
             - dt * dt / (2.0 * self.cfg.sigma_h ** 2))
        cand_ids = [ids[i] for i in ci]
        where = None
        for e, we in w.items():
            owners = self.by_entity.get(e)
            if not owners:
                continue
            p0 = self.phi0(e)
            bp0 = b * p0
            lb = math.log(bp0)
            if len(owners) > len(cand_ids):               # common entity: scan the candidates instead
                for j, nid in enumerate(cand_ids):
                    c = self.narratives[nid].ents.get(e)
                    if c:
                        g[j] += we * (math.log(c / u_now + bp0) - lb) / T
            else:
                if where is None:
                    where = {int(c): j for j, c in enumerate(ci)}
                for o in owners:
                    j = where.get(pos[o])
                    if j is not None:
                        g[j] += we * (math.log(self.narratives[o].ents[e] / u_now + bp0) - lb) / T
        if with_cos:
            return cand_ids, g, cos_all[ci].astype(float)
        return cand_ids, g

    def membership(self, x: np.ndarray, w: dict, t_h: float, idf=None, score: bool = False
                   ) -> tuple[list[str], np.ndarray, str | None]:
        """Top-m narratives with uint8 shares (background share last) and the MAP narrative (None = background)."""
        cand, g, cos = self.gains(x, w, t_h, idf, with_cos=True)
        if score:
            self.score_new(x, w, cand, g, cos)
        if len(cand) == 0:
            return [], np.array([255], np.uint8), None
        order = np.lexsort((np.arange(len(g)), -g))[: self.cfg.top_m]
        logits = np.array([g[i] for i in order] + [0.0])
        p = np.exp(logits - logits.max())
        p /= p.sum()
        routed = cand[int(order[0])] if g[order[0]] > 0 else None
        return [cand[i] for i in order], largest_remainder_uint8(p), routed

    def score_new(self, x: np.ndarray, w: dict, cand: list[str], g: np.ndarray, cos: np.ndarray) -> float:
        """Prequential log p(x | w) for a brand-new event, before any update (see module doc)."""
        ent0 = sum(we * math.log(self.phi0(e)) for e, we in w.items()) / self.cfg.temp
        bg_vmf = self._lc_0 + self.kappa0 * float(self.mu0 @ x)
        base = self._log_pi0() + ent0                   # log r_k up to a shared constant
        n_vmf = self._lc_s + self.cfg.kappa_s * cos      # log vMF density of x under each candidate
        r = np.concatenate([[base], base + g - (n_vmf - bg_vmf)])
        r -= np.logaddexp.reduce(r)
        val = float(np.logaddexp.reduce(r + np.concatenate([[bg_vmf], n_vmf])))
        self.preq["sum"] += val
        self.preq["n"] += 1
        return val

    # ------------------------------------------------------------ evidence (closed form)
    def log_z_vmf(self, S: np.ndarray, n: float) -> float:
        """Conjugate evidence of n unit vectors with sum S: vMF(kappa_s) likelihood, direction prior vMF(mu_0, kappa_0)."""
        r = float(np.linalg.norm(self.cfg.kappa_s * S + self.kappa0 * self.mu0))
        return n * self._lc_s + self._lc_0 - log_cd(r, self.dim)

    def log_dm(self, cnt: dict) -> float:
        """Dirichlet-multinomial evidence of entity counts under the prior beta * phi_0, minus the background likelihood."""
        b = self.cfg.beta
        if not cnt:
            return 0.0
        c = np.fromiter(cnt.values(), float, len(cnt))
        p0 = np.fromiter((self.phi0(e) for e in cnt), float, len(cnt))
        return float(gammaln(b) - gammaln(b + c.sum()) + (gammaln(b * p0 + c) - gammaln(b * p0) - c * np.log(p0)).sum())

    def group_evidence(self, X: np.ndarray, W: list[dict]) -> float:
        """log BF(these events share a narrative direction and entity profile vs the background), without alpha."""
        S = X.sum(0)
        bg = len(X) * self._lc_0 + self.kappa0 * float(self.mu0 @ S)
        E = defaultdict(float)
        for w in W:
            for e, c in w.items():
                E[e] += c
        return self.log_z_vmf(S, len(X)) - bg + self.log_dm(dict(E)) / self.cfg.temp

    # ------------------------------------------------------------ birth pool (recent background events)
    def pool_upsert(self, cid: int, x: np.ndarray, t_h: float) -> None:
        s = self.pool.get(cid)
        if s is None:
            if self.P_free:
                s = self.P_free.pop()
            else:
                if self.P_next >= len(self.P):
                    self.P = np.concatenate([self.P, np.zeros_like(self.P)])
                    self.P_cid = np.concatenate([self.P_cid, np.full(len(self.P_cid), -1, dtype=np.int64)])
                    self.P_t = np.concatenate([self.P_t, np.zeros_like(self.P_t)])
                s = self.P_next
                self.P_next += 1
            self.pool[cid] = s
            self.P_cid[s] = cid
        self.P[s] = x
        self.P_t[s] = t_h

    def pool_remove(self, cid: int) -> None:
        s = self.pool.pop(cid, None)
        if s is not None:
            self.P[s] = 0.0
            self.P_cid[s] = -1
            self.P_free.append(s)

    def try_birth(self, cid: int, x: np.ndarray, w: dict, clusters: dict, t_h: float, window: int, titles: dict,
                  k: int = 8, max_group: int = 8) -> str | None:
        """Grow G from the event's nearest pool events while the evidence rises; start a narrative if
        evidence + log alpha > 0. The pool is a proposal mechanism only; acceptance is the Bayes factor."""
        if self.P_next == 0:
            return None
        cos = self.P[: self.P_next] @ x.astype(np.float32)
        own = self.pool.get(cid)
        if own is not None:
            cos[own] = -2.0
        cos[self.P_cid[: self.P_next] < 0] = -2.0
        kk = min(k, self.P_next)
        top = np.argpartition(-cos, kk - 1)[:kk]
        top = [int(s) for s in sorted(top, key=lambda s: (-cos[s], int(self.P_cid[s]))) if cos[s] > -1.5]
        nbrs = [(int(self.P_cid[s]), clusters[int(self.P_cid[s])]) for s in top if int(self.P_cid[s]) in clusters]
        G, Wg, members = [x.astype(float)], [w], [cid]
        best = -math.inf
        for ncid, cl in nbrs:
            if len(G) >= max_group:
                break
            wn = {e: c / cl.n for e, c in cl.cnt.items()}
            ev = self.group_evidence(np.stack(G + [cl.centroid.astype(float)]), Wg + [wn])
            if ev > best:
                best = ev
                G.append(cl.centroid.astype(float))
                Wg.append(wn)
                members.append(ncid)
        if len(G) < 2 or best + self.cfg.log_alpha <= 0:
            return None
        lead = max(members, key=lambda c: (clusters[c].n if c in clusters else 1, -c))
        nid = stable_hash("narrative", *map(str, sorted(members)), str(window))[:16]
        n = LNarrative(nid, self._new_slot(), np.zeros(self.dim), 0.0, {}, 0.0, "alive", t_h, t_h, 0.0, titles.get(lead, ""))
        self.narratives[nid] = n
        self._active = None
        for c, xg, wg in zip(members, G, Wg):
            self._leave_background(c, xg)
            self.pool_remove(c)
            th = self.assigned.get(c, (None, t_h))[1]
            self.assigned[c] = ("nar", th)
            self._add(n, xg, wg, th)
            n.events.append((th, c))
            self.emerged_from.add(c)
        self.lineage.append({"window": window, "kind": "emerge", "parents": [], "children": [nid], "shares": [1.0]})
        return nid

    def _now(self, n: LNarrative, t_h: float) -> tuple[np.ndarray, float, dict]:
        s = 1.0 / self._u(t_h)
        return n.S * s, n.N * s, {e: c * s for e, c in n.ents.items()}

    def merge_evidence(self, a: LNarrative, b: LNarrative, t_h: float) -> float:
        Sa, Na, Ea = self._now(a, t_h)
        Sb, Nb, Eb = self._now(b, t_h)
        Eab = dict(Ea)
        for e, c in Eb.items():
            Eab[e] = Eab.get(e, 0.0) + c
        v = self.log_z_vmf(Sa + Sb, Na + Nb) - self.log_z_vmf(Sa, Na) - self.log_z_vmf(Sb, Nb)
        ent = self.log_dm(Eab) - self.log_dm(Ea) - self.log_dm(Eb)
        return v + ent / self.cfg.temp - self.cfg.log_alpha

    # ------------------------------------------------------------ updates
    def background_add(self, cid: int, x: np.ndarray, t_h: float) -> None:
        if cid in self.assigned:
            return
        self.assigned[cid] = ("~bg", t_h)
        u = self._u(t_h)
        self.S0 = self.S0 + u * x
        self.N0 += u
        self._refresh_bg()

    def _leave_background(self, cid: int, x: np.ndarray) -> None:
        prev = self.assigned.get(cid)
        if prev is not None and prev[0] == "~bg":
            u0 = self._u(prev[1])
            self.S0 = self.S0 - u0 * x
            self.N0 = max(self.N0 - u0, 0.0)

    def route(self, cid: int, nid: str, x: np.ndarray, w: dict, mass: float, t_h: float, window: int) -> None:
        n = self.narratives[nid]
        if n.state == "dormant":
            n.state = "alive"
            self.lineage.append({"window": window, "kind": "reactivate", "parents": [nid], "children": [nid], "shares": [1.0]})
        prev = self.assigned.get(cid)
        if prev is None or prev[0] == "~bg":
            self._leave_background(cid, x)
            self.pool_remove(cid)
            self.assigned[cid] = ("nar", t_h)
            self._add(n, x, w, t_h)
            n.events.append((t_h, cid))
        n.t_last_h = t_h
        n.mass_total += mass
        self.Tv[n.slot] = t_h

    def _add(self, n: LNarrative, x: np.ndarray, w: dict, t_h: float) -> None:
        u = self._u(t_h)
        n.S = n.S + u * x
        n.N += u
        self.Ntot += u
        for e, we in w.items():
            if e not in n.ents:
                self.by_entity[e].add(n.nid)
            n.ents[e] = n.ents.get(e, 0.0) + u * we
            n.E += u * we
        if len(n.ents) > self.cfg.ent_keep * 4 // 3:
            keep = dict(sorted(n.ents.items(), key=lambda kv: (-kv[1], kv[0]))[: self.cfg.ent_keep])
            for e in n.ents:
                if e not in keep:
                    self._unindex(e, n.nid)
            n.ents = keep
        self._set_row(n)

    def _unindex(self, e: str, nid: str) -> None:
        s = self.by_entity.get(e)
        if s is not None:
            s.discard(nid)
            if not s:
                del self.by_entity[e]

    def emerge(self, cid: int, x: np.ndarray, w: dict, t_h: float, window: int, label: str) -> str:
        nid = stable_hash("narrative", str(cid), str(window))[:16]
        n = LNarrative(nid, self._new_slot(), np.zeros(self.dim), 0.0, {}, 0.0, "alive", t_h, t_h, 0.0, label)
        self.narratives[nid] = n
        self._active = None
        self._leave_background(cid, x)
        self.assigned[cid] = ("nar", t_h)
        self._add(n, x, w, t_h)
        n.events.append((t_h, cid))
        self.emerged_from.add(cid)
        self.lineage.append({"window": window, "kind": "emerge", "parents": [], "children": [nid], "shares": [1.0]})
        return nid

    def _drop(self, nid: str) -> LNarrative:
        n = self.narratives.pop(nid)
        for e in n.ents:
            self._unindex(e, nid)
        self.MU[n.slot] = 0.0
        self.Nv[n.slot] = self.Ev[n.slot] = 0.0
        self.Ntot -= n.N
        self.slots_free.append(n.slot)
        self._active = None
        return n

    def _make(self, nid, S, N, ents, E, state, born_h, t_last_h, mass, label, events) -> LNarrative:
        n = LNarrative(nid, self._new_slot(), S, N, ents, E, state, born_h, t_last_h, mass, label, events)
        self.narratives[nid] = n
        self.Ntot += N
        self._active = None
        for e in ents:
            self.by_entity[e].add(nid)
        self._set_row(n)
        return n

    # ------------------------------------------------------------ 6-hourly structure checks
    def lineage_check(self, now_h: float, window: int, clusters: dict | None = None) -> list[dict]:
        out = []
        for nid in self._ids(("alive",)):
            n = self.narratives[nid]
            n.events = [(t, c) for t, c in n.events if t >= now_h - 7 * 24.0]
            if now_h - n.t_last_h > self.cfg.dormant_after_h:
                n.state = "dormant"
                out.append({"window": window, "kind": "dormant", "parents": [nid], "children": [nid], "shares": [1.0]})
        out += self._merges(now_h, window)
        if clusters is not None:
            out += self._splits(now_h, window, clusters)
        for cid in [c for c, (_, th) in self.assigned.items() if th < now_h - 7 * 24.0]:
            del self.assigned[cid]
        for cid in [c for c, s in self.pool.items() if self.P_t[s] < now_h - 7 * 24.0]:
            self.pool_remove(cid)
        self.lineage += out
        return out

    def _merges(self, now_h: float, window: int) -> list[dict]:
        ids = self._ids(("alive",))
        if len(ids) < 2:
            return []
        M = self.MU[np.array([self.narratives[n].slot for n in ids])]
        C = M @ M.T
        np.fill_diagonal(C, -2.0)
        nn = np.argmax(C, axis=1)
        props = sorted({(min(i, int(j)), max(i, int(j))) for i, j in enumerate(nn)}, key=lambda p: (-float(C[p]), p))
        out, used = [], set()
        for i, j in props:
            a, b = ids[i], ids[j]
            if a in used or b in used or self.merge_evidence(self.narratives[a], self.narratives[b], now_h) <= 0:
                continue
            used |= {a, b}
            na, nb = self._drop(a), self._drop(b)
            ents = dict(na.ents)
            for e, c in nb.ents.items():
                ents[e] = ents.get(e, 0.0) + c
            nid = stable_hash("merge", a, b, str(window))[:16]
            heavier = na if na.mass_total >= nb.mass_total else nb
            self._make(nid, na.S + nb.S, na.N + nb.N, ents, na.E + nb.E, "alive", min(na.born_h, nb.born_h),
                       max(na.t_last_h, nb.t_last_h), na.mass_total + nb.mass_total, heavier.label, sorted(na.events + nb.events))
            out.append({"window": window, "kind": "merge", "parents": [a, b], "children": [nid], "shares": [1.0]})
        return out

    def _splits(self, now_h: float, window: int, clusters: dict) -> list[dict]:
        out = []
        u_now = self._u(now_h)
        for nid in self._ids(("alive",)):
            n = self.narratives[nid]
            evs = [(t, c, clusters[c]) for t, c in n.events if c in clusters]
            if len(evs) < self.cfg.split_min_events:
                continue
            X = np.stack([cl.centroid for _, _, cl in evs]).astype(float)
            D = np.array([self._u(t) for t, _, _ in evs]) / u_now          # decay weights
            c1 = X[int(np.argmin(X @ n.mu))]
            c2 = X[int(np.argmin(X @ c1))]
            lab = None
            for _ in range(8):
                new = (X @ c1 < X @ c2).astype(int)
                if (lab is not None and np.array_equal(new, lab)) or new.min() == new.max():
                    lab = new
                    break
                lab = new
                c1 = X[lab == 0].sum(0); c1 /= np.linalg.norm(c1)
                c2 = X[lab == 1].sum(0); c2 /= np.linalg.norm(c2)
            if lab.min() == lab.max():
                continue
            halves = []
            for side in (0, 1):
                idx = np.flatnonzero(lab == side)
                E = defaultdict(float)
                for i in idx:
                    cl = evs[i][2]
                    for e, c in cl.cnt.items():
                        E[e] += D[i] * c / cl.n
                halves.append(((D[idx, None] * X[idx]).sum(0), float(D[idx].sum()), dict(E), idx))
            (Sa, Na, Ea, _), (Sb, Nb, Eb, _) = halves
            Eab = dict(Ea)
            for e, c in Eb.items():
                Eab[e] = Eab.get(e, 0.0) + c
            ev = (self.log_z_vmf(Sa, Na) + self.log_z_vmf(Sb, Nb) - self.log_z_vmf(Sa + Sb, Na + Nb)
                  + (self.log_dm(Ea) + self.log_dm(Eb) - self.log_dm(Eab)) / self.cfg.temp + self.cfg.log_alpha)
            if ev <= 0:
                continue
            parent = self._drop(nid)
            share = Na / (Na + Nb)
            kids = []
            for k, (S, N, E, idx) in enumerate(halves):
                kid = stable_hash("split", nid, str(k), str(window))[:16]
                q = share if k == 0 else 1 - share
                self._make(kid, S * u_now, N * u_now, {e: c * u_now for e, c in E.items()}, sum(E.values()) * u_now, "alive",
                           now_h, now_h, parent.mass_total * q, parent.label, [(evs[i][0], evs[i][1]) for i in idx])
                kids.append(kid)
            out.append({"window": window, "kind": "split", "parents": [nid], "children": kids, "shares": [float(share), float(1 - share)]})
        return out

    # ------------------------------------------------------------ canonical state (digest material)
    def canon(self) -> tuple:
        nar = [(n.nid, n.S.tobytes(), n.N, sorted(n.ents.items()), n.E, n.state, n.born_h, n.t_last_h, n.mass_total, n.events)
               for n in sorted(self.narratives.values(), key=lambda n: n.nid)]
        pool = sorted((c, self.P[s].tobytes(), self.P_t[s]) for c, s in self.pool.items())
        return (nar, self.S0.tobytes(), self.N0, sorted(self.assigned.items()), len(self.lineage), self.preq["n"], self.preq["sum"], pool)
