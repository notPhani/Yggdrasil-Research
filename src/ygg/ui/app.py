"""Yggdrasil terminal: a live control panel and a full-page investigation workspace (Textual + plotext).

  ygg ui            live control panel: GDELT world feed, 1-minute candles, the recorded world model, investigations
  ygg ui --demo     adds the DEMO investigation fixture (labelled MODE: DEMO everywhere it appears)

The UI is a projection of recorded state: it never recomputes a result, never moves tau*, and never shows a record
whose first_seen is after the clock it is drawing (live: the latest served batch; replay: the replay clock).
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rich.console import Group
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static, TabbedContent, TabPane
from textual_plotext import PlotextPlot

from ygg.ui import live as L
from ygg.ui.domain import LATE, POST, PRE, UNMATCHED, CaseRow, Investigation, short
from ygg.ui.recorded import World, list_cases, load_investigation, replay_clock_range
from ygg.ui.render import (AMBER, CYAN, GRAY, GREEN, INK, PHASE_MARK, RED, VERDICT_SHORT, VERDICT_STYLE, bits_table,
                           evidence_wall, explanation_tree, fmt_pct, fmt_sig, fmt_t, odds_text, sparkline)

CSS = """
Screen { background: #0a0f13; color: #d7e0e6; }
#hdr, #ihdr { height: 1; background: #111a21; padding: 0 1; }
#row1 { height: 22; }
#watch { width: 60; border: round #2c3a45; }
#chartbox { width: 1fr; border: round #2c3a45; }
#chart { height: 1fr; }
#volchart { height: 7; }
#params { width: 46; height: 100%; border: round #2c3a45; padding: 0 1; }
#row2 { height: 16; }
#world { width: 1fr; height: 100%; border: round #2c3a45; padding: 0 1; }
#feed { width: 1fr; height: 100%; border: round #2c3a45; padding: 0 1; }
#cases { height: 7; border: round #58c4dd; }
#row4 { height: 1fr; }
#pipeline { width: 1fr; height: 100%; border: round #2c3a45; padding: 0 1; }
#tape { width: 1fr; height: 100%; border: round #2c3a45; padding: 0 1; }
DataTable { background: #0a0f13; }
DataTable > .datatable--header { background: #111a21; color: #76828c; }
DataTable > .datatable--cursor { background: #1d3340; color: #ffffff; }
TabbedContent { height: 1fr; }
.panel { border: round #2c3a45; padding: 0 1; height: auto; }
#ov_metrics { height: auto; border: round #58c4dd; padding: 0 1; }
#ov_top { height: auto; }
#ov_case { width: 66; }
#ov_paths { width: 1fr; }
#ov_charts { height: 16; }
.mk { width: 1fr; border: round #2c3a45; }
#st_plot { height: 20; border: round #2c3a45; }
#st_alpha { height: 12; border: round #2c3a45; }
#pl_plot { height: 16; border: round #2c3a45; }
"""


def _border(w, title: str, sub: str = "") -> None:
    w.border_title = title
    if sub:
        w.border_subtitle = sub


def _paths(e) -> list[list]:
    """Every root-to-terminal path of an explanation tree (BOT -> ... -> terminal), as lists of edges."""
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
            if any(x.dst == y.src for y in acc):
                continue
            walk(x.dst, acc + [x])

    walk("BOT", [])
    return out


def _is_term(nid: str) -> bool:
    return nid.startswith("T") and nid[1:].isdigit()


# ====================================================================================================== control panel
class ControlPanel(Screen):
    BINDINGS = [Binding("enter", "open_case", "open case"), Binding("w", "focus_watch", "market"),
                Binding("c", "focus_cases", "investigations"), Binding("n", "poll_news", "check news now"),
                Binding("q", "app.quit", "quit")]

    def compose(self) -> ComposeResult:
        yield Static(id="hdr")
        with Horizontal(id="row1"):
            yield DataTable(id="watch", cursor_type="row")
            with Vertical(id="chartbox"):
                yield PlotextPlot(id="chart")
                yield PlotextPlot(id="volchart")
            yield Static(id="params")
        with Horizontal(id="row2"):
            yield Static(id="world")
            yield Static(id="feed")
        yield DataTable(id="cases", cursor_type="row")
        with Horizontal(id="row4"):
            yield Static(id="pipeline")
            yield Static(id="tape")
        yield Footer()

    def on_mount(self) -> None:
        w = self.query_one("#watch", DataTable)
        for col, wd in (("symbol", 9), ("last", 11), ("chg", 7), ("1m · last 2h", 20), ("z1m", 5), ("state", 6)):
            w.add_column(col, key=col, width=wd)
        for s in L.WATCH:
            w.add_row(Text(s, style=AMBER if s in L.DEMO_EXTRA else INK), Text("loading", style=GRAY), "", "", "", "", key=s)
        _border(w, "MARKET WATCH", "Yahoo 1-min bars · * = 24/7 demo extra")
        c = self.query_one("#cases", DataTable)
        for col in ("", "case", "phase", "clusters", "max|SAR|", "best explanation", "odds vs we-don't-know", "placebo p", "source"):
            c.add_column(col, key=col or "mark")
        _border(c, "INVESTIGATIONS", "active (live) · archived (recorded) · enter opens a full-page workspace")
        _border(self.query_one("#chartbox"), "SELECTED ASSET · 1-minute candles")
        _border(self.query_one("#params"), "PARAMETERS")
        _border(self.query_one("#world"), "WORLD MODEL", "recorded replay state · the live model is cold")
        _border(self.query_one("#feed"), "WORLD FEED", "GDELT GKG · latest served batch")
        _border(self.query_one("#pipeline"), "PIPELINE", "what each engine is doing now")
        _border(self.query_one("#tape"), "EVENT TAPE")
        self.feed_offset = 0
        self.next_poll = time.time() + 60
        self.load_cases()
        self.render_world()
        self.render_header()
        self.render_pipeline()
        self.set_interval(1.0, self.render_header)
        self.set_interval(2.0, self.scroll_feed)
        self.set_interval(10.0, self.render_pipeline)
        self.set_interval(30.0, self.refresh_quotes)
        self.set_interval(60.0, self.action_poll_news)
        self.set_interval(120.0, self.render_world)
        self.refresh_quotes()
        self.action_poll_news()
        w.focus()

    # ---------------------------------------------------------------- data
    def refresh_quotes(self) -> None:
        self.run_worker(self._quotes, thread=True, exclusive=True, group="quotes")

    def _quotes(self) -> None:
        out = {s: L.quote(s) for s in L.WATCH}
        self.app.call_from_thread(self._apply_quotes, out)

    def _apply_quotes(self, qs: dict) -> None:
        app: YggApp = self.app
        app.quotes.update(qs)
        w = self.query_one("#watch", DataTable)
        for s, q in qs.items():
            if q.state == "UNAVAILABLE":
                w.update_cell(s, "last", Text("unavailable", style=RED))
                continue
            p = L.params(q)
            chg = q.change
            closes = [c.c for c in q.candles[-120:]]
            lo, hi = (min(closes), max(closes)) if closes else (0, 1)
            spark = sparkline([c - lo for c in closes], 20, (hi - lo) or 1.0)
            w.update_cell(s, "last", Text(f"{q.last:,.2f}", style=INK))
            w.update_cell(s, "chg", Text(fmt_pct(chg), style=GREEN if (chg or 0) >= 0 else RED) if chg is not None else Text("n/a", style=GRAY))
            w.update_cell(s, "1m · last 2h", Text(spark, style=GREEN if closes and closes[-1] >= closes[0] else RED))
            z = p.get("z_ret")
            w.update_cell(s, "z1m", Text(f"{z:+.1f}" if z is not None else "n/a", style=(RED if z is not None and abs(z) >= 4 else GRAY)))
            w.update_cell(s, "state", Text(q.state, style=GREEN if q.state == "OPEN" else GRAY))
        app.tape(f"QUOTES     {sum(q.state != 'UNAVAILABLE' for q in qs.values())}/{len(qs)} symbols · 1-min bars")
        self.render_asset()

    def action_poll_news(self) -> None:
        self.next_poll = time.time() + 60
        self.run_worker(self._news, thread=True, exclusive=True, group="news")

    def _news(self) -> None:
        b = self.app.world.poll()
        self.app.call_from_thread(self._apply_news, b)

    def _apply_news(self, b) -> None:
        app: YggApp = self.app
        for x in app.world.batches[-8:]:
            key = (x.ts, x.status)
            if key not in app.seen_batches:
                app.seen_batches.add(key)
                app.tape(f"BATCH      {x.ts:%H:%M} UTC  " + (f"served · {x.docs} docs" if x.status == "OK" else "listed, not served yet"))
                if x.status == "OK":
                    self.feed_offset = 0
        if b is None and app.world.error:
            app.tape(f"BATCH      error: {app.world.error}")
        self.render_feed()
        self.render_pipeline()

    def load_cases(self) -> None:
        app: YggApp = self.app
        c = self.query_one("#cases", DataTable)
        c.clear()
        c.add_row(Text("●", style=GREEN), Text("LIVE", style=GREEN), Text("WAITING", style=GRAY),
                  Text("no live anomaly: equities closed; the intraday live trigger is outside the hackathon cut", style=GRAY),
                  "", "", "", "", Text("LIVE", style=GREEN), key="__live__")
        rows: list[CaseRow] = list_cases(app.data_dir)
        if app.demo:
            from ygg.ui.demo import demo_investigation

            inv = demo_investigation()
            b = inv.best
            rows.append(CaseRow(inv.case_id, "ARCHIVED", "VERDICTS", "C1(5)  C2(4)", 7.8, b.entry_label if b else "",
                                inv.abstention.odds_vs_best if inv.abstention else None, inv.placebo.p_emp if inv.placebo else None, "DEMO"))
        for r in rows:
            c.add_row(Text("◉", style=CYAN), Text(r.case_id, style=f"bold {CYAN}"), r.phase, r.terminals,
                      f"{r.max_sar:.1f}" if r.max_sar else "", Text(r.best[:56], style=INK), odds_text(r.odds) if r.odds else "",
                      f"{r.p_emp:.3f}" if r.p_emp is not None else "",
                      Text(r.source, style=AMBER if r.source == "DEMO" else GREEN), key=f"{r.source}:{r.case_id}")

    # ---------------------------------------------------------------- render
    def render_header(self) -> None:
        app: YggApp = self.app
        now = datetime.now(timezone.utc)
        t = Text()
        t.append(" YGGDRASIL ", style=f"bold {CYAN}")
        t.append("● LIVE ", style=f"bold {GREEN}")
        wt = app.world.last_ok
        if wt:
            t.append(f"world @ {wt:%H:%M} UTC (lag {int((now - wt).total_seconds() // 60)} min) ", style=INK)
        else:
            t.append("world: waiting for a served batch ", style=AMBER)
        t.append(f"│ next news check {max(0, int(self.next_poll - time.time()))}s ", style=GRAY)
        wk = now.weekday() >= 5
        t.append("│ US ", style=GRAY)
        t.append("CLOSED " if wk else "SESSION ", style=GRAY if wk else GREEN)
        t.append("EU ", style=GRAY)
        t.append("CLOSED " if wk else "SESSION ", style=GRAY if wk else GREEN)
        t.append("crypto ", style=GRAY)
        t.append("OPEN ", style=GREEN)
        rp = app.replay_progress()
        if rp:
            t.append(f"│ {rp} ", style=CYAN)
        t.append(f"│ {now:%H:%M:%S} UTC │ cfg {app.cfg_hash[:8]} ", style=GRAY)
        if app.demo:
            t.append("│ MODE: DEMO fixture listed ", style=f"bold {AMBER}")
        self.query_one("#hdr", Static).update(t)

    def _selected(self) -> str:
        w = self.query_one("#watch", DataTable)
        return L.WATCH[min(max(w.cursor_row, 0), len(L.WATCH) - 1)]

    def render_asset(self) -> None:
        app: YggApp = self.app
        sym = self._selected()
        q = app.quotes.get(sym)
        box = self.query_one("#chartbox")
        chart, volc, par = self.query_one("#chart", PlotextPlot), self.query_one("#volchart", PlotextPlot), self.query_one("#params", Static)
        if q is None:
            return
        if q.state == "UNAVAILABLE" or not q.candles:
            par.update(Text(f"{sym}\nprice source could not be queried\n{q.error}", style=RED))
            return
        n = max(30, min(len(q.candles), (chart.size.width or 120) - 14))
        cs = q.candles[-n:]
        x = list(range(len(cs)))
        p = chart.plt
        p.clear_figure()
        p.candlestick(x, {"Open": [c.o for c in cs], "Close": [c.c for c in cs], "High": [c.h for c in cs], "Low": [c.l for c in cs]})
        ticks = [0, len(cs) // 4, len(cs) // 2, 3 * len(cs) // 4, len(cs) - 1]
        p.xticks(ticks, [cs[i].t.strftime("%H:%M") for i in ticks])
        p.title(f"{sym} · 1-minute · {cs[0].t:%a %H:%M} → {cs[-1].t:%H:%M} UTC · {q.state}")
        pr = L.params(q)
        if pr.get("vwap"):
            p.hline(pr["vwap"], "cyan")
        chart.refresh()
        v = volc.plt
        v.clear_figure()
        v.bar(x, [c.v for c in cs], color="gray", width=0.4)
        v.xticks([], [])
        v.ylabel("vol")
        volc.refresh()
        box.border_title = f"SELECTED ASSET · {sym} · 1-minute candles" + ("  · 24/7 demo extra, outside the equity universe" if sym in L.DEMO_EXTRA else "")
        t = Table.grid(padding=(0, 1))
        t.add_column(style=GRAY)
        t.add_column(justify="right")
        chg = q.change
        t.add_row("last", Text(f"{q.last:,.2f}", style=f"bold {INK}"))
        t.add_row("vs prev close", Text(f"{fmt_pct(chg)}  ({q.prev_close:,.2f})" if chg is not None and q.prev_close else "n/a",
                                        style=GREEN if (chg or 0) >= 0 else RED))
        t.add_row("state", Text(q.state + ("  (last session shown)" if q.state == "CLOSED" else ""), style=GREEN if q.state == "OPEN" else GRAY))
        t.add_row("open", f"{pr['open']:,.2f}" if pr else "")
        t.add_row("high / low", f"{pr['high']:,.2f} / {pr['low']:,.2f}" if pr else "")
        t.add_row("range", f"{100 * (pr['high'] / pr['low'] - 1):.2f}%" if pr else "")
        t.add_row("VWAP (cyan line)", f"{pr['vwap']:,.2f}" if pr.get("vwap") else "no volume")
        t.add_row("volume", f"{pr['volume']:,.0f}" if pr else "")
        t.add_row("bars", f"{pr['bars']} × 1m" if pr else "")
        t.add_row("RV 1m, annualized", f"{100 * pr['rv_ann']:.1f}%" if pr.get("rv_ann") else "")
        zr, zv = pr.get("z_ret"), pr.get("z_vol")
        t.add_row("last 1m return z", Text(f"{zr:+.2f}" if zr is not None else "", style=RED if zr is not None and abs(zr) >= 4 else INK))
        t.add_row("last 1m volume z", Text(f"{zv:+.2f}" if zv is not None else "no volume", style=INK if zv is not None else GRAY))
        t.add_row("bars from", f"{pr['first']:%m-%d %H:%M} UTC" if pr else "")
        t.add_row("last bar", f"{pr['last']:%m-%d %H:%M} UTC" if pr else "")
        note = Text("\nrobust z = 0.6745·(x − median)/MAD over the bars shown.\nDescriptive only: the case trigger is the daily "
                    "market-only SAR gate; the live intraday test is outside the cut.", style=GRAY)
        par.update(Group(t, note))

    def on_data_table_row_highlighted(self, ev: DataTable.RowHighlighted) -> None:
        if ev.data_table.id == "watch":
            self.render_asset()

    def on_data_table_row_selected(self, ev: DataTable.RowSelected) -> None:
        if ev.data_table.id == "cases":
            self.action_open_case()

    def scroll_feed(self) -> None:
        self.feed_offset += 1
        self.render_feed()

    def render_feed(self) -> None:
        app: YggApp = self.app
        box = self.query_one("#feed", Static)
        feed = app.world.feed
        ok = [b for b in app.world.batches if b.status == "OK"]
        if not feed:
            box.update(Text(app.world.error or "waiting for the first served GDELT batch…", style=AMBER))
            return
        latest = ok[-1] if ok else None
        h = max(4, box.size.height - 4)
        n = len(feed)
        i0 = self.feed_offset % n
        rows = [feed[(i0 + k) % n] for k in range(min(h, n))]
        from collections import Counter

        top = Counter(f.source for f in feed[: latest.docs if latest else n]).most_common(3)
        t = Text()
        t.append(f"batch {latest.ts:%H:%M} UTC · {latest.docs} docs · showing {i0 + 1}–{min(n, i0 + h)} of {n} · "
                 f"top sources {', '.join(s for s, _ in top)}\n" if latest else "", style=GRAY)
        width = max(20, box.size.width - 28)
        for f in rows:
            t.append(f"{f.t:%H:%M} ", style=GRAY)
            t.append(f"{f.source[:18]:<18} ", style=CYAN)
            t.append(f"{f.title[:width]}\n", style=INK)
        box.update(t)

    def render_world(self) -> None:
        app: YggApp = self.app
        box = self.query_one("#world", Static)
        try:
            from ygg.ui.stats import world_stats

            s = world_stats(app.data_dir)
        except Exception as e:
            box.update(Text(f"world model unavailable: {e}", style=RED))
            return
        if s is None:
            box.update(Text("no recorded world model yet (run ygg replay)", style=AMBER))
            return
        box.border_title = f"WORLD MODEL · recorded through {s.day} ({s.days_done} replay days)"
        g = Table.grid(expand=True, padding=(0, 2))
        for _ in range(4):
            g.add_column()
        kv = lambda k, v, st=INK: Text.assemble((f"{k} ", GRAY), (v, st))
        g.add_row(kv("narratives alive", f"{s.alive}/300", AMBER if s.alive >= 300 else INK), kv("dormant", str(s.dormant)),
                  kv("total", str(s.total)), kv("born 24h", str(s.born_day)))
        g.add_row(kv("stories/day", f"{s.roots_day:,}"), kv("copies merged", f"{s.copies_day:,}"), kv("none share", f"{s.none_share:.2f}"),
                  kv("bursts 24h", f"{s.bursts_day} on {s.burst_narratives}", AMBER if s.bursts_day else INK))
        g.add_row(kv("κ_s / implied", f"{s.kappa_s:.0f} / {s.kappa_implied:.0f}" if s.kappa_implied else f"{s.kappa_s:.0f}"),
                  kv("κ₀ background", f"{s.kappa0:.0f}"), kv("price/narrative", f"{-s.price:.0f} nats"), kv("cap term", f"{s.cap_term:.0f} nats"))
        g.add_row(kv("ω competition", f"{s.omega:.2f}"), kv("NB2 r", f"{s.r:.2f}"), kv("edges 24h", f"{s.edges_day:,}"),
                  kv("BOT share", f"{100 * s.bot_share:.0f}%" if s.bot_share is not None else "n/a"))
        top = Table(box=None, expand=True, padding=(0, 1), header_style=f"bold {GRAY}")
        top.add_column("top narratives by attention (24h)", ratio=3, no_wrap=True)
        top.add_column("48h", width=26)
        top.add_column("mass", justify="right", width=7)
        top.add_column("b", justify="right", width=3)
        vmax = max((max(n.series) for n in s.top if n.series), default=1.0) or 1.0
        for n in s.top:
            lab = Text(f"{short('N', n.nid)} ", style=CYAN)
            lab.append(n.label[:46], style=INK)
            if n.entities:
                lab.append(f"  {', '.join(n.entities[:2])}", style=GRAY)
            top.add_row(lab, Text(sparkline(n.series, 26, vmax), style=GREEN), f"{n.mass_day:,.0f}",
                        Text(str(n.bursts), style=AMBER if n.bursts else GRAY))
        box.update(Group(g, Text(""), top))

    def render_pipeline(self) -> None:
        app: YggApp = self.app
        wd = app.world
        ok = [b for b in wd.batches if b.status == "OK"]
        waiting = [b for b in wd.batches if b.status == "NOT_YET" and (not ok or b.ts > ok[-1].ts)]
        rp = app.replay_progress()
        t = Table(box=None, expand=True, padding=(0, 1), show_header=False)
        t.add_column(width=26)
        t.add_column(width=12)
        t.add_column(ratio=1)
        st = {"RUNNING": GREEN, "WAITING": AMBER, "IDLE": GRAY, "UNAVAILABLE": RED, "COLD": AMBER, "REPLAYING": CYAN}
        rows = [("E1  observation · news", "RUNNING" if ok else "WAITING",
                 (f"batch {ok[-1].ts:%H:%M} · {ok[-1].docs} docs" if ok else "no served batch yet") + (f" · {len(waiting)} listed, not served" if waiting else "")),
                ("E2a grouping (live)", "COLD", "no warmed live state · recorded model shown"),
                ("E2  replay engine", "REPLAYING" if rp and "running" in rp else "IDLE", rp or "no replay running"),
                ("OBS stock observer", "IDLE", "daily SAR gate · equities closed"),
                ("E3a search", "IDLE", "exact DPBF on open · 20 placebos"),
                ("E3b evidence", "UNAVAILABLE" if not app.serpapi else "IDLE",
                 "no SerpApi key: GDELT + Wayback only" if not app.serpapi else "SerpApi · ≤15 queries/case"),
                ("E3b verdicts", "IDLE", "clingo four bits · Lean stretch not run")]
        for name, s_, d in rows:
            t.add_row(Text(name, style=CYAN), Text(s_, style=st.get(s_, GRAY)), Text(d, style=INK))
        self.query_one("#pipeline", Static).update(t)
        self.render_tape()

    def render_tape(self) -> None:
        app: YggApp = self.app
        t = Text()
        box = self.query_one("#tape", Static)
        for ts, msg in list(app.events)[-max(4, box.size.height - 2):][::-1]:
            t.append(f"{ts:%H:%M:%S}  ", style=GRAY)
            t.append(msg + "\n", style=INK)
        box.update(t)

    # ---------------------------------------------------------------- actions
    def action_focus_watch(self) -> None:
        self.query_one("#watch").focus()

    def action_focus_cases(self) -> None:
        self.query_one("#cases").focus()

    def action_open_case(self) -> None:
        import json

        c = self.query_one("#cases", DataTable)
        if c.row_count == 0:
            return
        key = c.coordinate_to_cell_key((c.cursor_row, 0)).row_key.value
        if not key or key == "__live__":
            return
        src, day = key.split(":", 1)
        app: YggApp = self.app
        if src == "DEMO":
            from ygg.ui.demo import demo_case

            raw = demo_case()
            inv = load_investigation(raw, source="DEMO")
        else:
            raw = json.loads((app.data_dir / "cases" / f"{day}.json").read_text())
            inv = load_investigation(raw)
        app.tape(f"OPEN       case {day} ({src})")
        app.push_screen(InvestigationScreen(inv, raw))


# ====================================================================================================== investigation
STEPS = ["trigger", "snapshot", "search", "placebos", "queries", "claims", "verdicts", "lean"]


class InvestigationScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "back"), Binding("r", "toggle_replay", "replay (recorded)"),
                Binding("plus,equals", "faster", "faster"), Binding("minus", "slower", "slower"),
                Binding("h", "next_hyp", "next hypothesis"), Binding("g", "graph_focus", "graph: focus next node"),
                Binding("q", "app.quit", "quit")]

    def __init__(self, inv: Investigation, raw: dict | None = None):
        super().__init__()
        self.inv, self.raw = inv, raw
        self.clock: datetime | None = None
        self.speed = 8
        self.revealed = len(STEPS)
        self.hyp_i = 0
        self.focus_i = -1
        self._timer = None
        self._step_wait = 0

    def compose(self) -> ComposeResult:
        yield Static(id="ihdr")
        with TabbedContent(id="tabs"):
            with TabPane("Overview", id="t_over"):
                with VerticalScroll():
                    yield Static(id="ov_metrics")
                    with Horizontal(id="ov_top"):
                        yield Static(id="ov_case", classes="panel")
                        yield Static(id="ov_paths", classes="panel")
                    with Horizontal(id="ov_charts"):
                        for k in range(3):
                            yield PlotextPlot(id=f"mk{k}", classes="mk")
                    yield Static(id="ov_matrix", classes="panel")
                    yield Static(id="ov_prog", classes="panel")
            with TabPane("Story", id="t_story"):
                with VerticalScroll():
                    yield PlotextPlot(id="st_plot")
                    yield PlotextPlot(id="st_alpha")
                    yield Static(id="st_feed", classes="panel")
            with TabPane("Tree", id="t_tree"):
                with VerticalScroll():
                    yield Static(id="tr_main", classes="panel")
            with TabPane("Evidence", id="t_ev"):
                with VerticalScroll():
                    yield Static(id="ev_main", classes="panel")
            with TabPane("Logic", id="t_logic"):
                with VerticalScroll():
                    yield Static(id="lg_main", classes="panel")
            with TabPane("Placebos", id="t_plac"):
                with VerticalScroll():
                    yield PlotextPlot(id="pl_plot")
                    yield Static(id="pl_main", classes="panel")
            with TabPane("Search trace", id="t_trace"):
                with VerticalScroll():
                    yield Static(id="sx_main", classes="panel")
            with TabPane("Audit", id="t_audit"):
                with VerticalScroll():
                    yield Static(id="au_main", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        app: YggApp = self.app
        self.world = app.recorded_world()
        for wid, title in (("ov_metrics", "CASE AT A GLANCE"), ("ov_case", "INSTRUMENTS · market-only abnormal returns"),
                           ("ov_paths", "EXPLANATIONS · every path the search kept, BOT → narratives → market cluster"),
                           ("ov_matrix", "VERDICT MATRIX · hypotheses × programs × evidence"), ("ov_prog", "RESEARCH PROGRESS"),
                           ("st_plot", "ATTENTION · narratives in the explanations · τ* marked"),
                           ("st_alpha", "SPILLOVER · edge shares α along the explanation paths"),
                           ("st_feed", "DOCUMENTS of those narratives · first_seen ≤ clock"),
                           ("tr_main", "EXPLANATION TREES"), ("ev_main", "EVIDENCE"), ("lg_main", "LOGIC · every consistent reading (clingo)"),
                           ("pl_plot", "PLACEBOS · best-explanation cost on quiet days vs this case"), ("pl_main", "PLACEBO STATISTICS"),
                           ("sx_main", "EVIDENCE ACQUISITION"), ("au_main", "AUDIT")):
            _border(self.query_one(f"#{wid}"), title)
        self.render_all()
        self.set_interval(1.0, self.render_header)
        from ygg.ui.graph_server import payload_for

        app.graph.show(payload_for(self.inv, self.raw))
        app.tape(f"GRAPH      showing case {self.inv.case_id} at {app.graph.url}")

    # ---------------------------------------------------------------- graph link
    def action_graph_focus(self) -> None:
        order = []
        for e in sorted(self.inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
            for x in e.edges:
                for nid in (x.src, x.dst):
                    if nid not in order:
                        order.append(nid)
        if not order:
            return
        self.focus_i = (self.focus_i + 1) % len(order)
        nid = order[self.focus_i]
        self.app.graph.focus(nid)
        self.app.tape(f"GRAPH      focus {nid if nid == 'BOT' or _is_term(nid) else short('N', nid)}")
        self.notify(f"graph ← focus {nid if nid == 'BOT' or _is_term(nid) else short('N', nid)}", timeout=2)

    def graph_selected(self, nid: str) -> None:
        for i, h in enumerate(self.inv.hypotheses):
            if h.entry == nid:
                self.hyp_i = i
                self.query_one("#tabs", TabbedContent).active = "t_ev"
                self.render_evidence()
                self.notify(f"graph → {h.hid}: {h.label[:60]}", timeout=3)
                return
        lab = next((x.dst_label for e in self.inv.explanations for x in e.edges if x.dst == nid), nid)
        self.notify(f"graph → {nid if nid == 'BOT' or _is_term(nid) else short('N', nid)}  {lab[:60]}", timeout=3)

    # ---------------------------------------------------------------- replay
    def action_toggle_replay(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
            self.app.tape(f"REPLAY     paused at {fmt_t(self.clock, True)}")
            self.render_all()
            return
        t0, t1 = replay_clock_range(self.inv)
        if self.clock is None or (self.clock >= t1 and self.revealed >= len(STEPS)):
            self.clock, self.revealed = t0, 0
        self._timer = self.set_interval(0.25, self.tick)
        self.app.tape(f"REPLAY     case {self.inv.case_id} from {fmt_t(self.clock, True)} (recorded state, no recomputation)")

    def tick(self) -> None:
        _, t1 = replay_clock_range(self.inv)
        if self.clock < t1:
            self.clock = min(t1, self.clock + timedelta(minutes=15 * self.speed))
        elif self.revealed < len(STEPS):
            self._step_wait += 1
            if self._step_wait >= 6:
                self._step_wait = 0
                self.revealed += 1
                self.app.tape(f"STEP       {STEPS[self.revealed - 1]} (recorded order {self.revealed}/{len(STEPS)})")
        else:
            self._timer.stop()
            self._timer = None
            self.app.tape("REPLAY     reached the recorded verdict")
        self.render_all()

    def action_faster(self) -> None:
        self.speed = min(96, self.speed * 2)

    def action_slower(self) -> None:
        self.speed = max(1, self.speed // 2)

    def action_next_hyp(self) -> None:
        if self.inv.hypotheses:
            self.hyp_i = (self.hyp_i + 1) % len(self.inv.hypotheses)
            self.render_evidence()

    def visible(self, step: str) -> bool:
        if self.clock is None:
            return True
        return STEPS.index(step) < self.revealed and self.clock >= (self.inv.detected or self.clock)

    def _locked(self, wid: str, step: str) -> bool:
        if self.visible(step):
            return False
        self.query_one(f"#{wid}", Static).update(Text(
            f"◉ replay clock {fmt_t(self.clock, True)} UTC · the case opens at {fmt_t(self.inv.detected, True)} UTC (daily close); "
            f"'{step}' appears after that, in recorded order", style=GRAY))
        return True

    # ---------------------------------------------------------------- render
    def render_all(self) -> None:
        self.render_header()
        self.render_metrics()
        self.render_case()
        self.render_paths()
        self.render_market()
        self.render_matrix()
        self.render_progress()
        self.render_story()
        self.render_tree()
        self.render_evidence()
        self.render_logic()
        self.render_placebos()
        self.render_trace()
        self.render_audit()

    def render_header(self) -> None:
        inv = self.inv
        t = Text()
        t.append(f" CASE {inv.case_id} ", style=f"bold {CYAN}")
        t.append(f"│ detected {fmt_t(inv.detected)} UTC (daily close) ", style=INK)
        t.append(f"│ τ* {fmt_t(inv.tau_star)} UTC (first abnormal print) ", style=f"bold {AMBER}")
        t.append(f"│ snapshot w{inv.snapshot} ", style=GRAY)
        t.append(f"│ {inv.source} ", style=f"bold {AMBER}" if inv.source == "DEMO" else f"bold {GREEN}")
        if self.clock is not None:
            t.append(f"│ ◉ REPLAY {self.speed * 15} min/tick · clock {fmt_t(self.clock, True)} UTC ", style=f"bold {CYAN}")
            if inv.tau_star and self.clock >= inv.tau_star:
                t.append("· past τ*: new documents are truth-only ", style=AMBER)
        else:
            t.append("│ archive view · r replays it ", style=GRAY)
        self.query_one("#ihdr", Static).update(t)

    def render_metrics(self) -> None:
        inv = self.inv
        b, a = inv.best, inv.abstention
        g = Table.grid(expand=True, padding=(0, 2))
        for _ in range(6):
            g.add_column()
        kv = lambda k, v, st=INK: Text.assemble((f"{k} ", GRAY), (str(v), st))
        nfire = sum(1 for i in inv.instruments if i.fired)
        g.add_row(kv("fired", f"{nfire} instruments"), kv("clusters", f"{len(inv.clusters)} (terminals)"),
                  kv("τ*", fmt_t(inv.tau_star, True), AMBER),
                  kv("graph searched", f"{inv.graph_nodes} nodes · {inv.graph_edges} edges" if inv.graph_nodes else "trees only"),
                  kv("solver", "exact DPBF (optimal)"), kv("rivals kept", f"{sum(1 for e in inv.explanations if e.rank >= 2)} within 1:20"))
        if self.visible("search") and b:
            ent = b.entry_label if b.entry != "BOT" else "WE DO NOT KNOW"
            g.add_row(kv("best", f"{b.cost_mnats / 1000:.2f} nats", f"bold {INK}"),
                      kv("we-don't-know", f"{a.cost_mnats / 1000:.2f} nats" if a else "n/a"),
                      kv("odds best : abstain", f"{a.odds_vs_best:.1f} : 1" if a else "n/a", GREEN if a and a.odds_vs_best > 1 else AMBER),
                      kv("placebo p", f"{inv.placebo.p_emp:.3f} (K={inv.placebo.k})" if inv.placebo and self.visible("placebos") else "pending",
                         GREEN if inv.placebo and inv.placebo.p_emp <= 0.05 else AMBER),
                      kv("FER", f"{inv.placebo.fer:.2f}" if inv.placebo and self.visible("placebos") else "pending"),
                      kv("entry story", ent[:40], f"bold {CYAN}"))
        if self.visible("verdicts") and inv.hypotheses:
            from collections import Counter

            cp = Counter(VERDICT_SHORT.get(h.verdict_pre, h.verdict_pre) for h in inv.hypotheses)
            ev = [e for h in inv.hypotheses for e in h.evidence]
            ns = Counter(e.status for e in ev)
            nq = list(inv.searches)
            g.add_row(kv("hypotheses", len(inv.hypotheses)), kv("P_pre", " · ".join(f"{k} {v}" for k, v in cp.items())),
                      kv("evidence", f"{ns[PRE]} admissible · {ns[LATE] + ns[POST] + ns[UNMATCHED]} truth-only"),
                      kv("diagnostic", sum(1 for e in ev if e.diagnostic), AMBER),
                      kv("queries", f"{sum(1 for q in nq if q.status in ('DONE', 'CACHED'))}/{len(nq)}"
                         + (" (no key)" if nq and all(q.status == "UNAVAILABLE" for q in nq) else "")),
                      kv("stable models", f"pre {inv.models_pre} · all {inv.models_all}"))
        self.query_one("#ov_metrics", Static).update(g)

    def render_case(self) -> None:
        inv = self.inv
        case = Table(box=None, expand=True, header_style=f"bold {GRAY}", padding=(0, 1))
        for c in ("sym", "R", "gap", "SAR", "Mz", "Mv", "Mg", "role"):
            case.add_column(c, justify="right" if c not in ("sym", "role") else "left")
        for i in inv.instruments:
            role = Text(f"C{i.cluster + 1} terminal" if i.cluster is not None else ("opening shock" if i.secondary else ""),
                        style=CYAN if i.cluster is not None else GRAY)
            case.add_row(Text(i.symbol, style=f"bold {RED}" if i.fired else GRAY), fmt_pct(i.R), fmt_pct(i.gap) if i.gap is not None else "",
                         Text(fmt_sig(i.SAR), style=RED if i.SAR is not None and abs(i.SAR) >= 4 else INK), fmt_sig(i.Mz), fmt_sig(i.Mv),
                         fmt_sig(i.Mg), role)
        head = Text()
        for k, c in enumerate(inv.clusters):
            head.append(f"C{k + 1}  ", style=f"bold {CYAN}")
            head.append(", ".join(c) + "\n", style=INK)
        head.append("gate: (|SAR| ≥ 4 or |Mz| ≥ 5) and (Mv ≥ 3.5 or |Mg| ≥ 5) · clusters by residual correlation ≥ 0.4\n", style=GRAY)
        self.query_one("#ov_case", Static).update(Group(head, case))

    def render_paths(self) -> None:
        box = self.query_one("#ov_paths", Static)
        if self._locked("ov_paths", "search"):
            return
        inv = self.inv
        cl = {f"T{k}": c for k, c in enumerate(inv.clusters)}
        out = Text()
        for e in sorted(inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
            tag = "BEST" if e.rank == 1 else ("WE DO NOT KNOW" if e.rank == 0 else f"RIVAL {e.rank}")
            col = GREEN if e.rank == 1 else (AMBER if e.rank == 0 else INK)
            out.append(f"{tag:<15}", style=f"bold {col}")
            out.append(f"{e.cost_mnats / 1000:6.2f} nats   odds vs best {odds_text(e.odds_vs_best):>8}", style=GRAY)
            narr = {x.dst for x in e.edges if not _is_term(x.dst)}
            out.append(f"   {len(e.edges)} edges · {len(narr)} narratives\n", style=GRAY)
            for path in _paths(e):
                out.append("   BOT", style=f"bold {AMBER}")
                for x in path:
                    out.append(f" ─{x.p:.2f}→ " if x.p else " ───→ ", style=GRAY)
                    if _is_term(x.dst):
                        out.append(f"{x.dst} [{' '.join(cl.get(x.dst, ()))}]", style=f"bold {RED}")
                    else:
                        out.append(short("N", x.dst) + " ", style=CYAN)
                        out.append(x.dst_label[:34], style=INK)
                cost = sum(x.cost_mnats for x in path)
                out.append(f"   ({cost / 1000:.2f})\n", style=GRAY)
            out.append("\n")
        out.append("p = edge probability (Hawkes attribution share or terminal link); cost = Σ(−log p + λ_node); shared trunks are paid once.\n"
                   "Edges mean timing, not cause. Rivals: the best tree through every other entry story within odds 1:20.", style=GRAY)
        box.update(out)

    def render_market(self) -> None:
        inv = self.inv
        etf = {"SMH", "XLK", "XLU", "SPY", "QQQ"}
        syms = []
        for k in range(len(inv.clusters)):
            m = [i for i in inv.instruments if i.cluster == k and i.symbol not in etf and i.SAR is not None]
            if m:
                syms.append(min(m, key=lambda i: i.SAR).symbol)
        syms += [i.symbol for i in inv.instruments if i.secondary][: max(0, 3 - len(syms))]
        data = self.world.daily(syms, (inv.tau_star - timedelta(days=30)).strftime("%Y-%m-%d"),
                                (inv.tau_star + timedelta(days=3)).strftime("%Y-%m-%d")) if self.world and inv.tau_star else {}
        for k in range(3):
            w = self.query_one(f"#mk{k}", PlotextPlot)
            p = w.plt
            p.clear_figure()
            if k >= len(syms) or not data.get(syms[k]):
                w.border_title = (f"{syms[k]} · not in the price table" if k < len(syms) else "")
                w.refresh()
                continue
            rows = data[syms[k]]
            if self.clock is not None:
                rows = [r for r in rows if datetime.fromisoformat(r[0]).replace(tzinfo=timezone.utc, hour=21) <= self.clock]
            if not rows:
                w.border_title = f"{syms[k]} · no completed daily bar before the replay clock"
                w.refresh()
                continue
            x = list(range(len(rows)))
            p.candlestick(x, {"Open": [r[1] for r in rows], "Close": [r[4] for r in rows], "High": [r[2] for r in rows], "Low": [r[3] for r in rows]})
            idx = next((i for i, r in enumerate(rows) if r[0] >= inv.tau_star.strftime("%Y-%m-%d")), None)
            if idx is not None:
                p.vline(idx, "orange")
            ticks = sorted({0, len(rows) // 2, len(rows) - 1} | ({idx} if idx is not None else set()))
            p.xticks(ticks, [rows[i][0][5:] for i in ticks])
            last = rows[-1][4] / rows[-2][4] - 1 if len(rows) > 1 else 0
            w.border_title = f"{syms[k]} daily · {rows[-1][4]:,.2f} ({fmt_pct(last)}) · orange = τ* day"
            w.refresh()

    def render_matrix(self) -> None:
        if self._locked("ov_matrix", "verdicts"):
            return
        inv = self.inv
        t = Table(box=None, expand=True, header_style=f"bold {GRAY}", padding=(0, 1))
        for c, kw in (("hyp", {"width": 14}), ("entry story", {"ratio": 3}), ("P_pre · could it have moved the price", {"width": 30}),
                      ("P_all · is it true", {"width": 25}), ("signature", {"width": 17}), ("PRE", {"width": 4, "justify": "right"}),
                      ("truth-only", {"width": 10, "justify": "right"}), ("◆", {"width": 3, "justify": "right"}), ("queries", {"width": 9})):
            t.add_column(c, **kw)
        qs: dict[str, list] = {}
        for q in inv.searches:
            qs.setdefault(q.hid, []).append(q)
        for h in inv.hypotheses:
            cell = lambda v, bits: Text.assemble((VERDICT_SHORT.get(v, v), f"bold {VERDICT_STYLE.get(v, GRAY)}"),
                                                 (f"  {''.join(map(str, bits))}" if bits else "", GRAY))
            sig = Text.assemble(("burst " + ("✓" if h.burst else "✗") + " ", GREEN if h.burst else GRAY),
                                ("surprise " + ("✓" if h.surprise_ok else "✗"), GREEN if h.surprise_ok else GRAY))
            n_pre = sum(1 for e in h.evidence if e.status == PRE)
            hq = qs.get(h.hid, [])
            t.add_row(Text(h.hid, style=CYAN), Text(h.label[:70], style=INK), cell(h.verdict_pre, h.bits_pre), cell(h.verdict_all, h.bits_all), sig,
                      str(n_pre), str(len(h.evidence) - n_pre), Text(str(sum(1 for e in h.evidence if e.diagnostic)), style=AMBER),
                      Text(f"{sum(1 for q in hq if q.status in ('DONE', 'CACHED'))}/{len(hq)}" if hq else "", style=GRAY))
        foot = Text("bits = bIN cIN bOUT cOUT (explained / refuted in some / every stable reading). ◆ = evidence whose removal flips the verdict.", style=GRAY)
        self.query_one("#ov_matrix", Static).update(Group(t, foot) if inv.hypotheses else Text("verdicts not run yet", style=GRAY))

    def render_progress(self) -> None:
        inv = self.inv
        prog = Text()
        for k, (ph, st) in enumerate(inv.phases):
            if self.clock is not None and not (k < self.revealed and self.clock >= (inv.detected or self.clock)):
                st = "PENDING"
            m, col = PHASE_MARK.get(st, ("?", GRAY))
            prog.append(f" {m} {ph}  ", style=col)
        self.query_one("#ov_prog", Static).update(prog)

    def _nids(self) -> list[tuple[str, str]]:
        seen, out = set(), []
        for e in sorted(self.inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
            for x in e.edges:
                for nid, lab in ((x.src, x.src_label), (x.dst, x.dst_label)):
                    if nid != "BOT" and not _is_term(nid) and nid not in seen:
                        seen.add(nid)
                        out.append((nid, lab))
        return out

    def render_story(self) -> None:
        inv = self.inv
        plot, ap, feed = self.query_one("#st_plot", PlotextPlot), self.query_one("#st_alpha", PlotextPlot), self.query_one("#st_feed", Static)
        nids = self._nids()
        if self.world is None or inv.tau_star is None or "e2b_series" not in self.world.have:
            feed.update(Text("no recorded attention tables", style=AMBER))
            return
        t0, _ = replay_clock_range(inv)
        upto = min(self.clock or inv.tau_star, inv.detected or inv.tau_star)
        att = self.world.attention([n for n, _ in nids], t0, upto + timedelta(minutes=15))
        if inv.source == "DEMO" and not any(att.values()):
            feed.update(Text("the DEMO fixture's narratives are not in the replay tables: open a recorded case to see its story", style=AMBER))
            return
        w0 = self.world.window(t0)
        p = plot.plt
        p.clear_figure()
        colors = ["green", "cyan", "yellow", "magenta", "blue", "red", "white", "orange"]
        nw = self.world.window(upto) - w0 + 1
        nh = max(1, nw // 4)
        for k, (nid, lab) in enumerate(nids[:8]):
            ys = {w: y for w, y, _, _ in att.get(nid, [])}
            hours = [sum(ys.get(w0 + 4 * h + j, 0.0) for j in range(4)) for h in range(nh)]
            p.plot(list(range(nh)), hours, label=f"{short('N', nid)} {lab[:28]}", color=colors[k % len(colors)])
            bursts = sorted({(w - w0) // 4 for w, _, _, b in att.get(nid, []) if b and (w - w0) // 4 < nh})
            if bursts:
                p.scatter(bursts, [hours[b] for b in bursts], marker="dot", color=colors[k % len(colors)])
        tau_h = int((inv.tau_star - t0).total_seconds() // 3600)
        if self.clock is None or self.clock >= inv.tau_star:
            p.vline(tau_h, "orange")
        days = list(range(0, nh, 24))
        p.xticks(days, [(t0 + timedelta(hours=d)).strftime("%m-%d") for d in days])
        p.ylabel("attention / hour")
        plot.refresh()
        pairs = [(x.src, x.dst) for e in inv.explanations for x in e.edges if x.src != "BOT" and not _is_term(x.dst)]
        sp = self.world.spill(pairs, t0, upto + timedelta(minutes=15))
        q = ap.plt
        q.clear_figure()
        for k, ((s, d), rows) in enumerate(sp.items()):
            hs: dict[int, list] = {}
            for w, a in rows:
                hs.setdefault((w - w0) // 4, []).append(a)
            xs = sorted(hs)
            if xs:
                q.plot(xs, [sum(hs[x]) / len(hs[x]) for x in xs], label=f"{short('N', s)} → {short('N', d)}", color=colors[k % len(colors)])
        if self.clock is None or self.clock >= inv.tau_star:
            q.vline(tau_h, "orange")
        q.xticks(days, [(t0 + timedelta(hours=d)).strftime("%m-%d") for d in days])
        q.ylabel("α")
        ap.refresh()
        items = self.world.feed(t0, upto, [n for n, _ in nids], limit=80)
        ft = Text()
        for f in items:
            late = f.t >= inv.tau_star
            ft.append(f"{fmt_t(f.t)} ", style=GRAY)
            ft.append("POST-τ* " if late else "PRE-τ*  ", style=AMBER if late else GREEN)
            ft.append(f"{short('N', f.narrative)} ", style=CYAN)
            ft.append(f"{f.source[:18]:<18} ", style=GRAY)
            ft.append(f"{f.title[:110]}\n", style=GRAY if late else INK)
        feed.update(ft or Text("no documents for these narratives before the clock", style=GRAY))

    def render_tree(self) -> None:
        if self._locked("tr_main", "search"):
            return
        parts = []
        for e in sorted(self.inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
            parts.append(explanation_tree(e, ("BEST" if e.rank == 1 else "WE DO NOT KNOW" if e.rank == 0 else f"RIVAL {e.rank}") +
                                          f" · {e.cost_mnats / 1000:.2f} nats · odds vs best {odds_text(e.odds_vs_best)}"))
            parts.append(Text(""))
        self.query_one("#tr_main", Static).update(Group(*parts))

    def render_evidence(self) -> None:
        if self._locked("ev_main", "claims"):
            return
        inv = self.inv
        box = self.query_one("#ev_main", Static)
        if not inv.hypotheses:
            box.update(Text("verdicts not run yet", style=GRAY))
            return
        h = inv.hypotheses[self.hyp_i]
        box.border_title = f"EVIDENCE · {h.hid} · {h.label[:60]}   (h: next hypothesis, {self.hyp_i + 1}/{len(inv.hypotheses)})"
        head = Text.assemble((f"P_pre {VERDICT_SHORT.get(h.verdict_pre, h.verdict_pre)}", f"bold {VERDICT_STYLE.get(h.verdict_pre, GRAY)}"), ("   ", ""),
                             (f"P_all {VERDICT_SHORT.get(h.verdict_all, h.verdict_all)}", f"bold {VERDICT_STYLE.get(h.verdict_all, GRAY)}"),
                             ("   ◆ diagnostic = removing it flips the verdict", AMBER))
        box.update(Group(head, evidence_wall(h, inv.tau_star)))

    def render_logic(self) -> None:
        if self._locked("lg_main", "verdicts"):
            return
        inv = self.inv
        expl = Text("\nbits = bIN cIN bOUT cOUT: explained in some / every reading, refuted in some / every reading.\n"
                    "SUPPORTED iff cIN · CONTRADICTED iff cOUT · UNRESOLVED iff bOUT and not cOUT · otherwise CONSISTENT-BUT-UNPROVEN.\n"
                    "A report is believed unless an independent contrary report of equal or better tier overrides it; copies add nothing.\n"
                    f"P_pre: {inv.models_pre} stable model(s) · P_all: {inv.models_all}. No stable model would be reported as INCOHERENT-EVIDENCE.", style=GRAY)
        self.query_one("#lg_main", Static).update(Group(bits_table(inv), expl))

    def render_placebos(self) -> None:
        if self._locked("pl_main", "placebos"):
            return
        inv, pl = self.inv, self.inv.placebo
        box, plot = self.query_one("#pl_main", Static), self.query_one("#pl_plot", PlotextPlot)
        if pl is None:
            box.update(Text("placebos were not run for this case", style=GRAY))
            return
        b = inv.best
        p = plot.plt
        p.clear_figure()
        if pl.costs:
            p.hist([c / 1000 for c in pl.costs], bins=20, color="gray", label="quiet-day best cost")
            if b:
                p.vline(b.cost_mnats / 1000, "orange")
            p.xlabel("best-explanation cost (nats); orange = this case")
        plot.refresh()
        t = Text()
        t.append(f"empirical p = (1 + #placebo explanations at least as cheap) / (1 + K) = {pl.p_emp:.3f}   K = {pl.k}\n", style=f"bold {INK}")
        t.append(f"false-explanation rate on quiet days = {pl.fer:.2f}  (target ≤ 0.05)\n\n", style=INK)
        t.append("hub frequency (share of placebo explanations that use the narrative):\n", style=GRAY)
        for n, f in pl.hubs[:10]:
            nid, _, lab = n.partition(" :: ")
            t.append(f"  {short('N', nid)} ", style=CYAN)
            t.append(f"{lab[:60]:<60} {100 * f:4.0f}%", style=AMBER if f >= 0.3 else INK)
            t.append("  low diagnosticity\n" if f >= 0.3 else "\n", style=AMBER)
        box.update(t)

    def render_trace(self) -> None:
        if self._locked("sx_main", "queries"):
            return
        inv = self.inv
        t = Text()
        t.append("EXPLANATION SEARCH → TARGETED SEARCH → SerpApi → EVIDENCE ARCHIVE → VERIFICATION\n", style=CYAN)
        t.append("one-way valve: pages fetched here never enter Engine 2 counts or fits\n\n", style=AMBER)
        if not inv.searches:
            t.append("no search operations recorded for this case\n", style=GRAY)
        for q in inv.searches:
            t.append(f"{short('Q', q.qid)}  target {q.hid}  provider {q.provider}  ", style=INK)
            t.append(q.status + "\n", style=RED if q.status in ("UNAVAILABLE", "ERROR") else GREEN)
            t.append(f"  query  {q.query}\n", style=GRAY)
            if q.status in ("DONE", "CACHED"):
                t.append(f"  {q.results} results → {q.matched} canonical-URL matches (first_seen inherited) → {q.unmatched} unmatched (truth only)\n", style=GRAY)
            if q.note:
                t.append(f"  {q.note}\n", style=GRAY)
        self.query_one("#sx_main", Static).update(t)

    def render_audit(self) -> None:
        inv = self.inv
        t = Text()
        rows = [("source", inv.source), ("cfg_hash", inv.cfg_hash or "not recorded"), ("snapshot window", inv.snapshot or "not recorded"),
                ("τ* rule", "earliest first abnormal print across the clusters; venue session start in replay; earlier when unsure"),
                ("detection", "daily close (the replay trigger runs on daily bars)"),
                ("admissibility", "first_seen < τ* for P_pre; everything up to report time for P_all"),
                ("determinism", "D1 no wall clock · D2 keyed Philox · D3 fixed reductions, pinned threads · D4 tie keys · D5 archived calls · D6 cfg stamps"),
                ("not proven here", "claim extraction, copy detection, source tiers, the attention model; Lean certification not run")]
        for k, v in rows:
            t.append(f"{k:<18}", style=GRAY)
            t.append(f"{v}\n", style=INK)
        for n in inv.notes:
            t.append(f"\n{n}", style=AMBER)
        self.query_one("#au_main", Static).update(t)


# ====================================================================================================== app
class YggApp(App):
    CSS = CSS
    TITLE = "Yggdrasil"

    def __init__(self, data_dir: Path, cfg: dict, demo: bool = False):
        super().__init__()
        import os
        from collections import deque

        from ygg.config import cfg_hash
        from ygg.ui.graph_server import GraphServer

        self.data_dir, self.cfg, self.demo = Path(data_dir), cfg, demo
        self.cfg_hash = cfg_hash(cfg)
        self.world = L.LiveWorld()
        self.quotes: dict = {}
        self.events: deque = deque(maxlen=300)
        self.seen_batches: set = set()
        self.serpapi = bool(os.environ.get("SERPAPI_API_KEY"))
        self._recorded = None
        self.graph = GraphServer(self.on_graph_select, port=int(os.environ.get("YGG_GRAPH_PORT", "8765")))

    def on_graph_select(self, nid: str) -> None:
        self.tape(f"GRAPH      selected {nid if nid == 'BOT' or _is_term(nid) else short('N', nid)} in the graph window")
        if isinstance(self.screen, InvestigationScreen):
            self.screen.graph_selected(nid)

    def tape(self, msg: str) -> None:
        self.events.append((datetime.now(timezone.utc), msg))

    def recorded_world(self) -> World | None:
        if self._recorded is None:
            from ygg.determinism import WindowClock, parse_utc

            r = self.cfg["replay"]
            try:
                self._recorded = World(self.data_dir, WindowClock(parse_utc(r["start"]), r["window_seconds"], r["ingest_lag_seconds"]))
            except Exception as e:
                self.tape(f"RECORDED   tables unavailable: {e}")
                return None
        return self._recorded

    def replay_progress(self) -> str:
        p = self.data_dir / "replay_full.out"
        if not p.exists():
            return ""
        try:
            lines = [ln for ln in p.read_text().splitlines() if ln.startswith("replay ")]
        except OSError:
            return ""
        if not lines:
            return ""
        last = lines[-1]
        if last.startswith("replay done"):
            return "replay engine: finished"
        day = last.split()[1].rstrip(":")
        age = time.time() - p.stat().st_mtime
        return f"replay engine: through {day}" + (" (running)" if age < 1500 else " (stalled?)")

    async def on_mount(self) -> None:
        self.tape("START      control panel · world feed = latest served GDELT batch")
        try:
            await self.graph.start()
            self.tape(f"GRAPH      window at {self.graph.url}")
            import os
            import sys
            import threading
            import webbrowser

            gui = sys.platform in ("win32", "darwin") or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
            if gui and not os.environ.get("YGG_NO_BROWSER"):
                threading.Thread(target=lambda: webbrowser.open(self.graph.url, new=1), daemon=True).start()
        except OSError as e:
            self.tape(f"GRAPH      could not bind {self.graph.url}: {e}")
        self.push_screen(ControlPanel())


def run(data_dir: Path, cfg: dict, demo: bool = False) -> None:
    YggApp(data_dir, cfg, demo).run()
