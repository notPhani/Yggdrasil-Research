"""Engine 3a: the explanation graph at the cutoff tau* (decisions 5.1-5.4, 5.11, 5.12).

  nodes      BOT + narratives active in [tau* - 14 d, tau*) + one terminal per market cluster
  p_H(j->i)  = sum_t w_t y_i(t) alpha_{i<-j}(t) / sum_t w_t y_i(t),  w_t = exp(-(tau* - t) / 3 d), kept if >= p_floor
  tilt       p*(j->i) proportional to p_H exp(gamma * max(0, sigma_{j->i})), renormalized with BOT -> i,
             where sigma = robust z of the last-24 h mean alpha against earlier daily means
  links      lift_{u,x} = (A_u(T_x) / A_u) / (A(T_x) / A); p_link = (1 - p0) softmax_u(log(lift + eps) + zatt_u)
  costs      c = round(1000 * (-ln p + lambda_node)) milli-nats; BOT -> x costs -ln p0 + lambda_node ("we do not know")
Terminal profiles T_x use the member companies' names and tickers from the dated 2024 revisions, plus their
GICS sub-industry phrases. No hand-written lexicon, so no hindsight.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from ygg.search.dpbf import Graph

SUFFIXES = {"inc", "corp", "corporation", "co", "company", "ltd", "limited", "plc", "holdings", "holding", "group", "nv", "sa", "ag", "the"}


@dataclass
class SearchConfig:
    horizon_days: float = 14.0
    tau_h_days: float = 3.0
    p_floor: float = 0.01
    p0: float = 0.05
    lambda_node: float = 0.3
    gamma: float = 0.5
    eps: float = 1e-3
    max_links: int = 25          # candidate narratives per terminal (by score)
    odds_window: float = math.log(20.0)


def norm_text(s: str) -> str:
    return " " + re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip() + " "


def aliases(names: list[str], ticker: str) -> list[str]:
    out = set()
    for n in names:
        toks = [t for t in re.sub(r"[^a-z0-9 ]+", " ", n.lower()).split() if t]
        while toks and toks[-1] in SUFFIXES:
            toks = toks[:-1]
        if toks and len(" ".join(toks)) >= 4:
            out.add(" ".join(toks))
    t = ticker.split(".")[0].lower()
    if len(t) >= 3:
        out.add(t)
    return sorted(out)


def lexicon(subs: list[str]) -> list[str]:
    phrases = set()
    for s in subs:
        for part in re.split(r"&|,| and ", s.lower()):
            words = [w[:-1] if w.endswith("s") and len(w) > 4 else w for w in re.sub(r"[^a-z ]+", " ", part).split()]
            if words:
                phrases.add(" ".join(words))
    return sorted(phrases)


@dataclass
class Terminal:
    name: str
    members: list[str]
    aliases: list[str]
    lexicon: list[str]


def build_terminals(clusters: list[list[str]], universe: dict) -> list[Terminal]:
    etfs = set(universe["etfs"])
    out = []
    for g in clusters:
        mem = [s for s in g if s not in etfs]
        if not mem:
            continue
        al = sorted({a for s in mem for a in aliases(universe["names"].get(s, []), s)})
        lx = lexicon(sorted({universe["gics_sub"][s] for s in mem if universe["gics_sub"].get(s)}))
        out.append(Terminal("+".join(mem), mem, al, lx))
    return out


def matches(text: str, term: Terminal) -> bool:
    return any(f" {a} " in text for a in term.aliases) or any(f" {p}" in text for p in term.lexicon)


def regex(term: Terminal) -> str:
    """The same rule as `matches`, as one regular expression over normalized text (for DuckDB)."""
    alts = [f" {a} " for a in term.aliases] + [f" {p}" for p in term.lexicon]     # aliases are [a-z0-9 ] only
    return "|".join(alts) if alts else "$^"


def robust_z(x: float, ref: np.ndarray) -> float:
    if len(ref) < 5:
        return 0.0
    med = np.median(ref)
    mad = np.median(np.abs(ref - med))
    return float(0.6745 * (x - med) / mad) if mad > 0 else 0.0


@dataclass
class Explanation:
    graph: Graph
    node_names: list[str]
    p: dict = field(default_factory=dict)          # (u, v) -> probability
    sigma: dict = field(default_factory=dict)      # (u, v) -> spillover surprise (robust z) for narrative edges


def build_graph(t_star: int, narratives: dict, alpha_rows: list[dict], y_rows: list[dict], objects: list[dict],
                terminals: list[Terminal], cfg: SearchConfig, now_hours) -> Explanation:
    """t_star: the last window that closes at or before the cutoff (the snapshot window); inputs cover windows <= t_star.
    objects: roots in the horizon with {window, hits or text, shares: [(narrative, share)]}.
    now_hours(t) gives hours since t0 for the start of window t."""
    t_end_h = now_hours(t_star + 1)
    horizon_h = cfg.horizon_days * 24.0
    active = sorted(n for n, v in narratives.items() if v.t_last_h >= t_end_h - horizon_h)
    idx = {n: i + 1 for i, n in enumerate(active)}
    w = lambda t: math.exp(-(t_end_h - now_hours(t + 1)) / (cfg.tau_h_days * 24.0))

    ymap = defaultdict(float)
    for r in y_rows:
        if r["narrative_id"] in idx:
            ymap[(r["narrative_id"], r["window"])] = r["y"]
    num = defaultdict(float)
    den = defaultdict(float)
    daily = defaultdict(lambda: defaultdict(list))
    for r in alpha_rows:
        i, j, t = r["target"], r["source"], r["window"]
        if i not in idx or (j != "BOT" and j not in idx):
            continue
        wy = w(t) * ymap.get((i, t), 0.0)
        num[(j, i)] += wy * r["alpha"]
        daily[(j, i)][int(now_hours(t) // 24)].append(r["alpha"])
    for (i, t), yv in ymap.items():
        den[i] += w(t) * yv
    pH = {}
    for (j, i), v in num.items():
        if den[i] > 0:
            pH[(j, i)] = v / den[i]
    # renormalize each target's parents (alpha was stored above a floor), then tilt by surprise
    by_target = defaultdict(dict)
    for (j, i), v in pH.items():
        by_target[i][j] = v
    today = int((t_end_h - 1e-9) // 24)
    p = {}
    sig = {}
    for i, par in by_target.items():
        tot = sum(par.values())
        tilted = {}
        for j, v in par.items():
            v = v / tot if tot > 0 else 0.0
            if j != "BOT":
                days = daily[(j, i)]
                recent = [a for d, xs in days.items() if d >= today for a in xs]
                hist = np.array([np.mean(xs) for d, xs in days.items() if d < today])
                sigma = robust_z(float(np.mean(recent)), hist) if recent else 0.0
                sig[(j, i)] = sigma
                v *= math.exp(cfg.gamma * max(0.0, sigma))
            tilted[j] = v
        z = sum(tilted.values())
        for j, v in tilted.items():
            if z > 0 and v / z >= cfg.p_floor:
                p[(j, i)] = v / z
    # terminal links
    k0 = len(active) + 1
    for xi, term in enumerate(terminals):
        p[("BOT", f"T{xi}")] = cfg.p0
        A_u, A_ux, A, A_x = defaultdict(float), defaultdict(float), 0.0, 0.0
        for o in objects:
            wt = w(o["window"])
            hit = (xi in o["hits"]) if "hits" in o else matches(o["text"], term)
            A += wt
            A_x += wt * hit
            for n, s in o["shares"]:
                if n in idx:
                    A_u[n] += wt * s
                    if hit:
                        A_ux[n] += wt * s
        if A_x <= 0:
            continue
        scores = {}
        for n in A_ux:
            lift = (A_ux[n] / A_u[n]) / (A_x / A) if A_u[n] > 0 else 0.0
            ys = [ymap.get((n, t), 0.0) for t in range(t_star - 96 * 30 + 1, t_star + 1)]
            day_sums = np.array([sum(ys[d * 96:(d + 1) * 96]) for d in range(len(ys) // 96)])
            zatt = robust_z(float(day_sums[-1]), day_sums[:-1]) if len(day_sums) > 5 else 0.0
            scores[n] = math.log(lift + cfg.eps) + zatt
        top = sorted(scores, key=lambda n: (-scores[n], n))[: cfg.max_links]
        if not top:
            continue
        m = max(scores[n] for n in top)
        zsum = sum(math.exp(scores[n] - m) for n in top)
        for n in top:
            pl = (1 - cfg.p0) * math.exp(scores[n] - m) / zsum
            if pl >= cfg.p_floor:
                p[(n, f"T{xi}")] = pl
    names = ["BOT"] + active + [t.name for t in terminals]
    node = {"BOT": 0, **idx, **{f"T{xi}": k0 + xi for xi in range(len(terminals))}}
    cost = {}
    probs = {}
    for (u, v), pv in p.items():
        if u in node and v in node and pv > 0:
            e = (node[u], node[v])
            cost[e] = int(round(1000.0 * (-math.log(pv) + cfg.lambda_node)))
            probs[e] = pv
    term_nodes = [k0 + xi for xi in range(len(terminals)) if (0, k0 + xi) in cost]
    sigmas = {(node[j], node[i]): v for (j, i), v in sig.items() if j in node and i in node}
    return Explanation(Graph(len(names), 0, term_nodes, cost), names, probs, sigmas)
