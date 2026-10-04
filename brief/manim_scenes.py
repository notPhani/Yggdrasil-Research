"""Manim scenes for the Yggdrasil research brief (Manim CE 0.20, no LaTeX: Pango text only)."""
import numpy as np
from manim import *

BG = "#10151b"
FONT = "Noto Sans"
INK = "#e9edf0"
DIM = "#8a949c"
GRID = "#2a333b"
YEL = "#f4d35e"   # exogenous / BOT
BLU = "#58c4dd"   # narrative A
GRN = "#83c167"   # self-excitation
RED = "#fc6255"
ORA = "#ff9b54"
VIO = "#b09cff"


def T(s, size=28, color=INK, **kw):
    return Text(s, font=FONT, font_size=size, color=color, **kw)


class Base(Scene):
    def setup(self):
        self.camera.background_color = BG

    def caption(self, s, size=30, color=INK):
        c = T(s, size, color).to_edge(UP, buff=0.4)
        return c


# --------------------------------------------------------------------------------------------
class HawkesBumps(Base):
    def construct(self):
        mu, n, beta = 0.45, 0.6, 1.3
        events = [1.0, 1.55, 1.85, 4.6, 4.95, 5.2, 8.2]

        def lam(t):
            return mu + sum(n * beta * np.exp(-beta * (t - e)) for e in events if e < t)

        title = self.caption("Every event adds a bump to the rate, and the bump fades")
        axes = Axes(x_range=[0, 10, 1], y_range=[0, 2.6, 0.5], x_length=10.4, y_length=3.9,
                    axis_config={"color": DIM, "stroke_width": 2, "include_ticks": False}, tips=False).shift(UP * 0.15 + LEFT * 0.5)
        xl = T("time", 22, DIM).next_to(axes.x_axis, DOWN, buff=0.15).align_to(axes.x_axis, RIGHT)
        yl = T("rate", 22, DIM).next_to(axes.y_axis, UP, buff=0.12)
        base = DashedLine(axes.c2p(0, mu), axes.c2p(10, mu), color=DIM, dash_length=0.12)
        bl = VGroup(T("baseline μ", 20, DIM), T("(outside news)", 16, DIM)).arrange(DOWN, buff=0.04).next_to(base, RIGHT, buff=0.15)
        self.play(FadeIn(title), Create(axes), FadeIn(xl), FadeIn(yl), run_time=1.2)
        self.play(Create(base), FadeIn(bl), run_time=0.8)

        tr = ValueTracker(0.001)

        def curve():
            tt = tr.get_value()
            pts = [0.0] + [e for e in events if e < tt] + [tt]
            g = VGroup()
            for a, b in zip(pts[:-1], pts[1:]):
                if b - a < 1e-4:
                    continue
                xs = np.linspace(a + 1e-5, b, max(2, int((b - a) * 40)))
                g.add(VMobject(color=YEL, stroke_width=4).set_points_as_corners([axes.c2p(x, lam(x)) for x in xs]))
            for e in events:
                if e < tt:
                    g.add(Line(axes.c2p(e, lam(e - 1e-6)), axes.c2p(e, lam(e + 1e-6)), color=YEL, stroke_width=4))
            return g

        def ticks():
            tt = tr.get_value()
            return VGroup(*[Line(axes.c2p(e, -0.12), axes.c2p(e, 0.12), color=ORA, stroke_width=5)
                            for e in events if e < tt])

        def dot():
            tt = tr.get_value()
            return Dot(axes.c2p(tt, lam(tt)), color=YEL, radius=0.07)

        cv, tk, dt = always_redraw(curve), always_redraw(ticks), always_redraw(dot)
        el = T("events", 20, ORA).next_to(axes.c2p(0, 0), LEFT, buff=0.2)
        self.add(cv, tk, dt)
        self.play(FadeIn(el), run_time=0.3)
        self.play(tr.animate.set_value(10), run_time=8, rate_func=linear)
        self.remove(dt)
        self.wait(0.3)

        # decomposition: each bump on its own
        bumps = VGroup()
        cols = [BLU, GRN, VIO]
        for e, c in zip(events[:3], cols):
            xs = np.linspace(e, 10, 200)
            bumps.add(VMobject(color=c, stroke_width=3).set_points_as_corners(
                [axes.c2p(x, mu + n * beta * np.exp(-beta * (x - e))) for x in xs]))
        cap2 = self.caption("The rate is the baseline plus the sum of every fading bump", 28)
        self.play(Transform(title, cap2), LaggedStart(*[Create(b) for b in bumps], lag_ratio=0.4), run_time=2)
        formula = T("λ(t) = μ + Σ  n·β·exp(−β·(t − tₖ))     over past events tₖ", 26, INK).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(formula, shift=UP * 0.2), run_time=1)
        note = T("n = area of one bump = average number of follow-on events", 22, DIM).next_to(formula, UP, buff=0.14)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(2.5)


# --------------------------------------------------------------------------------------------
class BranchingTree(Base):
    def draw_tree(self, nodes, edges, origin, sx, sy):
        pos = {k: origin + np.array([x * sx, -g * sy, 0]) for k, (x, g) in nodes.items()}
        dots = {k: Dot(pos[k], radius=0.09, color=(YEL if nodes[k][1] == 0 else BLU)) for k in nodes}
        arrows = [Arrow(pos[a], pos[b], buff=0.1, stroke_width=3, color=DIM,
                        max_tip_length_to_length_ratio=0.18, tip_length=0.14) for a, b in edges]
        return pos, dots, arrows

    def grow(self, nodes, edges, dots, arrows, run=0.6):
        gens = sorted(set(g for _, g in nodes.values()))
        for g in gens:
            ks = [k for k in nodes if nodes[k][1] == g]
            anims = [FadeIn(dots[k], scale=0.5) for k in ks]
            anims += [GrowArrow(arrows[i]) for i, (a, b) in enumerate(edges) if nodes[b][1] == g]
            self.play(LaggedStart(*anims, lag_ratio=0.08), run_time=run)

    def construct(self):
        title = self.caption("The same process, drawn as a family tree")
        self.play(FadeIn(title))
        leg = VGroup(
            VGroup(Dot(color=YEL, radius=0.09), T("immigrant: arrives from outside (news)", 20, INK)).arrange(RIGHT, buff=0.15),
            VGroup(Dot(color=BLU, radius=0.09), T("child: a reaction to an earlier event", 20, INK)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).to_corner(UL, buff=0.5).shift(DOWN * 0.7)
        self.play(FadeIn(leg))

        # n = 0.6: four immigrants, every cascade dies out
        nodes = {"a": (0.0, 0), "a1": (0.6, 1), "a2": (1.3, 1), "a11": (1.1, 2),
                 "b": (2.6, 0),
                 "c": (4.0, 0), "c1": (4.7, 1),
                 "d": (6.0, 0), "d1": (6.5, 1), "d11": (7.2, 2), "d2": (7.0, 1)}
        edges = [("a", "a1"), ("a", "a2"), ("a1", "a11"), ("c", "c1"), ("d", "d1"), ("d1", "d11"), ("d", "d2")]
        _, dots, arrows = self.draw_tree(nodes, edges, np.array([-4.2, 0.9, 0]), 1.15, 1.0)
        lab = T("n = 0.6", 30, GRN).move_to(np.array([4.6, 1.6, 0]))
        self.play(FadeIn(lab))
        self.grow(nodes, edges, dots, arrows)
        res = VGroup(T("every cascade dies out", 24, INK),
                     T("average cascade size = 1 / (1 − n) = 2.5", 24, INK),
                     T("share of events from outside = 1 − n = 40%", 24, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        res.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(res, shift=UP * 0.2))
        self.wait(2)
        self.play(*[FadeOut(m) for m in list(dots.values()) + arrows + [res, lab]], run_time=0.6)

        # n = 1.15: supercritical, one immigrant explodes
        widths = [1, 1, 2, 3, 3, 5, 7, 9]
        nodes, edges = {}, []
        rng = np.random.default_rng(4)
        prev = []
        for g, w in enumerate(widths):
            cur = []
            for j in range(w):
                k = f"g{g}_{j}"
                x = (j - (w - 1) / 2) * (9.0 / max(widths)) + rng.uniform(-0.15, 0.15)
                nodes[k] = (x, g)
                cur.append(k)
                if prev:
                    parent = prev[min(len(prev) - 1, int(j * len(prev) / w))]
                    edges.append((parent, k))
            prev = cur
        _, dots, arrows = self.draw_tree(nodes, edges, np.array([0.6, 1.5, 0]), 1.0, 0.62)
        lab = T("n = 1.15", 30, RED).move_to(np.array([4.8, 1.6, 0]))
        self.play(FadeIn(lab))
        self.grow(nodes, edges, dots, arrows, run=0.45)
        res = T("n > 1: each generation is bigger than the last, so the rate grows without limit", 24, INK).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(res, shift=UP * 0.2))
        self.wait(2.2)


# --------------------------------------------------------------------------------------------
class Competition(Base):
    names = ["AI", "Chips", "Power", "Macro", "Retail"]
    raw = [5.0, 3.0, 2.0, 1.0, 0.6]
    cols = [BLU, GRN, ORA, VIO, RED]
    unit = 0.55

    def bars(self, vals, origin, cols=None, names=None, w=0.6, gap=0.32):
        cols = cols or self.cols
        names = names or self.names
        g = VGroup()
        for i, v in enumerate(vals):
            h = max(v * self.unit, 0.001)
            r = Rectangle(width=w, height=h, stroke_width=0, fill_color=cols[i], fill_opacity=0.9 if v > 0 else 0.0)
            r.move_to(origin + np.array([i * (w + gap), h / 2, 0]))
            g.add(r)
        return g

    def labels(self, bars, names):
        return VGroup(*[T(nm, 15, DIM).next_to(b.get_bottom(), DOWN, buff=0.12) for b, nm in zip(bars, names)])

    def construct(self):
        title = self.caption("Two ways for narratives to compete for attention")
        self.play(FadeIn(title))
        oL, oR = np.array([-6.2, -2.2, 0]), np.array([0.9, -2.2, 0])
        hL = T("subtract  κ · total", 26, RED).move_to(np.array([-4.2, 2.3, 0]))
        hR = T("divide by  (1 + total / B)^ω", 26, GRN).move_to(np.array([2.7, 2.3, 0]))
        bL, bR = self.bars(self.raw, oL), self.bars(self.raw, oR)
        lL, lR = self.labels(bL, self.names), self.labels(bR, self.names)
        sL = T("AI share 43%", 22, INK).move_to(np.array([-4.2, 1.7, 0]))
        sR = T("AI share 43%", 22, INK).move_to(np.array([2.7, 1.7, 0]))
        rawlab = T("raw drive", 22, DIM).move_to(np.array([-0.8, -3.2, 0]))
        self.play(FadeIn(hL), FadeIn(hR), LaggedStart(*[GrowFromEdge(b, DOWN) for b in [*bL, *bR]], lag_ratio=0.05),
                  FadeIn(lL), FadeIn(lR), FadeIn(sL), FadeIn(sR), FadeIn(rawlab), run_time=1.6)
        self.wait(0.6)

        sub = [max(v - 0.8, 0) for v in self.raw]          # kappa * total = 0.8
        div = [v * 0.6 for v in self.raw]                  # common factor c = 0.6
        bL2, bR2 = self.bars(sub, oL), self.bars(div, oR)
        sL2 = T("AI share 54%  (shares tilt to the big narrative)", 20, INK).move_to(sL)
        sR2 = T("AI share 43%  (ratios unchanged)", 20, INK).move_to(sR)
        note = T("Retail is wiped out by subtraction; division only scales it", 22, DIM).to_edge(DOWN, buff=0.3)
        self.play(Transform(bL, bL2), Transform(bR, bR2), Transform(sL, sL2), Transform(sR, sR2),
                  FadeOut(rawlab), run_time=1.6)
        self.play(FadeIn(note))
        self.wait(1.6)

        # split AI into two equal children and compare the AI total
        cap2 = self.caption("Now split the AI narrative into two halves", 28)
        self.play(Transform(title, cap2), FadeOut(note))
        names2 = ["AI-a", "AI-b", "Chips", "Power", "Macro", "Retail"]
        cols2 = [BLU, "#3d8fa6", GRN, ORA, VIO, RED]
        raw2 = [2.5, 2.5, 3.0, 2.0, 1.0, 0.6]
        sub2 = [max(v - 0.8, 0) for v in raw2]
        div2 = [v * 0.6 for v in raw2]
        bL3 = self.bars(sub2, oL + np.array([-0.3, 0, 0]), cols2, names2, w=0.5, gap=0.3)
        bR3 = self.bars(div2, oR + np.array([-0.3, 0, 0]), cols2, names2, w=0.5, gap=0.3)
        lL3, lR3 = self.labels(bL3, names2), self.labels(bR3, names2)
        self.play(Transform(bL, bL3), Transform(bR, bR3), Transform(lL, lL3), Transform(lR, lR3), run_time=1.6)
        tL = T("AI total: 4.2 → 3.4", 24, RED).move_to(sL)
        tR = T("AI total: 3.0 → 3.0", 24, GRN).move_to(sR)
        self.play(Transform(sL, tL), Transform(sR, tR))
        concl = VGroup(T("Subtraction: the answer depends on how finely you cluster", 22, INK),
                       T("Division: splitting or merging changes nothing.  ω is fitted: 0 = no competition, 1 = hard capacity", 22, INK)
                       ).arrange(DOWN, buff=0.1).to_edge(DOWN, buff=0.25)
        self.play(FadeIn(concl, shift=UP * 0.2))
        self.wait(3)


# --------------------------------------------------------------------------------------------
class AttributionFlow(Base):
    def stack(self, parts, origin, scale=0.075):
        g = VGroup()
        y = 0.0
        for v, c in parts:
            h = v * scale
            r = Rectangle(width=0.9, height=h, stroke_width=0, fill_color=c, fill_opacity=0.9)
            r.move_to(origin + np.array([0, y + h / 2, 0]))
            g.add(r)
            y += h
        return g

    def stack_labels(self, bar, texts):
        return VGroup(*[T(s, 19, INK).next_to(r, RIGHT, buff=0.18) for r, s in zip(bar, texts)])

    def construct(self):
        title = self.caption("Where did the GPU narrative's attention come from?")
        self.play(FadeIn(title))
        P = {"BOT": np.array([-3.0, 2.0, 0]), "AI": np.array([-5.0, -1.4, 0]), "GPU": np.array([-1.0, -1.4, 0])}
        circ = {k: Circle(radius=0.62, color=c, stroke_width=4).move_to(P[k]) for k, c in
                [("BOT", YEL), ("AI", BLU), ("GPU", GRN)]}
        lab = {"BOT": T("BOT", 24, YEL).move_to(P["BOT"]), "AI": T("AI", 24, BLU).move_to(P["AI"]),
               "GPU": T("GPU", 24, GRN).move_to(P["GPU"])}
        bsub = T("outside world", 18, DIM).next_to(circ["BOT"], UP, buff=0.1)

        def arr(a, b, c=DIM):
            return Arrow(P[a], P[b], buff=0.68, stroke_width=4, color=c, tip_length=0.2)

        eBA, eBG, eAG = arr("BOT", "AI"), arr("BOT", "GPU"), arr("AI", "GPU")
        loopA = CurvedArrow(P["AI"] + np.array([-0.35, -0.55, 0]), P["AI"] + np.array([0.35, -0.55, 0]),
                            angle=-4.2, color=DIM, stroke_width=3, tip_length=0.16)
        loopG = CurvedArrow(P["GPU"] + np.array([-0.35, -0.55, 0]), P["GPU"] + np.array([0.35, -0.55, 0]),
                            angle=-4.2, color=DIM, stroke_width=3, tip_length=0.16)
        self.play(*[Create(c) for c in circ.values()], *[FadeIn(l) for l in lab.values()], FadeIn(bsub), run_time=1)
        self.play(GrowArrow(eBA), GrowArrow(eBG), GrowArrow(eAG), Create(loopA), Create(loopG), run_time=1)

        origin = np.array([2.6, -2.6, 0])
        parts0 = [(8.0, YEL), (13.1, BLU), (14.0, GRN)]
        bar = self.stack(parts0, origin)
        bl = self.stack_labels(bar, ["outside  8.0  (23%)", "from AI  13.1  (37%)", "from GPU itself  14.0  (40%)"])
        head = T("GPU attention, normal window: 35.1", 22, INK).next_to(origin, UP, buff=3.25).align_to(origin + LEFT * 0.45, LEFT)
        self.play(LaggedStart(*[GrowFromEdge(r, DOWN) for r in bar], lag_ratio=0.3), FadeIn(bl), FadeIn(head), run_time=1.5)
        self.wait(1)

        # shock arrives at AI through BOT
        cap = self.caption("Window t: R1 drops. AI gets 400 units where 43.5 were expected", 28)
        self.play(Transform(title, cap))
        pulse = Dot(P["BOT"], radius=0.13, color=YEL)
        self.play(Flash(P["BOT"], color=YEL, line_length=0.35), run_time=0.6)
        self.play(MoveAlongPath(pulse, Line(P["BOT"], P["AI"])), run_time=0.9)
        sig = T("+54σ surprise: new information", 19, YEL).move_to(np.array([-5.0, -2.6, 0]))
        self.play(circ["AI"].animate.scale(1.35).set_stroke(width=7), FadeOut(pulse), FadeIn(sig), run_time=0.8)
        self.wait(0.8)

        # next window: flow AI -> GPU, GPU decomposition changes
        cap = self.caption("Window t+1: AI's memory trace rises 43.5 → 58.0 and spills into GPU", 28)
        self.play(Transform(title, cap))
        pulse2 = Dot(P["AI"], radius=0.13, color=BLU)
        self.play(MoveAlongPath(pulse2, Line(P["AI"], P["GPU"])), run_time=0.9)
        self.play(FadeOut(pulse2), Indicate(circ["GPU"], color=GRN), run_time=0.5)
        parts1 = [(8.0, YEL), (17.4, BLU), (14.0, GRN)]
        bar2 = self.stack(parts1, origin)
        bl2 = self.stack_labels(bar2, ["outside  8.0  (20%)", "from AI  17.4  (44%)", "from GPU itself  14.0  (36%)"])
        head2 = T("GPU attention, window t+1: 39.5", 22, INK).move_to(head).align_to(head, LEFT)
        self.play(Transform(bar, bar2), Transform(bl, bl2), Transform(head, head2), run_time=1.4)
        self.wait(0.8)
        out = VGroup(T("These shares are the transition weights the search uses:", 22, INK),
                     T("p(BOT → GPU) = 0.20     p(AI → GPU) = 0.44     p(GPU → GPU) = 0.36", 22, YEL)
                     ).arrange(DOWN, buff=0.12).to_edge(DOWN, buff=0.25)
        self.play(FadeIn(out, shift=UP * 0.2))
        self.wait(3)


# --------------------------------------------------------------------------------------------
class CertifiedSearch(Base):
    def construct(self):
        title = self.caption("Finding the smallest explanation, with a certificate  (toy numbers)", 28)
        self.play(FadeIn(title))
        P = {"BOT": (-1.5, 2.35), "R1": (-5.0, 1.15), "App": (-2.9, 1.15), "Capex": (0.3, 1.15), "Chip": (2.8, 1.15),
             "Power": (-4.9, -0.25), "NVDA": (-1.4, -1.3), "VST": (1.6, -1.3),
             "Elect": (5.6, 1.9), "Crypto": (5.6, -0.2)}
        names = {"BOT": "BOT", "R1": "R1 release", "App": "App surge", "Capex": "Capex", "Chip": "Chip count",
                 "Power": "Power demand", "NVDA": "NVDA −17%", "VST": "VST −28%", "Elect": "Elections", "Crypto": "Crypto"}
        P = {k: np.array([x, y, 0]) for k, (x, y) in P.items()}
        node = {}
        for k in P:
            c = YEL if k == "BOT" else (RED if k in ("NVDA", "VST") else INK)
            box = RoundedRectangle(corner_radius=0.12, width=max(1.25, 0.2 + 0.17 * len(names[k])), height=0.5,
                                   stroke_color=c, stroke_width=2.5, fill_color=BG, fill_opacity=1)
            node[k] = VGroup(box, T(names[k], 17, c)).move_to(P[k])
        E = [("BOT", "R1", 0.30), ("BOT", "App", 0.15), ("BOT", "Capex", 0.20), ("BOT", "Chip", 0.10),
             ("R1", "App", 0.40), ("R1", "NVDA", 0.45), ("R1", "Power", 0.25), ("Power", "VST", 0.45),
             ("App", "NVDA", 0.20), ("Capex", "NVDA", 0.25), ("Capex", "VST", 0.15), ("Chip", "NVDA", 0.10),
             ("Elect", "Crypto", 0.30), ("Crypto", "NVDA", 0.01)]
        def rim(k, d):
            box = node[k][0]
            hw, hh = box.width / 2, box.height / 2
            dx, dy = abs(d[0]) + 1e-9, abs(d[1]) + 1e-9
            return node[k].get_center() + d * (min(hw / dx, hh / dy) + 0.06)

        def link(a, b, cls=Arrow, **kw):
            pa, pb = node[a].get_center(), node[b].get_center()
            d = (pb - pa) / np.linalg.norm(pb - pa)
            return cls(rim(a, d), rim(b, -d), buff=0, **kw)

        edge = {}
        for a, b, p in E:
            edge[(a, b)] = link(a, b, stroke_width=2.2, tip_length=0.13,
                                color=GRID if "Crypto" in (a, b) or "Elect" in (a, b) else DIM)
        abst = [link("BOT", t, DashedLine, color=YEL, stroke_width=2, dash_length=0.1) for t in ("NVDA", "VST")]
        self.play(*[FadeIn(n) for n in node.values()], run_time=0.8)
        self.play(*[GrowArrow(e) for e in edge.values()], *[Create(d) for d in abst], run_time=1.2)
        self.bring_to_front(*node.values())
        legend = VGroup(T("edge cost = −log p + 0.3 per node", 18, DIM),
                        T("dashed: BOT → event = \"we do not know\", p0 = 0.05", 18, YEL)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        legend.to_corner(DL, buff=0.35)
        self.play(FadeIn(legend))
        self.wait(0.5)

        # step 1: push from the events backwards
        cap = self.caption("Step 1: push probability mass backwards from the events", 28)
        self.play(Transform(title, cap))
        R = T("leftover mass R = 1.00", 22, INK).to_corner(DR, buff=0.45)
        self.play(FadeIn(R))
        waves = [["NVDA", "VST"], ["R1", "App", "Capex", "Chip", "Power"], ["BOT"]]
        Rs = ["leftover mass R = 0.34", "leftover mass R = 0.06", "leftover mass R = 0.02"]
        for wave, rs in zip(waves, Rs):
            self.play(*[node[k][0].animate.set_fill(BLU, opacity=0.25) for k in wave],
                      Transform(R, T(rs, 22, INK).to_corner(DR, buff=0.45)), run_time=0.8)
        far = T("never reached:\ntoo improbable", 17, DIM).next_to(node["Crypto"], DOWN, buff=0.25)
        self.play(FadeIn(far), node["Elect"].animate.set_opacity(0.45), node["Crypto"].animate.set_opacity(0.45), run_time=0.6)
        self.wait(0.6)

        # step 2: exact DP finds the cheapest tree covering both events
        cap = self.caption("Step 2: exact dynamic programming finds the cheapest tree covering both events", 26)
        self.play(Transform(title, cap), FadeOut(far))
        best = [("BOT", "R1"), ("R1", "NVDA"), ("R1", "Power"), ("Power", "VST")]
        self.play(*[edge[e].animate.set_color(YEL).set_stroke(width=5) for e in best], run_time=1.2)
        self.bring_to_front(*node.values())
        cost = VGroup(T("best:  1.20 + 0.80 + 1.39 + 0.80 + 4 × 0.30 = 5.39", 21, YEL),
                      T("runner-up via Capex:  5.79   (odds 1.5 : 1, reported)", 19, INK),
                      T("\"we do not know\":  6.59   (odds 3.3 : 1, reported)", 19, INK)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.08).to_edge(DOWN, buff=0.75).shift(LEFT * 0.4)
        self.play(Transform(R, cost), FadeOut(legend), run_time=1)
        self.wait(1.5)

        # step 3: certificate
        cap = self.caption("Step 3: leftover mass bounds every unexplored chain: cost ≥ Γ = 7.4", 26)
        self.play(Transform(title, cap))
        cert = T("5.39 ≤ 7.4  →  certified smallest explanation in the whole graph", 22, GRN).to_edge(DOWN, buff=0.25)
        self.play(FadeIn(cert, shift=UP * 0.2))
        self.play(*[Indicate(edge[e], color=YEL, scale_factor=1.0) for e in best], run_time=1)
        self.bring_to_front(*node.values())
        self.wait(3)
