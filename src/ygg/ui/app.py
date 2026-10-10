"""Yggdrasil terminal: a live control panel and a full-page investigation workspace (Textual).

  ygg ui            live control panel (world at the latest served GDELT batch, Yahoo 5-minute candles)
  ygg ui --demo     adds the DEMO investigation fixture (labelled MODE: DEMO everywhere it appears)

The UI is a projection of recorded state: it never recomputes a result, never moves tau*, and never shows a record
whose first_seen is after the clock it is drawing (live: the latest batch; replay: the replay clock).
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

from ygg.ui import live as L
from ygg.ui.domain import PRE, CaseRow, Investigation, short
from ygg.ui.recorded import World, list_cases, load_investigation, replay_clock_range
from ygg.ui.render import (AMBER, CYAN, GRAY, GREEN, INK, PHASE_MARK, RED, VERDICT_SHORT, VERDICT_STYLE, bits_table, candles,
                           evidence_wall, explanation_tree, fmt_pct, fmt_sig, fmt_t, histogram, odds_text, sparkline)

CSS = """
Screen { background: #0a0f13; color: #d7e0e6; }
#hdr, #ihdr { height: 1; background: #111a21; color: #d7e0e6; padding: 0 1; }
#top { height: 20; }
#watch { width: 44; border: solid #26313a; }
#asset { width: 1fr; border: solid #26313a; padding: 0 1; }
#feed { width: 1fr; border: solid #26313a; padding: 0 1; }
#pipeline { height: 5; border: solid #26313a; padding: 0 1; }
#cases { height: 9; border: solid #58c4dd; }
#tape { height: 1fr; border: solid #26313a; padding: 0 1; }
DataTable { background: #0a0f13; }
DataTable > .datatable--header { background: #111a21; color: #76828c; }
DataTable > .datatable--cursor { background: #1d3340; color: #ffffff; }
TabbedContent { height: 1fr; }
.panel { border: solid #26313a; padding: 0 1; height: auto; }
.half { width: 1fr; }
#ov_left { width: 58; }
"""


def _border(w, title: str, sub: str = "") -> None:
    w.border_title = title
    if sub:
        w.border_subtitle = sub


# ====================================================================================================== control panel
class ControlPanel(Screen):
    BINDINGS = [Binding("enter", "open_case", "open case"), Binding("w", "focus_watch", "market"),
                Binding("c", "focus_cases", "investigations"), Binding("n", "poll_news", "fetch news now"),
                Binding("q", "app.quit", "quit")]

    def compose(self) -> ComposeResult:
        yield Static(id="hdr")
        with Horizontal(id="top"):
            yield DataTable(id="watch", cursor_type="row", zebra_stripes=False)
            yield Static(id="asset")
            yield Static(id="feed")
        yield Static(id="pipeline")
        yield DataTable(id="cases", cursor_type="row")
        yield Static(id="tape")
        yield Footer()

    def on_mount(self) -> None:
        app: YggApp = self.app
        w = self.query_one("#watch", DataTable)
        for col, wd in (("symbol", 9), ("last", 11), ("chg", 7), ("state", 7)):
            w.add_column(col, key=col, width=wd)
        for s in L.WATCH:
            w.add_row(s, "…", "…", "…", key=s)
        _border(w, "MARKET WATCH", "Yahoo 5-min · equities closed on weekends")
        c = self.query_one("#cases", DataTable)
        c.add_columns("", "case", "phase", "clusters", "max|SAR|", "best explanation", "odds vs we-don't-know", "placebo p", "source")
        _border(c, "INVESTIGATIONS", "active (live) · archived (recorded) · enter opens")
        _border(self.query_one("#asset"), "SELECTED ASSET")
        _border(self.query_one("#feed"), "WORLD FEED", "GDELT GKG · latest served batch")
        _border(self.query_one("#pipeline"), "PIPELINE", "what each engine is doing now")
        _border(self.query_one("#tape"), "EVENT TAPE")
        self.load_cases()
        self.render_header()
        self.render_pipeline()
        self.render_feed()
        self.set_interval(1.0, self.render_header)
        self.set_interval(5.0, self.render_pipeline)
        self.set_interval(60.0, self.refresh_quotes)
        self.set_interval(300.0, self.action_poll_news)
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
            st = Text(q.state, style=GREEN if q.state == "OPEN" else (GRAY if q.state == "CLOSED" else RED))
            chg = q.change
            w.update_cell(s, "last", f"{q.last:,.2f}" if q.last else "—")
            w.update_cell(s, "chg", Text(fmt_pct(chg), style=(GREEN if (chg or 0) >= 0 else RED)) if chg is not None else "—")
            w.update_cell(s, "state", st)
            if s in L.DEMO_EXTRA:
                w.update_cell(s, "symbol", Text(f"{s} *", style=AMBER))
        app.tape(f"QUOTES     {sum(q.state != 'UNAVAILABLE' for q in qs.values())}/{len(qs)} symbols refreshed")
        self.render_asset()

    def action_poll_news(self) -> None:
        self.run_worker(self._news, thread=True, exclusive=True, group="news")

    def _news(self) -> None:
        b = self.app.world.poll()
        self.app.call_from_thread(self._apply_news, b)

    def _apply_news(self, b) -> None:
        app: YggApp = self.app
        if b is not None:
            for x in app.world.batches[-8:]:
                key = (x.ts, x.status)
                if key not in app.seen_batches:
                    app.seen_batches.add(key)
                    app.tape(f"BATCH      {x.ts:%H:%M} UTC  {x.status}" + (f"  {x.docs} docs" if x.status == "OK" else "  listed, not served yet"))
        elif app.world.error:
            app.tape(f"BATCH      error: {app.world.error}")
        self.render_feed()
        self.render_pipeline()

    def load_cases(self) -> None:
        app: YggApp = self.app
        c = self.query_one("#cases", DataTable)
        c.clear()
        c.add_row(Text("●", style=GRAY), Text("—", style=GRAY), Text("WAITING", style=GRAY),
                  Text("no active investigations · live trigger (intraday Lee-Mykland) is outside the hackathon cut", style=GRAY),
                  "", "", "", "", "LIVE", key="__live__")
        rows: list[CaseRow] = list_cases(app.data_dir)
        if app.demo:
            from ygg.ui.demo import demo_investigation

            inv = demo_investigation()
            b = inv.best
            rows.append(CaseRow(inv.case_id, "ARCHIVED", "VERDICTS", "C1(5)  C2(4)", 7.8, b.entry_label if b else "—",
                                inv.abstention.odds_vs_best if inv.abstention else None, inv.placebo.p_emp if inv.placebo else None, "DEMO"))
        for r in rows:
            c.add_row(Text("◉", style=CYAN), Text(r.case_id, style=CYAN), r.phase, r.terminals,
                      f"{r.max_sar:.1f}" if r.max_sar else "—", r.best[:48], odds_text(r.odds) if r.odds else "—",
                      f"{r.p_emp:.3f}" if r.p_emp is not None else "—",
                      Text(r.source, style=AMBER if r.source == "DEMO" else GRAY), key=f"{r.source}:{r.case_id}")
        if not rows:
            c.add_row("", Text("no archived investigations yet: run 'ygg case DAY' and 'ygg verdict DAY'", style=GRAY), "", "", "", "", "", "", "")

    # ---------------------------------------------------------------- render
    def render_header(self) -> None:
        app: YggApp = self.app
        now = datetime.now(timezone.utc)
        t = Text()
        t.append(" YGGDRASIL ", style=f"bold {CYAN}")
        t.append("│ ")
        t.append("● LIVE ", style=f"bold {GREEN}")
        wt = app.world.last_ok
        if wt:
            lag = now - wt
            t.append(f"world @ {wt:%H:%M} UTC (latest served batch, lag {int(lag.total_seconds() // 60)} min) ", style=INK)
        else:
            t.append("world: waiting for the first served batch ", style=GRAY)
        t.append(f"│ wall {now:%H:%M:%S} UTC │ cfg {app.cfg_hash[:8]} ", style=GRAY)
        if app.demo:
            t.append("│ MODE: DEMO fixtures present ", style=f"bold {AMBER}")
        self.query_one("#hdr", Static).update(t)

    def render_asset(self) -> None:
        app: YggApp = self.app
        w = self.query_one("#watch", DataTable)
        if w.row_count == 0:
            return
        sym = L.WATCH[min(w.cursor_row, len(L.WATCH) - 1)]
        q = app.quotes.get(sym)
        box = self.query_one("#asset", Static)
        box.border_title = f"SELECTED ASSET · {sym}" + ("  (24/7 demo extra, outside the equity universe)" if sym in L.DEMO_EXTRA else "")
        if q is None:
            box.update(Text("loading…", style=GRAY))
            return
        if q.state == "UNAVAILABLE":
            box.update(Text(f"UNAVAILABLE\nprice source could not be queried\nreason: {q.error}", style=RED))
            return
        width = max(20, box.size.width - 2)
        head = Text()
        head.append(f"{q.last:,.2f}  ", style=f"bold {INK}")
        chg = q.change
        head.append(fmt_pct(chg) + " vs prev close  ", style=GREEN if (chg or 0) >= 0 else RED)
        head.append(q.state, style=GREEN if q.state == "OPEN" else GRAY)
        if q.state == "CLOSED" and q.candles:
            head.append(f"  · last session bar {q.candles[-1].t:%a %H:%M} UTC", style=GRAY)
        if q.candles:
            day = [c for c in q.candles if c.t >= q.candles[-1].t - timedelta(hours=24)]
            head.append(f"\n24h range {min(c.l for c in day):,.2f} – {max(c.h for c in day):,.2f} · vol {sum(c.v for c in day):,.0f}", style=GRAY)
        foot = Text("\ntrigger: daily market-only SAR (replay) · live intraday test not in cut", style=GRAY)
        box.update(Group(head, candles(q.candles, width, 11), foot))

    def on_data_table_row_highlighted(self, ev: DataTable.RowHighlighted) -> None:
        if ev.data_table.id == "watch":
            self.render_asset()

    def on_data_table_row_selected(self, ev: DataTable.RowSelected) -> None:
        if ev.data_table.id == "cases":
            self.action_open_case()

    def render_feed(self) -> None:
        app: YggApp = self.app
        box = self.query_one("#feed", Static)
        if not app.world.feed:
            msg = app.world.error or "waiting for the first served GDELT batch…"
            box.update(Text(msg, style=GRAY))
            return
        t = Text()
        for f in app.world.feed[: max(5, box.size.height - 2)]:
            t.append(f"{f.t:%H:%M} ", style=GRAY)
            t.append(f"{f.source[:18]:<18} ", style=CYAN)
            t.append(f"{f.title[:max(10, box.size.width - 28)]}\n", style=INK)
        box.update(t)

    def render_pipeline(self) -> None:
        app: YggApp = self.app
        wd = app.world
        ok = [b for b in wd.batches if b.status == "OK"]
        waiting = sum(1 for b in wd.batches if b.status == "NOT_YET" and (not ok or b.ts > ok[-1].ts))
        rp = app.replay_progress()
        stages = [
            ("NEWS", "RUNNING" if ok else "WAITING", f"{ok[-1].docs} docs @ {ok[-1].ts:%H:%M}" if ok else "no batch yet",
             f"{waiting} listed, not served" if waiting else ""),
            ("EVENTS·NARRATIVES·ATTENTION", "COLD (live)", "live world model not warmed", rp or "no replay running"),
            ("ANOMALY", "IDLE", "markets closed (Sat)" if datetime.now(timezone.utc).weekday() >= 5 else "daily trigger",
             "BTC-USD shown as demo extra"),
            ("HYPOTHESES·SEARCH", "IDLE", "no open case", "exact DPBF on open"),
            ("EVIDENCE", "UNAVAILABLE" if not app.serpapi else "IDLE", "SerpApi key absent" if not app.serpapi else "SerpApi ready",
             "Engine 1 + Wayback only" if not app.serpapi else ""),
            ("VERDICT", "IDLE", "clingo, 4 bits", "Lean: stretch, not run"),
        ]
        t = Table.grid(expand=True, padding=(0, 1))
        for _ in stages:
            t.add_column(ratio=1)
        style = {"RUNNING": GREEN, "WAITING": AMBER, "IDLE": GRAY, "UNAVAILABLE": RED}
        t.add_row(*[Text(f"{n} ▸" if i < len(stages) - 1 else n, style=f"bold {CYAN}") for i, (n, *_r) in enumerate(stages)])
        t.add_row(*[Text(s, style=style.get(s.split()[0], AMBER)) for _, s, *_r in stages])
        t.add_row(*[Text(a, style=INK) for _, _, a, _ in stages])
        t.add_row(*[Text(b, style=GRAY) for _, _, _, b in stages])
        self.query_one("#pipeline", Static).update(t)
        self.render_tape()

    def render_tape(self) -> None:
        app: YggApp = self.app
        t = Text()
        for ts, msg in list(app.events)[-12:][::-1]:
            t.append(f"{ts:%H:%M:%S}  ", style=GRAY)
            t.append(msg + "\n", style=INK)
        self.query_one("#tape", Static).update(t or Text("no events yet", style=GRAY))

    # ---------------------------------------------------------------- actions
    def action_focus_watch(self) -> None:
        self.query_one("#watch").focus()

    def action_focus_cases(self) -> None:
        self.query_one("#cases").focus()

    def action_open_case(self) -> None:
        c = self.query_one("#cases", DataTable)
        if c.row_count == 0:
            return
        key = c.coordinate_to_cell_key((c.cursor_row, 0)).row_key.value
        if not key or key == "__live__":
            return
        src, day = key.split(":", 1)
        app: YggApp = self.app
        import json

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
        self.focus_i = -1
        self.clock: datetime | None = None          # None: archive view (everything recorded is visible)
        self.speed = 8                              # windows (15 min) per tick
        self.revealed = len(STEPS)
        self.hyp_i = 0
        self._timer = None

    def compose(self) -> ComposeResult:
        yield Static(id="ihdr")
        with TabbedContent(id="tabs"):
            with TabPane("Overview", id="t_over"):
                with Horizontal():
                    with VerticalScroll(id="ov_left"):
                        yield Static(id="ov_case", classes="panel")
                        yield Static(id="ov_prog", classes="panel")
                    with VerticalScroll():
                        yield Static(id="ov_mkt", classes="panel")
                        yield Static(id="ov_best", classes="panel")
            with TabPane("Story", id="t_story"):
                with VerticalScroll():
                    yield Static(id="st_att", classes="panel")
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
        for wid, title in (("ov_case", "CASE"), ("ov_prog", "RESEARCH PROGRESS"), ("ov_mkt", "MARKET · daily bars · τ* marked"),
                           ("ov_best", "CURRENT UNDERSTANDING"), ("st_att", "ATTENTION BEFORE τ* · narratives in the explanations"),
                           ("st_feed", "DOCUMENTS · those narratives · first_seen ≤ clock"), ("tr_main", "EXPLANATIONS · exact DPBF · rivals within 1:20 · abstention always"),
                           ("ev_main", "EVIDENCE"), ("lg_main", "LOGIC · every consistent reading of the evidence (clingo)"),
                           ("pl_main", "PLACEBOS · the same search on quiet days"), ("sx_main", "EVIDENCE ACQUISITION"), ("au_main", "AUDIT")):
            _border(self.query_one(f"#{wid}"), title)
        self.render_all()
        self.set_interval(1.0, self.render_header)
        from ygg.ui.graph_server import payload_for

        app.graph.show(payload_for(self.inv, self.raw))
        app.tape(f"GRAPH      showing case {self.inv.case_id} at {app.graph.url}")

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
        self.app.tape(f"GRAPH      focus {short('N', nid) if nid != 'BOT' and not nid.startswith('T') else nid}")

    def graph_selected(self, nid: str) -> None:
        for i, h in enumerate(self.inv.hypotheses):
            if h.entry == nid:
                self.hyp_i = i
                self.query_one("#tabs", TabbedContent).active = "t_ev"
                self.render_evidence()
                self.notify(f"graph → {h.hid}: {h.label[:60]}", timeout=3)
                return
        lab = next((x.dst_label for e in self.inv.explanations for x in e.edges if x.dst == nid), nid)
        self.notify(f"graph → {nid if nid in ('BOT',) or nid.startswith('T') else short('N', nid)}  {lab[:60]}", timeout=3)

    # ---------------------------------------------------------------- replay
    def action_toggle_replay(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
            self.app.tape(f"REPLAY     paused at {fmt_t(self.clock, True)}")
            self.render_all()
            return
        t0, t1 = replay_clock_range(self.inv)
        if self.clock is None or self.clock >= t1 and self.revealed >= len(STEPS):
            self.clock, self.revealed = t0, 0
        self._timer = self.set_interval(0.25, self.tick)
        self.app.tape(f"REPLAY     case {self.inv.case_id} from {fmt_t(self.clock, True)} (recorded state, no recomputation)")

    def tick(self) -> None:
        _, t1 = replay_clock_range(self.inv)
        if self.clock < t1:
            self.clock = min(t1, self.clock + timedelta(minutes=15 * self.speed))
        elif self.revealed < len(STEPS):
            self._step_wait = getattr(self, "_step_wait", 0) + 1
            if self._step_wait >= 6:                 # one recorded step every 1.5 s, in recorded order
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
        self.render_header()

    def action_slower(self) -> None:
        self.speed = max(1, self.speed // 2)
        self.render_header()

    def action_next_hyp(self) -> None:
        if self.inv.hypotheses:
            self.hyp_i = (self.hyp_i + 1) % len(self.inv.hypotheses)
            self.render_evidence()

    def visible(self, step: str) -> bool:
        return self.clock is None or STEPS.index(step) < self.revealed and (self.clock >= (self.inv.detected or self.clock))

    # ---------------------------------------------------------------- render
    def render_all(self) -> None:
        self.render_header()
        self.render_overview()
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
        t.append(f"│ DETECTED {fmt_t(inv.detected)} UTC (daily close) ", style=INK)
        t.append(f"│ τ* {fmt_t(inv.tau_star)} UTC (first abnormal print) ", style=f"bold {AMBER}")
        t.append(f"│ snapshot window {inv.snapshot} ", style=GRAY)
        t.append(f"│ {inv.source} ", style=f"bold {AMBER}" if inv.source == "DEMO" else GREEN)
        if self.clock is not None:
            t.append(f"│ ◉ REPLAY ×{self.speed * 15 // 60 if self.speed >= 4 else self.speed * 15}{'h' if self.speed >= 4 else 'm'}/tick "
                     f"clock {fmt_t(self.clock, True)} UTC ", style=f"bold {CYAN}")
            if inv.tau_star and self.clock >= inv.tau_star:
                t.append("· past τ*: later documents are truth-only ", style=AMBER)
        else:
            t.append("│ archive view · r replays the recorded investigation ", style=GRAY)
        self.query_one("#ihdr", Static).update(t)

    def _locked(self, wid: str, step: str) -> bool:
        if self.visible(step):
            return False
        when = fmt_t(self.inv.detected, True)
        self.query_one(f"#{wid}", Static).update(Text(f"not yet: the case opens at {when} UTC (replay clock {fmt_t(self.clock, True)}); "
                                                      f"step '{step}' is shown in recorded order after that", style=GRAY))
        return True

    def render_overview(self) -> None:
        inv = self.inv
        case = Table(box=None, expand=True, header_style=f"bold {GRAY}")
        for c in ("sym", "R", "SAR", "Mz", "Mv", "Mg", ""):
            case.add_column(c, justify="right" if c not in ("sym", "") else "left")
        for i in inv.instruments:
            tag = Text(f"C{i.cluster + 1}" if i.cluster is not None else ("gap" if i.secondary else ""),
                       style=CYAN if i.cluster is not None else GRAY)
            case.add_row(Text(i.symbol, style=f"bold {RED}" if i.fired else GRAY), fmt_pct(i.R), fmt_sig(i.SAR), fmt_sig(i.Mz),
                         fmt_sig(i.Mv), fmt_sig(i.Mg), tag)
        head = Text()
        for k, c in enumerate(inv.clusters):
            head.append(f"C{k + 1}  ", style=f"bold {CYAN}")
            head.append(", ".join(c) + "\n", style=INK)
        head.append("one search terminal per cluster; ETFs are members, not terminals\n", style=GRAY)
        self.query_one("#ov_case", Static).update(Group(head, case))
        prog = Text()
        for k, (ph, st) in enumerate(inv.phases):
            if self.clock is not None and not (k < self.revealed and self.clock >= (inv.detected or self.clock)):
                st = "PENDING"
            m, col = PHASE_MARK.get(st, ("?", GRAY))
            prog.append(f" {m} {ph:<10}", style=col)
            prog.append({"trigger": "market-only SAR gate, clusters, τ*", "snapshot": f"frozen at window {inv.snapshot}, read-only",
                         "search": f"{inv.graph_nodes} nodes · {inv.graph_edges} edges · exact", "placebos": "quiet-day calibration",
                         "queries": "SerpApi (key absent)" if st == "UNAVAILABLE" else "1 confirming + 2 disconfirming per hypothesis",
                         "claims": "GKG structure → rules → verifier", "verdicts": f"P_pre {inv.models_pre} model(s) · P_all {inv.models_all}",
                         "lean": "stretch: not run"}.get(ph, "") + "\n", style=GRAY)
        self.query_one("#ov_prog", Static).update(prog)
        self.render_market()
        best = Text()
        if self._locked("ov_best", "search"):
            return
        b, a = inv.best, inv.abstention
        if b:
            best.append("best   ", style=GRAY)
            best.append(f"{b.entry_label[:80]}\n", style=f"bold {INK}" if b.entry != "BOT" else f"bold {AMBER}")
            best.append(f"       {b.cost_mnats / 1000:.2f} nats", style=GRAY)
            if a:
                best.append(f" · we-don't-know {a.cost_mnats / 1000:.2f} nats · odds best : abstain = {a.odds_vs_best:.1f} : 1\n", style=GRAY)
        if inv.placebo and self.visible("placebos"):
            p = inv.placebo
            best.append(f"placebo  p = {p.p_emp:.3f} over {p.k} quiet days · false-explanation rate {p.fer:.2f}\n", style=INK)
        for h in inv.hypotheses if self.visible("verdicts") else []:
            best.append(f"{h.hid:<4}", style=CYAN)
            best.append(f"{VERDICT_SHORT.get(h.verdict_pre, h.verdict_pre):<20}", style=VERDICT_STYLE.get(h.verdict_pre, GRAY))
            best.append(f"{h.label[:60]}\n", style=INK)
        self.query_one("#ov_best", Static).update(best)

    def render_market(self) -> None:
        inv = self.inv
        box = self.query_one("#ov_mkt", Static)
        if self.world is None or inv.tau_star is None:
            box.update(Text("no price table", style=GRAY))
            return
        etf = {"SMH", "XLK", "XLU", "SPY", "QQQ"}
        syms = []
        for k in range(len(inv.clusters)):               # the strongest non-ETF member of each cluster, then one opening shock
            m = [i for i in inv.instruments if i.cluster == k and i.symbol not in etf and i.SAR is not None]
            if m:
                syms.append(min(m, key=lambda i: i.SAR).symbol)
        syms += [i.symbol for i in inv.instruments if i.secondary][:1]
        d0 = (inv.tau_star - timedelta(days=21)).strftime("%Y-%m-%d")
        d1 = (inv.tau_star + timedelta(days=3)).strftime("%Y-%m-%d")
        data = self.world.daily(syms, d0, d1)
        parts = []
        for s in syms:
            rows = data.get(s, [])
            if self.clock is not None:                # a daily bar exists only after its close
                rows = [r for r in rows if datetime.fromisoformat(r[0]).replace(tzinfo=timezone.utc, hour=21) <= self.clock]
            cs = [L.Candle(datetime.fromisoformat(r[0]).replace(tzinfo=timezone.utc), *r[1:]) for r in rows]
            head = Text(f"{s}  ", style=f"bold {INK}")
            if len(cs) >= 2:
                head.append(f"{cs[-1].c:,.2f}  {fmt_pct(cs[-1].c / cs[-2].c - 1)}", style=GREEN if cs[-1].c >= cs[-2].c else RED)
            parts += [head, candles(cs, max(30, box.size.width - 2), 5, marker=inv.tau_star.replace(hour=0, minute=0), label_fmt="%m-%d"), Text("")]
        parts.append(Text("daily bars only: Yahoo serves intraday for the last 60 days. τ* is the first abnormal print "
                          "(earlier when unsure); the trigger itself fires on the daily close.", style=GRAY))
        box.update(Group(*parts))

    def _nids(self) -> list[tuple[str, str]]:
        seen, out = set(), []
        for e in self.inv.explanations:
            for x in e.edges:
                for nid, lab in ((x.src, x.src_label), (x.dst, x.dst_label)):
                    if nid != "BOT" and not (nid.startswith("T") and nid[1:].isdigit()) and nid not in seen:
                        seen.add(nid)
                        out.append((nid, lab))
        return out

    def render_story(self) -> None:
        inv = self.inv
        box, feed = self.query_one("#st_att", Static), self.query_one("#st_feed", Static)
        nids = self._nids()
        if self.world is None or inv.tau_star is None or "e2b_series" not in self.world.have:
            box.update(Text("no recorded attention tables for this case" + (" (DEMO fixture: narratives are not in the replay tables)"
                                                                            if inv.source == "DEMO" else ""), style=GRAY))
            feed.update(Text(""))
            return
        t0, _ = replay_clock_range(inv)
        upto = self.clock or inv.tau_star
        att = self.world.attention([n for n, _ in nids], t0, min(upto, inv.detected or upto) + timedelta(minutes=15))
        width = max(30, box.size.width - 40)
        t = Text()
        n_windows = int((inv.tau_star - t0).total_seconds() // 900) + 1
        vmax = max([y for s in att.values() for _, y, _, _ in s] or [1.0])
        for nid, lab in nids:
            ser = att.get(nid, [])
            ys = {w: (y, b) for w, y, _, b in ser}
            w0 = self.world.window(t0)
            vals = [ys.get(w0 + k, (0.0, False))[0] for k in range(n_windows)]
            bursts = sum(1 for _, (_, b) in ys.items() if b)
            t.append(f"{short('N', nid)} ", style=CYAN)
            t.append(f"{lab[:28]:<28} ", style=INK)
            t.append(sparkline(vals, width, vmax), style=GREEN)
            t.append(f"  bursts {bursts}\n", style=AMBER if bursts else GRAY)
        t.append(f"{' ' * 38}{t0:%m-%d}{' ' * max(1, width - 10)}τ* {inv.tau_star:%m-%d %H:%M}\n", style=GRAY)
        t.append("attention y per 15-min window (Engine 2b); bursts = BOCPD on PIT residuals, new information entering through BOT", style=GRAY)
        box.update(t)
        items = self.world.feed(t0, upto, [n for n, _ in nids], limit=60)
        ft = Text()
        for f in items:
            late = inv.tau_star and f.t >= inv.tau_star
            ft.append(f"{fmt_t(f.t)} ", style=GRAY)
            ft.append("POST-τ* " if late else "PRE-τ*  ", style=AMBER if late else GREEN)
            ft.append(f"{f.source[:18]:<18} ", style=CYAN)
            ft.append(f"{f.title[:100]}\n", style=GRAY if late else INK)
        feed.update(ft or Text("no documents for these narratives before the clock", style=GRAY))

    def render_tree(self) -> None:
        if self._locked("tr_main", "search"):
            return
        inv = self.inv
        parts = []
        tab = Table(box=None, expand=True, header_style=f"bold {GRAY}")
        for c in ("#", "entry story", "cost (nats)", "odds vs best", "verdict P_pre", "verdict P_all"):
            tab.add_column(c)
        hv = {**{h.label: h for h in inv.hypotheses}, **{h.entry: h for h in inv.hypotheses if h.entry}}
        for e in sorted(inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
            h = hv.get(e.entry) or hv.get(e.entry_label)
            tab.add_row(str(e.rank) if e.rank else "0", Text(e.entry_label[:60], style=AMBER if e.rank == 0 else INK),
                        f"{e.cost_mnats / 1000:.2f}", odds_text(e.odds_vs_best),
                        Text(VERDICT_SHORT.get(h.verdict_pre, "—") if h else "—", style=VERDICT_STYLE.get(h.verdict_pre, GRAY) if h else GRAY),
                        Text(VERDICT_SHORT.get(h.verdict_all, "—") if h else "—", style=VERDICT_STYLE.get(h.verdict_all, GRAY) if h else GRAY))
        parts.append(tab)
        for e in inv.explanations:
            parts.append(Text(""))
            parts.append(explanation_tree(e, ("BEST" if e.rank == 1 else "WE DO NOT KNOW" if e.rank == 0 else f"RIVAL {e.rank}") +
                                          f" · {e.cost_mnats / 1000:.2f} nats"))
        parts.append(Text("\ncost = −log p + λ_node per edge (milli-nats); odds = exp(Δcost); rivals are the best tree through each "
                          "other entry story within 1:20; 'we do not know' is always shown. Edges mean timing, not cause.", style=GRAY))
        self.query_one("#tr_main", Static).update(Group(*parts))

    def render_evidence(self) -> None:
        if self._locked("ev_main", "claims"):
            return
        inv = self.inv
        box = self.query_one("#ev_main", Static)
        if not inv.hypotheses:
            box.update(Text("verdicts not run yet: no evidence", style=GRAY))
            return
        h = inv.hypotheses[self.hyp_i]
        box.border_title = f"EVIDENCE · {h.hid} {h.label[:60]}   (h: next hypothesis {self.hyp_i + 1}/{len(inv.hypotheses)})"
        n = {s: sum(1 for e in h.evidence if e.status == s) for s in ("PRE", "LATE", "POST", "UNMATCHED")}
        head = Text(f"{n['PRE']} admissible · {n['LATE'] + n['POST'] + n['UNMATCHED']} truth-only   ", style=INK)
        head.append("◆ diagnostic = removing it flips the verdict", style=AMBER)
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
        inv, p = self.inv, self.inv.placebo
        box = self.query_one("#pl_main", Static)
        if p is None:
            box.update(Text("placebos were not run for this case", style=GRAY))
            return
        b = inv.best
        t = Text()
        t.append(f"empirical p = (1 + #placebo explanations at least as cheap) / (1 + K) = {p.p_emp:.3f}   K = {p.k}\n", style=f"bold {INK}")
        t.append(f"false-explanation rate on quiet days = {p.fer:.2f}  (target ≤ 0.05)\n\n", style=INK)
        t.append(histogram(list(p.costs), b.cost_mnats if b else None))
        t.append("\n\nhub frequency (share of placebo explanations that use the narrative):\n", style=GRAY)
        for n, f in p.hubs[:8]:
            nid, _, lab = n.partition(" :: ")
            t.append(f"  {short('N', nid)} ", style=CYAN)
            t.append(f"{lab[:60]:<60} {100 * f:.0f}%", style=AMBER if f >= 0.3 else INK)
            t.append("  low diagnosticity\n" if f >= 0.3 else "\n", style=AMBER)
        box.update(t)

    def render_trace(self) -> None:
        if self._locked("sx_main", "queries"):
            return
        inv = self.inv
        t = Text()
        t.append("EXPLANATION SEARCH → TARGETED SEARCH → provider → EVIDENCE ARCHIVE → VERIFICATION\n", style=CYAN)
        t.append("one-way valve: pages fetched here never enter Engine 2 counts or fits\n\n", style=AMBER)
        if not inv.searches:
            t.append("no search operations recorded for this case\n", style=GRAY)
        for q in inv.searches:
            t.append(f"{short('Q', q.qid)}  target {q.hid}  provider {q.provider}  ", style=INK)
            t.append(q.status + "\n", style=RED if q.status == "UNAVAILABLE" else GREEN)
            t.append(f"  query  {q.query}\n", style=GRAY)
            if q.status != "UNAVAILABLE":
                t.append(f"  {q.results} results → {q.matched} canonical-URL matches (first_seen inherited) → {q.unmatched} unmatched (P_all only)\n", style=GRAY)
            if q.note:
                t.append(f"  {q.note}\n", style=GRAY)
        self.query_one("#sx_main", Static).update(t)

    def render_audit(self) -> None:
        inv = self.inv
        t = Text()
        rows = [("source", inv.source), ("cfg_hash", inv.cfg_hash or "—"), ("snapshot window", inv.snapshot or "—"),
                ("τ* rule", "earliest first abnormal print across the clusters; venue session start in replay; earlier when unsure"),
                ("detection", "daily close (replay trigger runs on daily bars)"),
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

        self.data_dir, self.cfg, self.demo = Path(data_dir), cfg, demo
        self.cfg_hash = cfg_hash(cfg)
        self.world = L.LiveWorld()
        self.quotes: dict = {}
        self.events: deque = deque(maxlen=200)
        self.seen_batches: set = set()
        self.serpapi = bool(os.environ.get("SERPAPI_API_KEY"))
        self._recorded = None
        from ygg.ui.graph_server import GraphServer

        self.graph = GraphServer(self.on_graph_select, port=int(os.environ.get("YGG_GRAPH_PORT", "8765")))

    def on_graph_select(self, nid: str) -> None:
        self.tape(f"GRAPH      selected {nid if nid == 'BOT' or nid.startswith('T') else short('N', nid)} in the graph window")
        scr = self.screen
        if isinstance(scr, InvestigationScreen):
            scr.graph_selected(nid)

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
            return "recorded replay finished"
        day = last.split()[1].rstrip(":")
        age = time.time() - p.stat().st_mtime
        return f"replay engine: processed through {day}" + (" (running)" if age < 1200 else " (stalled?)")

    async def on_mount(self) -> None:
        self.tape("START      control panel; world feed = latest served GDELT batch")
        try:
            await self.graph.start()
            self.tape(f"GRAPH      window at {self.graph.url} (open it next to the terminal)")
            import os
            import sys
            import threading
            import webbrowser

            gui = sys.platform in ("win32", "darwin") or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
            if gui and not os.environ.get("YGG_NO_BROWSER"):    # never launch a console browser into the terminal
                threading.Thread(target=lambda: webbrowser.open(self.graph.url, new=1), daemon=True).start()
        except OSError as e:
            self.tape(f"GRAPH      could not bind {self.graph.url}: {e}")
        self.push_screen(ControlPanel())


def run(data_dir: Path, cfg: dict, demo: bool = False) -> None:
    YggApp(data_dir, cfg, demo).run()
