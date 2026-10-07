"""E2 (red-team): directed DPBF equals brute-force enumeration; plus rivals (Lemma 11.2) and abstention."""
import itertools
import random

from ygg.search.dpbf import Graph, rivals, solve


def brute(g: Graph):
    E = sorted(g.cost)
    best = None
    for s in range(1, g.n):
        for sub in itertools.combinations(E, s):
            par = {}
            ok = True
            for u, v in sub:
                if v == g.root or v in par:
                    ok = False
                    break
                par[v] = u
            if not ok or not set(g.terminals) <= set(par) | {g.root}:
                continue
            nodes = set(par) | {g.root}
            if any(u not in nodes for u in par.values()):
                continue
            good = True
            for v in par:
                seen, w = set(), v
                while w != g.root:
                    if w in seen:
                        good = False
                        break
                    seen.add(w)
                    w = par[w]
                if not good:
                    break
            if good:
                c = sum(g.cost[e] for e in sub)
                best = c if best is None or c < best else best
    return best


def test_e2_dpbf_matches_brute_force():
    rng = random.Random(11)
    feasible = 0
    for _ in range(250):
        n = rng.randint(3, 7)
        k = rng.randint(1, min(3, n - 1))
        terms = rng.sample(range(1, n), k)
        p = rng.uniform(0.25, 0.6)
        cost = {}
        for u in range(n):
            for v in range(1, n):
                if u != v and rng.random() < p and len(cost) < 13:
                    cost[(u, v)] = rng.randint(0, 9)
        g = Graph(n, 0, terms, cost)
        b = brute(g)
        a, edges = solve(g)
        feasible += b is not None
        assert (a == float("inf") and b is None) or a == b
        if b is not None:
            assert sum(cost[e] for e in edges) == a
    assert feasible > 100


def test_shared_trunk_beats_two_stories_and_abstention_exists():
    # 0 = BOT, 1 = R1, 2 = AI, 3 = chips story, 4 = power story, 5 = politics hub, 6 = chips terminal, 7 = power terminal
    c = {(0, 1): 900, (1, 2): 800, (2, 3): 1100, (2, 4): 1600, (3, 6): 500, (4, 7): 900,
         (0, 5): 400, (5, 6): 3400, (5, 7): 3500, (0, 6): 3300, (0, 7): 3300}
    g = Graph(8, 0, [6, 7], c)
    cost, edges = solve(g)
    assert cost == 5800 and (0, 1) in edges and (0, 6) not in edges
    rv = rivals(g, cost, window=2996)                     # ln 20 = 2.996 nats in milli-nats
    entries = {r["entry"]: r["cost"] for r in rv}
    assert entries[1] == 5800 and entries[5] == 7300


def test_abstention_wins_when_no_story_is_cheap():
    c = {(0, 1): 2000, (1, 2): 3000, (0, 2): 3300}
    cost, edges = solve(Graph(3, 0, [2], c))
    assert cost == 3300 and edges == {(0, 2)}
