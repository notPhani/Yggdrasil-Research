"""Abnormal-move trigger, clusters and the cutoff tau* (Session 2, with 2.3' market-only detection).

  AR   = R - (alpha + beta * R_SPY), OLS on trading days [t-260, t-11]
  SAR  = AR / prediction-error sd;  Mz = robust z of AR vs estimation residuals
  Mv   = robust z of log volume vs the prior 60 days;  Mg = robust z of the opening gap
  fire = (|SAR| >= 4 or |Mz| >= 5) and (Mv >= 3.5 or |Mg| >= 5)
Clusters: fired instruments linked when estimation residuals correlate at >= rho0 with the same sign.
ETFs are members but never terminals; secondary(x) = |Mg| >= 5 and not fired (opening shocks).
tau*: the earliest first-abnormal time; a gap shock counts from its venue's first print, otherwise the
regular open. When unsure, the earlier time.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from ygg.observer.prices import adjusted_closes

MAD_K = 0.6745
SESSION_FIRST_PRINT_UTC = {"AS": (8, 0), "US": (9, 0)}     # Euronext open; US pre-market 04:00 ET in winter
REGULAR_OPEN_UTC = {"AS": (8, 0), "US": (14, 30)}


@dataclass(frozen=True)
class Thresholds:
    sar: float = 4.0
    mz: float = 5.0
    mv: float = 3.5
    mg: float = 5.0
    rho0: float = 0.4
    est_start: int = 260
    est_end: int = 11
    vol_window: int = 60


def robust_z(x: float, ref: np.ndarray) -> float:
    ref = ref[np.isfinite(ref)]
    med = np.median(ref)
    mad = np.median(np.abs(ref - med))
    return float(MAD_K * (x - med) / mad) if mad > 0 else 0.0


class Series:
    """One instrument's aligned daily series."""

    def __init__(self, rows: list[dict], actions: list[dict]):
        rows = sorted(rows, key=lambda r: r["date"])
        self.dates = [r["date"] for r in rows]
        self.pos = {d: i for i, d in enumerate(self.dates)}
        self.open = np.array([r["open"] for r in rows], float)
        self.close = np.array([r["close"] for r in rows], float)
        self.volume = np.array([r["volume"] for r in rows], float)
        self.adj = adjusted_closes(self.dates, self.close, actions)
        prev = np.roll(self.close, 1)          # quotes are split-adjusted at the source (see prices.py)
        prev[0] = np.nan
        self.gap = self.open / prev - 1.0
        self.ret = np.concatenate([[np.nan], self.adj[1:] / self.adj[:-1] - 1.0])


def stats_for_day(sym: str, s: Series, m: Series, day: str, th: Thresholds) -> dict | None:
    if day not in s.pos or day not in m.pos:
        return None
    common = [d for d in s.dates if d in m.pos and d <= day]
    if len(common) < th.est_start + 2:
        return None
    k = len(common) - 1
    est = common[k - th.est_start: k - th.est_end + 1]
    y = np.array([s.ret[s.pos[d]] for d in est])
    x = np.array([m.ret[m.pos[d]] for d in est])
    ok = np.isfinite(y) & np.isfinite(x)
    y, x = y[ok], x[ok]
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    M, p = len(y), 2
    s2 = resid @ resid / (M - p)
    x0 = np.array([1.0, m.ret[m.pos[day]]])
    var = s2 * (1.0 + x0 @ np.linalg.inv(X.T @ X) @ x0)
    R = s.ret[s.pos[day]]
    ar = R - x0 @ beta
    i = s.pos[day]
    lv = np.log(np.maximum(s.volume, 1.0))
    gaps_est = np.array([s.gap[s.pos[d]] for d in est])
    st = {
        "symbol": sym, "date": day, "R": float(R), "gap": float(s.gap[i]), "AR": float(ar), "SAR": float(ar / np.sqrt(var)),
        "Mz": robust_z(ar, resid), "Mv": robust_z(lv[i], lv[max(0, i - th.vol_window): i]), "Mg": robust_z(s.gap[i], gaps_est),
        "alpha": float(beta[0]), "beta": float(beta[1]),
    }
    st["fired"] = bool((abs(st["SAR"]) >= th.sar or abs(st["Mz"]) >= th.mz) and (st["Mv"] >= th.mv or abs(st["Mg"]) >= th.mg))
    st["_resid"] = (est, y - X @ beta if ok.all() else None)
    return st


def residual_corr(a: dict, b: dict, s_by: dict, m: Series) -> float:
    """Correlation of market-model residuals over the shared estimation window."""
    def resid(st):
        sym = st["symbol"]
        s = s_by[sym]
        est = st["_resid"][0]
        y = np.array([s.ret[s.pos[d]] if d in s.pos else np.nan for d in est])
        x = np.array([m.ret[m.pos[d]] for d in est])
        return dict(zip(est, y - (st["alpha"] + st["beta"] * x)))
    ra, rb = resid(a), resid(b)
    common = [d for d in ra if d in rb and np.isfinite(ra[d]) and np.isfinite(rb[d])]
    if len(common) < 60:
        return 0.0
    return float(np.corrcoef([ra[d] for d in common], [rb[d] for d in common])[0, 1])


def clusters_for(fired: list[dict], s_by: dict, m: Series, rho0: float) -> list[list[str]]:
    syms = [f["symbol"] for f in fired]
    parent = {x: x for x in syms}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i in range(len(fired)):
        for k in range(i + 1, len(fired)):
            a, b = fired[i], fired[k]
            if np.sign(a["AR"]) == np.sign(b["AR"]) and residual_corr(a, b, s_by, m) >= rho0:
                ra, rb = find(a["symbol"]), find(b["symbol"])
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
    groups: dict[str, list[str]] = {}
    for x in sorted(syms):
        groups.setdefault(find(x), []).append(x)
    return sorted(groups.values(), key=lambda g: (-len(g), g))


def venue(sym: str) -> str:
    return "AS" if sym.endswith(".AS") else "US"


def first_abnormal_utc(st: dict, day: str, th: Thresholds) -> datetime:
    v = venue(st["symbol"])
    h, mnt = SESSION_FIRST_PRINT_UTC[v] if abs(st["Mg"]) >= th.mg else REGULAR_OPEN_UTC[v]
    d = datetime.strptime(day, "%Y-%m-%d")
    return datetime(d.year, d.month, d.day, h, mnt, tzinfo=timezone.utc)


def build_case(day: str, prices: list[dict], actions: list[dict], etfs: set[str], th: Thresholds = Thresholds()) -> dict:
    by_sym: dict[str, list[dict]] = {}
    for r in prices:
        by_sym.setdefault(r["symbol"], []).append(r)
    acts: dict[str, list[dict]] = {}
    for a in actions:
        acts.setdefault(a["symbol"], []).append(a)
    s_by = {sym: Series(rows, acts.get(sym, [])) for sym, rows in by_sym.items()}
    m = s_by["SPY"]
    stats = []
    for sym in sorted(s_by):
        if sym == "SPY":
            continue
        st = stats_for_day(sym, s_by[sym], m, day, th)
        if st:
            stats.append(st)
    fired = [s for s in stats if s["fired"]]
    groups = clusters_for(fired, s_by, m, th.rho0)
    secondary = [s["symbol"] for s in stats if not s["fired"] and abs(s["Mg"]) >= th.mg]
    terminals = [g for g in groups if any(x not in etfs for x in g)]
    tau = min((first_abnormal_utc(s, day, th) for s in fired), default=None)
    public = [{k: v for k, v in s.items() if not k.startswith("_")} for s in stats]
    return {"day": day, "stats": public, "fired": [s["symbol"] for s in fired], "clusters": groups,
            "terminal_clusters": terminals, "secondary": sorted(secondary), "tau_star": tau.isoformat() if tau else None}
