"""Layer 2: persistent narratives with content-only assignment (3.9'), learned vMF calibration (3.4'),
soft membership (3.3) and explicit lineage (3.5).

  gain(c, n) = kappa * cos(x_c, mu_n) + log pi_n - log pi_0 + log C_d(kappa) + log A_d
               + w_ent * J_idf(ents_c, E_n) - (t_c - t_n)^2 / (2 * sigma_narr^2)
  route: alive argmax if gain >= tau_alive; dormant argmax if gain >= tau_dormant (> tau_alive); else none
  emerge: an event cluster that reaches m_emerge objects while routed to none starts a narrative
  membership: posterior over the top 3 narratives plus none; uint8 via largest-remainder rounding (sums to 255)
  EM (daily, trailing 7 days, fixed iteration count): mu_n, kappa (Banerjee et al. 2005), pi_n, pi_0
  lineage: merge after 3 agreeing 6-hour checks; split after 3 agreeing checks; dormant after 7 days without mass

Cut note: the entity weight w_ent is fixed in config, and themes are not used yet. 3.4' fits w_ent in the M-step.

Changes from the first real-data run (proposed, pending lock):
  - "none" is a broad vMF fitted to the corpus (its own EM component), not the uniform density on the sphere.
    Against uniform, a story joined a narrative once its cosine to the centroid exceeded ~0.11 (kappa 60),
    which let a few narratives absorb most of the news.
  - Joining requires salient shared entities (IDF-weighted Jaccard >= 0.05) or a very high title cosine
    (>= 0.6). Title cosine alone is a weak signal here (same-event pairs average 0.39).
  - m_emerge = 25 keeps emergence at ~58 narratives a day (target 100-300 alive under 7-day dormancy).
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field

import numpy as np
from scipy.special import gammaln, ive

from ygg.determinism import stable_hash
from ygg.narratives.features import weighted_jaccard


@dataclass
class NarrativeConfig:
    kappa0: float = 60.0
    w_ent: float = 6.0
    tau_alive: float = 2.0
    tau_dormant: float = 4.0
    sigma_narr_h: float = 14 * 24.0       # locked (3.9')
    m_emerge: int = 25                    # event-cluster objects needed before it may start a narrative (calibrated: ~58 new/day)
    eta: float = 0.02                     # slow centroid drift per absorbed event-cluster update
    top_m: int = 3
    ent_top: int = 10                     # entity term computed for the 10 most similar narratives
    dormant_after_h: float = 7 * 24.0
    em_iters: int = 3
    rbar_max: float = 0.98                # clip in the M-step (red-team proposal: kappa must stay finite)
    check_every_windows: int = 24         # 6 hours
    checks_needed: int = 3
    tau_merge: float = 0.93
    tau_split: float = 0.55
    split_min_share: float = 0.25
    split_min_items: int = 12
    background: str = "corpus_vmf"        # "uniform" (3.4' as written) or "corpus_vmf" (proposed fix, see module doc)
    j_gate: float = 0.05                  # join only with salient shared entities (IDF-weighted Jaccard) ...
    cos_gate: float = 0.6                 # ... or, without entity overlap, a very high title cosine


@dataclass
class Narrative:
    nid: str
    mu: np.ndarray
    ents: dict
    state: str
    born_h: float
    t_last_h: float
    mass_total: float = 0.0
    label: str = ""
    ent_sum: float = -1.0

    def esum(self) -> float:
        if self.ent_sum < 0:
            self.ent_sum = float(sum(self.ents.values()))
        return self.ent_sum


def log_vmf_norm(kappa: float, d: int) -> float:
    """log C_d(kappa) + log A_d: log density ratio of a vMF at its mode vs the uniform sphere, minus kappa."""
    nu = d / 2.0 - 1.0
    log_c = nu * math.log(kappa) - (d / 2.0) * math.log(2 * math.pi) - (math.log(ive(nu, kappa)) + kappa)
    log_a = math.log(2.0) + (d / 2.0) * math.log(math.pi) - float(gammaln(d / 2.0))
    return log_c + log_a


def log_c(kappa: float, d: int) -> float:
    """log C_d(kappa), the vMF normalizer on the unit sphere in d dimensions."""
    nu = d / 2.0 - 1.0
    return nu * math.log(kappa) - (d / 2.0) * math.log(2 * math.pi) - (math.log(ive(nu, kappa)) + kappa)


def largest_remainder_uint8(p: np.ndarray) -> np.ndarray:
    """Quantize a probability vector to integers summing to exactly 255 (keeps Lemma 5.1 exact)."""
    x = p * 255.0
    base = np.floor(x).astype(int)
    rem = 255 - int(base.sum())
    order = np.lexsort((np.arange(len(p)), -(x - base)))      # ties: lower index first (D4)
    base[order[:rem]] += 1
    return base.astype(np.uint8)


@dataclass
class NarrativeModel:
    dim: int
    cfg: NarrativeConfig = field(default_factory=NarrativeConfig)
    narratives: dict = field(default_factory=dict)
    kappa: float = 0.0
    log_pi: dict = field(default_factory=dict)
    log_pi0: float = math.log(0.5)
    lineage: list = field(default_factory=list)
    em_buffer: deque = field(default_factory=deque)         # (t_h, cid, x, ents, mass)
    merge_streak: dict = field(default_factory=lambda: defaultdict(int))
    split_streak: dict = field(default_factory=lambda: defaultdict(int))
    emerged_from: set = field(default_factory=set)
    refit_count: int = 0

    def __post_init__(self):
        self.kappa = self.kappa or self.cfg.kappa0
        self.mu0 = np.zeros(self.dim)                       # background ("none") direction
        self.kappa0 = 1.0
        self.bg_sum = np.zeros(self.dim)                    # causal running sum of event vectors (initial background)
        self.bg_n = 0.0
        self._refresh_norm()

    def _refresh_norm(self) -> None:
        if self.cfg.background == "uniform":
            self._norm = log_vmf_norm(self.kappa, self.dim)
        else:
            self._norm = log_c(self.kappa, self.dim) - log_c(self.kappa0, self.dim)

    def _bg(self, X: np.ndarray) -> np.ndarray:
        """kappa0 * cos(x, mu0): the background log-density up to its constant (zero for the uniform background)."""
        if self.cfg.background == "uniform":
            return np.zeros(X.shape[0]) if X.ndim == 2 else 0.0
        return self.kappa0 * (X @ self.mu0)

    def _update_bg_running(self, x: np.ndarray, mass: float) -> None:
        if self.cfg.background == "uniform" or self.refit_count > 0:
            return
        self.bg_sum += mass * x
        self.bg_n += mass
        r = float(np.linalg.norm(self.bg_sum) / max(self.bg_n, 1e-9))
        if self.bg_n >= 20 and r > 0:
            self.mu0 = self.bg_sum / np.linalg.norm(self.bg_sum)
            r = min(r, self.cfg.rbar_max)
            self.kappa0 = max(r * (self.dim - r * r) / (1 - r * r), 1.0)
            self._refresh_norm()

    # ------------------------------------------------------------ scoring
    def _ids(self, states=("alive", "dormant")) -> list[str]:
        return sorted(n for n, v in self.narratives.items() if v.state in states)

    def gains(self, x: np.ndarray, ents: dict, t_h: float, ids: list[str], gate: bool = False) -> np.ndarray:
        if not ids:
            return np.zeros(0)
        mus = np.stack([self.narratives[n].mu for n in ids])
        cos = mus @ x
        g = self.kappa * cos + np.array([self.log_pi.get(n, math.log(1e-3)) for n in ids]) - self.log_pi0 + self._norm - self._bg(x)
        top = np.argsort(-cos, kind="stable")[: self.cfg.ent_top]
        e_sum = sum(ents.values())
        jac = np.zeros(len(ids))
        for i in top:
            nar = self.narratives[ids[i]]
            jac[i] = weighted_jaccard(ents, nar.ents, e_sum, nar.esum())
            g[i] += self.cfg.w_ent * jac[i]
        dt = np.array([t_h - self.narratives[n].t_last_h for n in ids])
        g = g - dt * dt / (2.0 * self.cfg.sigma_narr_h ** 2)
        if gate:
            ok = (jac >= self.cfg.j_gate) | (cos >= self.cfg.cos_gate)
            g = np.where(ok, g, -np.inf)
        return g

    def membership(self, x: np.ndarray, ents: dict, t_h: float) -> tuple[list[str], np.ndarray, str | None]:
        """Top-m narratives (alive or dormant) with uint8 shares, the none share last; plus the routed narrative."""
        ids = self._ids()
        g = self.gains(x, ents, t_h, ids, gate=True)
        if len(ids) == 0:
            return [], np.array([255], np.uint8), None
        alive = np.array([self.narratives[n].state == "alive" for n in ids])
        routed = None
        if alive.any() and g[alive].max() >= self.cfg.tau_alive:
            routed = ids[int(np.flatnonzero(alive)[np.argmax(g[alive])])]
        elif (~alive).any() and g[~alive].max() >= self.cfg.tau_dormant:
            routed = ids[int(np.flatnonzero(~alive)[np.argmax(g[~alive])])]
        order = np.argsort(-g, kind="stable")[: self.cfg.top_m]
        # only narratives a cluster may join (alive, or dormant above the stricter bar) receive mass
        keep = [i for i in order if np.isfinite(g[i]) and ((alive[i] and g[i] >= self.cfg.tau_alive) or (not alive[i] and g[i] >= self.cfg.tau_dormant))]
        logits = np.array([g[i] for i in keep] + [0.0])
        p = np.exp(logits - logits.max())
        p /= p.sum()
        return [ids[i] for i in keep], largest_remainder_uint8(p), routed

    # ------------------------------------------------------------ updates
    def absorb(self, nid: str, x: np.ndarray, ents: dict, mass: float, t_h: float, window: int) -> None:
        n = self.narratives[nid]
        if n.state == "dormant":
            n.state = "alive"
            self.lineage.append({"window": window, "kind": "reactivate", "parents": [nid], "children": [nid], "shares": [1.0]})
        v = (1 - self.cfg.eta) * n.mu + self.cfg.eta * x
        n.mu = v / max(np.linalg.norm(v), 1e-12)
        for e, w in ents.items():
            n.ents[e] = 0.98 * n.ents.get(e, 0.0) + w
        if len(n.ents) > 400:
            n.ents = dict(sorted(n.ents.items(), key=lambda kv: (-kv[1], kv[0]))[:300])
        n.ent_sum = -1.0
        n.t_last_h = t_h
        n.mass_total += mass

    def emerge(self, cid: int, x: np.ndarray, ents: dict, t_h: float, window: int, label: str) -> str:
        nid = stable_hash("narrative", str(cid), str(window))[:16]
        self.narratives[nid] = Narrative(nid, x.copy(), dict(ents), "alive", t_h, t_h, 0.0, label)
        alive = len(self._ids(("alive",)))
        self.log_pi[nid] = math.log(1.0 / max(alive, 1))
        self.emerged_from.add(cid)
        self.lineage.append({"window": window, "kind": "emerge", "parents": [], "children": [nid], "shares": [1.0]})
        return nid

    def record(self, t_h: float, cid: int, x: np.ndarray, ents: dict, mass: float) -> None:
        self.em_buffer.append((t_h, cid, np.asarray(x, np.float32), None, mass))
        self._update_bg_running(np.asarray(x, float), mass)

    # ------------------------------------------------------------ daily EM (fitted through the previous day: D7)
    def refit(self, now_h: float) -> dict:
        while self.em_buffer and self.em_buffer[0][0] < now_h - 7 * 24.0:
            self.em_buffer.popleft()
        ids = self._ids(("alive",))
        if not ids or len(self.em_buffer) < 50:
            return {"skipped": True}
        latest = {}
        for item in self.em_buffer:
            latest[item[1]] = item                       # last state of each event cluster in the window
        items = [latest[k] for k in sorted(latest)]
        X = np.stack([it[2] for it in items])
        m = np.array([it[4] for it in items], float)
        d = self.dim
        T_items = np.array([it[0] for it in items])
        for _ in range(self.cfg.em_iters):
            # vMF E-step (cosine part; the entity term is a fixed-weight feature, not a calibrated density)
            MU = np.stack([self.narratives[n].mu for n in ids])
            lp = np.array([self.log_pi.get(n, math.log(1e-3)) for n in ids])
            tl = np.array([self.narratives[n].t_last_h for n in ids])
            G = self.kappa * (X @ MU.T) + lp - self.log_pi0 + self._norm - self._bg(X)[:, None]
            G -= (T_items[:, None] - tl[None, :]) ** 2 / (2.0 * self.cfg.sigma_narr_h ** 2)
            L = np.concatenate([G, np.zeros((len(items), 1))], axis=1)
            L -= L.max(axis=1, keepdims=True)
            R = np.exp(L)
            R /= R.sum(axis=1, keepdims=True)
            W = R * m[:, None]
            tot = W.sum()
            S = W[:, :-1].T @ X                                                      # narratives x d
            norms = np.linalg.norm(S, axis=1)
            mass_n = W[:, :-1].sum(axis=0)
            for j, nid in enumerate(ids):
                if norms[j] > 0 and mass_n[j] > 0:
                    self.narratives[nid].mu = S[j] / norms[j]
                self.log_pi[nid] = math.log(max(mass_n[j] / tot, 1e-6))
            self.log_pi0 = math.log(max(W[:, -1].sum() / tot, 1e-6))
            rbar = min(float(norms.sum() / max(mass_n.sum(), 1e-12)), self.cfg.rbar_max)
            self.kappa = max(rbar * (d - rbar * rbar) / (1 - rbar * rbar), 1.0)
            if self.cfg.background != "uniform":
                s0 = W[:, -1] @ X
                n0 = float(np.linalg.norm(s0))
                if n0 > 0:
                    self.mu0 = s0 / n0
                    r0 = min(n0 / max(float(W[:, -1].sum()), 1e-12), self.cfg.rbar_max)
                    self.kappa0 = max(r0 * (d - r0 * r0) / (1 - r0 * r0), 1.0)
            self._refresh_norm()
        self.refit_count += 1
        return {"kappa": self.kappa, "pi0": math.exp(self.log_pi0), "items": len(items), "narratives": len(ids)}

    # ------------------------------------------------------------ 6-hourly lineage checks
    def lineage_check(self, now_h: float, window: int) -> list[dict]:
        events = []
        for nid in self._ids(("alive",)):
            n = self.narratives[nid]
            if now_h - n.t_last_h > self.cfg.dormant_after_h:
                n.state = "dormant"
                events.append({"window": window, "kind": "dormant", "parents": [nid], "children": [nid], "shares": [1.0]})
        alive = self._ids(("alive",))
        seen = set()
        for i, a in enumerate(alive):
            for b in alive[i + 1:]:
                key = (a, b)
                if float(self.narratives[a].mu @ self.narratives[b].mu) >= self.cfg.tau_merge:
                    self.merge_streak[key] += 1
                    seen.add(key)
        for key in list(self.merge_streak):
            if key not in seen:
                del self.merge_streak[key]
        merged = set()
        for (a, b), streak in sorted(self.merge_streak.items()):
            if streak >= self.cfg.checks_needed and a not in merged and b not in merged and a in self.narratives and b in self.narratives:
                events.append(self._merge(a, b, now_h, window))
                merged |= {a, b}
        for key in [k for k in self.merge_streak if k[0] in merged or k[1] in merged]:
            del self.merge_streak[key]
        events += self._split_checks(now_h, window)
        self.lineage += events
        return events

    def _merge(self, a: str, b: str, now_h: float, window: int) -> dict:
        na, nb = self.narratives.pop(a), self.narratives.pop(b)
        wa, wb = max(na.mass_total, 1e-9), max(nb.mass_total, 1e-9)
        v = wa * na.mu + wb * nb.mu
        nid = stable_hash("merge", a, b, str(window))[:16]
        ents = dict(na.ents)
        for e, w in nb.ents.items():
            ents[e] = ents.get(e, 0.0) + w
        self.narratives[nid] = Narrative(nid, v / np.linalg.norm(v), ents, "alive", min(na.born_h, nb.born_h),
                                         max(na.t_last_h, nb.t_last_h), na.mass_total + nb.mass_total,
                                         na.label if wa >= wb else nb.label)
        self.log_pi[nid] = float(np.logaddexp(self.log_pi.pop(a, -20.0), self.log_pi.pop(b, -20.0)))
        return {"window": window, "kind": "merge", "parents": [a, b], "children": [nid], "shares": [1.0]}

    def _split_checks(self, now_h: float, window: int) -> list[dict]:
        out = []
        latest = {}
        for item in self.em_buffer:
            latest[item[1]] = item
        by_n = defaultdict(list)
        ids = self._ids(("alive",))
        if not ids:
            return out
        keys = sorted(latest)
        if keys:
            Xs = np.stack([latest[c][2] for c in keys])
            MU = np.stack([self.narratives[n].mu for n in ids])
            lp = np.array([self.log_pi.get(n, math.log(1e-3)) for n in ids])
            G = self.kappa * (Xs @ MU.T) + lp - self.log_pi0 + self._norm - self._bg(Xs)[:, None]
            best = np.argmax(G, axis=1)
            for r, c in enumerate(keys):
                j = int(best[r])
                if G[r, j] >= self.cfg.tau_alive:
                    by_n[ids[j]].append((latest[c][2], latest[c][4]))
        for nid in ids:
            pts = by_n.get(nid, [])
            ok = False
            if len(pts) >= self.cfg.split_min_items:
                X = np.stack([p[0] for p in pts])
                w = np.array([p[1] for p in pts], float)
                c1 = X[int(np.argmin(X @ self.narratives[nid].mu))]
                c2 = X[int(np.argmin(X @ c1))]
                for _ in range(5):
                    lab = (X @ c1 < X @ c2).astype(int)
                    if lab.min() == lab.max():
                        break
                    c1 = (w[lab == 0, None] * X[lab == 0]).sum(0); c1 /= np.linalg.norm(c1)
                    c2 = (w[lab == 1, None] * X[lab == 1]).sum(0); c2 /= np.linalg.norm(c2)
                share = w[lab == 0].sum() / w.sum() if lab.min() != lab.max() else 0.0
                if min(share, 1 - share) >= self.cfg.split_min_share and float(c1 @ c2) <= self.cfg.tau_split:
                    ok = True
            if ok:
                self.split_streak[nid] += 1
            else:
                self.split_streak.pop(nid, None)
            if self.split_streak.get(nid, 0) >= self.cfg.checks_needed:
                parent = self.narratives.pop(nid)
                pi = self.log_pi.pop(nid, -20.0)
                kids, shares = [], [float(share), float(1 - share)]
                for k, (c, q) in enumerate(zip((c1, c2), shares)):
                    kid = stable_hash("split", nid, str(k), str(window))[:16]
                    self.narratives[kid] = Narrative(kid, c, dict(parent.ents), "alive", now_h, now_h,
                                                     parent.mass_total * q, parent.label)
                    self.log_pi[kid] = pi + math.log(max(q, 1e-6))
                    kids.append(kid)
                self.split_streak.pop(nid, None)
                out.append({"window": window, "kind": "split", "parents": [nid], "children": kids, "shares": shares})
        return out
