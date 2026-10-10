"""One visual system for every panel (Bloomberg-like discipline: black, amber labels, white values, green up /
red down with a sign, inverse amber selection). Panels are separated by numbered title bars, not boxes."""
from __future__ import annotations

from rich.text import Text

BG = "#000000"
BAR = "#141414"           # panel title bar background
AMBER = "#fa7900"         # labels, titles (third-party estimate of the Bloomberg orange)
AMBER_HI = "#ffb000"      # emphasis
WHITE = "#e8e8e8"         # values
DIM = "#7a7f87"           # secondary text
FAINT = "#3a3d42"         # rules, gridlines
UP = "#2fbf71"
DOWN = "#ff4d4d"
ID = "#5fb3c8"            # identifiers (narratives, cases), used sparingly
WARN = "#ffcc00"

RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in
       {"AMBER": AMBER, "AMBER_HI": AMBER_HI, "WHITE": WHITE, "DIM": DIM, "FAINT": FAINT, "UP": UP, "DOWN": DOWN, "ID": ID}.items()}
SERIES = [RGB["AMBER"], RGB["ID"], RGB["WHITE"], (186, 120, 255), (255, 214, 102), (120, 200, 120)]


def bar(n: int, title: str, right: str = "", width: int = 200) -> Text:
    """'1) TITLE ──────────── right' in amber on the bar colour."""
    t = Text(style=f"on {BAR}", no_wrap=True, overflow="crop")
    t.append(f" {n}) " if n else " ", style=f"bold {AMBER_HI} on {BAR}")
    t.append(title.upper(), style=f"bold {AMBER} on {BAR}")
    t.append(" ", style=f"on {BAR}")
    pad = max(1, width - len(t.plain) - len(right) - 2)
    t.append("─" * pad, style=f"{FAINT} on {BAR}")
    if right:
        t.append(f" {right} ", style=f"{DIM} on {BAR}")
    return t


def signed(x: float | None, pct: bool = True, digits: int = 2) -> Text:
    if x is None:
        return Text("n/a", style=DIM)
    v = 100 * x if pct else x
    arrow = "▲" if v > 0 else ("▼" if v < 0 else "■")
    return Text(f"{arrow} {abs(v):.{digits}f}{'%' if pct else ''}", style=UP if v > 0 else (DOWN if v < 0 else DIM))


def kv(label: str, value: str, style: str = WHITE) -> Text:
    return Text.assemble((f"{label} ", AMBER), (value, style))


CSS = f"""
Screen {{ background: {BG}; color: {WHITE}; }}
.bar {{ height: 1; background: {BAR}; }}
.panel {{ background: {BG}; padding: 0 1; }}
Input#cmd {{ height: 1; border: none; background: {BG}; color: {AMBER_HI}; padding: 0 1; }}
Input#cmd:focus {{ border: none; }}
DataTable {{ background: {BG}; scrollbar-size-vertical: 1; }}
DataTable > .datatable--header {{ background: {BG}; color: {AMBER}; text-style: bold; }}
DataTable > .datatable--cursor {{ background: {AMBER}; color: #000000; text-style: bold; }}
DataTable > .datatable--hover {{ background: #1c1c1c; }}
DataTable:blur > .datatable--cursor {{ background: #2a2a2a; color: {WHITE}; }}
Toast {{ background: #1a1a1a; color: {WHITE}; border-left: thick {AMBER}; }}
"""
