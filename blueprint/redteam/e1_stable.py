"""E1: does the locked verdict template always have a stable model? + per-program tightness check."""
import clingo, random, sys
TEMPLATE = r"""
contrary(X, Y) :- contrary(Y, X).
independent(R1, R2) :- reported(R1, S1, _, _), reported(R2, S2, _, _), owner(S1, O1), owner(S2, O2), O1 != O2.
ok(R)       :- reported(R, _, _, _), not defeated(R).
holds(L)    :- reported(R, _, L, _), ok(R).
defeated(R) :- reported(R, S, L, _), contrary(L, L2), reported(R2, S2, L2, _), ok(R2),
               independent(R, R2), tier(S, K), tier(S2, K2), K2 <= K.
defeated(R) :- retracted(R).
defeated(R) :- copy_of(R, _).
refuted(H)  :- schema_refuter(H, L), holds(L).
expl(H)     :- trigger(H, E), holds(occurred(E)), before(E, move), signature_ok(H), not refuted(H).
"""
class Obs:
    def __init__(s): s.edges = {}
    def rule(s, choice, head, body):
        for h in head:
            s.edges.setdefault(h, set()).update(b for b in body if b > 0)
def tight(edges):
    idx, low, st, on, cnt, comp = {}, {}, [], set(), [0], []
    sys.setrecursionlimit(100000)
    def sc(v):
        idx[v] = low[v] = cnt[0]; cnt[0] += 1; st.append(v); on.add(v)
        for w in edges.get(v, ()):
            if w not in idx: sc(w); low[v] = min(low[v], low[w])
            elif w in on: low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            c = []
            while True:
                w = st.pop(); on.discard(w); c.append(w)
                if w == v: break
            comp.append(c)
    for v in list(edges):
        if v not in idx: sc(v)
    return all(len(c) == 1 and c[0] not in edges.get(c[0], ()) for c in comp)
def solve(prog):
    ctl = clingo.Control(["1"]); o = Obs(); ctl.register_observer(o)
    ctl.add("base", [], TEMPLATE + prog); ctl.ground([("base", [])])
    return ctl.solve().satisfiable, tight(o.edges)
rng = random.Random(7); N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
empty = nontight = 0; maxrep = 0
for it in range(N):
    nl = rng.randint(2, 8); ns = rng.randint(2, 6); nr = rng.randint(2, 14); maxrep = max(maxrep, nr)
    f = []
    for s in range(ns): f += [f"tier(s{s},{rng.randint(0,3)}).", f"owner(s{s},o{rng.randint(0,ns-1)})."]
    for a in range(nl):
        for b in range(a + 1, nl):
            if rng.random() < 0.45: f.append(f"contrary(l{a},l{b}).")
    for r in range(nr):
        f.append(f"reported(r{r},s{rng.randrange(ns)},l{rng.randrange(nl)},t).")
        if rng.random() < 0.08: f.append(f"retracted(r{r}).")
        if r and rng.random() < 0.1: f.append(f"copy_of(r{r},r{rng.randrange(r)}).")
    sat, tg = solve("\n".join(f))
    empty += not sat; nontight += not tg
print(f"E1 random programs: {N} (up to {maxrep} reports, dense contrary pairs, 4 tiers, shared owners)")
print(f"   with NO stable model: {empty}    non-tight: {nontight}")
# control: a bridge loop must be flagged non-tight
sat, tg = solve("reported(r1,s1,a,t). tier(s1,1). owner(s1,o1).\nholds(b) :- holds(a).\nholds(a) :- holds(b).")
print(f"   control (bridge rules holds(a)<->holds(b)): tight = {tg}  (must be False)")
# control: an asymmetric undercut cycle CAN be incoherent -> shows the checker would catch it
ctl = clingo.Control(["1"]); ctl.add("base", [], "a :- not b. b :- not c. c :- not a."); ctl.ground([("base", [])])
print(f"   control (odd negative cycle a<-not b<-not c<-not a): satisfiable = {ctl.solve().satisfiable}  (must be False)")
