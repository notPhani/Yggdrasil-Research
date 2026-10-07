"""Engine 3a end to end for one cutoff: snapshot S_tau* -> graph -> exact best tree, rivals, abstention.

Reads only windows <= t_snap (the last window closing at or before tau*). Terminal matching runs as one
DuckDB regular-expression pass over the horizon's roots. A3: an exact solve is capped at 8 terminals; larger
cases are solved in groups of <= 8 (the largest clusters first) and the result says sharing across groups
was not searched.
"""
from __future__ import annotations

import math
import pickle
from pathlib import Path

from ygg.search.dpbf import rivals, solve
from ygg.search.graph import SearchConfig, Terminal, build_graph, regex
from ygg.store.tables import connect

K_CAP = 8


def load_snapshot(data_dir: Path, t: int) -> dict:
    return pickle.loads((Path(data_dir) / "snapshots" / f"t={t}" / "engines.pkl").read_bytes())


def horizon_inputs(data_dir: Path, t_snap: int, terminals: list[Terminal], cfg: SearchConfig):
    con = connect(data_dir)
    lo_alpha = t_snap - 30 * 96 + 1
    lo_obj = t_snap - int(cfg.horizon_days * 96) + 1
    alpha = con.execute("SELECT target, source, \"window\", alpha FROM e2b_alpha WHERE \"window\" BETWEEN ? AND ? "
                        "ORDER BY \"window\", target, source", [lo_alpha, t_snap]).fetchall()
    ys = con.execute("SELECT narrative_id, \"window\", y FROM e2b_series WHERE \"window\" BETWEEN ? AND ? "
                     "ORDER BY \"window\", narrative_id", [lo_alpha, t_snap]).fetchall()
    hit_cols = ", ".join(f"regexp_matches(txt, '{regex(t)}') AS h{i}" for i, t in enumerate(terminals)) or "NULL AS h0"
    q = f"""
      WITH o AS (
        SELECT m."window", m.n1, m.n2, m.n3, m.p1, m.p2, m.p3,
               ' ' || regexp_replace(lower(d.title || ' ' || array_to_string(d.all_names, ' ') || ' ' || array_to_string(d.orgs, ' ')),
                                     '[^a-z0-9 ]+', ' ', 'g') || ' ' AS txt
        FROM e2a_memberships m JOIN obs_doc d USING (observation_id)
        WHERE m.is_root AND m."window" BETWEEN {lo_obj} AND {t_snap})
      SELECT "window", n1, n2, n3, p1, p2, p3, {hit_cols} FROM o ORDER BY "window"
    """
    objects = []
    for row in con.execute(q).fetchall():
        w, n1, n2, n3, p1, p2, p3 = row[:7]
        hits = {i for i, h in enumerate(row[7:]) if h}
        shares = [(n, p / 255.0) for n, p in ((n1, p1), (n2, p2), (n3, p3)) if n]
        objects.append({"window": w, "hits": hits, "shares": shares})
    alpha_rows = [{"target": a, "source": b, "window": w, "alpha": v} for a, b, w, v in alpha]
    y_rows = [{"narrative_id": n, "window": w, "y": y} for n, w, y in ys]
    return alpha_rows, y_rows, objects


def explain(data_dir: Path, clock, t_snap: int, terminals: list[Terminal], cfg: SearchConfig, snap: dict | None = None) -> dict:
    snap = snap or load_snapshot(data_dir, t_snap)
    hours = lambda t: (clock.start(t) - clock.t0).total_seconds() / 3600.0
    groups = [terminals[i:i + K_CAP] for i in range(0, len(terminals), K_CAP)]
    alpha_rows, y_rows, objects = horizon_inputs(data_dir, t_snap, terminals, cfg)
    results = []
    for gi, group in enumerate(groups):
        offset = gi * K_CAP
        objs = [{**o, "hits": {h - offset for h in o["hits"] if offset <= h < offset + len(group)}} for o in objects]
        ex = build_graph(t_snap, snap["narratives"], alpha_rows, y_rows, objs, group, cfg, hours)
        g = ex.graph
        best_cost, best_edges = solve(g)
        abst = sum(g.cost[(0, x)] for x in g.terminals)
        rv = rivals(g, best_cost, int(round(1000 * cfg.odds_window)))
        label = lambda v: ex.node_names[v] if v == 0 or v > len(ex.node_names) - len(group) - 1 else \
            f"{ex.node_names[v]} :: {snap['narratives'][ex.node_names[v]].label[:90]}"

        def tree(edges):
            return [{"from": label(u), "to": label(v), "p": round(ex.p[(u, v)], 4), "cost_mnats": g.cost[(u, v)]} for u, v in sorted(edges)]
        results.append({
            "terminals": [t.name for t in group],
            "nodes": len(ex.node_names), "edges": len(g.cost),
            "best": {"cost_mnats": best_cost, "tree": tree(best_edges),
                     "abstained_on": [ex.node_names[v] for (u, v) in best_edges if u == 0 and v in g.terminals]},
            "abstention_cost_mnats": abst,
            "odds_best_vs_abstain": math.exp((abst - best_cost) / 1000.0),
            "rivals": [{"entry": label(r["entry"]), "cost_mnats": r["cost"], "odds_vs_best": math.exp((r["cost"] - best_cost) / 1000.0),
                        "tree": tree(set(r["edges"]))} for r in rv],
            "used_narratives": sorted({ex.node_names[v] for (u, v) in best_edges if 0 < v <= len(ex.node_names) - len(group) - 1}),
        })
    return {"t_snap": t_snap, "groups": results, "sharing_across_groups_searched": len(groups) == 1}
