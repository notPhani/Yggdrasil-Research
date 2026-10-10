"""Yggdrasil Terminal User Interface (TUI).

Rich-powered terminal dashboard for inspecting market event forensic cases:
1. Market Shock & Trigger Header (tau*, instruments, venues, volume anomalies)
2. Directed Steiner Explanation Tree (Narrative Arborescence, odds vs abstain, costs)
3. Corroborating Evidence & Source Grounding (Tiers, Pre/Post-cutoff integrity, quotes)
4. Four-bit verdicts (clingo, brave/cautious) and the verdict fingerprint (a content hash, not a proof)
5. Rival Competitor Breakdown
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.layout import Layout
from rich import box


class ForensicsTUI:
    def __init__(self, data_dir: Path | str, day: str = "2025-01-27", console: Console | None = None):
        self.data_dir = Path(data_dir)
        self.day = day
        self.console = console or Console()
        self.case_data = self._load_case()
        self.cert_data = self._load_certificates()

    def _load_case(self) -> dict[str, Any]:
        path = self.data_dir / "cases" / f"{self.day}.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_certificates(self) -> list[dict[str, Any]]:
        path = self.data_dir / "cases" / f"{self.day}_certificates.json"
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def render_header(self) -> Panel:
        c = self.case_data.get("case", {})
        day_str = c.get("day", self.day)
        tau_str = c.get("tau_star", "N/A")
        fired = c.get("fired", [])
        secondary = c.get("secondary", [])

        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=2)
        grid.add_column(justify="right", ratio=3)

        left_text = Text()
        left_text.append("SHOCK CUTOFF (tau*): ", style="bold cyan")
        left_text.append(f"{tau_str}\n", style="bold white")
        left_text.append("TRIGGERED CLUSTERS: ", style="bold cyan")
        left_text.append(f"{len(c.get('terminal_clusters', []))} Terminal Groups\n", style="white")
        left_text.append("SHOCKED INSTRUMENTS: ", style="bold cyan")
        left_text.append(f"{', '.join(fired[:8])}{'...' if len(fired) > 8 else ''}", style="bold yellow")

        right_text = Text()
        right_text.append("SYSTEM STATUS: ", style="bold green")
        right_text.append("FORENSIC DOSSIER COMPILED\n", style="bold white")
        right_text.append("CUTOFF RULE: ", style="dim")
        right_text.append("first_seen < tau* for P_pre (Session 0 rule 0.6)\n", style="dim italic")
        if secondary:
            right_text.append("SECONDARY SHOCKS: ", style="bold magenta")
            right_text.append(f"{', '.join(secondary[:6])}...", style="dim")

        grid.add_row(left_text, right_text)

        title = f"[bold white on blue] YGGDRASIL MARKET EVENT FORENSICS [/bold white on blue] [bold yellow]CASE: {day_str}[/bold yellow]"
        return Panel(grid, title=title, border_style="blue", box=box.ROUNDED)

    def render_tree(self) -> Panel:
        s = self.case_data.get("search", {})
        groups = s.get("groups", [])
        if not groups:
            return Panel("[yellow]No explanation tree available for this case.[/yellow]", title="Explanation Tree")

        best = groups[0].get("best", {})
        cost_mnats = best.get("cost_mnats", 0)
        cost_nats = cost_mnats / 1000.0
        abst_mnats = groups[0].get("abstention_cost_mnats", 0)
        abst_nats = abst_mnats / 1000.0
        odds = groups[0].get("odds_best_vs_abstain", 0.0)

        root_label = Text()
        root_label.append("[ROOT] BOT ", style="bold magenta")
        root_label.append(f"[Best Tree Cost: {cost_nats:.2f} nats | ", style="white")
        root_label.append(f"Abstention: {abst_nats:.2f} nats | ", style="dim")
        root_label.append(f"Odds: {odds:.2f} : 1 vs Abstain]", style="bold green")

        tree = Tree(root_label)

        # Parse tree edges
        tree_edges = best.get("tree", [])
        narratives_added = {}

        for edge in tree_edges:
            frm = edge.get("from", "")
            to = edge.get("to", "")
            p_val = edge.get("p", 0.0)
            cost = edge.get("cost_mnats", 0)

            if frm == "BOT":
                # Narrative node
                parts = to.split(" :: ", 1)
                nid = parts[0]
                label = parts[1] if len(parts) > 1 else nid
                n_text = Text()
                n_text.append("[NARR] ", style="bold yellow")
                n_text.append(f"[{nid[:8]}] ", style="dim yellow")
                n_text.append(f'"{label}" ', style="bold white")
                n_text.append(f"(p={p_val:.3f}, cost={cost} mnats)", style="dim cyan")
                node = tree.add(n_text)
                narratives_added[to] = node
            elif frm in narratives_added:
                # Terminal cluster edge
                parent_node = narratives_added[frm]
                term_text = Text()
                term_text.append("[TERM] ", style="bold green")
                term_text.append(f"{to} ", style="bold white")
                term_text.append(f"(p={p_val:.3f}, edge cost={cost} mnats)", style="dim")
                parent_node.add(term_text)

        # Add Abstention comparison node
        abst_text = Text()
        abst_text.append("[ABST] ABSTENTION BASELINE: ", style="bold red")
        abst_text.append(f"{abst_nats:.2f} nats ", style="red")
        abst_text.append(f"(Defeated by {odds:.2f}x odds advantage)", style="dim italic")
        tree.add(abst_text)

        return Panel(tree, title="[bold cyan]Steiner Explanation Arborescence (Dreyfus-Wagner DPBF)[/bold cyan]",
                     border_style="cyan", box=box.ROUNDED)

    def render_rivals(self) -> Panel:
        s = self.case_data.get("search", {})
        groups = s.get("groups", [])
        if not groups:
            return Panel("[yellow]No rival data available.[/yellow]", title="Rival Explanations")

        rivals = groups[0].get("rivals", [])
        table = Table(box=box.SIMPLE_HEAVY, expand=True)
        table.add_column("Rank", style="bold cyan", width=6)
        table.add_column("Rival Entry Narrative", style="white")
        table.add_column("Cost (nats)", justify="right", style="yellow", width=12)
        table.add_column("Odds vs Best", justify="right", style="bold red", width=14)

        for i, r in enumerate(rivals[:5]):
            rank_str = "#1 (Best)" if i == 0 else f"#{i + 1}"
            entry = r.get("entry", "N/A")
            parts = entry.split(" :: ", 1)
            title = parts[1] if len(parts) > 1 else parts[0]
            cost = r.get("cost_mnats", 0) / 1000.0
            odds = r.get("odds_vs_best", 1.0)
            odds_str = "1.00 : 1" if i == 0 else f"{odds:.2f} : 1 against"
            
            row_style = "bold white" if i == 0 else "dim"
            table.add_row(rank_str, Text(title[:75], style=row_style), f"{cost:.2f}", odds_str)

        return Panel(table, title="[bold magenta]Competing Hypotheses (Rivals / Lemma 11.2)[/bold magenta]",
                     border_style="magenta", box=box.ROUNDED)

    def render_evidence(self) -> Panel:
        v = self.case_data.get("verdicts", {})
        hyps = v.get("hypotheses", [])
        if not hyps:
            return Panel("[yellow]No evidence reports compiled.[/yellow]", title="Corroborating Evidence")

        table = Table(box=box.SIMPLE_HEAVY, expand=True)
        table.add_column("Tier", justify="center", width=8)
        table.add_column("Source", style="bold cyan", width=18)
        table.add_column("Timing", justify="center", width=14)
        table.add_column("Evidence Title / Wire Dispatch", style="white")

        count = 0
        for h in hyps[:2]:
            for r in h.get("reports", [])[:5]:
                tier_val = r.get("tier", 3)
                if tier_val == 0:
                    tier_badge = Text("T0 OWN", style="bold cyan")           # Yggdrasil's own measurements
                elif tier_val == 1:
                    tier_badge = Text("T1 PRIMARY", style="bold green on black")   # the actor: filing, paper, statement
                elif tier_val == 2:
                    tier_badge = Text("T2 WIRE", style="bold yellow on black")     # wire services and national outlets
                else:
                    tier_badge = Text("T3 LOCAL", style="dim")                     # local, aggregators, blogs, unknown

                is_pre = r.get("pre", True)
                time_badge = Text("PRE-tau* OK", style="bold green") if is_pre else Text("POST-tau*", style="red")
                
                src = r.get("source", "unknown")
                title = r.get("title", "Untitled")
                table.add_row(tier_badge, src, time_badge, Text(title[:80], style="white"))
                count += 1

        return Panel(table, title="[bold green]Corroborating Evidence & Source Integrity (Tiers & Cutoff Filter)[/bold green]",
                     border_style="green", box=box.ROUNDED)

    def render_verdicts(self) -> Panel:
        v = self.case_data.get("verdicts", {})
        hyps = v.get("hypotheses", [])
        p_pre = v.get("P_pre", {}).get("verdicts", {})
        p_all = v.get("P_all", {}).get("verdicts", {})

        table = Table(box=box.SIMPLE_HEAVY, expand=True)
        table.add_column("Hypothesis", style="bold white", ratio=3)
        table.add_column("Before tau* (P_pre)", justify="center", width=22)
        table.add_column("At Report (P_all)", justify="center", width=20)
        table.add_column("Signature", justify="center", width=18)

        for h in hyps:
            hid = h.get("hid", "")
            label = h.get("label", hid)
            vp = p_pre.get(hid, "UNRESOLVED")
            va = p_all.get(hid, "UNRESOLVED")

            def style_verdict(v_str: str) -> Text:
                if v_str == "SUPPORTED":
                    return Text("[OK] SUPPORTED", style="bold green")
                elif v_str == "CONSISTENT-BUT-UNPROVEN":
                    return Text("[~] CONSISTENT", style="bold yellow")
                elif v_str == "CONTRADICTED":
                    return Text("[X] CONTRADICTED", style="bold red")
                return Text("[-] UNRESOLVED", style="dim")

            sig_ok = h.get("signature_ok", False)
            burst = h.get("burst", False)
            sig_str = "Burst + Surprisal" if sig_ok else ("Burst" if burst else "None")
            sig_style = "bold green" if sig_ok else ("yellow" if burst else "dim")

            table.add_row(
                Text(label[:55], style="white"),
                style_verdict(vp),
                style_verdict(va),
                Text(sig_str, style=sig_style)
            )

        cert_panel_content = table
        cert_info = ""
        if self.cert_data:
            cert = self.cert_data[0]
            cert_id = cert.get("certificate_id", "N/A")
            cert_hash = cert.get("inputs_hash", "N/A")
            cert_info = f"\n[dim]Verdict fingerprint (sha256 of day, tau*, hypothesis, verdict, consequences; not a proof): [/dim][bold cyan]{cert_id}[/bold cyan] [dim]{cert_hash[:24]}...[/dim]"

        return Panel(
            Group(table, Text.from_markup(cert_info) if cert_info else Text("")),
            title="[bold yellow]Formal Logic Program Verdicts (Clingo ASP 4-Bit Resolution)[/bold yellow]",
            border_style="yellow", box=box.ROUNDED
        )

    def render_full_dashboard(self) -> None:
        """Renders the complete forensic dossier view."""
        self.console.print(self.render_header())
        self.console.print(self.render_tree())
        self.console.print(self.render_rivals())
        self.console.print(self.render_evidence())
        self.console.print(self.render_verdicts())
        self.console.print("[dim italic center]_Yggdrasil never forecasts prices and never recommends trades. Edges are timing, not cause._[/dim italic center]\n")
