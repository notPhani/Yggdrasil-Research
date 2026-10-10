"""Rich renderables for the terminal: candles, sparklines, the evidence wall, trees. Pure functions of domain objects."""
from __future__ import annotations

import math
from datetime import datetime

from rich.console import Group
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from ygg.ui.domain import LATE, POST, PRE, UNMATCHED, Candle, Evidence, Explanation, Hypothesis, Investigation, short

from ygg.ui.theme import AMBER_HI as AMBER, DIM as GRAY, DOWN as RED, ID as CYAN, UP as GREEN, WHITE as INK  # one palette
BLOCKS = " ▁▂▃▄▅▆▇█"
VERDICT_STYLE = {"SUPPORTED": GREEN, "CONTRADICTED": RED, "UNRESOLVED": AMBER, "CONSISTENT-BUT-UNPROVEN": GRAY, "—": GRAY}
VERDICT_SHORT = {"SUPPORTED": "SUPPORTED", "CONTRADICTED": "CONTRADICTED", "UNRESOLVED": "UNRESOLVED",
                 "CONSISTENT-BUT-UNPROVEN": "CONSISTENT-UNPROVEN", "—": "—"}
STATUS_STYLE = {PRE: GREEN, LATE: AMBER, POST: AMBER, UNMATCHED: GRAY}
STATUS_TEXT = {PRE: "PRE-τ*   admissible", LATE: "PRE-τ*   text fetched after τ*: truth only", POST: "POST-τ*  truth only",
               UNMATCHED: "UNMATCHED  no Engine 1 sighting: truth only"}
PHASE_MARK = {"DONE": ("✓", GREEN), "PENDING": ("○", GRAY), "RUNNING": ("●", AMBER), "UNAVAILABLE": ("✗", RED), "SKIPPED": ("–", GRAY)}


def fmt_pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:+.1f}%"


def fmt_sig(x: float | None) -> str:
    return "—" if x is None else f"{x:+.1f}"


def fmt_t(t: datetime | None, full: bool = False) -> str:
    if t is None:
        return "—"
    return t.strftime("%Y-%m-%d %H:%M" if full else "%m-%d %H:%M")


def odds_text(x: float) -> str:
    return "1 : 1" if abs(x - 1.0) < 1e-9 else f"1 : {x:.1f}" if x >= 1 else f"{1 / x:.1f} : 1"


def sparkline(values: list[float], width: int | None = None, vmax: float | None = None) -> str:
    if not values:
        return ""
    if width and len(values) > width:                     # bucket by max so bursts survive downsampling
        step = len(values) / width
        values = [max(values[int(i * step): max(int((i + 1) * step), int(i * step) + 1)]) for i in range(width)]
    top = vmax if vmax is not None else max(values)
    if top <= 0:
        return BLOCKS[1] * len(values)
    return "".join(BLOCKS[min(8, max(1, int(round(8 * v / top))))] if v > 0 else BLOCKS[0] for v in values)


def candles(cs: list[Candle], width: int, height: int, marker: datetime | None = None, label_fmt: str = "%H:%M") -> Text:
    """One column per candle: body █ (green up, red down), wick │, volume row underneath, price axis on the right."""
    width = max(10, width - 10)
    cs = cs[-width:]
    out = Text()
    if not cs:
        out.append("no candles", style=GRAY)
        return out
    hi, lo = max(c.h for c in cs), min(c.l for c in cs)
    span = (hi - lo) or 1.0
    row = lambda p: int(round((hi - p) / span * (height - 1)))
    mcol = None
    if marker is not None:
        mcol = next((i for i, c in enumerate(cs) if c.t >= marker), None)
    for r in range(height):
        for i, c in enumerate(cs):
            top, bot = row(max(c.o, c.c)), row(min(c.o, c.c))
            wt, wb = row(c.h), row(c.l)
            col = GREEN if c.c >= c.o else RED
            if top <= r <= bot:
                out.append("█", style=col)
            elif wt <= r <= wb:
                out.append("│", style=col)
            elif mcol is not None and i == mcol:
                out.append("┊", style=AMBER)
            else:
                out.append(" ")
        price = hi - span * r / max(height - 1, 1)
        out.append(f" {price:,.2f}\n" if r in (0, height // 2, height - 1) else "\n", style=GRAY)
    vols = [c.v for c in cs]
    out.append(sparkline(vols, vmax=max(vols) or 1.0) + "  vol\n", style=GRAY)
    left, right = cs[0].t.strftime(label_fmt), cs[-1].t.strftime(label_fmt)
    pad = max(1, len(cs) - len(left) - len(right))
    out.append(left + " " * pad + right, style=GRAY)
    if mcol is not None:
        out.append(f"\n{' ' * mcol}┊ τ*", style=AMBER)
    return out


def explanation_tree(e: Explanation, title: str) -> Tree:
    t = Tree(Text(title, style=f"bold {CYAN}"))
    kids: dict[str, list] = {}
    for x in e.edges:
        kids.setdefault(x.src, []).append(x)
    seen = set()

    def add(node: Tree, nid: str):
        for x in sorted(kids.get(nid, []), key=lambda x: x.cost_mnats):
            if (x.src, x.dst) in seen:
                continue
            seen.add((x.src, x.dst))
            lab = Text()
            if x.dst.startswith("T") and x.dst[1:].isdigit():
                lab.append(f"terminal {x.dst}", style=f"bold {RED}")
            else:
                lab.append(short("N", x.dst) + " ", style=CYAN)
                lab.append(x.dst_label[:70], style=INK)
            if x.p:
                lab.append(f"   p {x.p:.3f} · {x.cost_mnats / 1000:.2f} nats", style=GRAY)
            add(node.add(lab), x.dst)

    add(t, "BOT")
    return t


def evidence_wall(h: Hypothesis, tau: datetime | None) -> Table:
    """Evidence in bands separated by the tau* wall: PRE (admissible) | LATE | POST | UNMATCHED (truth only)."""
    t = Table(box=None, expand=True, show_edge=False, pad_edge=False, header_style=f"bold {GRAY}")
    t.add_column("tier", width=4)
    t.add_column("source", width=22, no_wrap=True)
    t.add_column("first seen", width=12)
    t.add_column("evidence and grounded claims", ratio=1)
    t.add_column("", width=12)
    bands = [(PRE, "── PRE-τ*  admissible · enters P_pre and P_all"), (LATE, "── PRE-τ* sighting, text fetched after τ* · P_all only"),
             (POST, "── POST-τ*  truth only · P_all"), (UNMATCHED, "── UNMATCHED  no Engine 1 sighting · provenance insufficient · P_all only")]
    wall_done = False
    for status, head in bands:
        rows = sorted((e for e in h.evidence if e.status == status), key=lambda e: (e.first_seen is None, e.first_seen or datetime.max, e.rid))
        if status != PRE and not wall_done:
            t.add_row("", "", "", Text(f"══ τ*  {fmt_t(tau, True)} UTC " + "═" * 60, style=f"bold {AMBER}"), "")
            wall_done = True
        if not rows:
            continue
        t.add_row("", "", "", Text(head, style=STATUS_STYLE[status]), "")
        for e in rows:
            body = Text(e.title[:90] or "(untitled)", style=INK if status == PRE else GRAY)
            for c in e.claims[:3]:
                body.append(f"\n  {c.predicate}", style=CYAN)
                if c.text:
                    body.append(f'  "{c.text[:70]}"', style=GRAY)
            flag = Text("◆ diagnostic", style=f"bold {AMBER}") if e.diagnostic else Text("copy" if e.copy else "", style=GRAY)
            t.add_row(f"T{e.tier}", e.source[:22], fmt_t(e.first_seen), body, flag)
    if not h.evidence:
        t.add_row("", "", "", Text("no evidence recorded for this hypothesis", style=GRAY), "")
    return t


def bits_table(inv: Investigation) -> Table:
    t = Table(box=None, expand=True, header_style=f"bold {GRAY}")
    for c, kw in (("hypothesis", {"ratio": 1}), ("P_pre  (could it have moved the price?)", {"width": 40}),
                  ("P_all  (is it true?)", {"width": 26}), ("signature", {"width": 18})):
        t.add_column(c, **kw)
    for h in inv.hypotheses:
        def cell(v, bits):
            x = Text(VERDICT_SHORT.get(v, v), style=f"bold {VERDICT_STYLE.get(v, GRAY)}")
            if bits:
                x.append(f"   {''.join(map(str, bits))}", style=GRAY)
            return x
        sig = Text("burst ✓ " if h.burst else "burst ✗ ", style=GREEN if h.burst else GRAY)
        sig.append("surprise ✓" if h.surprise_ok else "surprise ✗", style=GREEN if h.surprise_ok else GRAY)
        t.add_row(Text(f"{h.hid}  {h.label[:60]}", style=INK), cell(h.verdict_pre, h.bits_pre), cell(h.verdict_all, h.bits_all), sig)
    if not inv.hypotheses:
        t.add_row(Text("verdicts not run yet", style=GRAY), "", "", "")
    return t


def histogram(costs: list[int], real: int | None, width: int = 40, height: int = 6) -> Text:
    out = Text()
    if not costs:
        out.append("no placebo costs recorded", style=GRAY)
        return out
    lo, hi = min(costs + ([real] if real else [])), max(costs + ([real] if real else []))
    span = (hi - lo) or 1
    bins = [0] * width
    for c in costs:
        bins[min(width - 1, int((c - lo) / span * (width - 1)))] += 1
    rcol = min(width - 1, int((real - lo) / span * (width - 1))) if real is not None else None
    top = max(bins) or 1
    for r in range(height, 0, -1):
        for i, b in enumerate(bins):
            if i == rcol:
                out.append("┃", style=f"bold {AMBER}")
            else:
                out.append("█" if b / top * height >= r else " ", style=GRAY)
        out.append("\n")
    out.append(f"{lo / 1000:.1f}".ljust(width - 6) + f"{hi / 1000:.1f} nats\n", style=GRAY)
    if rcol is not None:
        out.append(" " * rcol + f"┃ this case {real / 1000:.2f}", style=f"bold {AMBER}")
    return out
