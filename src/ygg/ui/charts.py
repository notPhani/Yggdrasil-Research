"""The hero chart: one clean price chart drawn with braille dots (2x4 sub-pixels per cell) via plotext, sized to
its widget and re-rendered on resize. Line by default (Bloomberg's default price view); candles as a toggle."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import plotext as plt
from rich.text import Text
from textual.widgets import Static

from ygg.ui.theme import RGB, SERIES


@dataclass
class Series:
    label: str
    xs: list[float]
    ys: list[float]
    color: tuple = RGB["AMBER"]


@dataclass
class ChartSpec:
    series: list[Series] = field(default_factory=list)
    candles: list | None = None                 # list of (o, h, l, c) when mode == "candles"
    mode: str = "line"
    hlines: list[tuple[float, tuple, str]] = field(default_factory=list)   # (y, colour, label)
    hist: list[float] | None = None             # histogram values (placebo costs), with vlines marking the case
    vlines: list[tuple[float, tuple, str]] = field(default_factory=list)   # (x, colour, label)
    xticks: tuple[list, list] | None = None
    volume: list[float] | None = None
    last_tag: bool = True
    y_fmt: str = "{:,.2f}"
    empty: str = "no data"


def render(spec: ChartSpec, width: int, height: int) -> Text:
    width, height = max(30, width), max(6, height)
    if spec.hist:
        plt.clear_figure()
        plt.limit_size(False, False)
        plt.plotsize(width, height)
        _style()
        plt.hist(spec.hist, bins=min(20, max(5, len(spec.hist))), color=RGB["DIM"])
        for x, col, _ in spec.vlines:
            plt.vline(x, col)
        return Text.from_ansi(plt.build())
    if not spec.series and not spec.candles:
        return Text(spec.empty, style="#7a7f87")
    vol_h = 5 if spec.volume and height >= 16 else 0
    # y ticks formatted by us, so the price and volume panes share one left margin
    ys = [y for s in spec.series for y in s.ys] + ([c[1] for c in spec.candles] + [c[2] for c in spec.candles] if spec.mode == "candles" and spec.candles else [])
    ys += [y for y, _, _ in spec.hlines]
    lo, hi = min(ys), max(ys)
    pad = (hi - lo) * 0.04 or abs(hi) * 0.01 or 1.0
    lo, hi = lo - pad, hi + pad
    n_t = 5 if height - vol_h >= 12 else 3
    tv = [lo + (hi - lo) * i / (n_t - 1) for i in range(n_t)]
    tl = [spec.y_fmt.format(v) for v in tv]
    lw = max(len(x) for x in tl)
    plt.clear_figure()
    plt.limit_size(False, False)
    plt.plotsize(width, height - vol_h)
    _style()
    plt.ylim(lo, hi)
    plt.yticks(tv, [x.rjust(lw) for x in tl])
    if spec.mode == "candles" and spec.candles:
        xs = list(range(len(spec.candles)))
        plt.candlestick(xs, {"Open": [c[0] for c in spec.candles], "High": [c[1] for c in spec.candles],
                             "Low": [c[2] for c in spec.candles], "Close": [c[3] for c in spec.candles]},
                        colors=[RGB["UP"], RGB["DOWN"]])
    else:
        for s in spec.series:
            if s.xs:
                plt.plot(s.xs, s.ys, marker="braille", color=s.color, label=s.label if len(spec.series) > 1 else None)
    for y, col, _ in spec.hlines:
        plt.hline(y, col)
    for x, col, _ in spec.vlines:
        plt.vline(x, col)
    if spec.xticks:
        plt.xticks(*spec.xticks)
    if spec.last_tag and spec.series and spec.series[0].ys:
        s = spec.series[0]
        lab = "◀ " + spec.y_fmt.format(s.ys[-1])
        span = (s.xs[-1] - s.xs[0]) or 1
        x = s.xs[-1] - span * (len(lab) + 2) / max(width - lw - 4, 10)
        plt.text(lab, x, s.ys[-1], color=s.color, background=(0, 0, 0))
    out = plt.build()
    if vol_h:
        plt.clear_figure()
        plt.limit_size(False, False)
        plt.plotsize(width, vol_h)
        _style()
        top = max(spec.volume) or 1.0
        plt.bar(list(range(len(spec.volume))), spec.volume, color=RGB["DIM"], width=0.6)
        plt.xticks([], [])
        plt.yticks([top], ["vol".rjust(lw)])
        out = out + "\n" + plt.build()
    return Text.from_ansi(out)


def _style() -> None:
    plt.canvas_color((0, 0, 0))
    plt.axes_color((0, 0, 0))
    plt.ticks_color(RGB["DIM"])
    plt.frame(False)
    plt.grid(False, False)


class HeroChart(Static):
    """A Static that renders a ChartSpec at its current size."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.spec = ChartSpec()

    def show(self, spec: ChartSpec) -> None:
        self.spec = spec
        self._draw()

    def on_resize(self) -> None:
        self._draw()

    def _draw(self) -> None:
        w, h = self.size.width, self.size.height
        if w and h:
            self.update(render(self.spec, w, h))


def pct_overlay(rows_by_sym: dict[str, list[tuple]], ref_date: str) -> tuple[list[Series], list[str]]:
    """Daily closes of several instruments as % change from their close on the last day before ref_date."""
    dates = sorted({r[0] for rows in rows_by_sym.values() for r in rows})
    idx = {d: i for i, d in enumerate(dates)}
    out = []
    for k, (sym, rows) in enumerate(rows_by_sym.items()):
        base = [r for r in rows if r[0] < ref_date]
        if not base:
            continue
        b = base[-1][4]
        out.append(Series(sym, [idx[r[0]] for r in rows], [100 * (r[4] / b - 1) for r in rows], SERIES[k % len(SERIES)]))
    return out, dates
