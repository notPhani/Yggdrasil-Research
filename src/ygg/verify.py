"""Offline verification of a recorded investigation, from archived artifacts only (no network, no credits).

Each check re-runs the production code on what the case file recorded and compares the result:
  manifest   every fixture file matches its recorded sha256 (when MANIFEST.sha256 is present)
  observer   build_case on the archived daily bars reproduces the fired set, clusters and the event cutoff tau*
  search     DPBF on the recorded explanation graph reproduces the best cost and tree, the abstention cost and
             the rivals within ln 20 (exact optimum of the ranking objective sum(-ln p + lambda); not a causal claim)
  verdicts   clingo on the recorded evidence reproduces every P_pre and P_all verdict and its four bits
  placebo    the empirical p and the false-explanation rate follow from the recorded placebo costs and runs
  serpapi    every sent or cached SerpApi query has its archived response with the recorded result count, and no
             archived response carries a credential field
What this establishes: the recorded outputs follow from the recorded inputs under the implemented rules. It does
not re-run the GDELT replay (Engines 1-2), which needs the full corpus.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace


@dataclass
class Check:
    case: str
    name: str
    ok: bool
    detail: str


def _nid(label: str) -> str:
    return label.split(" :: ", 1)[0]


def check_manifest(data_dir: Path) -> list[Check]:
    man = data_dir / "MANIFEST.sha256"
    if not man.exists():
        return []
    bad, n = [], 0
    for line in man.read_text().splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(None, 1)
        n += 1
        p = data_dir / rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(rel)
    return [Check("*", "manifest", not bad, f"{n - len(bad)}/{n} files match" + (f"; changed: {', '.join(bad[:3])}" if bad else ""))]


def check_observer(data_dir: Path, d: dict) -> Check:
    import pyarrow.parquet as pq

    from ygg.observer.trigger import build_case
    from ygg.observer.universe import load_universe

    day = d["case"]["day"]
    prices = pq.read_table(data_dir / "prices" / "daily.parquet").to_pylist()
    actions = pq.read_table(data_dir / "prices" / "actions.parquet").to_pylist()
    c = build_case(day, prices, actions, set(load_universe(data_dir)["etfs"]))
    same = c["fired"] == d["case"]["fired"] and c["clusters"] == d["case"]["clusters"] and c["tau_star"] == d["case"]["tau_star"]
    return Check(day, "observer", same, f"{len(c['fired'])} fired, {len(c['clusters'])} clusters, tau* {c['tau_star']} (session start, daily bars)")


def check_search(d: dict) -> Check:
    from ygg.search.dpbf import Graph, rivals, solve

    day, grp = d["case"]["day"], d["search"]["groups"][0]
    rec = grp["graph"]
    names = [n["id"] for n in rec["nodes"]]
    idx = {n: i for i, n in enumerate(names)}
    terms = [idx[n["id"]] for n in rec["nodes"] if n["kind"] == "terminal"]
    cost = {(idx[e["u"]], idx[e["v"]]): int(e["cost"]) for e in rec["edges"]}
    g = Graph(len(names), idx["BOT"], terms, cost)
    if len(terms) > 8:
        return Check(day, "search", False, f"{len(terms)} terminals: grouped solve, not re-checked here")
    best, edges = solve(g)
    tree = {(names[u], names[v]) for u, v in edges}
    rec_tree = {(_nid(e["from"]), _nid(e["to"])) for e in grp["best"]["tree"]}
    abst = sum(c for (u, v), c in cost.items() if u == g.root and v in terms)
    rv = rivals(g, best, int(round(1000 * math.log(20.0))))
    got_rv = sorted((names[r["entry"]], r["cost"]) for r in rv)
    rec_rv = sorted((_nid(r["entry"]), r["cost_mnats"]) for r in grp["rivals"])
    ok = best == grp["best"]["cost_mnats"] and tree == rec_tree and abst == grp["abstention_cost_mnats"] and got_rv == rec_rv
    return Check(day, "search", ok, f"best {best / 1000:.3f} nats over {len(names)} nodes / {len(cost)} edges; "
                                    f"abstention {abst / 1000:.3f}; {len(got_rv)} rivals within ln 20")


def check_verdicts(d: dict) -> Check:
    from ygg.verdicts.claims import Claim
    from ygg.verdicts.engine3b import facts_for
    from ygg.verdicts.program import decide

    day, v = d["case"]["day"], d["verdicts"]
    hyps = [SimpleNamespace(hid=h["hid"], event=h["event"], signature_ok=h["signature_ok"]) for h in v["hypotheses"]]
    reps = {h["hid"]: [{**r, "claims": [Claim(**c) for c in r["claims"]]} for r in h["reports"]] for h in v["hypotheses"]}
    tau = datetime.fromisoformat(d["case"]["tau_star"])
    ok, n = True, 0
    for kind, pre in (("P_pre", True), ("P_all", False)):       # judge() minus its per-report diagnosticity pass
        got = decide("\n".join(facts_for(hyps, reps, tau, pre)))
        rec_bits = {k: list(b) for k, b in v[kind]["bits"].items()}
        ok &= got.verdict == v[kind]["verdicts"] and {k: list(b) for k, b in got.bits.items()} == rec_bits
        n += len(got.verdict)
    labels = sorted(set(v["P_all"]["verdicts"].values()))
    return Check(day, "verdicts", ok, f"{n} verdicts (P_pre and P_all) re-derived with clingo; labels {', '.join(labels)}")


def check_placebo(d: dict) -> Check:
    from ygg.search.placebo import empirical_p

    day, p = d["case"]["day"], d.get("placebo")
    if not p:
        return Check(day, "placebo", False, "no placebo record")
    real = d["search"]["groups"][0]["best"]["cost_mnats"]
    pe = empirical_p(real, p["costs"])
    total = sum(len(r["terminals"]) for r in p["runs"])
    told = total - sum(len(r["explained"]) for r in p["runs"])           # 'explained' records the abstained terminals
    fer = told / max(total, 1)
    ok = abs(pe - p["p_emp"]) < 1e-12 and abs(fer - p["fer"]) < 1e-12 and len(p["costs"]) == p["k"]
    return Check(day, "placebo", ok, f"K = {p['k']}, empirical p = {pe:.4f}, false-explanation rate = {fer:.2f}")


def check_serpapi(data_dir: Path, d: dict) -> Check:
    from ygg.verdicts.serpapi import Sensor

    day = d["case"]["day"]
    ops = [o for o in d["verdicts"].get("searches", []) if o["status"] in ("DONE", "CACHED")]
    if not ops:
        return Check(day, "serpapi", True, "no searches recorded")
    s = Sensor(data_dir, api_key="")
    tau = datetime.fromisoformat(d["case"]["tau_star"])
    missing, wrong = 0, 0
    for o in ops:
        params = s._params(o["query"], tau, o["bounded"])
        f = s.cache / f"{hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()}.json"
        if not f.exists():
            missing += 1
            continue
        if len(json.loads(f.read_text()).get("organic_results", [])) != o["results"]:
            wrong += 1
    leaky = [p.name for p in s.cache.glob("*.json") if any(k in p.read_text() for k in ('"api_key"', '"search_metadata"'))]
    ok = not missing and not wrong and not leaky
    return Check(day, "serpapi", ok, f"{len(ops) - missing}/{len(ops)} archived responses present, result counts "
                                     f"{'match' if not wrong else 'differ'}, credential fields {'none' if not leaky else leaky[:2]}")


def verify(data_dir: Path, days: list[str] | None = None) -> list[Check]:
    data_dir = Path(data_dir)
    out = check_manifest(data_dir)
    paths = [data_dir / "cases" / f"{x}.json" for x in days] if days else sorted((data_dir / "cases").glob("????-??-??.json"))
    for p in paths:
        d = json.loads(p.read_text())
        day = d["case"]["day"]
        for fn in (lambda: check_observer(data_dir, d), lambda: check_search(d), lambda: check_verdicts(d),
                   lambda: check_placebo(d), lambda: check_serpapi(data_dir, d)):
            try:
                out.append(fn())
            except Exception as e:                       # a check that cannot run is a failed check, never skipped
                out.append(Check(day, getattr(fn, "__name__", "check"), False, f"error: {type(e).__name__}: {e}"[:160]))
    return out
