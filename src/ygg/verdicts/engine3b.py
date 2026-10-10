"""Engine 3b: explanation trees -> hypotheses -> evidence -> claims -> two programs -> four-bit verdicts.

Hypothesis H_S for each tree S (best and rivals; abstention is not a hypothesis):
  trigger(H, e)     e = the entry narrative's largest event cluster in the 48 h before tau*
  before(e, move)   the event's earliest first_seen < tau*
  signature_ok(H)   a burst on the entry narrative in those 48 h AND positive spillover surprise on every
                    narrative -> narrative edge of S (tier 0: Yggdrasil's own measurements, no text)
Evidence: the trigger event's documents (each one reports occurred(e)). Claims come from their titles,
GKG amounts and quotations, and fetched pages (Wayback snapshot at or before tau*, A5 span grounding).
Contradictions are computed by rule. Central claims are the claims made in the trigger event's own
documents; schema_refuter(H, L) holds for every L contrary to a central claim.
P_pre: reports first seen before tau* whose text is grounded in a pre-cutoff snapshot. P_all: everything.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ygg.verdicts import claims as C
from ygg.verdicts.program import atom, decide, diagnosticity
from ygg.verdicts.sources import owner, tier


@dataclass
class Hypothesis:
    hid: str
    entry: str
    entry_label: str
    tree: list
    event: int | None
    signature_ok: bool
    burst: bool
    edges_surprise_ok: bool
    docs: list = field(default_factory=list)


def _nid(label: str) -> str:
    return label.split(" :: ")[0]


def build_hypotheses(con, search: dict, t_snap: int) -> list[Hypothesis]:
    out = []
    trees = []
    for g in search["groups"]:
        trees.append(("best", g["best"]["tree"]))
        trees += [(f"rival{i}", r["tree"]) for i, r in enumerate(g["rivals"])]
    seen = set()
    for name, tree in trees:
        entry = next((e["to"] for e in tree if e["from"] == "BOT" and " :: " in e["to"]), None)
        if entry is None or _nid(entry) in seen:
            continue
        seen.add(_nid(entry))
        r = _nid(entry)
        ev = con.execute("""SELECT event_cluster, count(*) c FROM e2a_memberships
                            WHERE is_root AND n1 = ? AND "window" BETWEEN ? AND ? GROUP BY 1 ORDER BY c DESC, event_cluster LIMIT 1""",
                         [r, t_snap - 191, t_snap]).fetchone()
        burst = bool(con.execute("""SELECT count(*) FROM e2b_series WHERE narrative_id = ? AND burst AND "window" BETWEEN ? AND ?""",
                                 [r, t_snap - 191, t_snap]).fetchone()[0])
        nar_edges = [e for e in tree if " :: " in e["from"] and " :: " in e["to"]]
        surprise_ok = all((e.get("sigma") or 0) > 0 for e in nar_edges)
        h = Hypothesis(f"h_{atom(r)[:12]}", r, entry.split(" :: ", 1)[1], tree, ev[0] if ev else None,
                       burst and surprise_ok, burst, surprise_ok)
        if ev:
            h.docs = [dict(zip(["observation_id", "url", "source_name", "title", "first_seen", "copy_group", "quotations", "amounts", "all_names", "orgs"], row))
                      for row in con.execute("""SELECT d.observation_id, d.url, d.source_name, d.title, d.first_seen, d.copy_group,
                                                       d.quotations, d.amounts, d.all_names, d.orgs
                                                FROM e2a_memberships m JOIN obs_doc d USING (observation_id)
                                                WHERE m.event_cluster = ? AND m."window" <= ?
                                                ORDER BY d.first_seen, d.observation_id LIMIT 60""", [ev[0], t_snap]).fetchall()]
        out.append(h)
    return out


def _subject(h: Hypothesis) -> str:
    counts = defaultdict(int)
    for d in h.docs:
        for o in (d["orgs"] or []) + [n.lower() for n in (d["all_names"] or [])]:
            counts[o] += 1
    return max(sorted(counts), key=lambda k: counts[k]) if counts else atom(h.entry_label)[:20]


def evidence(h: Hypothesis, tau: datetime, fetcher=None, fetch_top: int = 6) -> list[dict]:
    """Reports for the trigger event, with grounded claims. Each report: id, source, tier, owner, group, first_seen,
    pre (admissible before tau*), claims[]."""
    subj = atom(_subject(h))
    reps = []
    by_tier = sorted(h.docs, key=lambda d: (tier(d["source_name"]), d["first_seen"], d["observation_id"]))
    fetched = {d["observation_id"] for d in by_tier[:fetch_top]} if fetcher else set()
    for d in h.docs:
        rid = f"r_{d['observation_id'][:12]}"
        fs = d["first_seen"] if d["first_seen"].tzinfo else d["first_seen"].replace(tzinfo=timezone.utc)
        page, pre_text = "", True
        if d["observation_id"] in fetched:
            rec = fetcher.fetch(d["url"], tau.strftime("%Y%m%d%H%M%S"))
            page, pre_text = fetcher.text(rec), bool(rec.get("before_cutoff"))
        cl = C.from_title(rid, d["title"] or "", subj)
        cl += C.from_amounts(rid, list(d["amounts"] or []), page, subj)
        cl += C.from_quotes(rid, list(d["quotations"] or []), subj)
        if page:
            grounded = [c for c in cl if C.grounded(c, page)]
        else:
            grounded = []          # A5: no fetched page, no text claim; the report still witnesses occurred(e)
        reps.append({"id": rid, "source": d["source_name"], "tier": tier(d["source_name"]), "owner": owner(d["source_name"]),
                     "group": d["copy_group"][:12], "first_seen": fs.isoformat(), "pre": fs < tau and pre_text,
                     "url": d["url"], "title": d["title"], "claims": grounded, "copy": d["copy_group"] != d["observation_id"]})
    return reps


def facts_for(hyps: list[Hypothesis], reps_by_h: dict, tau: datetime, pre_only: bool) -> list[str]:
    lines, seen_src, contraries = [], set(), set()
    allclaims = []
    for h in hyps:
        e = f"ev{h.event}" if h.event is not None else "ev_none"
        lines.append(f"trigger({h.hid}, {e}).")
        reps = [r for r in reps_by_h[h.hid] if r["pre"] or not pre_only]
        seen_at = [r["first_seen"] for r in reps if r.get("first_seen") and r.get("witness", True)]
        if seen_at and min(seen_at) < tau.isoformat():
            lines.append(f"before({e}, move).")
        if h.signature_ok:
            lines.append(f"signature_ok({h.hid}).")
        for r in reps:
            src = atom(r["source"])
            if r.get("witness", True):                    # targeted search results add claims, not witnesses of e
                lines.append(f"reported({r['id']}, {src}, occurred({e}), d).")
            if r["copy"]:
                lines.append(f"copy_of({r['id']}, {atom(r['group'])}).")
            lines.append(f"group({r['id']}, g_{atom(r['group'])}).")
            if src not in seen_src:
                seen_src.add(src)
                lines += [f"tier({src}, {r['tier']}).", f"owner({src}, {atom(r['owner'])})."]
            for c in r["claims"]:
                lit = f"{c.predicate}({atom(c.subject)}, {atom(c.value)}, {c.scope}, {'pos' if c.polarity > 0 else 'neg'})"
                lines.append(f"reported({r['id']}_{len(allclaims)}, {src}, {lit}, d).")
                lines.append(f"group({r['id']}_{len(allclaims)}, g_{atom(r['group'])}).")
                allclaims.append((h.hid, c, lit))
    lines += ["tier(ygg, 0).", "owner(ygg, ygg)."]       # tier 0 enters only through signature_ok, never as a witness
    for i, (hi, a, la) in enumerate(allclaims):
        for hj, b, lb in allclaims[i + 1:]:
            if C.contrary(a, b) and (la, lb) not in contraries:
                contraries.add((la, lb))
                lines.append(f"contrary({la}, {lb}).")
                for h_owner, lit in ((hi, lb), (hj, la)):
                    lines.append(f"schema_refuter({h_owner}, {lit}).")
    return sorted(set(lines))


def judge(hyps: list[Hypothesis], reps_by_h: dict, tau: datetime) -> dict:
    out = {}
    for kind, pre in (("P_pre", True), ("P_all", False)):
        facts = facts_for(hyps, reps_by_h, tau, pre)
        v = decide("\n".join(facts))
        out[kind] = {"verdicts": v.verdict, "bits": v.bits, "models": v.n_models, "tight": v.tight, "incoherent": v.incoherent,
                     "facts": len(facts), "diagnostic": {h: diagnosticity(facts, h, v)[:5] for h in v.verdict} if len(facts) < 400 else {}}
    return out
