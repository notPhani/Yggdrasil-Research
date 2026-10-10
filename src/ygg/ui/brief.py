"""The explanation brief: a short, deterministic account of one explanation, assembled only from the recorded case
(no language model, so it cannot add a fact the system did not record). Sections: the claim, why this path
(each step with its own number), what it was tested against, the verdict and the evidence it hinges on, what would
change it, and the limits."""
from __future__ import annotations

import math

from rich.console import Group
from rich.text import Text

from ygg.ui.domain import LATE, POST, PRE, UNMATCHED, Explanation, Investigation, short
from ygg.ui.theme import AMBER, AMBER_HI, DIM, DOWN, ID, UP, WARN, WHITE

VSTYLE = {"SUPPORTED": UP, "CONTRADICTED": DOWN, "UNRESOLVED": WARN, "CONSISTENT-BUT-UNPROVEN": DIM}


def _h(t: Text, title: str) -> None:
    t.append(f"\n{title}\n", style=f"bold {AMBER}")


def _paths(e: Explanation) -> list[list]:
    kids: dict[str, list] = {}
    for x in e.edges:
        kids.setdefault(x.src, []).append(x)
    out = []

    def walk(node, acc):
        nxt = sorted(kids.get(node, []), key=lambda x: x.cost_mnats)
        if not nxt:
            if acc:
                out.append(acc)
            return
        for x in nxt:
            if not any(x.dst == y.src for y in acc):
                walk(x.dst, acc + [x])

    walk("BOT", [])
    return out


def brief(inv: Investigation, e: Explanation, term_label, visible) -> Group:
    t = Text()
    is_term = lambda n: n in inv.terminals or (n.startswith("T") and n[1:].isdigit())
    best, abst = inv.best, inv.abstention
    hyp = next((h for h in inv.hypotheses if h.entry and h.entry == e.entry), None) or \
        next((h for h in inv.hypotheses if h.label == e.entry_label), None)

    # ---- claim
    t.append("CLAIM\n", style=f"bold {AMBER}")
    if e.rank == 0:
        t.append("No narrative chain explains the move more cheaply than an unexplained move.\n", style=f"bold {WHITE}")
        t.append(f"Abstention costs {e.cost_mnats / 1000:.2f} nats: −log p0 + λ per market cluster (p0 = 0.05, the prior chance of an "
                 f"unexplained move).\n", style=DIM)
        if best and best.rank == 1 and best is not e:
            t.append(f"The best chain is {e.odds_vs_best:.1f}× more probable than this, so 'we do not know' does not win here.\n", style=WHITE)
    else:
        terms = sorted({x.dst for x in e.edges if is_term(x.dst) and x.src != "BOT"})
        t.append(f"“{e.entry_label}”", style=f"bold {WHITE}")
        t.append(" moved ", style=DIM)
        t.append(" and ".join(term_label(x) for x in terms) or "no market cluster", style=f"bold {DOWN}")
        t.append(".\n", style=DIM)
        odds_abst = math.exp(((abst.cost_mnats if abst else e.cost_mnats) - e.cost_mnats) / 1000)
        t.append(f"{e.cost_mnats / 1000:.2f} nats · {odds_abst:.1f} : 1 against WE DO NOT KNOW", style=UP if odds_abst > 1 else WARN)
        if e.rank != 1:
            t.append(f" · 1 : {e.odds_vs_best:.1f} against the best explanation", style=DIM)
        t.append("\n")

    # ---- why this path
    _h(t, "WHY THIS PATH  (each step is a recorded edge)")
    step = 0
    for path in _paths(e):
        for x in path:
            step += 1
            t.append(f" {step}. ", style=f"bold {AMBER_HI}")
            if x.src == "BOT" and not is_term(x.dst):
                t.append("New information enters ", style=WHITE)
                t.append(f"{short('N', x.dst)} {x.dst_label[:60]}", style=ID)
                t.append(f"  p={x.p:.2f}", style=AMBER_HI)
                t.append(" (the share of its attention the attention model could not attribute to other narratives)\n", style=DIM)
            elif x.src == "BOT" and is_term(x.dst):
                t.append("Unexplained: ", style=WHITE)
                t.append(term_label(x.dst), style=DOWN)
                t.append(f"  p0={math.exp(-(x.cost_mnats / 1000 - 0.3)):.2f}\n" if x.cost_mnats else "\n", style=DIM)
            elif is_term(x.dst):
                t.append(f"{short('N', x.src)} points at ", style=WHITE)
                t.append(term_label(x.dst), style=f"bold {DOWN}")
                t.append(f"  p={x.p:.2f}", style=AMBER_HI)
                t.append(" (lift: how much more this narrative talks about the cluster's companies than everyone else, times recent heat)\n", style=DIM)
            else:
                t.append(f"{short('N', x.src)} → ", style=WHITE)
                t.append(f"{short('N', x.dst)} {x.dst_label[:50]}", style=ID)
                t.append(f"  p={x.p:.2f}", style=AMBER_HI)
                if x.sigma is not None:
                    t.append(f"  spillover surprise {x.sigma:+.1f}σ", style=UP if x.sigma > 0 else DIM)
                t.append(" (Hawkes attribution share: attention on the second caused by the first, recency-weighted over 14 days)\n", style=DIM)
    t.append(f" Σ cost = Σ(−log p + 0.3) over {len(e.edges)} edges = {e.cost_mnats / 1000:.2f} nats; shared trunks are paid once.\n", style=DIM)

    # ---- tested against
    if visible("placebos") or visible("search"):
        _h(t, "TESTED AGAINST")
        rivals = [r for r in inv.explanations if r.rank >= 2 and r is not e]
        if e.rank == 1 and rivals:
            r = min(rivals, key=lambda r: r.cost_mnats)
            t.append(f" next rival: “{r.entry_label[:60]}” at 1 : {r.odds_vs_best:.1f}\n", style=WHITE)
        if inv.placebo and visible("placebos"):
            p = inv.placebo
            beats = sum(1 for c in p.costs if c > e.cost_mnats) if p.costs else None
            t.append(f" placebo: p = {p.p_emp:.3f}" + (f" · cheaper than {beats} of {p.k} quiet-day explanations" if beats is not None else "")
                     + f" · false-explanation rate {p.fer:.2f}\n", style=WHITE)
            used = {x.dst for x in e.edges}
            for n, f in p.hubs:
                nid = n.split(" :: ")[0]
                if nid in used:
                    t.append(f" hub warning: {short('N', nid)} appears in {100 * f:.0f}% of quiet-day explanations (low diagnosticity)\n", style=WARN)
        elif not inv.placebo:
            t.append(" placebos were not run for this case\n", style=DIM)

    # ---- verdict and evidence
    if hyp is not None and visible("verdicts"):
        _h(t, "VERDICT")
        t.append(f" P_pre ", style=AMBER)
        t.append(f"{hyp.verdict_pre}", style=f"bold {VSTYLE.get(hyp.verdict_pre, DIM)}")
        t.append(f"  {''.join(map(str, hyp.bits_pre)) if hyp.bits_pre else ''}   could it have moved the price (evidence first seen before τ*)\n", style=DIM)
        t.append(f" P_all ", style=AMBER)
        t.append(f"{hyp.verdict_all}", style=f"bold {VSTYLE.get(hyp.verdict_all, DIM)}")
        t.append(f"  {''.join(map(str, hyp.bits_all)) if hyp.bits_all else ''}   is it true (everything up to report time)\n", style=DIM)
        t.append(" signature: ", style=AMBER)
        t.append(("burst before τ* ✓ " if hyp.burst else "no burst ✗ ") + ("· spillover surprise on every narrative edge ✓" if hyp.surprise_ok else "· spillover surprise ✗"),
                 style=UP if hyp.signature_ok else DIM)
        t.append("   (Yggdrasil's own measurements, tier 0, no text)\n", style=DIM)
        ev = list(hyp.evidence)
        n_pre = sum(1 for x in ev if x.status == PRE)
        t.append(f" evidence: {n_pre} admissible before τ* · {len(ev) - n_pre} truth-only\n", style=WHITE)
        _h(t, "EVIDENCE IT HINGES ON  (◆ removing it flips the verdict)")
        key = [x for x in ev if x.diagnostic] or [x for x in ev if x.claims][:3] or ev[:3]
        for x in key[:4]:
            col = UP if x.status == PRE else WARN
            t.append(" ◆ " if x.diagnostic else " · ", style=f"bold {AMBER_HI}")
            t.append(f"{x.source}  T{x.tier}  ", style=AMBER)
            t.append(f"{x.first_seen:%m-%d %H:%M}  " if x.first_seen else "not seen by Engine 1  ", style=DIM)
            t.append({PRE: "PRE-τ*", LATE: "LATE TEXT", POST: "POST-τ*", UNMATCHED: "UNMATCHED"}[x.status] + "\n", style=f"bold {col}")
            t.append(f"   “{x.title[:110]}”\n", style=WHITE)
            for c in x.claims[:2]:
                t.append(f"   {c.predicate}", style=ID)
                if c.text:
                    t.append(f"  “{c.text[:90]}”", style=f"italic {AMBER_HI}")
                t.append("\n")
        if not key:
            t.append(" no evidence recorded\n", style=DIM)
        _h(t, "WHAT WOULD CHANGE IT")
        flips = [x for x in ev if x.diagnostic]
        if flips:
            t.append(f" retracting or contradicting the ◆ item{'s' if len(flips) > 1 else ''} above (an independent source of equal or better tier)\n", style=WHITE)
        qs = [q for q in inv.searches if q.hid == hyp.hid]
        if qs:
            t.append(f" disconfirming searches: {sum(1 for q in qs if q.status in ('DONE', 'CACHED'))}/{len(qs)} run"
                     + (" (SerpApi key absent: recorded, not sent)" if all(q.status == 'UNAVAILABLE' for q in qs) else "") + "\n", style=DIM)
    elif e.rank != 0 and visible("verdicts"):
        _h(t, "VERDICT")
        t.append(" this explanation was not tested as a hypothesis (only distinct entry stories within the budget are)\n", style=DIM)

    _h(t, "LIMITS")
    t.append(" edges are timing, not cause · claims are extracted by rules and a verifier, not proven · source tiers are a frozen registry · "
             "Lean certification not run\n", style=DIM)
    return Group(t)
