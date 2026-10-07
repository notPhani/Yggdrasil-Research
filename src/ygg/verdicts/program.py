"""Engine 3b verdicts (decisions 6.6, A4; Theorems 14.1 and 14.4): evidence as a tight normal logic program.

Facts come from typed claim tuples and Engine 2's own measurements (tier 0). Per hypothesis H, four bits:
  bIN = expl(H) in some stable model,     cIN = expl(H) in every stable model
  bOUT = refuted(H) in some stable model, cOUT = refuted(H) in every stable model
  SUPPORTED iff cIN; CONTRADICTED iff cOUT; UNRESOLVED iff bOUT and not cOUT; else CONSISTENT-BUT-UNPROVEN
Theorem 14.4: this template always has a stable model, so INCOHERENT-EVIDENCE is reachable only if extra
rules are added. Those are caught by the per-program tightness check (A4), which also gates the Lean path.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import clingo

TEMPLATE = r"""
contrary(X, Y) :- contrary(Y, X).
independent(R1, R2) :- reported(R1, S1, _, _), reported(R2, S2, _, _), owner(S1, O1), owner(S2, O2), O1 != O2,
                       group(R1, G1), group(R2, G2), G1 != G2.
ok(R)       :- reported(R, _, _, _), not defeated(R).
holds(L)    :- reported(R, _, L, _), ok(R).
defeated(R) :- reported(R, S, L, _), contrary(L, L2), reported(R2, S2, L2, _), ok(R2),
               independent(R, R2), tier(S, K), tier(S2, K2), K2 <= K.
defeated(R) :- retracted(R).
defeated(R) :- copy_of(R, _).
refuted(H)  :- schema_refuter(H, L), holds(L).
corroborated(E) :- reported(R, S, occurred(E), _), ok(R), tier(S, K), K <= 2.
corroborated(E) :- reported(R1, _, occurred(E), _), ok(R1), reported(R2, _, occurred(E), _), ok(R2), independent(R1, R2).
expl(H)     :- trigger(H, E), holds(occurred(E)), corroborated(E), before(E, move), signature_ok(H), not refuted(H).
hyp(H) :- trigger(H, _).
#show expl/1. #show refuted/1. #show hyp/1.
"""
VERDICTS = ("SUPPORTED", "CONTRADICTED", "UNRESOLVED", "CONSISTENT-BUT-UNPROVEN")


class _Observer:
    def __init__(self):
        self.edges: dict[int, set[int]] = {}

    def rule(self, choice, head, body):
        for h in head:
            self.edges.setdefault(h, set()).update(b for b in body if b > 0)


def is_tight(edges: dict[int, set[int]]) -> bool:
    """A4: no cycle through positive dependencies (iterative Tarjan-free check via DFS colouring)."""
    color: dict[int, int] = {}
    for start in sorted(edges):
        if color.get(start):
            continue
        stack = [(start, iter(sorted(edges.get(start, ()))))]
        color[start] = 1
        while stack:
            v, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                color[v] = 2
                stack.pop()
            elif color.get(nxt) == 1:
                return False
            elif not color.get(nxt):
                color[nxt] = 1
                stack.append((nxt, iter(sorted(edges.get(nxt, ())))))
    return True


def _consequences(program: str, mode: str) -> tuple[set[str] | None, int]:
    args = ["0"] if mode == "all" else ["0", f"--enum-mode={mode}"]
    ctl = clingo.Control(args + ["--warn=none"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    last, n = None, 0
    with ctl.solve(yield_=True) as h:
        for m in h:
            last = {str(s) for s in m.symbols(shown=True)}
            n += 1
    return last, n


@dataclass
class Verdicts:
    bits: dict = field(default_factory=dict)       # H -> (bIN, cIN, bOUT, cOUT)
    verdict: dict = field(default_factory=dict)    # H -> label
    n_models: int = 0
    tight: bool = True
    incoherent: bool = False


def decide(facts: str) -> Verdicts:
    program = TEMPLATE + "\n" + facts
    obs = _Observer()
    ctl = clingo.Control(["--warn=none"])
    ctl.register_observer(obs)
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    tight = is_tight(obs.edges)
    brave, _ = _consequences(program, "brave")
    cautious, _ = _consequences(program, "cautious")
    out = Verdicts(tight=tight)
    if brave is None:                        # unreachable under the template (Theorem 14.4)
        out.incoherent = True
        return out
    out.n_models = count_models(program)
    hyps = sorted(x[4:-1] for x in cautious if x.startswith("hyp("))
    for h in hyps:
        b_in, c_in = f"expl({h})" in brave, f"expl({h})" in cautious
        b_out, c_out = f"refuted({h})" in brave, f"refuted({h})" in cautious
        out.bits[h] = (int(b_in), int(c_in), int(b_out), int(c_out))
        out.verdict[h] = ("SUPPORTED" if c_in else "CONTRADICTED" if c_out else "UNRESOLVED" if b_out else "CONSISTENT-BUT-UNPROVEN")
    return out


def count_models(program: str, cap: int = 1000) -> int:
    ctl = clingo.Control([str(cap), "--warn=none"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    n = 0
    with ctl.solve(yield_=True) as h:
        for _ in h:
            n += 1
    return n


def diagnosticity(facts_lines: list[str], hyp: str, base: Verdicts) -> list[str]:
    """Evidence items (reported/1 facts) whose removal flips the verdict of hyp (n + 1 solver runs)."""
    flips = []
    for i, line in enumerate(facts_lines):
        if not line.startswith("reported("):
            continue
        v = decide("\n".join(facts_lines[:i] + facts_lines[i + 1:]))
        if v.verdict.get(hyp) != base.verdict.get(hyp):
            flips.append(line)
    return flips


def atom(s: str) -> str:
    """Make a clingo constant from arbitrary text: lowercase, [a-z0-9_], starting with a letter."""
    import re
    t = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "x"
    return t if t[0].isalpha() else "x_" + t
