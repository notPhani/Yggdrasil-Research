"""Recorded adapter: archived investigations and the world as it was, read from the replay's own artifacts.

Nothing here recomputes a result. A case file (data/cases/DAY.json, written by 'ygg case' and 'ygg verdict') is
projected onto ygg.ui.domain; the story behind it comes from the Engine 2 tables (attention series, edge shares,
memberships) and the Engine 1 document table. Every query that feeds a replay is bounded by the replay clock:
nothing with first_seen after the clock is ever returned.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ygg.ui.domain import (LATE, POST, PRE, UNMATCHED, CaseRow, Claim, Edge, Evidence, Explanation, FeedItem, Hypothesis,
                           Instrument, Investigation, Placebo, SearchOp)

SKIP = {"plan", "acceptance_2024"}


def _dt(s) -> datetime | None:
    if not s:
        return None
    d = s if isinstance(s, datetime) else datetime.fromisoformat(str(s))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _node(label: str) -> tuple[str, str]:
    if " :: " in label:
        nid, text = label.split(" :: ", 1)
        return nid, text
    return label, label


def _edges(tree: list[dict]) -> tuple[Edge, ...]:
    out = []
    for e in tree:
        s_id, s_lab = _node(e["from"])
        d_id, d_lab = _node(e["to"])
        out.append(Edge(s_id, d_id, float(e.get("p", 0.0)), int(e.get("cost_mnats", 0)), s_lab, d_lab, e.get("sigma")))
    return tuple(out)


def _entry(edges: tuple[Edge, ...]) -> tuple[str, str]:
    for e in edges:
        if e.src == "BOT" and not e.dst.startswith("T") and e.dst_label != e.dst:
            return e.dst, e.dst_label
    for e in edges:
        if e.src == "BOT":
            return e.dst, e.dst_label
    return "BOT", "we do not know"


def detected_at(day: str) -> datetime:
    """The replay trigger runs on daily bars: a move is detectable only after the US close (21:00 UTC in winter)."""
    d = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return d.replace(hour=21, minute=0)


def evidence_status(r: dict, tau: datetime | None) -> str:
    fs = _dt(r.get("first_seen"))
    if fs is None:
        return UNMATCHED
    if tau is not None and fs >= tau:
        return POST
    return PRE if r.get("pre", False) else LATE


def load_investigation(path: Path | dict, source: str = "RECORDED") -> Investigation:
    d = path if isinstance(path, dict) else json.loads(Path(path).read_text())
    case, search = d.get("case", {}), d.get("search", {})
    day = case.get("day", "" if isinstance(path, dict) else Path(path).stem)
    tau = _dt(case.get("tau_star"))
    clusters = tuple(tuple(c) for c in case.get("clusters", []))
    cl_of = {s: i for i, c in enumerate(clusters) for s in c}
    secondary = set(case.get("secondary", []))
    stats = case.get("stats", [])
    inst = []
    if stats:
        for s in sorted(stats, key=lambda s: (not s.get("fired"), s.get("SAR") or 0.0)):
            if s.get("fired") or s["symbol"] in secondary:
                inst.append(Instrument(s["symbol"], s.get("R"), s.get("SAR"), s.get("Mz"), s.get("Mv"), s.get("Mg"), s.get("g"),
                                       bool(s.get("fired")), cl_of.get(s["symbol"]), s["symbol"] in secondary))
    else:
        inst = [Instrument(sym, fired=True, cluster=cl_of.get(sym)) for sym in case.get("fired", [])]
        inst += [Instrument(sym, secondary=True) for sym in sorted(secondary)]

    expl, nodes, edges_n = [], 0, 0
    groups = search.get("groups", [])
    if groups:
        g = groups[0]
        nodes, edges_n = g.get("nodes", 0), g.get("edges", 0)
        best = g["best"]
        be = _edges(best.get("tree", []))
        eid, elab = _entry(be)
        expl.append(Explanation(1, eid, elab, be, int(best["cost_mnats"]), 1.0, tuple(best.get("abstained_on", []))))
        for k, r in enumerate(g.get("rivals", []), start=2):
            re_ = _edges(r.get("tree", []))
            rid, rlab = _node(r.get("entry", ""))
            if rid == eid and k == 2 and int(r["cost_mnats"]) == int(best["cost_mnats"]):
                continue                                  # the best tree reported again as its own entry's rival
            expl.append(Explanation(k, rid, rlab, re_, int(r["cost_mnats"]), float(r.get("odds_vs_best", 1.0))))
        abst = int(g.get("abstention_cost_mnats", 0))
        terms = g.get("terminals", [])
        expl.append(Explanation(0, "BOT", "we do not know", tuple(Edge("BOT", t, 0.0, 0) for t in terms), abst,
                                math.exp((abst - int(best["cost_mnats"])) / 1000.0), tuple(terms)))

    v = d.get("verdicts", {})
    pre, alls = v.get("P_pre", {}), v.get("P_all", {})
    diag = set()
    for side in (pre, alls):
        for lines in (side.get("diagnostic") or {}).values():
            for line in lines:
                if line.startswith("reported("):
                    diag.add(line[len("reported("):].split(",")[0])
    hyps = []
    for h in v.get("hypotheses", []):
        ev = []
        for r in h.get("reports", []):
            claims = tuple(Claim(f"{c.get('predicate', '?')}({c.get('subject', '?')}, {c.get('value', '')}"
                                 f"{', ' + c['scope'] if c.get('scope') else ''}){'' if c.get('polarity', 1) > 0 else ' NOT'}"
                                 f" [{c.get('extractor', '?')}]", str(c.get("span", ""))[:120])
                           for c in r.get("claims", []))
            ev.append(Evidence(r["id"], r.get("source", "?"), int(r.get("tier", 3)), _dt(r.get("first_seen")),
                               evidence_status(r, tau), r.get("title") or "", r.get("url", ""), claims, bool(r.get("copy")),
                               r["id"] in diag))
        hid = h["hid"]
        bp, ba = pre.get("bits", {}).get(hid), alls.get("bits", {}).get(hid)
        hyps.append(Hypothesis(hid, h.get("label", hid), _node(h.get("entry") or "")[0], bool(h.get("signature_ok")), bool(h.get("burst")),
                               bool(h.get("surprise_ok")), pre.get("verdicts", {}).get(hid, "—"), alls.get("verdicts", {}).get(hid, "—"),
                               tuple(bp) if bp else None, tuple(ba) if ba else None, tuple(ev)))

    searches = tuple(SearchOp(q.get("qid", f"q{i}"), q.get("hid", ""), q.get("query", ""), q.get("provider", "serpapi"),
                              q.get("status", "DONE"), q.get("results", 0), q.get("matched", 0), q.get("unmatched", 0), q.get("note", ""))
                     for i, q in enumerate(v.get("searches", [])))
    pl = d.get("placebo")
    placebo = Placebo(pl["k"], pl["fer"], pl["p_emp"], tuple((h[0], h[1]) for h in pl.get("hubs", [])),
                      tuple(pl.get("costs", []))) if pl else None
    phases = (("trigger", "DONE" if case else "PENDING"), ("snapshot", "DONE" if search else "PENDING"),
              ("search", "DONE" if groups else "PENDING"), ("placebos", "DONE" if pl else "SKIPPED"),
              ("queries", ("UNAVAILABLE" if all(q.status == "UNAVAILABLE" for q in searches) else "DONE") if searches
                          else ("UNAVAILABLE" if v else "PENDING")),
              ("claims", "DONE" if hyps else "PENDING"), ("verdicts", "DONE" if pre else "PENDING"), ("lean", "SKIPPED"))
    return Investigation(day, tau, detected_at(day), str(search.get("t_snap", "")), tuple(inst), clusters, tuple(expl),
                         tuple(hyps), searches, placebo, phases, nodes, edges_n, pre.get("models", 0), alls.get("models", 0),
                         d.get("cfg_hash", ""), source, tuple(d.get("notes", [])), tuple(groups[0].get("terminals", [])) if groups else ())


def list_cases(data_dir: Path) -> list[CaseRow]:
    rows = []
    for p in sorted((Path(data_dir) / "cases").glob("*.json"), reverse=True):
        if p.stem in SKIP or p.stem.endswith("_certificates"):
            continue
        try:
            inv = load_investigation(p)
        except Exception as e:                            # a broken file is shown as broken, never hidden
            rows.append(CaseRow(p.stem, "ARCHIVED", "UNREADABLE", str(e)[:40], None, "—", None, None))
            continue
        b = inv.best
        last = [ph for ph, st in inv.phases if st == "DONE"]
        sars = [abs(i.SAR) for i in inv.instruments if i.SAR is not None and i.fired]
        rows.append(CaseRow(inv.case_id, "ARCHIVED", (last[-1] if last else "—").upper(),
                            "  ".join(f"C{k + 1}({len(c)})" for k, c in enumerate(inv.clusters)), max(sars) if sars else None,
                            (b.entry_label if b and b.entry != "BOT" else "we do not know") if b else "—",
                            (inv.abstention.odds_vs_best if inv.abstention else None), inv.placebo.p_emp if inv.placebo else None))
    return rows


# ---------------------------------------------------------------- the world behind a case (replay projections)
class World:
    """Read-only DuckDB views over the replay tables, every query bounded by a clock."""

    def __init__(self, data_dir: Path, clock):
        import duckdb

        self.data_dir, self.clock = Path(data_dir), clock
        self.con = duckdb.connect()
        root = self.data_dir / "tables"
        self.have = set()
        for name in ("obs_doc", "e2b_series", "e2b_alpha", "e2a_memberships"):
            d = root / name
            if d.exists() and any(d.glob("day=*/*.parquet")):
                self.con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{(d / 'day=*/*.parquet').as_posix()}', hive_partitioning=true)")
                self.have.add(name)

    def window(self, t: datetime) -> int:
        return self.clock.window_of(t)

    def attention(self, nids: list[str], t0: datetime, t1: datetime) -> dict[str, list[tuple[int, float, float, bool]]]:
        """(window, y, lam, burst) per narrative for windows in [t0, t1)."""
        if "e2b_series" not in self.have or not nids:
            return {}
        w0, w1 = self.window(t0), self.window(t1)
        rows = self.con.execute("SELECT narrative_id, \"window\", y, lam, burst FROM e2b_series WHERE \"window\" >= ? AND \"window\" < ? AND "
                                "narrative_id IN (SELECT unnest(?)) ORDER BY narrative_id, \"window\"", [w0, w1, nids]).fetchall()
        out: dict[str, list] = {n: [] for n in nids}
        for n, w, y, lam, b in rows:
            out[n].append((int(w), float(y or 0.0), float(lam or 0.0), bool(b)))
        return out

    def spill(self, pairs: list[tuple[str, str]], t0: datetime, t1: datetime) -> dict[tuple[str, str], list[tuple[int, float]]]:
        """Edge shares alpha[src -> dst] per window in [t0, t1) for the given (src, dst) pairs."""
        if "e2b_alpha" not in self.have or not pairs:
            return {}
        w0, w1 = self.window(t0), self.window(t1)
        out = {p: [] for p in pairs}
        for s, t in pairs:
            rows = self.con.execute("SELECT \"window\", alpha FROM e2b_alpha WHERE \"window\" >= ? AND \"window\" < ? AND source = ? AND target = ? "
                                    "ORDER BY \"window\"", [w0, w1, s, t]).fetchall()
            out[(s, t)] = [(int(w), float(a)) for w, a in rows]
        return out

    def feed(self, t0: datetime, t1: datetime, nids: list[str] | None = None, limit: int = 200) -> list[FeedItem]:
        """Root documents first seen in [t0, t1), newest first; restricted to documents whose top narrative is in nids."""
        if "obs_doc" not in self.have:
            return []
        q = ("SELECT d.first_seen, d.source_name, d.title, d.observation_id, {nar} FROM obs_doc d {join} "
             "WHERE d.first_seen >= ? AND d.first_seen < ? AND d.copy_group = d.observation_id {cond} ORDER BY d.first_seen DESC, d.observation_id LIMIT ?")
        args: list = [t0.replace(tzinfo=None), t1.replace(tzinfo=None)]
        if nids and "e2a_memberships" in self.have:
            q = q.format(nar="m.n1", join="JOIN e2a_memberships m ON m.observation_id = d.observation_id", cond="AND m.n1 IN (SELECT unnest(?))")
            args.append(nids)
        else:
            q = q.format(nar="''", join="", cond="")
        args.append(limit)
        rows = self.con.execute(q, args).fetchall()
        return [FeedItem(_dt(fs), src or "?", (title or "").strip(), oid, n or "") for fs, src, title, oid, n in rows]

    def daily(self, symbols: list[str], d0: str, d1: str) -> dict[str, list[tuple[str, float, float, float, float, float]]]:
        import pyarrow.parquet as pq

        p = self.data_dir / "prices" / "daily.parquet"
        if not p.exists():
            return {}
        out = {s: [] for s in symbols}
        for r in pq.read_table(p, filters=[("symbol", "in", symbols)]).to_pylist():
            if d0 <= str(r["date"]) <= d1:
                out[r["symbol"]].append((str(r["date"]), r["open"] / 1e4, r["high"] / 1e4, r["low"] / 1e4, r["close"] / 1e4, float(r["volume"])))
        for s in out:
            out[s].sort()
        return out


def replay_clock_range(inv: Investigation, story_days: int = 7) -> tuple[datetime, datetime]:
    """A recorded replay runs from a week before tau* to the moment the case could open (the daily close)."""
    tau = inv.tau_star or detected_at(inv.case_id)
    return tau - timedelta(days=story_days), inv.detected or tau
