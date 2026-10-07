"""The dossier (decision 6.8) and its terminal view: case, clusters, tau*, explanations with odds and placebo
p-value, verdicts before the cutoff and at report time, and evidence. No forecast and no advice, anywhere.
Abstention is worded "no admissible explanation in observed English news before tau*" (A8).
"""
from __future__ import annotations

ABSTAIN = "no admissible explanation in observed English news before tau*"


def render_markdown(d: dict) -> str:
    c, s = d["case"], d["search"]
    lines = [f"# Case {c['day']}", "", f"**tau\\* = {c['tau_star']}** (earliest first abnormal print; earlier time when unsure)", "",
             "## Clusters (search terminals)", ""]
    for g in c["terminal_clusters"]:
        lines.append(f"- {', '.join(g)}")
    if c.get("secondary"):
        lines += ["", f"Opening shocks (secondary, not terminals): {', '.join(c['secondary'])}"]
    for gi, g in enumerate(s["groups"]):
        lines += ["", f"## Explanations{'' if len(s['groups']) == 1 else f' (group {gi + 1})'}", "",
                  f"Best tree, cost {g['best']['cost_mnats'] / 1000:.2f} nats; abstention {g['abstention_cost_mnats'] / 1000:.2f} nats; "
                  f"odds best : abstain = {g['odds_best_vs_abstain']:.2f} : 1", ""]
        for e in g["best"]["tree"]:
            lines.append(f"- {e['from']} -> {e['to']}  (p {e['p']:.3f}{'' if e.get('sigma') is None else ', surprise %+.1f' % e['sigma']})")
        if g["best"]["abstained_on"]:
            lines.append(f"- abstained on {', '.join(g['best']['abstained_on'])}: {ABSTAIN}")
        for r in g["rivals"][1:6]:
            lines.append(f"- rival via {r['entry']}: odds {r['odds_vs_best']:.1f} : 1 against")
    if "placebo" in d:
        p = d["placebo"]
        lines += ["", "## Placebo calibration", "", f"K = {p['k']}, false-explanation rate {p['fer']:.0%}, empirical p = {p['p_emp']:.3f}"]
        if p.get("hubs"):
            lines.append("Hub frequency on ordinary days: " + "; ".join(f"{k[:40]} {v:.0%}" for k, v in p["hubs"][:5]))
    if "verdicts" in d:
        lines += ["", "## Verdicts", "", "| hypothesis | before tau* (P_pre) | at report time (P_all) | signature |", "|---|---|---|---|"]
        for h in d["verdicts"]["hypotheses"]:
            vp = d["verdicts"]["P_pre"]["verdicts"].get(h["hid"], "-")
            va = d["verdicts"]["P_all"]["verdicts"].get(h["hid"], "-")
            lines.append(f"| {h['label'][:60]} | {vp} | {va} | {'burst + surprise' if h['signature_ok'] else ('burst' if h['burst'] else 'none')} |")
        lines += ["", "## Evidence (sample)", ""]
        for h in d["verdicts"]["hypotheses"][:3]:
            for r in h["reports"][:6]:
                lines.append(f"- [{h['label'][:30]}] tier {r['tier']} {r['source']} first_seen {r['first_seen'][:16]} "
                             f"{'(before tau*)' if r['pre'] else '(after cutoff: truth only)'}: {r['title'][:100]}")
    lines += ["", "_Yggdrasil never forecasts prices and never recommends trades. Edges are timing, not cause._"]
    return "\n".join(lines)


def render_terminal(d: dict) -> None:
    from rich.console import Console
    from rich.markdown import Markdown

    Console().print(Markdown(render_markdown(d)))
