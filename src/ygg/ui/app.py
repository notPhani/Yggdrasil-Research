"""Yggdrasil terminal: a live control panel and a full-page investigation workspace.

  ygg ui            live control panel: one central price chart, watchlist, quote, recorded world model, news, cases
  ygg ui --demo     adds the DEMO investigation fixture (labelled MODE: DEMO everywhere it appears)

The UI is a projection of recorded state: it never recomputes a result, never moves tau*, and never shows a record
whose first_seen is after the clock it is drawing (live: the latest served batch; replay: the replay clock).
"""
from __future__ import annotations

import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rich.console import Group
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import ContentSwitcher, DataTable, Input, Static

from ygg.ui import live as L
from ygg.ui.charts import ChartSpec, HeroChart, Series, pct_overlay
from ygg.ui.domain import LATE, POST, PRE, UNMATCHED, CaseRow, Investigation, short
from ygg.ui.recorded import World, list_cases, load_investigation, replay_clock_range
from ygg.ui.render import evidence_wall, explanation_tree, sparkline
from ygg.ui.theme import (AMBER, AMBER_HI, BAR, CSS as THEME_CSS, DIM, DOWN, FAINT, ID, RGB, UP, WARN, WHITE, bar, kv, signed)

VERDICT_STYLE = {"SUPPORTED": UP, "CONTRADICTED": DOWN, "UNRESOLVED": WARN, "CONSISTENT-BUT-UNPROVEN": DIM}
VERDICT_SHORT = {"SUPPORTED": "SUPPORTED", "CONTRADICTED": "CONTRADICTED", "UNRESOLVED": "UNRESOLVED",
                 "CONSISTENT-BUT-UNPROVEN": "CONS-UNPROVEN"}

CSS = THEME_CSS + """
#top { height: 1; background: #000000; }
#brand { width: 12; color: #fa7900; text-style: bold; }
#cmd { width: 46; }
#status { width: 1fr; }
#main { height: 1fr; }
#p1 { width: 44; }
#p2 { width: 1fr; }
#p3 { width: 36; }
#mid { height: 15; }
#p4 { width: 1fr; }
#p5 { width: 1fr; }
#p6 { height: 7; }
#watch { height: 1fr; }
#chart { height: 1fr; }
#quote, #world, #feed { height: 1fr; }
#cases { height: 1fr; }
#keys, #ikeys { height: 1; background: #141414; }
#ihdr { height: 1; background: #000000; }
#views { height: 1fr; }
#v_over { height: 1fr; }
#verdict { height: auto; max-height: 5; }
#omid { height: 1fr; }
#obot { height: 14; }
#hyps { height: 1fr; }
#ev { height: 1fr; }
#ichart { height: 1fr; }
#paths { height: 1fr; }
#p3sw { height: 1fr; }
#p3list { height: 1fr; }
#expl { height: auto; max-height: 12; }
#p3brief { height: 1fr; }
.half { width: 1fr; }
#att { height: 18; }
#spill { height: 10; }
#plach { height: 16; }
.pdim { opacity: 22%; text-opacity: 35%; }
DataTable.pdim > .datatable--header, DataTable.pdim > .datatable--cursor { text-opacity: 35%; }
#caption { dock: bottom; height: 4; padding: 0 4; background: #000000; color: #ffffff; text-style: bold;
           content-align: center middle; border-top: heavy #fa7900; }
"""


class Bar(Static):
    """A numbered amber title bar that fills its width."""

    def __init__(self, n: int, title: str, right: str = "", **kw):
        super().__init__(classes="bar", **kw)
        self.n, self.title_, self.right = n, title, right

    def set(self, title: str | None = None, right: str | None = None) -> None:
        self.title_ = title if title is not None else self.title_
        self.right = right if right is not None else self.right
        self._draw()

    def on_resize(self) -> None:
        self._draw()

    def _draw(self) -> None:
        self.update(bar(self.n, self.title_, self.right, self.size.width or 120))


TERMS: set[str] = set()                 # terminal ids of the open investigation (recorded names like "EIX+PCG")


def _is_term(nid: str) -> bool:
    return nid in TERMS or (nid.startswith("T") and nid[1:].isdigit())


def _sid(nid: str) -> str:
    return nid if nid == "BOT" or _is_term(nid) else short("N", nid)


def _paths(e) -> list[list]:
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


def _odds(x: float) -> str:
    return "1 : 1" if abs(x - 1) < 1e-9 else (f"1 : {x:.1f}" if x >= 1 else f"{1 / x:.1f} : 1")


# ====================================================================================================== control panel
class ControlPanel(Screen):
    BINDINGS = [Binding("f1", "help", show=False), Binding("f2", "focus_watch", show=False), Binding("f3", "focus_cases", show=False),
                Binding("f4", "toggle_feed", show=False), Binding("f5", "refresh_all", show=False), Binding("slash", "focus_cmd", show=False),
                Binding("l", "mode('line')", show=False), Binding("c", "mode('candles')", show=False),
                Binding("d", "range", show=False), Binding("enter", "open_case", show=False), Binding("q", "app.quit", show=False)]

    def compose(self) -> ComposeResult:
        with Horizontal(id="top"):
            yield Static(" YGGDRASIL", id="brand")
            yield Input(placeholder="NVDA GP · CASE 2025-01-27 · 5D · C · HELP", id="cmd")
            yield Static(id="status")
        with Horizontal(id="main"):
            with Vertical(id="p1"):
                yield Bar(1, "Watchlist", "1-min bars")
                yield DataTable(id="watch", cursor_type="row", show_cursor=True)
            with Vertical(id="p2"):
                yield Bar(2, "Chart")
                yield HeroChart(id="chart", classes="panel")
            with Vertical(id="p3"):
                yield Bar(3, "Quote")
                yield Static(id="quote", classes="panel")
        with Horizontal(id="mid"):
            with Vertical(id="p4"):
                yield Bar(4, "World model", "recorded replay state")
                yield Static(id="world", classes="panel")
            with Vertical(id="p5"):
                yield Bar(5, "News", "GDELT")
                yield Static(id="feed", classes="panel")
        with Vertical(id="p6"):
            yield Bar(6, "Investigations", "enter opens")
            yield DataTable(id="cases", cursor_type="row")
        yield Static(id="keys")

    def on_mount(self) -> None:
        self.feed_offset, self.show_tape, self.mode, self.days = 0, False, "line", 1
        self.next_poll = time.time() + 60
        w = self.query_one("#watch", DataTable)
        for col, wd in (("SYM", 8), ("LAST", 11), ("CHG", 9), ("2H", 12)):
            w.add_column(col, key=col, width=wd)
        for s in L.WATCH:
            w.add_row(Text(s, style=AMBER_HI if s in L.DEMO_EXTRA else WHITE), Text("…", style=DIM), "", "", key=s)
        c = self.query_one("#cases", DataTable)
        for col, wd in (("", 2), ("CASE", 11), ("STATE", 9), ("CLUSTERS", 22), ("BEST EXPLANATION", 54), ("ODDS VS WE-DON'T-KNOW", 22),
                        ("PLACEBO P", 10), ("SOURCE", 9)):
            c.add_column(col, key=col or "mark", width=wd)
        self.load_cases()
        self.render_world()
        self.render_keys()
        self.set_interval(1.0, self.render_status)
        self.set_interval(2.0, self.scroll_feed)
        self.set_interval(10.0, self.render_keys)
        self.set_interval(30.0, self.refresh_quotes)
        self.set_interval(60.0, self.poll_news)
        self.set_interval(120.0, self.render_world)
        self.refresh_quotes()
        self.poll_news()
        w.focus()

    # ---------------------------------------------------------------- data
    def refresh_quotes(self) -> None:
        self.run_worker(self._quotes, thread=True, exclusive=True, group="quotes")

    def _quotes(self) -> None:
        rng = "1d" if self.days == 1 else "5d"
        iv = "1m" if self.days == 1 else "5m"
        out = {s: L.quote(s, rng=rng, iv=iv) for s in L.WATCH}
        self.app.call_from_thread(self._apply_quotes, out)

    def _apply_quotes(self, qs: dict) -> None:
        app: YggApp = self.app
        app.quotes.update(qs)
        w = self.query_one("#watch", DataTable)
        for s, q in qs.items():
            if q.state == "UNAVAILABLE":
                w.update_cell(s, "LAST", Text("unavail.", style=DOWN))
                continue
            closes = [c.c for c in q.candles[-120:]]
            lo, hi = (min(closes), max(closes)) if closes else (0, 1)
            up = bool(closes) and closes[-1] >= closes[0]
            w.update_cell(s, "LAST", Text(f"{q.last:,.2f}", style=WHITE, justify="right"))
            w.update_cell(s, "CHG", signed(q.change))
            w.update_cell(s, "2H", Text(sparkline([c - lo for c in closes], 12, (hi - lo) or 1.0), style=UP if up else DOWN))
        app.tape(f"QUOTES     {sum(q.state != 'UNAVAILABLE' for q in qs.values())}/{len(qs)} symbols")
        self.render_chart()

    def poll_news(self) -> None:
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
        self.render_feed()
        self.render_keys()

    def load_cases(self) -> None:
        app: YggApp = self.app
        c = self.query_one("#cases", DataTable)
        c.clear()
        c.add_row(Text("●", style=UP), Text("LIVE", style=UP), Text("WAITING", style=DIM),
                  Text("—", style=DIM), Text("no live anomaly · equities closed · intraday trigger outside the cut", style=DIM), "", "",
                  Text("LIVE", style=UP), key="__live__")
        rows: list[CaseRow] = list_cases(app.data_dir)
        if app.demo:
            from ygg.ui.demo import demo_investigation

            inv = demo_investigation()
            b = inv.best
            rows.append(CaseRow(inv.case_id, "ARCHIVED", "VERDICT", "C1 chips · C2 power", 7.8, b.entry_label if b else "",
                                inv.abstention.odds_vs_best if inv.abstention else None, inv.placebo.p_emp if inv.placebo else None, "DEMO"))
        for r in rows:
            c.add_row(Text("◉", style=ID), Text(r.case_id, style=f"bold {ID}"), Text(r.phase, style=WHITE), Text(r.terminals, style=WHITE),
                      Text(r.best[:54], style=WHITE), Text(_odds(r.odds) if r.odds else "", style=WHITE),
                      Text(f"{r.p_emp:.3f}" if r.p_emp is not None else "", style=WHITE),
                      Text(r.source, style=AMBER_HI if r.source == "DEMO" else UP), key=f"{r.source}:{r.case_id}")

    # ---------------------------------------------------------------- render
    def render_status(self) -> None:
        app: YggApp = self.app
        now = datetime.now(timezone.utc)
        t = Text(no_wrap=True, overflow="crop")
        t.append(" ● LIVE ", style=f"bold {UP}")
        wt = app.world.last_ok
        t.append(f" WORLD {wt:%H:%M} UTC" if wt else " WORLD waiting", style=WHITE)
        if wt:
            t.append(f" (lag {int((now - wt).total_seconds() // 60)}m)", style=DIM)
        wk = now.weekday() >= 5
        for name, open_ in (("US", not wk), ("EU", not wk), ("CRYPTO", True)):
            t.append(f"   {name} ", style=AMBER)
            t.append("OPEN" if open_ else "CLOSED", style=UP if open_ else DIM)
        t.append(f"   {now:%H:%M:%S} UTC", style=WHITE)
        if app.demo:
            t.append("   MODE: DEMO", style=f"bold {AMBER_HI}")
        self.query_one("#status", Static).update(t)

    def _selected(self) -> str:
        w = self.query_one("#watch", DataTable)
        return L.WATCH[min(max(w.cursor_row, 0), len(L.WATCH) - 1)]

    def render_chart(self) -> None:
        app: YggApp = self.app
        sym = self._selected()
        q = app.quotes.get(sym)
        bar2 = self.query_one("#p2 Bar", Bar)
        chart = self.query_one("#chart", HeroChart)
        if q is None:
            return
        if q.state == "UNAVAILABLE" or not q.candles:
            chart.show(ChartSpec(empty=f"{sym}: price source unavailable ({q.error})"))
            self.render_quote(sym, q, {})
            return
        n = min(len(q.candles), 390 if self.days == 1 else 1000)
        cs = q.candles[-n:]
        xs = list(range(len(cs)))
        pr = L.params(q)
        k = len(cs)
        ticks = sorted({0, k // 4, k // 2, 3 * k // 4, k - 1})
        fmt = "%H:%M" if self.days == 1 else "%a %H:%M"
        spec = ChartSpec([Series(sym, xs, [c.c for c in cs], RGB["AMBER"])], [(c.o, c.h, c.l, c.c) for c in cs], self.mode,
                         hlines=[(q.prev_close, RGB["FAINT"], "prev close")] if q.prev_close else [],
                         xticks=(ticks, [cs[i].t.strftime(fmt) for i in ticks]), volume=[c.v for c in cs])
        if pr.get("vwap") and self.days == 1:
            spec.hlines.append((pr["vwap"], RGB["ID"], "VWAP"))
        chart.show(spec)
        tag = "24/7 demo extra" if sym in L.DEMO_EXTRA else q.state
        bar2.set(f"{sym} · {'1D · 1-min' if self.days == 1 else '5D · 5-min'} · {self.mode}",
                 f"{tag} · amber = price · grey = prev close" + (" · blue = VWAP" if pr.get("vwap") and self.days == 1 else "") + " · L/C/D")
        self.render_quote(sym, q, pr)

    def render_quote(self, sym: str, q, pr: dict) -> None:
        t = Table.grid(padding=(0, 1), expand=True)
        t.add_column(style=AMBER, no_wrap=True)
        t.add_column(justify="right", no_wrap=True)
        t.add_row("SYMBOL", Text(sym, style=f"bold {WHITE}"))
        t.add_row("LAST", Text(f"{q.last:,.2f}" if q.last else "n/a", style=f"bold {WHITE}"))
        t.add_row("CHANGE", signed(q.change))
        t.add_row("PREV CLOSE", Text(f"{q.prev_close:,.2f}" if q.prev_close else "n/a", style=WHITE))
        t.add_row("STATE", Text(q.state, style=UP if q.state == "OPEN" else DIM))
        if pr:
            t.add_row("", "")
            t.add_row("OPEN", Text(f"{pr['open']:,.2f}", style=WHITE))
            t.add_row("HIGH", Text(f"{pr['high']:,.2f}", style=WHITE))
            t.add_row("LOW", Text(f"{pr['low']:,.2f}", style=WHITE))
            t.add_row("RANGE", Text(f"{100 * (pr['high'] / pr['low'] - 1):.2f}%", style=WHITE))
            t.add_row("VWAP", Text(f"{pr['vwap']:,.2f}" if pr.get("vwap") else "no volume", style=WHITE if pr.get("vwap") else DIM))
            t.add_row("VOLUME", Text(f"{pr['volume']:,.0f}", style=WHITE))
            t.add_row("BARS", Text(f"{pr['bars']}", style=WHITE))
            t.add_row("RV (ANN.)", Text(f"{100 * pr['rv_ann']:.1f}%" if pr.get("rv_ann") else "n/a", style=WHITE))
            zr = pr.get("z_ret")
            t.add_row("1M RET Z", Text(f"{zr:+.2f}" if zr is not None else "n/a", style=DOWN if zr is not None and abs(zr) >= 4 else WHITE))
            t.add_row("LAST BAR", Text(f"{pr['last']:%a %H:%M}", style=WHITE))
        note = Text("\nrobust z vs the bars shown · descriptive,\nnot the case trigger (daily SAR gate)", style=DIM)
        self.query_one("#quote", Static).update(Group(t, note))

    def on_data_table_row_highlighted(self, ev: DataTable.RowHighlighted) -> None:
        if ev.data_table.id == "watch":
            self.render_chart()

    def on_data_table_row_selected(self, ev: DataTable.RowSelected) -> None:
        if ev.data_table.id == "cases":
            self.action_open_case()

    def scroll_feed(self) -> None:
        self.feed_offset += 1
        self.render_feed()

    def render_feed(self) -> None:
        app: YggApp = self.app
        box = self.query_one("#feed", Static)
        b5 = self.query_one("#p5 Bar", Bar)
        h = max(3, box.size.height)
        width = max(30, box.size.width - 2)
        if self.show_tape:
            b5.set("Event tape", "F4 news")
            t = Text(no_wrap=True, overflow="crop")
            for ts, msg in list(app.events)[-h:][::-1]:
                t.append(f"{ts:%H:%M:%S}  ", style=DIM)
                t.append(msg[: width - 10] + "\n", style=WHITE)
            box.update(t)
            return
        feed = app.world.feed
        ok = [b for b in app.world.batches if b.status == "OK"]
        if not feed:
            b5.set("News", "GDELT · waiting")
            box.update(Text(app.world.error or "waiting for the first served GDELT batch…", style=DIM))
            return
        latest = ok[-1]
        n = len(feed)
        i0 = self.feed_offset % n
        b5.set("News", f"GDELT batch {latest.ts:%H:%M} UTC · {latest.docs} docs · {i0 + 1}/{n} · next check {max(0, int(self.next_poll - time.time()))}s · F4 tape")
        t = Text(no_wrap=True, overflow="crop")
        for k in range(min(h, n)):
            f = feed[(i0 + k) % n]
            t.append(f"{f.t:%H:%M} ", style=DIM)
            t.append(f"{f.source[:20]:<20} ", style=AMBER)
            t.append(f"{f.title[: width - 28]}\n", style=WHITE)
        box.update(t)

    def render_world(self) -> None:
        app: YggApp = self.app
        box = self.query_one("#world", Static)
        try:
            from ygg.ui.stats import world_stats

            s = world_stats(app.data_dir, top_n=8)
        except Exception as e:
            box.update(Text(f"world model unavailable: {e}", style=DOWN))
            return
        if s is None:
            box.update(Text("no recorded world model yet (ygg replay)", style=DIM))
            return
        self.query_one("#p4 Bar", Bar).set(right=f"recorded through {s.day} · {s.days_done} replay days · live model cold")
        g = Text(no_wrap=True, overflow="crop")
        for k_, v_, st in (("ALIVE", f"{s.alive}/300", AMBER_HI if s.alive >= 300 else WHITE), ("DORMANT", str(s.dormant), WHITE),
                           ("BORN 24H", str(s.born_day), WHITE), ("BURSTS", f"{s.bursts_day}", WHITE), ("EDGES", f"{s.edges_day:,}", WHITE),
                           ("BOT", f"{100 * s.bot_share:.0f}%" if s.bot_share is not None else "n/a", WHITE),
                           ("STORIES/D", f"{s.roots_day:,}", WHITE), ("κ", f"{s.kappa_s:.0f}", WHITE)):
            g.append(f"{k_} ", style=AMBER)
            g.append(f"{v_}   ", style=st)
        t = Table(box=None, expand=True, padding=(0, 1), show_edge=False)
        t.add_column("NARRATIVE", style=WHITE, ratio=1, no_wrap=True, header_style=f"bold {AMBER}")
        t.add_column("48H", width=24, header_style=f"bold {AMBER}")
        t.add_column("MASS", justify="right", width=7, header_style=f"bold {AMBER}")
        t.add_column("B", justify="right", width=3, header_style=f"bold {AMBER}")
        vmax = max((max(n.series) for n in s.top if n.series), default=1.0) or 1.0
        for n in s.top:
            lab = Text(no_wrap=True, overflow="ellipsis")
            lab.append(f"{short('N', n.nid)} ", style=ID)
            lab.append(n.label, style=WHITE)
            t.add_row(lab, Text(sparkline(n.series, 24, vmax), style=AMBER), f"{n.mass_day:,.0f}", Text(str(n.bursts), style=AMBER_HI if n.bursts else DIM))
        box.update(Group(g, t))

    def render_keys(self) -> None:
        app: YggApp = self.app
        ok = [b for b in app.world.batches if b.status == "OK"]
        rp = app.replay_progress()
        t = Text(no_wrap=True, overflow="crop", style=f"on {BAR}")
        for k_, v_ in (("F1", "HELP"), ("F2", "WATCH"), ("F3", "CASES"), ("F4", "NEWS/TAPE"), ("F5", "REFRESH"), ("/", "COMMAND")):
            t.append(f" {k_} ", style=f"bold #000000 on {AMBER}")
            t.append(f" {v_} ", style=f"{WHITE} on {BAR}")
        t.append("  │ ", style=f"{FAINT} on {BAR}")
        for name, mark, col, detail in (("E1", "●" if ok else "○", UP if ok else DIM, f"{ok[-1].ts:%H:%M}" if ok else "wait"),
                                        ("E2a", "○", WARN, "cold"), ("E2", "◉" if rp and "running" in rp else "○", ID if rp else DIM,
                                                                       rp.replace("replay engine: ", "") if rp else "idle"),
                                        ("OBS", "○", DIM, "closed"), ("E3a", "○", DIM, "idle"),
                                        ("E3b", "✗" if not app.serpapi else "○", DOWN if not app.serpapi else DIM, "no key" if not app.serpapi else "idle")):
            t.append(f" {name} ", style=f"{AMBER} on {BAR}")
            t.append(f"{mark} {detail} ", style=f"{col} on {BAR}")
        self.query_one("#keys", Static).update(t)

    # ---------------------------------------------------------------- actions
    def action_help(self) -> None:
        self.app.notify("Watchlist ↑↓ selects · L line · C candles · D 1D/5D · / command: 'NVDA GP', 'CASE 2025-01-27', '5D', 'C' · "
                        "F3 then Enter opens a case · F4 news/tape · q quit", timeout=8)

    def action_focus_watch(self) -> None:
        self.query_one("#watch").focus()

    def action_focus_cases(self) -> None:
        self.query_one("#cases").focus()

    def action_focus_cmd(self) -> None:
        self.query_one("#cmd").focus()

    def action_toggle_feed(self) -> None:
        self.show_tape = not self.show_tape
        self.render_feed()

    def action_refresh_all(self) -> None:
        self.refresh_quotes()
        self.poll_news()
        self.render_world()

    def action_mode(self, m: str) -> None:
        self.mode = m
        self.render_chart()

    def action_range(self) -> None:
        self.days = 5 if self.days == 1 else 1
        self.refresh_quotes()

    def on_input_submitted(self, ev: Input.Submitted) -> None:
        cmd = ev.value.strip().upper()
        ev.input.value = ""
        parts = cmd.split()
        if not parts:
            return
        app: YggApp = self.app
        app.tape(f"COMMAND    {cmd}")
        if parts[0] == "CASE" and len(parts) > 1:
            self.open_case(f"RECORDED:{parts[1]}" if (app.data_dir / "cases" / f"{parts[1]}.json").exists() else f"DEMO:{parts[1]}")
        elif parts[0] in ("5D", "1D"):
            self.days = 5 if parts[0] == "5D" else 1
            self.refresh_quotes()
        elif parts[0] in ("C", "L"):
            self.action_mode("candles" if parts[0] == "C" else "line")
        elif parts[0] == "HELP":
            self.action_help()
        elif parts[0] in L.WATCH:
            w = self.query_one("#watch", DataTable)
            w.move_cursor(row=L.WATCH.index(parts[0]))
            w.focus()
        else:
            self.app.notify(f"unknown command '{cmd}'", severity="warning", timeout=3)

    def action_open_case(self) -> None:
        c = self.query_one("#cases", DataTable)
        if c.row_count == 0:
            return
        key = c.coordinate_to_cell_key((c.cursor_row, 0)).row_key.value
        if key and key != "__live__":
            self.open_case(key)

    def open_case(self, key: str) -> None:
        import json

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
VIEWS = [("f1", "v_over", "OVERVIEW"), ("f2", "v_story", "STORY"), ("f3", "v_ev", "EVIDENCE"), ("f4", "v_logic", "LOGIC"),
         ("f5", "v_plac", "PLACEBO"), ("f6", "v_trace", "TRACE"), ("f7", "v_audit", "AUDIT")]


class InvestigationScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", show=False), Binding("r", "toggle_replay", show=False),
                Binding("plus,equals", "faster", show=False), Binding("minus", "slower", show=False),
                Binding("g", "graph_focus", show=False), Binding("b", "brief_back", show=False), Binding("q", "app.quit", show=False)] + \
               [Binding(k, f"view('{v}')", show=False) for k, v, _ in VIEWS]

    def __init__(self, inv: Investigation, raw: dict | None = None):
        super().__init__()
        self.inv, self.raw = inv, raw
        TERMS.clear()
        TERMS.update(inv.terminals)
        self.clock: datetime | None = None
        self.speed, self.revealed, self.hyp_i, self.focus_i = 8, len(STEPS), 0, -1
        self._timer, self._step_wait, self.view = None, 0, "v_over"

    def compose(self) -> ComposeResult:
        yield Static(id="ihdr")
        with ContentSwitcher(initial="v_over", id="views"):
            with Vertical(id="v_over"):
                yield Bar(1, "Verdict")
                yield Static(id="verdict", classes="panel")
                with Horizontal(id="omid"):
                    with Vertical(classes="half"):
                        yield Bar(2, "Price", "cluster leads · % from the close before τ* · orange line = τ* day")
                        yield HeroChart(id="ichart", classes="panel")
                    with Vertical(classes="half", id="p3col"):
                        yield Bar(3, "Explanations", "click or Enter: brief · B: back to the list")
                        with ContentSwitcher(initial="p3list", id="p3sw"):
                            with Vertical(id="p3list"):
                                yield DataTable(id="expl", cursor_type="row")
                                yield Static(id="paths", classes="panel")
                            with VerticalScroll(id="p3brief"):
                                yield Static(id="brief", classes="panel")
                with Horizontal(id="obot"):
                    with Vertical(classes="half"):
                        yield Bar(4, "Hypotheses", "↑↓ selects · evidence shows right")
                        yield DataTable(id="hyps", cursor_type="row")
                    with Vertical(classes="half"):
                        yield Bar(5, "Evidence")
                        with VerticalScroll(id="ev"):
                            yield Static(id="evbody", classes="panel")
            with VerticalScroll(id="v_story"):
                yield Bar(1, "Attention", "narratives in the explanations · per hour · orange = τ*")
                yield HeroChart(id="att", classes="panel")
                yield Bar(2, "Spillover", "edge shares α along the explanation paths")
                yield HeroChart(id="spill", classes="panel")
                yield Bar(3, "Documents", "those narratives · first_seen ≤ clock")
                yield Static(id="docs", classes="panel")
            with VerticalScroll(id="v_ev"):
                yield Bar(1, "Evidence · every hypothesis", "τ* wall · ◆ = removing it flips the verdict")
                yield Static(id="evall", classes="panel")
            with VerticalScroll(id="v_logic"):
                yield Bar(1, "Logic", "every consistent reading of the evidence (clingo)")
                yield Static(id="logic", classes="panel")
            with VerticalScroll(id="v_plac"):
                yield Bar(1, "Placebo", "best-explanation cost on quiet days · orange = this case")
                yield HeroChart(id="plach", classes="panel")
                yield Static(id="plac", classes="panel")
            with VerticalScroll(id="v_trace"):
                yield Bar(1, "Evidence acquisition", "explanation search → targeted search → SerpApi → archive → verification")
                yield Static(id="trace", classes="panel")
            with VerticalScroll(id="v_audit"):
                yield Bar(1, "Audit")
                yield Static(id="audit", classes="panel")
                yield Bar(2, "Trees")
                yield Static(id="trees", classes="panel")
        yield Static(id="ikeys")

    def on_mount(self) -> None:
        app: YggApp = self.app
        self.world = app.recorded_world()
        h = self.query_one("#hyps", DataTable)
        for col, wd in (("HYP", 15), ("ENTRY STORY", 34), ("P_PRE", 14), ("P_ALL", 13), ("SIG", 5), ("PRE", 4), ("LATE", 5), ("◆", 2)):
            h.add_column(col, key=col, width=wd)
        for k, hy in enumerate(self.inv.hypotheses):
            sig = ("B" if hy.burst else "·") + ("S" if hy.surprise_ok else "·")
            n_pre = sum(1 for e in hy.evidence if e.status == PRE)
            h.add_row(Text(hy.hid, style=ID), Text(hy.label, style=WHITE, no_wrap=True, overflow="ellipsis"),
                      Text(VERDICT_SHORT.get(hy.verdict_pre, hy.verdict_pre), style=f"bold {VERDICT_STYLE.get(hy.verdict_pre, DIM)}"),
                      Text(VERDICT_SHORT.get(hy.verdict_all, hy.verdict_all), style=f"bold {VERDICT_STYLE.get(hy.verdict_all, DIM)}"),
                      Text(sig, style=UP if hy.signature_ok else DIM), str(n_pre), str(len(hy.evidence) - n_pre),
                      Text(str(sum(1 for e in hy.evidence if e.diagnostic)), style=AMBER_HI), key=str(k))
        x = self.query_one("#expl", DataTable)
        for col, wd in (("#", 2), ("", 14), ("NATS", 6), ("ODDS", 8), ("ENTRY STORY", 60)):
            x.add_column(col, key=col or "tag", width=wd)
        for k, e in enumerate(sorted(self.inv.explanations, key=lambda e: (e.rank == 0, e.rank))):
            tag = "BEST" if e.rank == 1 else ("WE DON'T KNOW" if e.rank == 0 else f"RIVAL {e.rank}")
            x.add_row(str(e.rank), Text(tag, style=f"bold {UP if e.rank == 1 else (AMBER_HI if e.rank == 0 else WHITE)}"),
                      f"{e.cost_mnats / 1000:.2f}", _odds(e.odds_vs_best), Text(e.entry_label if e.entry != "BOT" else "no narrative chain", style=WHITE,
                                                                               no_wrap=True, overflow="ellipsis"), key=str(k))
        self.expl_order = sorted(self.inv.explanations, key=lambda e: (e.rank == 0, e.rank))
        self.render_all()
        self.set_interval(1.0, self.render_header)
        from ygg.ui.graph_server import payload_for

        app.graph.show(payload_for(self.inv, self.raw))
        app.tape(f"GRAPH      showing case {self.inv.case_id} at {app.graph.url}")
        h.focus()

    # ---------------------------------------------------------------- navigation
    def action_view(self, v: str) -> None:
        self.view = v
        self.query_one("#views", ContentSwitcher).current = v
        self.render_keys()

    def on_data_table_row_highlighted(self, ev: DataTable.RowHighlighted) -> None:
        if ev.data_table.id == "hyps" and ev.row_key is not None:
            self.hyp_i = int(ev.row_key.value)
            self.render_evidence()

    def on_data_table_row_selected(self, ev: DataTable.RowSelected) -> None:
        if ev.data_table.id == "expl" and ev.row_key is not None:
            self.show_brief(self.expl_order[int(ev.row_key.value)])

    def action_brief_back(self) -> None:
        self.query_one("#p3sw", ContentSwitcher).current = "p3list"
        self.query_one("#p3col Bar", Bar).set("Explanations", "click or Enter: brief · B: back to the list")
        self.query_one("#expl").focus()

    def show_brief(self, e) -> None:
        if not self.visible("search"):
            return
        from ygg.ui.brief import brief

        tag = "BEST" if e.rank == 1 else ("WE DON'T KNOW" if e.rank == 0 else f"RIVAL {e.rank}")
        self.query_one("#brief", Static).update(brief(self.inv, e, self._term_label, self.visible))
        self.query_one("#p3col Bar", Bar).set(f"Explanation brief · {tag}", "B: back to the list · deterministic, from the recorded case")
        self.query_one("#p3sw", ContentSwitcher).current = "p3brief"
        if self.app.graph:
            first = next((x.dst for x in e.edges if x.src == "BOT"), None)
            if first:
                self.app.graph.focus(first)

    def action_graph_focus(self) -> None:
        order = []
        for e in sorted(self.inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
            for x in e.edges:
                for nid in (x.src, x.dst):
                    if nid not in order:
                        order.append(nid)
        if order:
            self.focus_i = (self.focus_i + 1) % len(order)
            self.app.graph.focus(order[self.focus_i])
            self.app.notify(f"graph ← {_sid(order[self.focus_i])}", timeout=2)

    def graph_selected(self, nid: str) -> None:
        for i, h in enumerate(self.inv.hypotheses):
            if h.entry == nid:
                self.hyp_i = i
                self.action_view("v_over")
                self.query_one("#hyps", DataTable).move_cursor(row=i)
                self.render_evidence()
                self.app.notify(f"graph → {h.hid}: {h.label[:60]}", timeout=3)
                return
        self.app.notify(f"graph → {_sid(nid)}", timeout=3)

    # ---------------------------------------------------------------- replay
    def action_toggle_replay(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
            self.render_all()
            return
        t0, t1 = replay_clock_range(self.inv)
        if self.clock is None or (self.clock >= t1 and self.revealed >= len(STEPS)):
            self.clock, self.revealed = t0, 0
        self._timer = self.set_interval(0.25, self.tick)
        self.app.tape(f"REPLAY     case {self.inv.case_id} from {self.clock:%m-%d %H:%M} (recorded state, no recomputation)")

    def tick(self) -> None:
        _, t1 = replay_clock_range(self.inv)
        if self.clock < t1:
            self.clock = min(t1, self.clock + timedelta(minutes=15 * self.speed))
        elif self.revealed < len(STEPS):
            self._step_wait += 1
            if self._step_wait >= 6:
                self._step_wait, self.revealed = 0, self.revealed + 1
        else:
            self._timer.stop()
            self._timer = None
        self.render_all()

    def action_faster(self) -> None:
        self.speed = min(96, self.speed * 2)

    def action_slower(self) -> None:
        self.speed = max(1, self.speed // 2)

    def visible(self, step: str) -> bool:
        if self.clock is None:
            return True
        return STEPS.index(step) < self.revealed and self.clock >= (self.inv.detected or self.clock)

    def _wait(self, step: str) -> Text:
        return Text(f"◉ replay clock {self.clock:%m-%d %H:%M} UTC · the case opens at {self.inv.detected:%m-%d %H:%M} UTC (daily close) · "
                    f"'{step}' appears after that, in recorded order", style=DIM)

    # ---------------------------------------------------------------- render
    def render_all(self) -> None:
        self.render_header()
        self.render_keys()
        self.render_verdict()
        self.render_chart()
        self.render_paths()
        self.render_evidence()
        self.render_story()
        self.render_evall()
        self.render_logic()
        self.render_placebo()
        self.render_trace()
        self.render_audit()

    def render_header(self) -> None:
        inv = self.inv
        t = Text(no_wrap=True, overflow="crop")
        t.append(f" CASE {inv.case_id} ", style=f"bold #000000 on {AMBER}")
        t.append(f"  τ* {inv.tau_star:%Y-%m-%d %H:%M} UTC" if inv.tau_star else "  τ* n/a", style=f"bold {AMBER_HI}")
        t.append(" first abnormal print", style=DIM)
        t.append(f"   DETECTED {inv.detected:%m-%d %H:%M}" if inv.detected else "", style=WHITE)
        t.append(" daily close", style=DIM)
        t.append(f"   SNAPSHOT w{inv.snapshot}", style=WHITE)
        t.append(f"   {inv.source}", style=f"bold {AMBER_HI if inv.source == 'DEMO' else UP}")
        if self.clock is not None:
            t.append(f"   ◉ REPLAY {self.clock:%m-%d %H:%M} UTC ×{self.speed * 15}m", style=f"bold {ID}")
            if inv.tau_star and self.clock >= inv.tau_star:
                t.append(" · past τ*: new documents are truth-only", style=WARN)
        self.query_one("#ihdr", Static).update(t)

    def render_keys(self) -> None:
        t = Text(no_wrap=True, overflow="crop", style=f"on {BAR}")
        for k, v, name in VIEWS:
            on = v == self.view
            t.append(f" {k.upper()} ", style=f"bold #000000 on {AMBER}")
            t.append(f" {name} ", style=f"{'bold ' + AMBER_HI if on else WHITE} on {BAR}")
        t.append("  │ ", style=f"{FAINT} on {BAR}")
        for k, v in (("R", "REPLAY"), ("+/-", "SPEED"), ("G", "GRAPH"), ("ESC", "BACK")):
            t.append(f" {k} ", style=f"bold #000000 on {AMBER}")
            t.append(f" {v} ", style=f"{WHITE} on {BAR}")
        self.query_one("#ikeys", Static).update(t)

    def render_verdict(self) -> None:
        box = self.query_one("#verdict", Static)
        inv = self.inv
        if not self.visible("search"):
            box.update(self._wait("search"))
            return
        b, a = inv.best, inv.abstention
        t = Text()
        if b is None:
            box.update(Text("no explanation recorded", style=DIM))
            return
        if b.entry == "BOT":
            t.append("WE DO NOT KNOW", style=f"bold {AMBER_HI}")
            t.append("  no narrative chain explains the move more cheaply than an unexplained move\n", style=WHITE)
        else:
            t.append("BEST  ", style=f"bold {AMBER}")
            t.append(b.entry_label[:70], style=f"bold {WHITE}")
            terms = sorted({x.dst for x in b.edges if _is_term(x.dst) and x.src != "BOT"})
            if terms:
                t.append("  →  ", style=DIM)
                t.append(" + ".join(self._term_label(x) for x in terms), style=WHITE)
            t.append(f"\n      {b.cost_mnats / 1000:.2f} nats", style=WHITE)
            if a:
                t.append(f"  ·  {a.odds_vs_best:.1f} : 1 against WE DO NOT KNOW", style=UP if a.odds_vs_best > 1 else WARN)
            rivals = [e for e in inv.explanations if e.rank >= 2]
            t.append(f"  ·  {len(rivals)} rival{'s' if len(rivals) != 1 else ''} within 1:20", style=WHITE)
        if inv.placebo and self.visible("placebos"):
            p = inv.placebo
            t.append(f"\n      placebo p {p.p_emp:.3f} ", style=WHITE)
            t.append(f"(beats {sum(1 for c in p.costs if c > b.cost_mnats) if p.costs else '?'} of {p.k} quiet days) · FER {p.fer:.2f}", style=DIM)
        if self.visible("verdicts"):
            for h in inv.hypotheses:
                if h.verdict_pre in ("SUPPORTED", "CONTRADICTED", "UNRESOLVED") or h.verdict_all in ("SUPPORTED", "CONTRADICTED"):
                    d = next((e for e in h.evidence if e.diagnostic), None)
                    t.append(f"\n      {h.hid} ", style=ID)
                    t.append(f"{h.label[:46]} ", style=WHITE)
                    t.append(f"P_pre {VERDICT_SHORT.get(h.verdict_pre)}", style=f"bold {VERDICT_STYLE.get(h.verdict_pre, DIM)}")
                    t.append(f"  P_all {VERDICT_SHORT.get(h.verdict_all)}", style=f"bold {VERDICT_STYLE.get(h.verdict_all, DIM)}")
                    if d:
                        t.append(f"  ◆ {d.source}", style=AMBER_HI)
        box.update(t)

    def render_chart(self) -> None:
        inv = self.inv
        chart = self.query_one("#ichart", HeroChart)
        if self.world is None or inv.tau_star is None:
            chart.show(ChartSpec(empty="no price table"))
            return
        etf = {"SMH", "XLK", "XLU", "SPY", "QQQ"}
        syms = []
        for k in range(len(inv.clusters)):
            m = [i for i in inv.instruments if i.cluster == k and i.symbol not in etf and i.SAR is not None]
            if m:
                syms.append(min(m, key=lambda i: i.SAR).symbol)
        syms += [i.symbol for i in inv.instruments if i.secondary][:1]
        data = self.world.daily(syms, (inv.tau_star - timedelta(days=21)).strftime("%Y-%m-%d"), (inv.tau_star + timedelta(days=4)).strftime("%Y-%m-%d"))
        if self.clock is not None:
            data = {s: [r for r in rows if datetime.fromisoformat(r[0]).replace(tzinfo=timezone.utc, hour=21) <= self.clock] for s, rows in data.items()}
        series, dates = pct_overlay({s: r for s, r in data.items() if r}, inv.tau_star.strftime("%Y-%m-%d"))
        if not series:
            chart.show(ChartSpec(empty="no completed daily bar before the clock"))
            return
        ti = next((i for i, d in enumerate(dates) if d >= inv.tau_star.strftime("%Y-%m-%d")), None)
        k = len(dates)
        ticks = sorted({0, k // 2, k - 1} | ({ti} if ti is not None else set()))
        spec = ChartSpec(series, hlines=[(0.0, RGB["FAINT"], "0")], vlines=[(ti, (255, 140, 0), "τ*")] if ti is not None else [],
                         xticks=(ticks, [dates[i][5:] for i in ticks]), last_tag=False, y_fmt="{:+.1f}%")
        chart.show(spec)
        leg = "  ".join(f"{s.label}" for s in series)
        self.query_one("#omid Bar", Bar).set(right=f"{leg} · % from the close before τ* · orange = τ* day")

    def _term_label(self, nid: str) -> str:
        """A terminal as 'C1 SMH+4' (cluster index from the recorded order) or its recorded name."""
        inv = self.inv
        if nid in inv.terminals:
            k = inv.terminals.index(nid)
        elif nid.startswith("T") and nid[1:].isdigit():
            k = int(nid[1:])
        else:
            return nid
        c = inv.clusters[k] if k < len(inv.clusters) else ()
        return f"C{k + 1} {c[0] if c else nid}{'+' + str(len(c) - 1) if len(c) > 1 else ''}"

    def render_paths(self) -> None:
        box = self.query_one("#paths", Static)
        inv = self.inv
        if not self.visible("search"):
            box.update(self._wait("search"))
            return
        cl = {f"T{k}": c for k, c in enumerate(inv.clusters)}
        t = Text()
        for e in sorted(inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
            tag = "BEST" if e.rank == 1 else ("WE DON'T KNOW" if e.rank == 0 else f"RIVAL {e.rank}")
            t.append(f"{e.rank if e.rank else 0}  {tag:<14}", style=f"bold {UP if e.rank == 1 else (AMBER_HI if e.rank == 0 else WHITE)}")
            t.append(f"{e.cost_mnats / 1000:5.2f} nats   {_odds(e.odds_vs_best):>8}\n", style=WHITE)
            for path in _paths(e):
                t.append("     BOT", style=AMBER)
                width = max(40, self.app.size.width // 2 - 6)
                n_narr = sum(1 for x in path if not _is_term(x.dst))
                room = max(10, (width - 10 - 9 * len(path) - 10) // max(1, n_narr))
                for x in path:
                    t.append(f" ─{x.p:.2f}→ " if x.p else " ──→ ", style=DIM)
                    if _is_term(x.dst):
                        t.append(self._term_label(x.dst), style=f"bold {DOWN}")
                    else:
                        t.append(x.dst_label[:room], style=WHITE)
                t.append("\n")
        used = {x.dst for e in inv.explanations for x in e.edges if not _is_term(x.dst)}
        t.append("\nGRAPH  ", style=f"bold {AMBER}")
        t.append(f"{inv.graph_nodes} nodes · {inv.graph_edges:,} edges searched exactly (DPBF) · {len(used)} narratives in the kept trees · "
                 f"{len(inv.clusters)} market terminals\n" if inv.graph_nodes else "explanation trees only (no recorded graph)\n", style=WHITE)
        t.append("p = attribution share or terminal link · cost Σ(−log p + λ) · shared trunks paid once · edges = timing, not cause · G focuses the graph window", style=DIM)
        box.update(t)

    def render_evidence(self) -> None:
        box = self.query_one("#evbody", Static)
        inv = self.inv
        if not self.visible("claims"):
            box.update(self._wait("claims"))
            return
        if not inv.hypotheses:
            box.update(Text("verdicts not run yet", style=DIM))
            return
        h = inv.hypotheses[min(self.hyp_i, len(inv.hypotheses) - 1)]
        self.query_one("#obot Vertical:last-of-type Bar", Bar).set(f"Evidence · {h.hid}", f"P_pre {VERDICT_SHORT.get(h.verdict_pre)} · P_all {VERDICT_SHORT.get(h.verdict_all)}")
        box.update(evidence_wall(h, inv.tau_star))

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
        att, sp, docs = self.query_one("#att", HeroChart), self.query_one("#spill", HeroChart), self.query_one("#docs", Static)
        nids = self._nids()
        if self.world is None or inv.tau_star is None or "e2b_series" not in self.world.have:
            docs.update(Text("no recorded attention tables", style=DIM))
            return
        t0, _ = replay_clock_range(inv)
        upto = min(self.clock or inv.tau_star, inv.detected or inv.tau_star)
        a = self.world.attention([n for n, _ in nids], t0, upto + timedelta(minutes=15))
        if not any(a.values()):
            att.show(ChartSpec(empty="no recorded attention for these narratives" + (" (DEMO fixture: open a recorded case)" if inv.source == "DEMO" else "")))
            sp.show(ChartSpec(empty=""))
            docs.update(Text(""))
            return
        w0 = self.world.window(t0)
        nh = max(1, (self.world.window(upto) - w0 + 1) // 4)
        series = []
        from ygg.ui.theme import SERIES

        for k, (nid, lab) in enumerate(nids[:6]):
            ys = {w: y for w, y, _, _ in a.get(nid, [])}
            series.append(Series(f"{short('N', nid)} {lab[:24]}", list(range(nh)), [sum(ys.get(w0 + 4 * h + j, 0.0) for j in range(4)) for h in range(nh)],
                                 SERIES[k % len(SERIES)]))
        tau_h = int((inv.tau_star - t0).total_seconds() // 3600)
        days = list(range(0, nh, 24))
        vl = [(tau_h, (255, 140, 0), "τ*")] if self.clock is None or self.clock >= inv.tau_star else []
        att.show(ChartSpec(series, vlines=vl, xticks=(days, [(t0 + timedelta(hours=d)).strftime("%m-%d") for d in days]), last_tag=False, y_fmt="{:.0f}"))
        pairs = [(x.src, x.dst) for e in inv.explanations for x in e.edges if x.src != "BOT" and not _is_term(x.dst)]
        spl = self.world.spill(pairs, t0, upto + timedelta(minutes=15))
        ss = []
        for k, ((s, d), rows) in enumerate(spl.items()):
            hs: dict[int, list] = {}
            for w, al in rows:
                hs.setdefault((w - w0) // 4, []).append(al)
            xs = sorted(hs)
            if xs:
                ss.append(Series(f"{short('N', s)}→{short('N', d)}", xs, [sum(hs[x]) / len(hs[x]) for x in xs], SERIES[k % len(SERIES)]))
        sp.show(ChartSpec(ss, vlines=vl, xticks=(days, [(t0 + timedelta(hours=d)).strftime("%m-%d") for d in days]), last_tag=False, y_fmt="{:.2f}",
                          empty="no spillover recorded on these edges"))
        items = self.world.feed(t0, upto, [n for n, _ in nids], limit=60)
        ft = Text(no_wrap=True, overflow="crop")
        for f in items:
            late = f.t >= inv.tau_star
            ft.append(f"{f.t:%m-%d %H:%M} ", style=DIM)
            ft.append("POST-τ* " if late else "PRE-τ*  ", style=WARN if late else UP)
            ft.append(f"{short('N', f.narrative)} ", style=ID)
            ft.append(f"{f.source[:18]:<18} ", style=AMBER)
            ft.append(f"{f.title}\n", style=DIM if late else WHITE)
        docs.update(ft)

    def render_evall(self) -> None:
        box = self.query_one("#evall", Static)
        if not self.visible("claims"):
            box.update(self._wait("claims"))
            return
        parts = []
        for h in self.inv.hypotheses:
            parts.append(Text.assemble((f"{h.hid} ", ID), (h.label, f"bold {WHITE}"), ("   P_pre ", AMBER),
                                       (VERDICT_SHORT.get(h.verdict_pre, ""), f"bold {VERDICT_STYLE.get(h.verdict_pre, DIM)}"), ("   P_all ", AMBER),
                                       (VERDICT_SHORT.get(h.verdict_all, ""), f"bold {VERDICT_STYLE.get(h.verdict_all, DIM)}")))
            parts.append(evidence_wall(h, self.inv.tau_star))
            parts.append(Text(""))
        box.update(Group(*parts) if parts else Text("verdicts not run yet", style=DIM))

    def render_logic(self) -> None:
        box = self.query_one("#logic", Static)
        if not self.visible("verdicts"):
            box.update(self._wait("verdicts"))
            return
        inv = self.inv
        t = Table(box=None, expand=True, padding=(0, 2), show_edge=False)
        for c in ("HYPOTHESIS", "P_PRE", "BITS", "P_ALL", "BITS ", "SIGNATURE"):
            t.add_column(c, header_style=f"bold {AMBER}")
        for h in inv.hypotheses:
            t.add_row(Text(f"{h.hid} {h.label[:60]}", style=WHITE),
                      Text(VERDICT_SHORT.get(h.verdict_pre, ""), style=f"bold {VERDICT_STYLE.get(h.verdict_pre, DIM)}"),
                      "".join(map(str, h.bits_pre)) if h.bits_pre else "", Text(VERDICT_SHORT.get(h.verdict_all, ""), style=f"bold {VERDICT_STYLE.get(h.verdict_all, DIM)}"),
                      "".join(map(str, h.bits_all)) if h.bits_all else "", Text(("burst " if h.burst else "") + ("surprise" if h.surprise_ok else ""), style=UP))
        expl = Text(f"\nbits = bIN cIN bOUT cOUT: explained in some / every stable reading, refuted in some / every reading.\n"
                    f"SUPPORTED iff cIN · CONTRADICTED iff cOUT · UNRESOLVED iff bOUT and not cOUT · otherwise CONSISTENT-BUT-UNPROVEN.\n"
                    f"A report is believed unless an independent contrary report of equal or better tier overrides it; copies add nothing.\n"
                    f"stable models: P_pre {inv.models_pre} · P_all {inv.models_all}", style=DIM)
        box.update(Group(t, expl))

    def render_placebo(self) -> None:
        box, ch = self.query_one("#plac", Static), self.query_one("#plach", HeroChart)
        inv, p = self.inv, self.inv.placebo
        if not self.visible("placebos"):
            box.update(self._wait("placebos"))
            return
        if p is None:
            box.update(Text("placebos were not run for this case", style=DIM))
            return
        b = inv.best
        if p.costs:
            ch.show(ChartSpec(hist=[c / 1000 for c in p.costs], vlines=[(b.cost_mnats / 1000, (255, 140, 0), "case")] if b else []))
        t = Text()
        t.append(f"empirical p = (1 + #quiet days explained at least as cheaply) / (1 + K) = {p.p_emp:.3f}   K = {p.k}\n", style=WHITE)
        t.append(f"false-explanation rate on quiet days = {p.fer:.2f} (target ≤ 0.05)\n\n", style=WHITE)
        t.append("HUB FREQUENCY\n", style=f"bold {AMBER}")
        for n, f in p.hubs[:10]:
            nid, _, lab = n.partition(" :: ")
            t.append(f"  {short('N', nid)} ", style=ID)
            t.append(f"{lab[:60]:<60} {100 * f:4.0f}%", style=AMBER_HI if f >= 0.3 else WHITE)
            t.append("  low diagnosticity\n" if f >= 0.3 else "\n", style=AMBER_HI)
        box.update(t)

    def render_trace(self) -> None:
        box = self.query_one("#trace", Static)
        if not self.visible("queries"):
            box.update(self._wait("queries"))
            return
        t = Text()
        t.append("one-way valve: pages fetched here never enter Engine 2 counts or fits\n\n", style=WARN)
        for q in self.inv.searches:
            t.append(f"{short('Q', q.qid)}  {q.hid}  {q.provider}  ", style=WHITE)
            t.append(q.status + "\n", style=DOWN if q.status in ("UNAVAILABLE", "ERROR") else UP)
            t.append(f"  {q.query}\n", style=DIM)
            if q.status in ("DONE", "CACHED"):
                t.append(f"  {q.results} results → {q.matched} canonical-URL matches (first_seen inherited) → {q.unmatched} unmatched (truth only)\n", style=DIM)
            if q.note:
                t.append(f"  {q.note}\n", style=DIM)
        box.update(t if self.inv.searches else Text("no search operations recorded", style=DIM))

    def render_audit(self) -> None:
        inv = self.inv
        t = Text()
        for k, v in (("SOURCE", inv.source), ("CFG HASH", inv.cfg_hash or "not recorded"), ("SNAPSHOT", f"window {inv.snapshot}"),
                     ("GRAPH", f"{inv.graph_nodes} nodes · {inv.graph_edges} edges · exact DPBF"),
                     ("τ* RULE", "earliest first abnormal print across the clusters; venue session start in replay; earlier when unsure"),
                     ("DETECTION", "daily close (the replay trigger runs on daily bars)"),
                     ("ADMISSIBILITY", "first_seen < τ* for P_pre; everything up to report time for P_all"),
                     ("DETERMINISM", "no wall clock · keyed Philox · fixed reductions, pinned threads · tie keys · archived calls · cfg stamps"),
                     ("NOT PROVEN", "claim extraction, copy detection, source tiers, the attention model; Lean not run")):
            t.append(f"{k:<15}", style=AMBER)
            t.append(f"{v}\n", style=WHITE)
        for n in inv.notes:
            t.append(f"\n{n}", style=AMBER_HI)
        self.query_one("#audit", Static).update(t)
        if self.visible("search"):
            parts = []
            for e in sorted(inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
                parts.append(explanation_tree(e, ("BEST" if e.rank == 1 else "WE DON'T KNOW" if e.rank == 0 else f"RIVAL {e.rank}") +
                                              f" · {e.cost_mnats / 1000:.2f} nats · {_odds(e.odds_vs_best)}"))
            self.query_one("#trees", Static).update(Group(*parts))


# ====================================================================================================== app
class YggApp(App):
    CSS = CSS
    TITLE = "Yggdrasil"
    BINDINGS = [Binding("right_square_bracket", "present(1)", show=False, priority=True),
                Binding("left_square_bracket", "present(-1)", show=False, priority=True),
                Binding("backslash", "present_off", show=False, priority=True)]

    def __init__(self, data_dir: Path, cfg: dict, demo: bool = False, present: list | None = None):
        super().__init__()
        self.present, self.pi = list(present or []), -1        # presenter steps: {"focus": [selectors], "caption": str}
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
        self.graph = GraphServer(self.on_graph_select, port=int(os.environ.get("YGG_GRAPH_PORT", "8765")),
                                 on_present=lambda d: (self.action_present_off() if d == 0 else self.action_present(d)))

    # ---- presenter mode: dim everything but the panel being explained, caption at the bottom (for the demo video)
    def action_present(self, d: int) -> None:
        if not self.present:
            return
        self.pi = max(0, min(len(self.present) - 1, self.pi + d))
        self._apply_present(self.present[self.pi])

    def action_present_off(self) -> None:
        self.pi = -1
        self._apply_present({"focus": [], "caption": ""})

    def _apply_present(self, step: dict) -> None:
        scr = self.screen
        sels = step.get("focus") or []
        sels = [sels] if isinstance(sels, str) else sels
        keep = set()
        for sel in sels:
            try:
                nodes = list(scr.query(sel))
            except Exception:
                nodes = []
            for n in nodes:
                keep.add(n)
                keep.update(n.query("*"))
                par = n.parent
                if par is not None:
                    sib = list(par.children)
                    i = sib.index(n)
                    if i > 0 and isinstance(sib[i - 1], Bar):     # the panel's numbered title bar stays lit
                        keep.add(sib[i - 1])
        for w in scr.query("Bar, .panel, DataTable, #ihdr, #top, #keys, #ikeys, #status, #brand, #cmd"):
            w.set_class(bool(keep) and w not in keep, "pdim")       # nothing matched on this screen: dim nothing
        cap = step.get("caption", "")
        try:
            box = scr.query_one("#caption", Static)
        except Exception:
            box = Static(id="caption")
            scr.mount(box)
        box.update(Text(cap, style="bold #ffffff", justify="center"))
        box.display = bool(cap)
        self.graph.publish({"type": "caption", "text": cap})            # the graph window shows the same caption
        if step.get("graph_view"):
            self.graph.publish({"type": "view", "view": step["graph_view"]})

    def on_graph_select(self, nid: str) -> None:
        self.tape(f"GRAPH      selected {_sid(nid)} in the graph window")
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
        return f"replay engine: {day}" + (" running" if age < 1500 else " stalled?")

    async def on_mount(self) -> None:
        self.tape("START      control panel")
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


def run(data_dir: Path, cfg: dict, demo: bool = False, present: Path | None = None) -> None:
    import json

    steps = json.loads(Path(present).read_text()) if present else None
    YggApp(data_dir, cfg, demo, steps).run()
