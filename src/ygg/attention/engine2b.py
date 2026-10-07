"""Engine 2b runtime: one step per window, a daily refit through the previous day (D7), surprises and edge shares.

Per window t, in order:
  1. lineage events from 2a (emerge / split / merge) carry traces and history forward (Lemma 5.2)
  2. lam(t) was computed at t-1 from traces built on y(<t) (predictable)
  3. PIT residual u(t) under NB2(lam, r) (randomized with Philox, D2) -> BOCPD -> burst flag (4.6)
  4. edge shares alpha(t) from positive parts, with unexplained mass to BOT (Lemma 7.1)
  5. traces and supply level update with y(t); missing batches are masked (4.8)
  6. lam(t+1) for every alive narrative
A daily refit at the first window of each day uses only windows before it (D7): rows by relaxed sparse
group lasso on the quasi-Poisson loss (4.2'), omega and beta_B profiled on the last held-out day.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field

import numpy as np
from scipy.stats import nbinom, norm

from ygg.attention.model import A_M, FitConfig, fit_row, fourier, qp_deviance, softplus
from ygg.determinism import keyed_rng

N_BASE = 11                                   # intercept + 10 Fourier hour-of-week terms


@dataclass
class B2Config:
    fit_days: int = 14
    k_neighbors: int = 20
    min_windows: int = 96 * 2                 # a narrative needs 2 days of history before its row is fitted
    kappa_l: float = 1.0 - math.exp(-0.25 / 168.0)
    hazard: float = 1.0 / (96 * 3)            # BOCPD prior run length about 3 days
    burst_post: float = 0.5
    rmax: int = 400
    alpha_floor: float = 0.01
    min_mass: float = 20.0                    # rows with less attention in the fit window keep the mean-rate predictor
    profile_every_days: int = 7               # omega and beta_B profiled on the first refit, then weekly
    cfg_hash: str = "dev"
    fit: FitConfig = field(default_factory=FitConfig)


class Bocpd:
    """Adams & MacKay run-length recursion for N(mu, 1) observations with a N(0, 1) prior on mu."""

    def __init__(self, hazard: float, rmax: int):
        self.h, self.rmax = hazard, rmax
        self.p = np.array([1.0])
        self.n = np.array([0.0])
        self.s = np.array([0.0])

    def update(self, x: float) -> tuple[float, float]:
        mean = self.s / (self.n + 1.0)
        var = 1.0 + 1.0 / (self.n + 1.0)
        pred = np.exp(-0.5 * (x - mean) ** 2 / var) / np.sqrt(2 * np.pi * var)
        grow = self.p * pred * (1 - self.h)
        cp = float((self.p * pred * self.h).sum())
        p = np.concatenate([[cp], grow])
        n = np.concatenate([[0.0], self.n + 1.0])
        s = np.concatenate([[0.0], self.s + x])
        p = p[: self.rmax]; n = n[: self.rmax]; s = s[: self.rmax]
        tot = p.sum()
        self.p = p / tot if tot > 0 else np.eye(1, len(p))[0]
        self.n, self.s = n, s
        short = float(self.p[:3].sum())
        run_mean = float((self.p[:3] * (s[:3] / np.maximum(n[:3], 1))).sum() / max(short, 1e-12))
        return short, run_mean


@dataclass
class Engine2b:
    clock: object
    cfg: B2Config = field(default_factory=B2Config)

    def __post_init__(self):
        self.ids: list[str] = []                            # narratives with state, in sorted order
        self.z: dict[str, np.ndarray] = {}
        self.hist: dict[str, deque] = {}                    # y history (fit window), aligned with self.hist_t
        self.hist_t: deque = deque()
        self.hist_missing: deque = deque()
        self.hist_v: deque = deque()
        self.theta: dict[str, np.ndarray] = {}
        self.nbrs: dict[str, list[str]] = {}
        self.omega = 0.0
        self.beta_b = 0.0
        self.r = 5.0
        self.level = 0.0
        self.vbar = np.zeros(168)
        self.vbar_n = np.zeros(168)
        self.lam_next: dict[str, float] = {}
        self.parts_next: dict[str, tuple] = {}
        self.bocpd: dict[str, Bocpd] = {}
        self.refits: list[dict] = []
        self.last_day = None

    # ------------------------------------------------------------ lineage
    def apply_lineage(self, events: list[dict]) -> None:
        for ev in events:
            if ev["kind"] == "emerge":
                for c in ev["children"]:
                    self._add(c, np.zeros(4), [0.0] * len(self.hist_t))
            elif ev["kind"] == "split":
                p = ev["parents"][0]
                if p in self.z:
                    zp, hp = self.z.pop(p), list(self.hist.pop(p))
                    for c, q in zip(ev["children"], ev["shares"]):
                        self._add(c, q * zp, [q * v for v in hp])
                    self._drop(p)
            elif ev["kind"] == "merge":
                c = ev["children"][0]
                zs = [self.z.pop(p) for p in ev["parents"] if p in self.z]
                hs = [list(self.hist.pop(p)) for p in ev["parents"] if p in self.hist]
                if zs:
                    self._add(c, sum(zs), [sum(v) for v in zip(*hs)] if hs else [0.0] * len(self.hist_t))
                for p in ev["parents"]:
                    self._drop(p)
        self.ids = sorted(self.z)

    def _add(self, nid: str, z: np.ndarray, h: list[float]) -> None:
        self.z[nid] = np.asarray(z, float)
        self.hist[nid] = deque(h, maxlen=None)
        self.bocpd[nid] = Bocpd(self.cfg.hazard, self.cfg.rmax)

    def _drop(self, nid: str) -> None:
        for d in (self.theta, self.nbrs, self.lam_next, self.parts_next, self.bocpd):
            d.pop(nid, None)

    # ------------------------------------------------------------ prediction
    def _features(self, nid: str, how: int, zmap: dict[str, np.ndarray]) -> np.ndarray:
        f = fourier(np.array([how]))[0]
        zs = [zmap.get(j, np.zeros(4)) for j in self.nbrs.get(nid, [nid])]
        return np.concatenate([[1.0], f, np.concatenate(zs)])

    def _predict(self, t_next: int) -> None:
        how = self._how(t_next)
        lam_raw, parts = {}, {}
        for nid in self.ids:
            th = self.theta.get(nid)
            if th is None:
                mean = float(np.mean(self.hist[nid])) if len(self.hist[nid]) else 0.0
                lam_raw[nid], parts[nid] = max(mean, 1e-3), (max(mean, 1e-3), {})
                continue
            x = self._features(nid, how, self.z)
            eta = float(x @ th)
            lam_raw[nid] = float(softplus(np.array([eta]), self.cfg.fit.s)[0])
            base = float(x[:N_BASE] @ th[:N_BASE])
            exc = {}
            for k, j in enumerate(self.nbrs[nid]):
                e = float(x[N_BASE + 4 * k: N_BASE + 4 * k + 4] @ th[N_BASE + 4 * k: N_BASE + 4 * k + 4])
                if e != 0.0:
                    exc[j] = e
            parts[nid] = (base, exc)
        s_raw = sum(lam_raw.values())
        b = math.exp(self.beta_b) * self._vhat(t_next)
        c = (b / (b + s_raw)) ** self.omega if s_raw > 0 else 1.0
        self.lam_next = {n: c * v for n, v in lam_raw.items()}
        self.parts_next = parts

    def _how(self, t: int) -> int:
        s = self.clock.start(t)
        return s.weekday() * 24 + s.hour

    def _vhat(self, t: int) -> float:
        h = self._how(t)
        base = self.vbar[h] if self.vbar_n[h] > 0 else (self.vbar[self.vbar_n > 0].mean() if (self.vbar_n > 0).any() else 1.0)
        return max(base, 1e-3) * math.exp(self.level)

    # ------------------------------------------------------------ one window
    def step(self, t: int, y: dict[str, float], v_total: float, missing: bool, lineage: list[dict]) -> dict:
        day = self.clock.start(t).strftime("%Y-%m-%d")
        if day != self.last_day:
            if self.last_day is not None:
                self.refit(t)
            self.last_day = day
            self._predict(t)
        for nid in y:
            if nid not in self.z:
                self._add(nid, np.zeros(4), [0.0] * len(self.hist_t))
        self.ids = sorted(self.z)
        out_rows, alpha_rows = [], []
        for nid in self.ids:
            lam = self.lam_next.get(nid, 1e-3)
            yv = y.get(nid, 0.0)
            burst, u = False, None
            if not missing:
                yi = int(round(yv))
                p = self.r / (self.r + lam)
                lo = nbinom.cdf(yi - 1, self.r, p) if yi > 0 else 0.0
                hi = nbinom.cdf(yi, self.r, p)
                uu = keyed_rng(self.cfg.cfg_hash, "pit", nid, str(t)).random()
                u = float(np.clip(lo + uu * (hi - lo), 1e-9, 1 - 1e-9))
                zsc = float(norm.ppf(u))
                short, run_mean = self.bocpd[nid].update(zsc)
                burst = short > self.cfg.burst_post and run_mean > 0
                alpha_rows += self._alpha(nid, t, yv, lam)
            out_rows.append({"narrative_id": nid, "window": t, "y": yv, "lam": lam, "pit": u, "burst": burst})
        # traces and supply (missing windows: the trace is fed its prediction, the level is not updated)
        for nid in self.ids:
            obs = self.lam_next.get(nid, 0.0) if missing else y.get(nid, 0.0)
            self.z[nid] = A_M * self.z[nid] + (1.0 - A_M) * obs
            self.hist[nid].append(obs)
        if not missing and v_total > 0:
            h = self._how(t)
            self.vbar_n[h] += 1
            self.vbar[h] += (v_total - self.vbar[h]) / self.vbar_n[h]
            self.level = (1 - self.cfg.kappa_l) * self.level + self.cfg.kappa_l * (math.log(v_total) - math.log(max(self.vbar[h], 1e-3)))
        self.hist_t.append(t)
        self.hist_missing.append(missing)
        self.hist_v.append(v_total)
        horizon = self.cfg.fit_days * 96
        while len(self.hist_t) > horizon:
            self.hist_t.popleft(); self.hist_missing.popleft(); self.hist_v.popleft()
            for d in self.hist.values():
                if len(d) > horizon:
                    d.popleft()
        if lineage:
            self.apply_lineage(lineage)
        self._predict(t + 1)
        return {"series": out_rows, "alpha": alpha_rows}

    def _alpha(self, nid: str, t: int, y: float, lam: float) -> list[dict]:
        if y <= 0:
            return []
        base, exc = self.parts_next.get(nid, (lam, {}))
        pos = {j: max(e, 0.0) for j, e in exc.items()}
        den = max(base, 0.0) + sum(pos.values())
        explained = min(y, lam)
        shares = {"BOT": (max(base, 0.0) / den if den > 0 else 1.0)}
        for j, e in pos.items():
            if e > 0 and den > 0:
                shares[j] = e / den
        mass = {k: explained * v for k, v in shares.items()}
        mass["BOT"] = mass.get("BOT", 0.0) + max(y - lam, 0.0)
        return [{"target": nid, "source": k, "window": t, "alpha": v / y} for k, v in sorted(mass.items())
                if v / y >= self.cfg.alpha_floor]

    # ------------------------------------------------------------ daily refit (D7: data strictly before t)
    def set_neighbors(self, centroids: dict[str, np.ndarray]) -> None:
        ids = [n for n in sorted(centroids) if n in self.z]
        if not ids:
            return
        M = np.stack([centroids[n] for n in ids])
        S = M @ M.T
        for a, nid in enumerate(ids):
            order = [ids[k] for k in np.argsort(-S[a], kind="stable") if ids[k] != nid][: self.cfg.k_neighbors]
            self.nbrs[nid] = [nid] + sorted(order)

    def refit(self, t: int) -> dict:
        T = len(self.hist_t)
        if T < self.cfg.min_windows:
            return {}
        ids = [n for n in self.ids if n in self.nbrs and len(self.hist[n]) == T and float(np.sum(self.hist[n])) >= self.cfg.min_mass]
        if not ids:
            return {}
        profile = (len(self.refits) % self.cfg.profile_every_days) == 0
        Y = {n: np.array(self.hist[n]) for n in self.ids if len(self.hist[n]) == T}
        Z = {}
        for n, yv in Y.items():
            zz = np.zeros((T, 4)); z = np.zeros(4)
            for k in range(T):
                zz[k] = z
                z = A_M * z + (1 - A_M) * yv[k]
            Z[n] = zz
        how = np.array([self._how(tt) for tt in self.hist_t])
        F = fourier(how)
        mask = ~np.array(self.hist_missing)
        val = np.zeros(T, bool); val[-96:] = True
        Xs = {}
        for n in ids:
            cols = [np.ones((T, 1)), F] + [Z.get(j, np.zeros((T, 4))) for j in self.nbrs[n]]
            Xs[n] = np.concatenate(cols, axis=1)
        vh = np.array([self._vhat(tt) for tt in self.hist_t])
        best = (float("nan"), self.omega, self.beta_b)
        grid = [(o, bb) for o in self.cfg.fit.omega_grid for bb in self.cfg.fit.beta_b_grid] if profile else []
        best = None if grid else best
        for omega, beta_b in grid:
            if True:
                theta = {n: self.theta.get(n, np.zeros(Xs[n].shape[1])) if self.theta.get(n) is not None and len(self.theta[n]) == Xs[n].shape[1] else np.zeros(Xs[n].shape[1]) for n in ids}
                c = np.ones(T)
                for _ in range(1):
                    for n in ids:
                        theta[n] = fit_row(Xs[n], Y[n], c, mask & ~val, theta[n], N_BASE, self.cfg.fit, cap=omega < 0.05)
                    s_raw = sum(softplus(Xs[n] @ theta[n], self.cfg.fit.s) for n in ids)
                    b = math.exp(beta_b) * vh
                    c = (b / (b + s_raw)) ** omega
                dev = sum(qp_deviance(Y[n][val & mask], (c * softplus(Xs[n] @ theta[n], self.cfg.fit.s))[val & mask]) for n in ids)
                if best is None or dev < best[0] - 1e-9:
                    best = (dev, omega, beta_b)
        _, self.omega, self.beta_b = best
        c = np.ones(T)
        theta = {n: np.zeros(Xs[n].shape[1]) for n in ids}
        for _ in range(self.cfg.fit.outer):
            for n in ids:
                theta[n] = fit_row(Xs[n], Y[n], c, mask, theta[n], N_BASE, self.cfg.fit, cap=self.omega < 0.05)
            s_raw = sum(softplus(Xs[n] @ theta[n], self.cfg.fit.s) for n in ids)
            b = math.exp(self.beta_b) * vh
            c = (b / (b + s_raw)) ** self.omega
        self.theta.update(theta)
        lam_all = np.concatenate([(c * softplus(Xs[n] @ theta[n], self.cfg.fit.s))[mask] for n in ids])
        y_all = np.concatenate([Y[n][mask] for n in ids])
        excess = float(np.sum((y_all - lam_all) ** 2 - lam_all))
        self.r = float(np.clip(np.sum(lam_all ** 2) / excess, 0.5, 1e4)) if excess > 0 else 1e4
        rho = max((sum(max(v, 0.0) for v in th[N_BASE:]) for th in theta.values()), default=0.0)
        info = {"window": t, "rows": len(ids), "omega": self.omega, "beta_b": self.beta_b, "r": self.r,
                "max_row_pos_sum": rho, "heldout_dev": best[0], "profiled": profile}
        self.refits.append(info)
        return info
