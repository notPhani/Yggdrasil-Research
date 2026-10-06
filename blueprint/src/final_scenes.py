"""New Manim scenes for the Yggdrasil Blueprint (Manim CE 0.20, Pango text, no LaTeX)."""
import numpy as np
from manim import *

BG = "#10151b"; FONT = "Noto Sans"; MONO = "DejaVu Sans Mono"
INK = "#e9edf0"; DIM = "#8a949c"; GRID = "#2a333b"
YEL = "#f4d35e"; BLU = "#58c4dd"; GRN = "#83c167"; RED = "#fc6255"; ORA = "#ff9b54"; VIO = "#b09cff"


def T(s, size=24, color=INK, font=FONT):
    return Text(s, font=font, font_size=size, color=color)


def M(s, size=16, color=INK):
    return Text(s, font=MONO, font_size=size, color=color)


def card(label, pos, color=DIM, w=3.3, size=13):
    t = T(label, size, color)
    box = RoundedRectangle(corner_radius=0.08, width=w, height=t.height + 0.22, stroke_color=color,
                           stroke_width=1.8, fill_color=BG, fill_opacity=1)
    t.move_to(box)
    return VGroup(box, t).move_to(pos)


class Base(Scene):
    def setup(self):
        self.camera.background_color = BG

    def title(self, s, size=28):
        return T(s, size).to_edge(UP, buff=0.35)

    def bottom(self, s, size=17, color=DIM):
        return T(s, size, color).to_edge(DOWN, buff=0.3)


# --------------------------------------------------------------------------------------------
class DedupCascade(Base):
    def construct(self):
        ttl = self.title("Semantic dedup: four steps, cheapest first")
        self.play(FadeIn(ttl))
        sites = ["wiltsglosstandard", "fenlandcitizen", "dudleynews", "timesandstar", "messengernews", "richmondtimes"]
        wire = VGroup(*[card(f"London City Airport seeks leisure growth...  ({s})", [-3.6, 2.3 - 0.42 * i, 0], DIM, 6.0) for i, s in enumerate(sites)])
        more = T("... and 9 more papers (15 copies, one PA wire story)", 14, DIM).next_to(wire, DOWN, buff=0.1)
        tmpl = VGroup(*[card(f"Gearing announcement | company announcement  (filing {k})", [3.6, 2.3 - 0.42 * i, 0], DIM, 6.0) for i, k in enumerate(["A", "B", "C"])])
        tmore = T("x14 from one site, all different filings", 14, DIM).next_to(tmpl, DOWN, buff=0.1)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in wire], lag_ratio=0.1), FadeIn(more),
                  LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in tmpl], lag_ratio=0.15), FadeIn(tmore), run_time=1.6)
        steps = VGroup(
            T("1  free GKG signals: same title AND (same image OR author OR names overlap)", 16, YEL),
            T("2  fetch first 32 KB: same rel=canonical / og:url, else lede shingles", 16, BLU),
            T("3  full body: MinHash Jaccard >= 0.8 or SimHash distance <= 3", 16, GRN),
            T("4  page won't load: fall back to step 1's checks (option A)", 16, ORA)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        steps.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(steps[0]), run_time=0.6)
        obj = card("1 object  ·  member_count = 15", [-3.6, 0.9, 0], YEL, 6.0, 15)
        self.play(*[Transform(c, obj.copy()) for c in wire], FadeOut(more), run_time=1.3)
        flag = T("same title, but names disjoint -> not merged here", 14, RED).next_to(tmpl, DOWN, buff=0.45)
        self.play(FadeOut(tmore), FadeIn(flag), run_time=0.6)
        self.play(FadeIn(steps[1]), run_time=0.6)
        canon = VGroup(*[T(f"canonical: investegate.co.uk/.../{k}", 12, BLU).next_to(c, RIGHT, buff=0.08).shift(LEFT * 2.2 + DOWN * 0.0) for c, k in zip(tmpl, ["8812", "8813", "8817"])])
        self.play(*[c[0].animate.set_stroke(BLU) for c in tmpl], run_time=0.6)
        keep = T("different canonical URLs and ledes -> 3 separate objects (no false merge)", 14, BLU).move_to(flag)
        self.play(Transform(flag, keep), run_time=0.7)
        self.play(FadeIn(steps[2]), FadeIn(steps[3]), run_time=0.8)
        note = T("Never merged: Reuters and Bloomberg each writing their own story (that is attention, L3)", 15, INK).next_to(steps, UP, buff=0.2)
        self.play(FadeIn(note))
        self.wait(3)


# --------------------------------------------------------------------------------------------
class TriggerClusters(Base):
    def construct(self):
        ttl = self.title("27 Jan 2025: which stocks were abnormal, and which moved together  (real data)", 24)
        self.play(FadeIn(ttl))
        names = ["NVDA", "AVGO", "TSM", "MU", "AMD", "MSFT", "VST", "CEG", "NRG", "TLN"]
        ms = {"NVDA": -2.3, "AVGO": -2.7, "TSM": -2.2, "MU": -0.2, "AMD": 1.6, "MSFT": 0.6, "VST": -7.6, "CEG": -5.5, "NRG": -5.1, "TLN": -7.1}
        mo = {"NVDA": -5.1, "AVGO": -5.0, "TSM": -5.0, "MU": -3.0, "AMD": -1.2, "MSFT": -0.5, "VST": -7.8, "CEG": -5.9, "NRG": -5.5, "TLN": -7.4}
        x0, x1, v0, v1 = -6.0, -0.6, -9.0, 3.0
        X = lambda v: x0 + (v - v0) / (v1 - v0) * (x1 - x0)
        ys = [2.25 - 0.42 * i for i in range(len(names))]
        axis = Line([x0, -2.15, 0], [x1, -2.15, 0], color=DIM, stroke_width=2)
        ticks = VGroup(*[T(str(v), 13, DIM).move_to([X(v), -2.4, 0]) for v in (-8, -4, 0)])
        thr = DashedLine([X(-4), 2.55, 0], [X(-4), -2.15, 0], color=RED, dash_length=0.08)
        thl = T("fires below -4", 13, RED).next_to(thr, UP, buff=0.05)
        labs = VGroup(*[T(n, 15, INK).move_to([x0 - 0.45, y, 0]) for n, y in zip(names, ys)])
        cap = T("SAR, market + sector model", 15, DIM).move_to([X(-3), -2.75, 0])
        dots = VGroup(*[Dot([X(ms[n]), y, 0], radius=0.09, color=DIM) for n, y in zip(names, ys)])
        self.play(Create(axis), FadeIn(ticks), FadeIn(labs), Create(thr), FadeIn(thl), FadeIn(cap), LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.05), run_time=1.6)
        bug = T("the sector ETF crashed too, so chips look normal", 15, RED).move_to([X(-3), 2.85, 0]).shift(DOWN * 0.0)
        self.play(FadeIn(bug), run_time=0.6)
        self.wait(0.8)
        cap2 = T("SAR, market-only model (locked)", 15, YEL).move_to(cap)
        self.play(*[d.animate.move_to([X(mo[n]), y, 0]).set_color(YEL if mo[n] <= -4 else DIM) for d, n, y in zip(dots, names, ys)],
                  Transform(cap, cap2), FadeOut(bug), run_time=1.4)
        self.wait(0.8)
        # residual-correlation clusters
        P = {"SMH": (2.2, 1.6), "XLK": (3.6, 2.2), "NVDA": (1.6, 0.4), "AVGO": (3.0, 0.6), "TSM": (4.2, 1.1),
             "VST": (2.0, -1.0), "CEG": (3.4, -0.6), "NRG": (2.4, -2.1), "TLN": (4.0, -1.7)}
        nodes = {k: VGroup(Circle(radius=0.3, color=(BLU if k in ("SMH", "XLK", "NVDA", "AVGO", "TSM") else ORA), stroke_width=2.5,
                                  fill_color=BG, fill_opacity=1), T(k, 12, INK)).move_to([x, y, 0]) for k, (x, y) in P.items()}
        E = [("SMH", "XLK", .79), ("SMH", "NVDA", .73), ("SMH", "AVGO", .59), ("SMH", "TSM", .72), ("XLK", "NVDA", .62), ("XLK", "AVGO", .52),
             ("XLK", "TSM", .54), ("NVDA", "TSM", .42), ("AVGO", "TSM", .44), ("VST", "CEG", .73), ("VST", "NRG", .69), ("VST", "TLN", .58),
             ("CEG", "NRG", .53), ("CEG", "TLN", .52), ("NRG", "TLN", .41)]
        lines = VGroup(*[Line(nodes[a].get_center(), nodes[b].get_center(), color=GRID, stroke_width=1.5 + 4 * (c - 0.4)) for a, b, c in E])
        h2 = T("residual correlation >= 0.4, same sign", 15, INK).move_to([3.0, 2.85, 0])
        self.play(FadeIn(h2), *[FadeIn(n) for n in nodes.values()], run_time=0.8)
        self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.05), run_time=1.2)
        self.bring_to_front(*nodes.values())
        cross = T("chips vs power: 0.02 - 0.21  (no link in market history)", 14, DIM).move_to([3.0, -2.75, 0])
        self.play(FadeIn(cross), run_time=0.6)
        k = T("one search terminal per cluster: k = 2, so the DP's 3^k is 9, not 19,683", 16, YEL).to_edge(DOWN, buff=0.25)
        self.play(FadeOut(cross), FadeIn(k), run_time=0.7)
        self.wait(3)


# --------------------------------------------------------------------------------------------
class ThreeLevels(Base):
    def construct(self):
        ttl = self.title("Grouping: one rule, three timescales  (content only, no attention feedback)", 24)
        self.play(FadeIn(ttl))
        axis = Arrow([-6.3, -2.6, 0], [6.3, -2.6, 0], color=DIM, stroke_width=2, buff=0, tip_length=0.15)
        tl = T("time", 14, DIM).next_to(axis, DOWN, buff=0.05).align_to(axis, RIGHT)
        self.play(Create(axis), FadeIn(tl), run_time=0.6)
        rng = np.random.default_rng(3)
        groups = [(-4.6, -1.6, BLU), (-2.0, -1.4, BLU), (0.8, -1.7, GRN), (3.4, -1.5, ORA), (5.2, -1.6, VIO)]
        dots, evs = VGroup(), VGroup()
        for gx, gy, c in groups:
            pts = [np.array([gx + rng.normal(0, 0.35), gy + rng.normal(0, 0.25), 0]) for _ in range(6)]
            ds = VGroup(*[Dot(p, radius=0.05, color=c) for p in pts]); dots.add(ds)
            evs.add(Circle(radius=0.55, color=c, stroke_width=2).move_to([gx, gy, 0]))
        l1 = T("objects -> event clusters  (freshness 72 h)", 15, INK).move_to([-3.4, -3.0, 0])
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for g in dots for d in g], lag_ratio=0.01), run_time=1.2)
        self.play(*[Create(e) for e in evs], FadeIn(l1), run_time=1.0)
        narr = {"AI models": ((-3.3, 1.0), BLU), "chips": ((0.8, 1.0), GRN), "power": ((3.4, 1.0), ORA), "macro": ((5.4, 1.0), VIO)}
        nb = {k: VGroup(Ellipse(width=2.2, height=0.9, color=c, stroke_width=2.5, fill_color=c, fill_opacity=0.12), T(k, 15, c)).move_to([x, y, 0])
              for k, ((x, y), c) in narr.items()}
        links = VGroup(*[Line(evs[i].get_top(), nb[n][0].get_bottom(), color=GRID, stroke_width=1.5) for i, n in
                         [(0, "AI models"), (1, "AI models"), (2, "chips"), (3, "power"), (4, "macro")]])
        l2 = T("event clusters -> narratives  (persistent IDs, freshness 14 days)", 15, INK).move_to([1.6, -0.3, 0])
        l2 = VGroup(BackgroundRectangle(l2, color=BG, fill_opacity=1, buff=0.06), l2)
        self.play(*[FadeIn(b) for b in nb.values()], Create(links), FadeIn(l2), run_time=1.2)
        self.wait(0.6)
        a1 = VGroup(Ellipse(width=1.6, height=0.75, color=BLU, stroke_width=2.5, fill_color=BLU, fill_opacity=0.12), T("AI models", 13, BLU)).move_to([-4.3, 1.0, 0])
        a2 = VGroup(Ellipse(width=1.6, height=0.75, color="#3d8fa6", stroke_width=2.5, fill_color="#3d8fa6", fill_opacity=0.12), T("AI apps", 13, "#3d8fa6")).move_to([-2.4, 1.0, 0])
        split = T("split after 3 agreeing checks; memory shared out: z[c] = q[c] * z[N]", 14, BLU).move_to([-3.2, 1.75, 0])
        self.play(ReplacementTransform(nb["AI models"], VGroup(a1, a2)), FadeIn(split), run_time=1.2)
        self.wait(0.6)
        halo = RoundedRectangle(corner_radius=0.4, width=9.4, height=1.6, color=YEL, stroke_width=2.5).move_to([-0.5, 1.0, 0])
        hl = T("phenomenon: AI boom  (daily Leiden communities, 7-check hysteresis, persistent)", 15, YEL).move_to([-0.5, 2.25, 0])
        self.play(FadeOut(split), Create(halo), FadeIn(hl), run_time=1.2)
        rule = T("2a never reads 2b: grouping decides by content; attention is computed afterwards", 16, INK).move_to([0, 3.15, 0]).shift(DOWN * 0.45)
        rule = VGroup(BackgroundRectangle(rule, color=BG, fill_opacity=1, buff=0.05), rule)
        self.play(FadeIn(rule))
        self.wait(3)


# --------------------------------------------------------------------------------------------
class HubPlacebo(Base):
    def construct(self):
        ttl = self.title("Hub bias, and how placebos expose it  (toy numbers)", 26)
        self.play(FadeIn(ttl))
        P = {"BOT": (-4.6, 2.2), "Politics": (-4.6, 0.6), "R1 release": (-2.2, 0.6), "chips": (-4.6, -1.4), "power": (-2.2, -1.4)}
        col = {"BOT": YEL, "Politics": INK, "R1 release": INK, "chips": RED, "power": RED}
        nodes = {k: VGroup(RoundedRectangle(corner_radius=0.1, width=1.8, height=0.5, color=col[k], stroke_width=2, fill_color=BG, fill_opacity=1),
                           T(k, 14, col[k])).move_to([x, y, 0]) for k, (x, y) in P.items()}
        nodes["Politics"][0].set_stroke(width=5)
        def ln(a, b, c=DIM, w=2):
            pa, pb = nodes[a].get_center(), nodes[b].get_center(); d = (pb - pa) / np.linalg.norm(pb - pa)
            return Arrow(pa + d * 0.35, pb - d * 0.35, buff=0, stroke_width=w, color=c, tip_length=0.12)
        E = {("BOT", "Politics"): ln("BOT", "Politics"), ("BOT", "R1 release"): ln("BOT", "R1 release"),
             ("Politics", "chips"): ln("Politics", "chips"), ("Politics", "power"): ln("Politics", "power"),
             ("R1 release", "chips"): ln("R1 release", "chips"), ("R1 release", "power"): ln("R1 release", "power")}
        self.play(*[FadeIn(n) for n in nodes.values()], *[GrowArrow(e) for e in E.values()], run_time=1.0)
        raw = T("raw scoring: the loudest narrative\ntouches everything -> cheapest trunk", 14, ORA).move_to([-3.4, -2.5, 0])
        self.play(FadeIn(raw), *[E[k].animate.set_color(ORA).set_stroke(width=4) for k in [("BOT", "Politics"), ("Politics", "chips"), ("Politics", "power")]], run_time=1.0)
        self.wait(0.8)
        fix = VGroup(T("lift: Politics mentions every company -> lift ~ 1", 13, INK),
                     T("surprise: R1's spillover jumped before the cutoff;", 13, INK),
                     T("Politics' was the same as any other day", 13, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.06).move_to([-3.4, -2.55, 0])
        self.play(FadeOut(raw), FadeIn(fix), *[E[k].animate.set_color(GRID).set_stroke(width=2) for k in [("BOT", "Politics"), ("Politics", "chips"), ("Politics", "power")]],
                  *[E[k].animate.set_color(YEL).set_stroke(width=4) for k in [("BOT", "R1 release"), ("R1 release", "chips"), ("R1 release", "power")]], run_time=1.2)
        self.bring_to_front(*nodes.values())
        self.wait(0.8)
        # placebo histogram
        rng = np.random.default_rng(5)
        costs = np.clip(rng.normal(9.0, 0.9, 20), 7.0, 11.5)
        hx0, hx1, c0, c1 = 0.6, 6.4, 5.0, 12.0
        HX = lambda c: hx0 + (c - c0) / (c1 - c0) * (hx1 - hx0)
        ax = Line([hx0, -1.6, 0], [hx1, -1.6, 0], color=DIM, stroke_width=2)
        bins = np.arange(7.0, 11.6, 0.5); counts, _ = np.histogram(costs, bins=bins)
        bars = VGroup(*[Rectangle(width=(hx1 - hx0) / (c1 - c0) * 0.5 - 0.04, height=0.32 * n, stroke_width=0, fill_color=DIM, fill_opacity=0.8)
                        .move_to([HX(b + 0.25), -1.6 + 0.16 * n, 0]) for b, n in zip(bins[:-1], counts) if n > 0])
        hl = T("best explanation cost on 20 placebo days (nothing happened)", 14, DIM).move_to([3.5, 1.6, 0])
        tk = VGroup(*[T(str(v), 12, DIM).move_to([HX(v), -1.85, 0]) for v in (6, 8, 10, 12)])
        self.play(Create(ax), FadeIn(tk), FadeIn(hl), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.05), run_time=1.2)
        real = Line([HX(5.6), -1.6, 0], [HX(5.6), 0.9, 0], color=YEL, stroke_width=4)
        rl = T("real case: 5.6", 14, YEL).next_to(real, UP, buff=0.05)
        self.play(Create(real), FadeIn(rl), run_time=0.8)
        pv = VGroup(T("empirical p = (1 + #placebos <= real) / (1 + K) = 1/21", 13, YEL),
                    T("tune p0, λ_node, γ until placebo days get", 13, INK),
                    T("'we do not know' at least 95% of the time", 13, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.06).move_to([3.5, -2.55, 0])
        self.play(FadeIn(pv))
        self.wait(3)


# --------------------------------------------------------------------------------------------
class Readings(Base):
    def construct(self):
        ttl = self.title("Verdicts: every consistent reading of the evidence  (verified with clingo)", 24)
        self.play(FadeIn(ttl))
        facts = VGroup(*[M(s, 13, c) for s, c in [
            ("arxiv_v3 (tier 1): costs exclude prior research", GRN), ("outlet_a (tier 2): $5.6M was the all-in cost", DIM),
            ("outlet_b (tier 2): DeepSeek smuggled chips", DIM), ("outlet_c (tier 2): no diversion happened", DIM),
            ("ygg (tier 0): R1 burst Jan 20, app surge Jan 26", YEL)]]).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([-3.4, 1.7, 0])
        self.play(LaggedStart(*[FadeIn(f) for f in facts], lag_ratio=0.15), run_time=1.2)
        rules = T("a report is believed unless an independent contrary report of equal or better tier overrides it", 14, INK).move_to([0, 0.45, 0])
        self.play(FadeIn(rules), run_time=0.6)
        w1 = VGroup(RoundedRectangle(corner_radius=0.12, width=3.3, height=1.3, color=BLU, stroke_width=2.5),
                    T("reading 1\nsmuggling accepted\nexpl(h4)  refuted(h3)", 14, BLU))
        w2 = VGroup(RoundedRectangle(corner_radius=0.12, width=3.3, height=1.3, color=ORA, stroke_width=2.5),
                    T("reading 2\ndenial accepted\nrefuted(h4)  refuted(h3)", 14, ORA))
        for w in (w1, w2): w[1].move_to(w[0])
        worlds = VGroup(w1, w2).arrange(RIGHT, buff=0.4).move_to([3.4, 1.7, 0])
        self.play(FadeIn(worlds), run_time=0.8)
        hdr = ["", "bIN", "cIN", "bOUT", "cOUT", "verdict"]
        rows = [("h1 R1 efficiency shock", "0", "0", "0", "0", ("CONSISTENT-BUT-UNPROVEN", BLU)),
                ("h3 $5.6M all-in cost", "0", "0", "1", "1", ("CONTRADICTED", RED)),
                ("h4 chip smuggling", "1", "0", "1", "0", ("UNRESOLVED", ORA)),
                ("h6 attention cascade", "1", "1", "0", "0", ("SUPPORTED", GRN))]
        xs = [-4.4, -1.4, -0.6, 0.2, 1.0, 3.6]
        tbl = VGroup(*[T(h, 13, DIM).move_to([xs[c], -0.35, 0]) for c, h in enumerate(hdr)])
        for r, row in enumerate(rows):
            y = -0.8 - r * 0.42
            for c, cell in enumerate(row):
                if c == 5: tbl.add(T(cell[0], 14, cell[1]).move_to([xs[c], y, 0]))
                elif c == 0: tbl.add(T(cell, 14, INK).move_to([xs[c], y, 0]).align_to(np.array([-6.2, 0, 0]), LEFT))
                else: tbl.add(T(cell, 14, INK).move_to([xs[c], y, 0]))
        self.play(LaggedStart(*[FadeIn(m) for m in tbl], lag_ratio=0.02), run_time=1.4)
        foot = T("b = in some reading, c = in every reading.  No reading at all (odd attack cycle) -> INCOHERENT-EVIDENCE", 15, DIM).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(foot))
        self.wait(3)
