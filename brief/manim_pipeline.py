"""Yggdrasil end-to-end pipeline film. Manim CE 0.20, no LaTeX (Pango text only). One scene per chapter."""
import numpy as np
from manim import *

BG = "#10151b"
FONT = "Noto Sans"
MONO = "DejaVu Sans Mono"
INK = "#e9edf0"
DIM = "#8a949c"
GRID = "#2a333b"
YEL = "#f4d35e"
BLU = "#58c4dd"
GRN = "#83c167"
RED = "#fc6255"
ORA = "#ff9b54"
VIO = "#b09cff"
OK_C = "#83c167"     # specified
PART_C = "#f4b860"   # partly open / designed, not built
NO_C = "#fc6255"     # not designed yet


def T(s, size=24, color=INK, font=FONT):
    return Text(s, font=font, font_size=size, color=color)


def Mono(s, size=18, color=INK):
    return Text(s, font=MONO, font_size=size, color=color)


class Chapter(Scene):
    num = 0
    name = ""
    status = ("SPECIFIED", OK_C)

    def setup(self):
        self.camera.background_color = BG

    def header(self):
        h = T(f"{self.num} · {self.name}", 30).to_corner(UL, buff=0.35)
        txt, col = self.status
        bt = T(txt, 17, col)
        box = RoundedRectangle(corner_radius=0.12, width=bt.width + 0.4, height=bt.height + 0.26,
                               stroke_color=col, stroke_width=2)
        bt.move_to(box)
        badge = VGroup(box, bt).to_corner(UR, buff=0.35)
        self.play(FadeIn(h, shift=RIGHT * 0.2), FadeIn(badge), run_time=0.6)
        return VGroup(h, badge)

    def eq(self, pieces, size=26):
        return VGroup(*[T(t, size, c) for t, c in pieces]).arrange(RIGHT, buff=0.09)

    def note(self, term, text, color, direction=DOWN, size=17, buff=0.45):
        lab = T(text, size, color).next_to(term, direction, buff=buff)
        arr = Arrow(lab.get_edge_center(-direction), term.get_edge_center(direction), buff=0.05,
                    stroke_width=2, color=color, tip_length=0.1, max_tip_length_to_length_ratio=0.35)
        return VGroup(lab, arr)

    def bottom(self, s, size=19, color=DIM):
        return T(s, size, color).to_edge(DOWN, buff=0.32)

    def node(self, label, pos, color=INK, w=None, size=18, fill=BG):
        t = T(label, size, color)
        box = RoundedRectangle(corner_radius=0.12, width=w or (t.width + 0.4), height=t.height + 0.32,
                               stroke_color=color, stroke_width=2.4, fill_color=fill, fill_opacity=1)
        t.move_to(box)
        return VGroup(box, t).move_to(pos)


def rim_point(mob, d):
    hw, hh = mob.width / 2, mob.height / 2
    dx, dy = abs(d[0]) + 1e-9, abs(d[1]) + 1e-9
    return mob.get_center() + d * (min(hw / dx, hh / dy) + 0.05)


def link(a, b, cls=Arrow, **kw):
    pa, pb = a.get_center(), b.get_center()
    d = (pb - pa) / np.linalg.norm(pb - pa)
    return cls(rim_point(a, d), rim_point(b, -d), buff=0, **kw)


# ============================================================================================ 0
class P00_Overview(Chapter):
    num, name, status = 0, "Yggdrasil, end to end", ("OVERVIEW", DIM)

    def construct(self):
        self.header()
        stages = [("Ingest", OK_C), ("Dedup", OK_C), ("Objects", OK_C), ("Narratives", PART_C), ("Attention", OK_C),
                  ("Anomaly", PART_C), ("Search", OK_C), ("Explanations", OK_C), ("Facts for clingo", NO_C), ("Verdicts + Lean", PART_C)]
        boxes = []
        for k, (s, c) in enumerate(stages):
            row, col = divmod(k, 5)
            x = -5.2 + col * 2.6 if row == 0 else 5.2 - col * 2.6
            y = 1.3 if row == 0 else -0.9
            b = self.node(f"{k + 1}  {s}", [x, y, 0], color=c, w=2.3, size=17)
            boxes.append(b)
        arrows = []
        for a, b in zip(boxes[:-1], boxes[1:]):
            arrows.append(link(a, b, stroke_width=2.5, color=DIM, tip_length=0.14))
        self.play(LaggedStart(*[AnimationGroup(FadeIn(b, scale=0.9), *( [GrowArrow(arrows[i - 1])] if i else [])) for i, b in enumerate(boxes)],
                              lag_ratio=0.25), run_time=4)
        layer = VGroup(
            T("always on, whatever stock anyone cares about", 17, BLU).move_to([0, 2.25, 0]),
            T("only when the market does something abnormal", 17, YEL).move_to([0, -1.85, 0]))
        self.play(FadeIn(layer), run_time=0.8)
        leg = VGroup(
            VGroup(Square(0.22, color=OK_C, fill_opacity=0.9, stroke_width=0), T("specified (math, and proofs where needed)", 18)).arrange(RIGHT, buff=0.15),
            VGroup(Square(0.22, color=PART_C, fill_opacity=0.9, stroke_width=0), T("partly open", 18)).arrange(RIGHT, buff=0.15),
            VGroup(Square(0.22, color=NO_C, fill_opacity=0.9, stroke_width=0), T("not designed yet", 18)).arrange(RIGHT, buff=0.15),
        ).arrange(RIGHT, buff=0.6).move_to([0, -2.75, 0])
        self.play(FadeIn(leg), run_time=0.8)
        self.play(FadeIn(self.bottom("No stage is implemented yet. Colors show how far the design has got, not code.", 20, INK)))
        self.wait(3.5)


# ============================================================================================ 1
class P01_Ingest(Chapter):
    num, name, status = 1, "Ingestion", ("SPECIFIED", OK_C)

    def construct(self):
        self.header()
        ys = [2.0, 1.0, 0.0]
        names = [("GDELT", BLU), ("RSS", GRN), ("SerpApi", DIM)]
        labs = VGroup(*[T(n, 22, c).move_to([-6.1, y, 0]) for (n, c), y in zip(names, ys)])
        lanes = VGroup(*[DashedLine([-5.3, y, 0], [0.6, y, 0], color=GRID, dash_length=0.1) for y in ys])
        hasher = VGroup(Circle(radius=0.5, color=ORA, stroke_width=3), T("sha256", 16, ORA)).move_to([1.4, 1.0, 0])
        arch = RoundedRectangle(width=2.6, height=2.9, corner_radius=0.15, stroke_color=YEL, stroke_width=2.5).move_to([4.2, 1.0, 0])
        alab = T("archive, addressed by hash", 17, YEL).next_to(arch, UP, buff=0.12)
        clock = T("every 15 min", 17, BLU).move_to([-3.2, 2.45, 0])
        on_req = T("only when asked", 15, DIM).move_to([-3.2, -0.42, 0])
        self.play(FadeIn(labs), Create(lanes), FadeIn(hasher), Create(arch), FadeIn(alab), FadeIn(clock), FadeIn(on_req), run_time=1.2)

        shelf = []
        hexes = ["a3f9..", "07bc..", "e21d..", "9c41..", "5f0a..", "c8e3..", "1b77..", "d40f.."]
        k = 0
        for batch in range(2):
            blocks = VGroup(*[Square(0.28, color=c, fill_opacity=0.85, stroke_width=0) for c in (BLU, VIO, GRN)]).arrange(RIGHT, buff=0.06)
            blocks.move_to([-5.0, 2.0, 0])
            rss = Dot([-5.0, 1.0, 0], radius=0.1, color=GRN)
            self.add(blocks, rss)
            self.play(blocks.animate.move_to(hasher.get_center()), rss.animate.move_to(hasher.get_center()), run_time=1.0, rate_func=smooth)
            for piece in [*blocks, rss]:
                slot = np.array([3.45 + (k % 2) * 1.5, 2.05 - (k // 2) * 0.5, 0])
                tag = Mono(hexes[k % len(hexes)], 15, YEL).move_to(slot)
                self.play(Transform(piece, tag), run_time=0.22)
                shelf.append(piece)
                k += 1
        serp = DashedLine([-5.0, 0.0, 0], [0.9, 0.85, 0], color=DIM, dash_length=0.08)
        self.play(Create(serp), run_time=0.6)

        e1 = self.eq([("raw_blob_id", YEL), (" = ", INK), ("sha256", ORA), ("(raw_bytes)", INK)], 24).move_to([0, -1.05, 0])
        n1 = self.note(e1[2], "same bytes give the same id, so a re-download changes nothing", ORA, DOWN, 15, 0.22)
        e2 = self.eq([("window(o)", BLU), (" = floor((observed_time - t0) / ", INK), ("Δ", BLU), (")", INK)], 24).move_to([0, -2.0, 0])
        n2 = self.note(e2[2], "Δ = 15 min, GDELT's heartbeat", BLU, DOWN, 15, 0.22)
        self.play(FadeIn(e1), run_time=0.7)
        self.play(FadeIn(n1), run_time=0.6)
        self.play(FadeIn(e2), run_time=0.7)
        self.play(FadeIn(n2), run_time=0.6)
        phys = T("Like a seismograph drum: the world is sampled at a fixed rate and nothing recorded is ever overwritten.", 18, INK).move_to([0, -3.1, 0])
        fact = self.bottom("Measured, 27 Jan 2025: 96 batches, 130,852 English documents, 534 MB zipped", 17)
        self.play(FadeIn(phys), FadeIn(fact))
        self.wait(3.5)


# ============================================================================================ 2
class P02_Dedup(Chapter):
    num, name, status = 2, "Deduplication", ("SPECIFIED", OK_C)

    def construct(self):
        self.header()
        t1 = T("Exact keys collapse copies", 22, INK).move_to([-3.6, 2.5, 0])
        t2 = T("Near-copies only annotate", 22, INK).move_to([3.6, 2.5, 0])
        self.play(FadeIn(t1), FadeIn(t2), run_time=0.6)
        urls = ["www.reuters.com/a?utm_source=x", "reuters.com/a#top", "m.reuters.com/a/"]
        cards = VGroup(*[self.node(u, [-3.6, 1.7 - i * 0.65, 0], color=DIM, size=15, w=4.6) for i, u in enumerate(urls)])
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.2) for c in cards], lag_ratio=0.3), run_time=1.2)
        canon = self.node("https://reuters.com/a", [-3.6, -0.55, 0], color=GRN, size=16, w=4.6)
        casc = T("exact keys, first match wins:\nnative id  →  canonical URL  →  content hash", 15, DIM).move_to([-3.6, -1.2, 0])
        self.play(*[Transform(c, canon.copy()) for c in cards], run_time=1.2)
        self.play(FadeIn(casc), run_time=0.6)

        group = VGroup()
        for i in range(6):
            col = YEL if i == 0 else DIM
            c = self.node(f"station{i + 1}.iheart.com/story", [3.6, 1.75 - i * 0.48, 0], color=col, size=13, w=3.6)
            group.add(c)
        wts = VGroup(*[T("v = 1" if i == 0 else "v = 0.1", 15, YEL if i == 0 else DIM).next_to(group[i], RIGHT, buff=0.15) for i in range(6)])
        self.play(LaggedStart(*[FadeIn(g, shift=LEFT * 0.2) for g in group], lag_ratio=0.15), run_time=1.2)
        self.play(FadeIn(wts), run_time=0.8)

        e1 = self.eq([("v[o]", YEL), (" = 1 for the first copy,  ", INK), ("α_copy", ORA), (" = 0.1 for later copies", INK)], 22).move_to([0, -1.95, 0])
        e2 = self.eq([("copy-group mass", YEL), (" = 1 + ", INK), ("α_copy", ORA), (" · (", INK), ("n", BLU), (" - 1)", INK)], 24).move_to([0, -2.55, 0])
        self.play(FadeIn(e1), run_time=0.7)
        self.play(FadeIn(e2), run_time=0.7)
        ex = T("Measured: one story ran on 271 iHeart stations. It counts 1 + 0.1 × 270 = 28 units, not 271.", 18, INK).move_to([0, -3.15, 0])
        self.play(FadeIn(ex))
        self.play(FadeIn(self.bottom("Count witnesses, not echoes. GDELT rows have no body text, so near-copy checks need fetched articles.", 16)))
        self.wait(3.5)


# ============================================================================================ 3
class P03_Objects(Chapter):
    num, name, status = 3, "Canonical objects and their clocks", ("SPECIFIED", OK_C)

    def construct(self):
        self.header()
        rows = [("observation", "9c41..e2"), ("source", "reuters.com"), ("entities", "DeepSeek, Nvidia"),
                ("themes", "TECH_AI, ECON_STOCKMARKET"), ("weight v", "1.0")]
        card_lines = VGroup(*[VGroup(Mono(k, 15, DIM), Mono(v, 15, INK)).arrange(RIGHT, buff=0.3) for k, v in rows])
        for line in card_lines:
            line[0].align_to(card_lines, LEFT)
        card_lines.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        card = VGroup(SurroundingRectangle(card_lines, color=GRN, buff=0.25, corner_radius=0.12), card_lines).move_to([-4.2, 1.2, 0])
        self.play(FadeIn(card), run_time=0.8)

        ax = Line([-0.6, 0.9, 0], [6.6, 0.9, 0], color=DIM, stroke_width=2)
        self.play(Create(ax), run_time=0.6)
        clocks = [("event", -0.2, BLU), ("published", 0.6, VIO), ("observed", 1.5, GRN), ("ingested", 2.1, ORA), ("first_seen", 2.7, YEL)]
        marks = VGroup()
        for i, (nm, x, c) in enumerate(clocks):
            d = Dot([x, 0.9, 0], color=c, radius=0.08)
            lab = T(nm, 14, c).next_to(d, UP if i % 2 == 0 else DOWN, buff=0.18)
            marks.add(VGroup(d, lab))
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in marks], lag_ratio=0.25), run_time=1.6)
        cut = DashedLine([4.3, 2.0, 0], [4.3, -0.2, 0], color=RED, dash_length=0.1)
        cl = T("τ*  market cutoff", 16, RED).next_to(cut, UP, buff=0.08)
        late = VGroup(Dot([5.6, 0.9, 0], color=DIM, radius=0.08), T("distillation story\nfirst seen 29 Jan", 13, DIM).move_to([5.7, 0.25, 0]))
        cross = Cross(late[0], stroke_color=RED, stroke_width=3, scale_factor=2.2)
        self.play(Create(cut), FadeIn(cl), FadeIn(late), run_time=0.8)
        self.play(Create(cross), run_time=0.5)

        e = self.eq([("admissible(o, ", INK), ("τ*", RED), (")  =  ", INK), ("first_seen[o]", YEL), ("  <  ", INK), ("τ*", RED)], 26).move_to([0.4, -1.3, 0])
        n1 = self.note(e[3], "when Yggdrasil first held it, never the date printed on the page", YEL, DOWN, 16, 0.34)
        self.play(FadeIn(e), run_time=0.7)
        self.play(FadeIn(n1), run_time=0.6)
        phys = T("Chain of custody: evidence counts from the moment we first held it.", 18, INK).move_to([0, -2.85, 0])
        self.play(FadeIn(phys))
        self.play(FadeIn(self.bottom("GDELT has no per-article publish time, and Google's date filter leaked post-cutoff pages for 71% of test questions.", 15)))
        self.wait(3.5)


# ============================================================================================ 4
class P04_Narratives(Chapter):
    num, name, status = 4, "Cold-starting the narrative graph", ("PARTLY OPEN", PART_C)

    def construct(self):
        self.header()
        pos = {"AI": [-4.6, 1.5, 0], "Chips": [-2.4, 1.9, 0], "Power": [-1.7, 0.2, 0], "Macro": [-4.0, -0.3, 0], "none": [-5.9, 0.3, 0]}
        sizes = {"AI": 0.55, "Chips": 0.48, "Power": 0.36, "Macro": 0.42, "none": 0.4}
        cols = {"AI": BLU, "Chips": GRN, "Power": ORA, "Macro": VIO, "none": DIM}
        nodes = {k: VGroup(Circle(radius=sizes[k], color=cols[k], stroke_width=3, fill_color=cols[k], fill_opacity=0.12),
                           T(k, 16, cols[k])).move_to(pos[k]) for k in pos}
        cs = T("Pre-period: 3 weeks of history (3 × the longest memory)", 18, INK).move_to([2.9, 2.45, 0])
        self.play(*[FadeIn(n, scale=0.6) for n in nodes.values()], FadeIn(cs), run_time=1.2)
        warm = T("memory traces start at their historical means: no fake start-up burst", 16, DIM).move_to([2.9, 2.0, 0])
        self.play(FadeIn(warm), *[n[0].animate.set_fill(opacity=0.3) for n in nodes.values()], run_time=0.9)

        art = Dot([-3.2, 3.0, 0], radius=0.12, color=YEL)
        al = T("one article, 1 unit", 15, YEL).next_to(art, RIGHT, buff=0.12)
        self.play(FadeIn(art), FadeIn(al), run_time=0.5)
        shares = [("AI", 0.60), ("Chips", 0.25), ("none", 0.15)]
        drops = []
        for k, p in shares:
            d = Dot(art.get_center(), radius=0.05 + 0.1 * p, color=YEL)
            drops.append((d, k, p))
        self.play(*[d.animate.move_to(nodes[k].get_center()) for d, k, p in drops], FadeOut(al), FadeOut(art), run_time=1.2)
        plabs = VGroup(*[T(f"{p:.2f}", 15, YEL).next_to(nodes[k], DOWN if k != "Chips" else UP, buff=0.08) for d, k, p in drops])
        self.play(FadeIn(plabs), *[FadeOut(d) for d, k, p in drops], run_time=0.6)

        e1 = self.eq([("p[o][n]", YEL), (" = exp(", INK), ("s[o][n]", BLU), (" / ", INK), ("T", ORA), (") / Z[o]", INK)], 23).move_to([2.9, 1.25, 0])
        n1a = T("s: similarity to narrative n's centroid   T: calibrated temperature   n = 0 is \"none\"", 14, DIM).next_to(e1, DOWN, buff=0.15)
        e2 = self.eq([("y[n][t]", BLU), (" = Σ_o  ", INK), ("v[o]", YEL), (" · ", INK), ("p[o][n]", YEL)], 23).move_to([2.9, 0.2, 0])
        n2a = T("attention mass: a weighted soft count of articles", 14, DIM).next_to(e2, DOWN, buff=0.15)
        e3 = self.eq([("Σ_n y[n][t] + ", INK), ("y[0][t]", DIM), (" = ", INK), ("V[t]", GRN)], 23).move_to([2.9, -0.85, 0])
        n3a = T("Lemma 5.1: total attention is conserved by construction", 14, GRN).next_to(e3, DOWN, buff=0.15)
        for e, n in [(e1, n1a), (e2, n2a), (e3, n3a)]:
            self.play(FadeIn(e), run_time=0.6)
            self.play(FadeIn(n), run_time=0.5)
        prism = T("Like a prism: each article's unit of attention is split across narratives, never duplicated.", 17, INK).move_to([0, -2.05, 0])
        self.play(FadeIn(prism))
        self.wait(1.0)

        # lineage split
        c1 = Circle(radius=0.38, color=BLU, stroke_width=3, fill_color=BLU, fill_opacity=0.3).move_to([-5.15, 1.75, 0])
        c2 = Circle(radius=0.3, color="#3d8fa6", stroke_width=3, fill_color="#3d8fa6", fill_opacity=0.3).move_to([-4.0, 1.4, 0])
        kids = VGroup(VGroup(c1, T("AI-models", 13, BLU).next_to(c1, UP, buff=0.06)),
                      VGroup(c2, T("AI-apps", 13, "#3d8fa6").next_to(c2, DOWN, buff=0.06)))
        sl = T("split: z[c] = q[c] · z[N]  (memory is shared out, Lemma 5.2)", 15, BLU).move_to([-3.6, -1.35, 0])
        self.play(ReplacementTransform(nodes["AI"], kids), FadeOut(plabs[0]), FadeIn(sl), run_time=1.2)
        open_t = self.bottom("Open: seed narratives · membership calibration (200-500 labeled pairs) · lineage threshold · rule for brand-new narratives", 15, PART_C)
        self.play(FadeIn(open_t))
        self.wait(3.5)


# ============================================================================================ 5
class P05_Attention(Chapter):
    num, name, status = 5, "How objects move attention", ("SPECIFIED · NOT FITTED", PART_C)

    def construct(self):
        self.header()
        P = {"AI": np.array([-5.2, 1.6, 0]), "Chips": np.array([-2.6, 1.6, 0]), "Power": np.array([-3.9, -0.2, 0])}
        cols = {"AI": BLU, "Chips": GRN, "Power": ORA}
        nodes = {k: VGroup(Circle(radius=0.48, color=cols[k], stroke_width=3), T(k, 17, cols[k])).move_to(P[k]) for k in P}
        e_ac = Arrow(P["AI"], P["Chips"], buff=0.52, stroke_width=7, color=DIM, tip_length=0.2)
        e_ap = Arrow(P["AI"], P["Power"], buff=0.52, stroke_width=2.5, color=DIM, tip_length=0.15)
        e_pc = Arrow(P["Power"], P["Chips"], buff=0.52, stroke_width=4, color=DIM, tip_length=0.17)
        self.play(*[FadeIn(n) for n in nodes.values()], GrowArrow(e_ac), GrowArrow(e_ap), GrowArrow(e_pc), run_time=1.0)
        wlab = T("edge width = A[i][j]", 14, DIM).move_to([-3.9, 2.45, 0])
        self.play(FadeIn(wlab), run_time=0.4)

        # four traces under AI
        tau = [1, 6, 24, 168]
        a = [np.exp(-0.25 / t) for t in tau]
        base = np.array([-6.35, -2.15, 0])
        vals = [1.0, 1.0, 1.0, 1.0]
        H = 0.012

        def bars(v):
            g = VGroup()
            for m in range(4):
                h = max(0.02, v[m] * H)
                r = Rectangle(width=0.32, height=h, stroke_width=0, fill_color=BLU, fill_opacity=0.85)
                r.move_to(base + np.array([m * 0.5, h / 2, 0]))
                g.add(r)
            return g

        vals = [43.5] * 4
        bg = bars(vals)
        tl = VGroup(*[T(s, 12, DIM).move_to(base + np.array([m * 0.5, -0.18, 0])) for m, s in enumerate(["1h", "6h", "1d", "1w"])])
        ttl = T("AI's memory traces", 14, BLU).move_to(base + np.array([0.75, 1.55, 0]))
        self.play(FadeIn(bg), FadeIn(tl), FadeIn(ttl), run_time=0.6)

        e1 = self.eq([("z[j][m][t]", BLU), (" = ", INK), ("a[m]", ORA), (" · z[j][m][t-1] + ", INK), ("(1 - a[m])", YEL), (" · y[j][t-1]", INK)], 22).move_to([2.6, 1.9, 0])
        n1 = self.note(e1[2], "a[m] = exp(-Δ/τ[m]): memory that survives a window", ORA, DOWN, 15, 0.3)
        n1b = self.note(e1[4], "share of the new mass that enters", YEL, DOWN, 15, 0.95)
        self.play(FadeIn(e1), run_time=0.7)
        self.play(FadeIn(n1), FadeIn(n1b), run_time=0.7)
        burst = T("R1 drops: y[AI] = 400", 15, YEL).move_to(base + np.array([0.75, 1.9, 0]))
        self.play(FadeIn(burst), Flash(nodes["AI"].get_center(), color=YEL, line_length=0.3), run_time=0.6)
        v = [a[m] * 43.5 + (1 - a[m]) * 400 for m in range(4)]
        self.play(Transform(bg, bars(v)), run_time=0.8)
        for _ in range(3):
            v = [a[m] * v[m] + (1 - a[m]) * 43.5 for m in range(4)]
            self.play(Transform(bg, bars(v)), run_time=0.4)
        rc = T("Each trace is an RC circuit: news charges a capacitor\nthat leaks with time constant τ.", 16, INK).move_to([2.6, 0.1, 0])
        self.play(FadeIn(rc))
        self.wait(1.2)
        self.play(FadeOut(VGroup(e1, n1, n1b, rc)), run_time=0.5)

        e2 = self.eq([("η[i]", INK), (" = ", INK), ("base[i]", GRN), (" + Σ_j Σ_m ", INK), ("A[i][j][m]", ORA), (" · ", INK), ("z[j][m]", BLU)], 22).move_to([2.6, 1.9, 0])
        n2a = self.note(e2[2], "outside inflow: hour of week, CPI, FOMC, earnings", GRN, DOWN, 14, 0.3)
        n2b = self.note(e2[4], "units of i caused per unit of j, at timescale m", ORA, DOWN, 14, 0.95)
        self.play(FadeIn(e2), run_time=0.6)
        self.play(FadeIn(n2a), FadeIn(n2b), Indicate(e_ac, color=ORA), run_time=0.9)
        e3 = self.eq([("λ_raw[i]", INK), (" = s · softplus(η[i] / s)", INK)], 22).move_to([2.6, 0.0, 0])
        n3 = T("keeps the rate positive; behaves linearly once it is large", 14, DIM).next_to(e3, DOWN, buff=0.12)
        self.play(FadeIn(e3), FadeIn(n3), run_time=0.7)
        e4 = self.eq([("λ[i]", INK), (" = λ_raw[i] · ", INK), ("(B / (B + S_raw))", GRN), (" ** ", INK), ("ω", YEL)], 24).move_to([2.6, -1.1, 0])
        n4 = T("one common gain for all narratives:  ω = 0 no competition,  ω = 1 hard capacity B", 14, DIM).next_to(e4, DOWN, buff=0.12)
        self.play(FadeIn(e4), FadeIn(n4), run_time=0.7)
        agc = T("Like automatic gain control in a radio: when the band gets loud,\nevery station is turned down by the same factor.", 16, INK).move_to([2.6, -2.55, 0])
        self.play(FadeIn(agc))
        self.play(FadeIn(self.bottom("y ~ quasi-Poisson(λ), fitted by a convex sparse group lasso.  ω, the timescales and every edge are tested by F1-F4.", 15, PART_C)))
        self.wait(3.5)


# ============================================================================================ 6
class P06_Attribution(Chapter):
    num, name, status = 6, "New information and transition weights", ("SPECIFIED", OK_C)

    def construct(self):
        self.header()
        P = {"BOT": np.array([-4.2, 1.9, 0]), "AI": np.array([-5.6, -0.6, 0]), "GPU": np.array([-2.8, -0.6, 0])}
        circ = {k: VGroup(Circle(radius=0.5, color=c, stroke_width=3), T(k, 18, c)).move_to(P[k]) for k, c in [("BOT", YEL), ("AI", BLU), ("GPU", GRN)]}
        arrs = [Arrow(P["BOT"], P["AI"], buff=0.55, color=DIM, stroke_width=3, tip_length=0.16),
                Arrow(P["BOT"], P["GPU"], buff=0.55, color=DIM, stroke_width=3, tip_length=0.16),
                Arrow(P["AI"], P["GPU"], buff=0.55, color=DIM, stroke_width=3, tip_length=0.16)]
        self.play(*[FadeIn(c) for c in circ.values()], *[GrowArrow(a) for a in arrs], run_time=0.9)
        bl = T("BOT = the outside world", 14, YEL).next_to(circ["BOT"], UP, buff=0.1)
        self.play(FadeIn(bl), run_time=0.4)

        e1 = self.eq([("resid", YEL), (" = (", INK), ("y", BLU), (" - ", INK), ("λ", ORA), (") / sqrt(", INK), ("φ", DIM), (" · λ)", INK)], 24).move_to([2.6, 2.0, 0])
        n1 = T("y: what arrived     λ: what the graph predicted     φ: overdispersion", 14, DIM).next_to(e1, DOWN, buff=0.15)
        self.play(FadeIn(e1), FadeIn(n1), run_time=0.8)
        ex = T("(400 - 43.5) / sqrt(43.5)  ≈  54σ", 22, YEL).move_to([2.6, 0.95, 0])
        pulse = Dot(P["BOT"], radius=0.13, color=YEL)
        self.play(FadeIn(ex), MoveAlongPath(pulse, Line(P["BOT"], P["AI"])), run_time=1.0)
        self.play(FadeOut(pulse), circ["AI"][0].animate.set_stroke(width=7), run_time=0.4)
        gauss = T("Gauss's law on a graph: attention the flows cannot explain\nmust have a source. That source is BOT.", 15, INK).move_to([2.6, 0.25, 0])
        self.play(FadeIn(gauss))
        self.wait(1.0)

        e2 = self.eq([("α[j→i]", YEL), (" = σ(η[i]/s) · Σ_m ", INK), ("A[i][j][m] · z[j][m]", ORA), (" / ", INK), ("λ_raw[i]", INK)], 22).move_to([2.6, -0.65, 0])
        n2 = T("the share of i's attention that j caused this window", 14, DIM).next_to(e2, DOWN, buff=0.12)
        e3 = self.eq([("p(BOT→i)", YEL), (" = 1 - Σ_j α[j→i]", INK)], 22).move_to([2.6, -1.75, 0])
        self.play(FadeIn(e2), FadeIn(n2), run_time=0.7)
        self.play(FadeIn(e3), run_time=0.6)
        vals = VGroup(T("p(BOT→GPU) = 0.20", 17, YEL), T("p(AI→GPU) = 0.44", 17, BLU), T("p(GPU→GPU) = 0.36", 17, GRN)).arrange(RIGHT, buff=0.5).move_to([0, -2.65, 0])
        pulse2 = Dot(P["AI"], radius=0.12, color=BLU)
        self.play(MoveAlongPath(pulse2, Line(P["AI"], P["GPU"])), run_time=0.8)
        self.play(FadeOut(pulse2), FadeIn(vals), run_time=0.6)
        self.play(FadeIn(self.bottom("These shares are the edge probabilities the search uses. Toy numbers from the design discussion.", 16)))
        self.wait(3.5)


# ============================================================================================ 7
class P07_Anomaly(Chapter):
    num, name, status = 7, "An anomaly is observed", ("PARTLY OPEN", PART_C)

    def construct(self):
        self.header()
        rng = np.random.default_rng(11)
        ars = list(rng.normal(0, 1.1, 19)) + [-16.9]
        x0, y0 = -6.3, 0.9
        axis = Line([x0, y0, 0], [x0 + 20 * 0.3, y0, 0], color=DIM, stroke_width=2)
        band = Rectangle(width=20 * 0.3, height=2 * 4.5 * 0.09, stroke_width=0, fill_color=GRID, fill_opacity=0.8).move_to([x0 + 3.0, y0, 0])
        bl = T("normal range", 13, DIM).next_to(band, UP, buff=0.06).align_to(band, LEFT)
        self.play(FadeIn(band), Create(axis), FadeIn(bl), run_time=0.7)
        bars = VGroup()
        for k, v in enumerate(ars):
            h = abs(v) * 0.09
            r = Rectangle(width=0.2, height=max(h, 0.01), stroke_width=0, fill_color=(RED if k == 19 else BLU), fill_opacity=0.9)
            r.move_to([x0 + 0.15 + k * 0.3, y0 + (h / 2 if v > 0 else -h / 2), 0])
            bars.add(r)
        self.play(LaggedStart(*[GrowFromEdge(b, UP if ars[i] < 0 else DOWN) for i, b in enumerate(bars[:19])], lag_ratio=0.05), run_time=1.4)
        self.play(GrowFromEdge(bars[19], UP), run_time=0.8)
        nv = T("NVDA, 27 Jan 2025:  -16.9%", 17, RED).next_to(bars[19], DOWN, buff=0.1).shift(LEFT * 1.5)
        self.play(FadeIn(nv), Flash(bars[19].get_bottom(), color=RED), run_time=0.7)
        cl = T("same day:  AVGO -17.4%   VST -28.3%   CEG -20.9%", 15, RED).move_to([2.7, -1.1, 0])
        ct = T("one cluster case", 14, DIM).next_to(cl, RIGHT, buff=0.25)
        self.play(FadeIn(cl), FadeIn(ct), run_time=0.7)

        e1 = self.eq([("AR[t]", RED), (" = R[t] - (", INK), ("α + β·R_m[t] + γ·R_sec[t]", BLU), (")", INK)], 21).move_to([4.3, 2.15, 0])
        n1 = T("what the market and sector would have predicted", 14, BLU).next_to(e1, DOWN, buff=0.1)
        e2 = self.eq([("Mz", RED), (" = 0.6745 · (AR - ", INK), ("median", GRN), (") / ", INK), ("MAD", GRN)], 21).move_to([4.3, 1.1, 0])
        n2 = T("robust z: one crash cannot inflate its own yardstick", 14, GRN).next_to(e2, DOWN, buff=0.1)
        e3 = T("open case if |SAR| ≥ 4 or |Mz| ≥ 5,\nand a jump test or abnormal volume agrees", 16, INK).move_to([4.3, -0.05, 0])
        for e, n in [(e1, n1), (e2, n2)]:
            self.play(FadeIn(e), FadeIn(n), run_time=0.7)
        self.play(FadeIn(e3), run_time=0.7)
        cut = T("cutoff τ* = earliest first abnormal print in the cluster (pre-market or the European open)", 16, YEL).move_to([0, -1.6, 0])
        self.play(FadeIn(cut))
        seis = T("A seismometer trigger: only a jolt far beyond background noise opens an investigation.", 17, INK).move_to([0, -2.35, 0])
        self.play(FadeIn(seis))
        self.play(FadeIn(self.bottom("Open: price data source (no intraday prices obtained yet), thresholds, overnight-gap cutoff. Earlier bars are illustrative.", 15, PART_C)))
        self.wait(3.5)


# ============================================================================================ 8
class P08_Search(Chapter):
    num, name, status = 8, "Searching for the smallest explanation", ("SPECIFIED", OK_C)

    def construct(self):
        self.header()
        P = {"BOT": (-1.7, 2.35), "R1": (-5.4, 1.25), "App": (-3.3, 1.25), "Capex": (-0.1, 1.25), "Chip": (2.3, 1.25),
             "Power": (-5.3, 0.15), "NVDA": (-1.6, -0.8), "VST": (1.4, -0.8), "Elect": (5.4, 1.9), "Crypto": (5.4, 0.3)}
        names = {"BOT": "BOT", "R1": "R1 release", "App": "App surge", "Capex": "Capex", "Chip": "Chip count", "Power": "Power demand",
                 "NVDA": "NVDA -17%", "VST": "VST -28%", "Elect": "Elections", "Crypto": "Crypto"}
        node = {}
        for k, (x, y) in P.items():
            c = YEL if k == "BOT" else (RED if k in ("NVDA", "VST") else INK)
            node[k] = self.node(names[k], [x, y, 0], color=c, size=15, w=max(1.15, 0.2 + 0.15 * len(names[k])))
        E = [("BOT", "R1"), ("BOT", "App"), ("BOT", "Capex"), ("BOT", "Chip"), ("R1", "App"), ("R1", "NVDA"), ("R1", "Power"),
             ("Power", "VST"), ("App", "NVDA"), ("Capex", "NVDA"), ("Capex", "VST"), ("Chip", "NVDA"), ("Elect", "Crypto"), ("Crypto", "NVDA")]
        edge = {e: link(node[e[0]], node[e[1]], stroke_width=2, tip_length=0.12,
                        color=GRID if ("Elect" in e or "Crypto" in e) else DIM) for e in E}
        abst = [link(node["BOT"], node[t], DashedLine, color=YEL, stroke_width=2, dash_length=0.09) for t in ("NVDA", "VST")]
        self.play(*[FadeIn(n) for n in node.values()], run_time=0.7)
        self.play(*[GrowArrow(e) for e in edge.values()], *[Create(d) for d in abst], run_time=1.0)
        self.bring_to_front(*node.values())

        e1 = self.eq([("c(u→v)", INK), (" = ", INK), ("-log p(u→v)", ORA), (" + ", INK), ("λ_node", VIO)], 23).move_to([-2.4, -1.75, 0])
        l1 = T("surprise of the edge, in nats", 14, ORA).next_to(e1, DOWN, buff=0.35).align_to(e1, LEFT).shift(LEFT * 0.9)
        l2 = T("price per extra node (parsimony)", 14, VIO).next_to(e1, DOWN, buff=0.35).align_to(e1, RIGHT).shift(RIGHT * 1.1)
        n1a = VGroup(l1, Arrow(l1.get_top(), e1[2].get_bottom(), buff=0.05, stroke_width=2, color=ORA, tip_length=0.1))
        n1b = VGroup(l2, Arrow(l2.get_top(), e1[4].get_bottom(), buff=0.05, stroke_width=2, color=VIO, tip_length=0.1))
        energy = T("Physics: cost is energy, the best\nexplanation is the ground state,\nrivals are excited states with\nodds exp(-ΔE).", 15, INK).move_to([4.6, -1.85, 0])
        self.play(FadeIn(e1), run_time=0.6)
        self.play(FadeIn(n1a), FadeIn(n1b), FadeIn(energy), run_time=0.8)
        self.wait(1.2)
        self.play(FadeOut(VGroup(e1, n1a, n1b, energy)), run_time=0.4)

        step = T("1. push probability mass backwards from the events", 18, INK).move_to([-1.5, -1.6, 0])
        R = T("leftover mass R = 1.00", 17, INK).move_to([-1.5, -2.15, 0])
        self.play(FadeIn(step), FadeIn(R), run_time=0.5)
        for wave, rs in zip([["NVDA", "VST"], ["R1", "App", "Capex", "Chip", "Power"], ["BOT"]], ["0.34", "0.06", "0.02"]):
            self.play(*[node[k][0].animate.set_fill(BLU, opacity=0.25) for k in wave],
                      Transform(R, T(f"leftover mass R = {rs}", 17, INK).move_to([-1.5, -2.15, 0])), run_time=0.7)
        self.play(node["Elect"].animate.set_opacity(0.4), node["Crypto"].animate.set_opacity(0.4), run_time=0.4)

        step2 = T("2. exact dynamic programming over states (node, set of events)", 18, INK).move_to([-1.0, -1.6, 0])
        rec = VGroup(T("grow:   T(u, X)  ≤  T(v, X) + c(u→v)", 16, BLU), T("merge:  T(v, X ∪ Y)  ≤  T(v, X) + T(v, Y)", 16, BLU)).arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to([-1.0, -2.3, 0])
        self.play(Transform(step, step2), FadeOut(R), FadeIn(rec), run_time=0.7)
        best = [("BOT", "R1"), ("R1", "NVDA"), ("R1", "Power"), ("Power", "VST")]
        self.play(*[edge[e].animate.set_color(YEL).set_stroke(width=5) for e in best], run_time=1.0)
        self.bring_to_front(*node.values())
        th = T("Theorem 12.1: the first time (BOT, all events) is popped, its cost is optimal", 15, DIM).move_to([-1.0, -3.0, 0])
        self.play(FadeIn(th), run_time=0.5)
        self.wait(0.8)

        self.play(FadeOut(VGroup(step, rec, th)), run_time=0.4)
        e3 = self.eq([("Γ", GRN), (" = min_x min( ", INK), ("-log(R_x / (α·(1-α)**L))", ORA), (" + λ_node,  ", INK), ("(L+1)·λ_node", VIO), (" )", INK)], 20).move_to([-0.6, -1.65, 0])
        n3 = T("no chain the push never reached can cost less than Γ", 14, DIM).next_to(e3, DOWN, buff=0.12)
        res = T("best = 5.39  ≤  Γ = 7.4   →   certified smallest explanation in the whole graph", 18, GRN).move_to([-0.3, -2.75, 0])
        self.play(FadeIn(e3), FadeIn(n3), run_time=0.7)
        self.play(FadeIn(res), run_time=0.6)
        self.play(FadeIn(self.bottom("Open: λ_node, push settings (α, ε, L), the abstention prior p0. Toy numbers.", 15, PART_C)))
        self.wait(3.5)


# ============================================================================================ 9
class P09_Competing(Chapter):
    num, name, status = 9, "Competing explanations", ("SPECIFIED", OK_C)

    def construct(self):
        self.header()

        def tree(spec, center, col):
            g = VGroup()
            nodes = {}
            for k, (lab, dx, dy, c) in spec.items():
                nodes[k] = self.node(lab, center + np.array([dx, dy, 0]), color=c, size=13, w=max(1.0, 0.18 + 0.13 * len(lab)))
            for k, (lab, dx, dy, c) in spec.items():
                pass
            return nodes

        cols = [-4.6, 0.0, 4.6]
        specs = [
            ({"B": ("BOT", 0, 1.5, YEL), "R": ("R1 release", 0, 0.6, INK), "P": ("Power", 0.9, -0.3, INK), "N": ("NVDA", -0.8, -1.2, RED), "V": ("VST", 0.9, -1.2, RED)},
             [("B", "R"), ("R", "N"), ("R", "P"), ("P", "V")], "through R1 release", "cost 5.39  ·  best"),
            ({"B": ("BOT", 0, 1.5, YEL), "C": ("Capex", 0, 0.45, INK), "N": ("NVDA", -0.8, -1.2, RED), "V": ("VST", 0.8, -1.2, RED)},
             [("B", "C"), ("C", "N"), ("C", "V")], "through Capex", "cost 5.79  ·  odds 1.5 : 1"),
            ({"B": ("BOT", 0, 1.5, YEL), "N": ("NVDA", -0.8, -1.2, RED), "V": ("VST", 0.8, -1.2, RED)},
             [("B", "N"), ("B", "V")], "\"we do not know\"", "cost 6.59  ·  odds 3.3 : 1"),
        ]
        groups = []
        for (spec, edges, title, cost), x in zip(specs, cols):
            nodes = tree(spec, np.array([x, 0.5, 0]), INK)
            es = VGroup(*[link(nodes[a], nodes[b], stroke_width=3, tip_length=0.12, color=YEL) if title != "\"we do not know\"" else
                          link(nodes[a], nodes[b], DashedLine, stroke_width=2.5, color=YEL, dash_length=0.09) for a, b in edges])
            tt = T(title, 17, INK).move_to([x, 2.6, 0])
            cc = T(cost, 16, YEL).move_to([x, -1.25, 0])
            g = VGroup(es, *nodes.values(), tt, cc)
            groups.append(g)
        for g in groups:
            self.play(FadeIn(g), run_time=0.9)
        rule = T("best explanation through each entry point (Lemma 11.2); report all within log 20 of the best", 17, INK).move_to([0, -1.95, 0])
        self.play(FadeIn(rule))
        corr_t = T("Correction: the search generates the competing explanations. clingo never invents them; it judges them.", 17, ORA)
        corr_s = T("Open-ended abduction would be Σ2P-complete; judging a fixed list stays inside NP and coNP.", 15, DIM)
        corr = VGroup(corr_t, corr_s).arrange(DOWN, buff=0.1).move_to([0, -2.85, 0])
        self.play(FadeIn(corr))
        self.wait(4)


# ============================================================================================ 10
class P10_Clingo(Chapter):
    num, name, status = 10, "From subgraph to clingo verdicts", ("PARTLY DESIGNED", PART_C)

    def construct(self):
        self.header()
        g_lab = T("graph-derived facts: deterministic", 16, OK_C).move_to([-3.7, 2.55, 0])
        e_lab = T("evidence facts: need claim extraction", 16, NO_C).move_to([3.4, 2.55, 0])
        self.play(FadeIn(g_lab), FadeIn(e_lab), run_time=0.5)
        gf = VGroup(*[Mono(s, 14, OK_C) for s in [
            "trigger(h1, ev_r1).", "before(ev_r1, move).", "trigger(h3, ev_r1).",
            "schema_refuter(h3, excludes_prior(v3)).", "trigger(h6, ev_surge).", "signature_ok(h6)."]]).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([-3.7, 1.35, 0])
        ef = VGroup(*[Mono(s, 14, NO_C) for s in [
            "reported(r17, deepseek, occurred(ev_r1), d0120).", "reported(r02, arxiv_v3, excludes_prior(v3), d1227).",
            "reported(r31, outlet_a, all_in_cost_5m(v3), d0126).", "contrary(all_in_cost_5m(v3), excludes_prior(v3)).",
            "tier(arxiv_v3, 1).   tier(outlet_a, 2)."]]).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([3.4, 1.35, 0])
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in gf], lag_ratio=0.15), run_time=1.4)
        self.play(LaggedStart(*[FadeIn(l, shift=LEFT * 0.1) for l in ef], lag_ratio=0.15), run_time=1.4)
        nd = T("NOT DESIGNED: turning article text into reported(...) facts", 14, NO_C).next_to(ef, DOWN, buff=0.15)
        self.play(FadeIn(nd), run_time=0.5)

        rules = VGroup(*[Mono(s, 14, INK) for s in [
            "ok(R)       :- reported(R,_,_,_), not defeated(R).          % assume a report is accurate...",
            "defeated(R) :- contrary report R2 is ok, independent, tier(R2) <= tier(R).   % ...unless overridden",
            "holds(L)    :- reported(R,_,L,_), ok(R).",
            "refuted(H)  :- schema_refuter(H, L), holds(L).",
            "expl(H)     :- trigger(H,E), holds(occurred(E)), before(E,move), signature_ok(H), not refuted(H)."]]).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([0, -0.85, 0])
        self.play(LaggedStart(*[FadeIn(r) for r in rules], lag_ratio=0.2), run_time=1.6)
        self.wait(1.5)
        self.play(FadeOut(VGroup(gf, ef, nd, rules, g_lab, e_lab)), run_time=0.5)

        # stable models = consistent readings
        w1 = VGroup(RoundedRectangle(width=3.2, height=1.5, corner_radius=0.12, stroke_color=BLU), T("reading 1:\nchip-smuggling report accepted\n→ expl(h4)", 14, BLU))
        w2 = VGroup(RoundedRectangle(width=3.2, height=1.5, corner_radius=0.12, stroke_color=ORA), T("reading 2:\nequal-tier denial accepted\n→ refuted(h4)", 14, ORA))
        for w in (w1, w2):
            w[1].move_to(w[0])
        worlds = VGroup(w1, w2).arrange(RIGHT, buff=0.4).move_to([-3.6, 1.35, 0])
        wt = T("each consistent reading is a stable model", 16, INK).next_to(worlds, UP, buff=0.15)
        self.play(FadeIn(wt), FadeIn(worlds), run_time=0.8)
        defs = VGroup(*[T(s, 15, INK) for s in [
            "bIN:  expl(H) in some reading      cIN:  in every reading",
            "bOUT: refuted(H) in some reading   cOUT: in every reading"]]).arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to([3.4, 1.4, 0])
        self.play(FadeIn(defs), run_time=0.6)

        hdr = ["", "bIN", "cIN", "bOUT", "cOUT", "verdict"]
        rows = [("H1 R1 efficiency shock", ".", ".", ".", ".", ("CONSISTENT-BUT-UNPROVEN", BLU)),
                ("H3 $5.6M all-in cost", ".", ".", "✓", "✓", ("CONTRADICTED", RED)),
                ("H4 chip smuggling", "✓", ".", "✓", ".", ("UNRESOLVED", ORA)),
                ("H6 attention cascade", "✓", "✓", ".", ".", ("SUPPORTED", GRN))]
        xs = [-4.6, -1.6, -0.8, 0.0, 0.8, 3.3]
        table = VGroup()
        for c, h in enumerate(hdr):
            table.add(T(h, 14, DIM).move_to([xs[c], -0.2, 0]))
        for r, row in enumerate(rows):
            y = -0.7 - r * 0.48
            for c, cell in enumerate(row):
                if c == 5:
                    table.add(T(cell[0], 15, cell[1]).move_to([xs[c], y, 0]))
                elif c == 0:
                    table.add(T(cell, 15, INK).move_to([xs[c], y, 0]).align_to(np.array([-6.2, 0, 0]), LEFT))
                else:
                    table.add(T(cell, 15, INK).move_to([xs[c], y, 0]))
        self.play(LaggedStart(*[FadeIn(m) for m in table], lag_ratio=0.02), run_time=1.6)
        self.play(FadeIn(self.bottom("Illustrative facts; the verdicts match the report's predictions. Any reading that refutes H is surfaced as UNRESOLVED.", 15)))
        self.wait(4)


# ============================================================================================ 11
class P11_Lean(Chapter):
    num, name, status = 11, "Certificates and the dossier", ("DESIGNED · NOT BUILT", PART_C)

    def construct(self):
        self.header()
        a = self.node("clingo + CaDiCaL\n(untrusted)", [-5.2, 1.4, 0], color=DIM, size=15, w=2.6)
        b = self.node("certificates\nwitness models · LRAT proofs", [-1.6, 1.4, 0], color=ORA, size=15, w=3.4)
        c = self.node("Lean 4 checker\n(proved sound once)", [2.2, 1.4, 0], color=GRN, size=15, w=3.0)
        ab, bc = link(a, b, stroke_width=3, color=DIM, tip_length=0.15), link(b, c, stroke_width=3, color=DIM, tip_length=0.15)
        self.play(FadeIn(a), run_time=0.5)
        self.play(GrowArrow(ab), FadeIn(b), run_time=0.7)
        self.play(GrowArrow(bc), FadeIn(c), run_time=0.7)
        thm = VGroup(Mono("theorem nvda_h3 : verdict P_pre h3 = .contradicted", 15, GRN),
                     Mono("#print axioms nvda_h3   -- records if the compiler was trusted", 15, DIM)).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([-0.8, 0.0, 0])
        self.play(FadeIn(thm), run_time=0.8)
        lim = T("Lean proves: given this program, the verdict is V.  Whether the program matches the world is outside any proof.", 15, INK).move_to([0, -0.85, 0])
        self.play(FadeIn(lim), run_time=0.6)

        doss = VGroup(*[T(s, 15, col) for s, col in [
            ("Dossier: NVDA -16.9%, 27 Jan 2025 (cluster: AVGO, VST, CEG)", INK),
            ("best: R1 release → AI attention → chips and power demand    odds 1.0", YEL),
            ("rival: capex worries    odds 1.5 : 1        \"we do not know\"    odds 3.3 : 1", INK),
            ("H3 $5.6M all-in: CONTRADICTED   H4 chips: UNRESOLVED   H6 cascade: SUPPORTED", INK),
            ("every claim linked to its sources; pre-cutoff and post-cutoff evidence kept apart", DIM)]]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        frame = SurroundingRectangle(doss, color=YEL, buff=0.25, corner_radius=0.12)
        dg = VGroup(frame, doss).move_to([0, -2.35, 0])
        self.play(Create(frame), LaggedStart(*[FadeIn(d) for d in doss], lag_ratio=0.2), run_time=1.6)
        self.play(FadeIn(self.bottom("Open: kernel-only Lean speed at 10k-100k clauses was never benchmarked; no Lean library for ASP semantics exists yet.", 14, PART_C)))
        self.wait(4)


# ============================================================================================ 12
class P12_Readiness(Chapter):
    num, name, status = 12, "What is ready, and what is not", ("SUMMARY", DIM)

    def construct(self):
        self.header()
        items = [
            ("Specified, with proofs where needed", OK_C, "ingestion · dedup · clocks · attention equations · transition weights · search and certificate · verdict semantics"),
            ("Specified, not fitted", PART_C, "attention model: needs the 6-27 Jan 2025 GDELT replay (not downloaded yet)"),
            ("Partly open", PART_C, "narrative seeds and calibration · price data and trigger thresholds · λ_node, push settings, p0 · Lean trust policy"),
            ("Not designed yet", NO_C, "claim extraction into reported(...) facts · explanation schemas per hypothesis type · source-tier policy"),
            ("Not built", NO_C, "everything: there is no code yet"),
        ]
        rows = VGroup()
        for head, col, body in items:
            sq = Square(0.24, color=col, fill_opacity=0.9, stroke_width=0)
            h = T(head, 20, INK)
            b = T(body, 15, DIM)
            line = VGroup(VGroup(sq, h).arrange(RIGHT, buff=0.2), b).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            rows.add(line)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, 0.0, 0])
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.2), run_time=0.8)
        self.play(FadeIn(self.bottom("For 10 October: every layer present in its simplest provable form, with SerpApi as the evidence sensor.", 17, INK)))
        self.wait(4)
