"""Exact minimum-cost arborescence search (Engine 3a, decisions 5.4-5.6, Theorem 12.1, Lemma 11.2).

Costs are integers (milli-nats), so the result is replay-identical. States (v, X): the cheapest arborescence
rooted at v whose leaves include terminal set X (bitmask). Grow along an edge u -> v, merge disjoint sets at
v. With non-negative costs, the first pop of (root, all) is optimal. Ties are broken by (cost, node, mask).
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass

INF = float("inf")


@dataclass
class Graph:
    n: int
    root: int
    terminals: list[int]
    cost: dict                                   # (u, v) -> non-negative int

    def parents(self) -> list[list[tuple[int, int]]]:
        par: list[list[tuple[int, int]]] = [[] for _ in range(self.n)]
        for (u, v), c in sorted(self.cost.items()):
            par[v].append((u, c))
        return par


def dp_all(g: Graph, removed: int | None = None, stop_at_root: bool = False):
    """Run the DP to completion. Returns (Tval, back): Tval[(v, mask)] = optimal cost, back for reconstruction."""
    par = g.parents()
    k = len(g.terminals)
    full = (1 << k) - 1
    tval: dict = {}
    back: dict = {}
    by_node: dict = {}
    heap = []
    for i, x in enumerate(g.terminals):
        if x != removed:
            heapq.heappush(heap, (0, x, 1 << i, ("leaf",)))
    while heap:
        val, v, mask, how = heapq.heappop(heap)
        if (v, mask) in tval:
            continue
        tval[(v, mask)] = val
        back[(v, mask)] = how
        if stop_at_root and v == g.root and mask == full:
            break
        for u, c in par[v]:
            if u != removed and (u, mask) not in tval:
                heapq.heappush(heap, (val + c, u, mask, ("grow", v)))
        for other in by_node.get(v, []):
            if not (other & mask) and (v, other | mask) not in tval:
                heapq.heappush(heap, (val + tval[(v, other)], v, other | mask, ("merge", mask, other)))
        by_node.setdefault(v, []).append(mask)
    return tval, back


def edges_of(back: dict, v: int, mask: int) -> set[tuple[int, int]]:
    out: set = set()
    stack = [(v, mask)]
    while stack:
        v, mask = stack.pop()
        how = back[(v, mask)]
        if how[0] == "grow":
            out.add((v, how[1]))
            stack.append((how[1], mask))
        elif how[0] == "merge":
            stack += [(v, how[1]), (v, how[2])]
    return out


def as_arborescence(edges: set[tuple[int, int]], g: Graph) -> set[tuple[int, int]]:
    """Turn the DP's grow/merge structure (whose parts may share nodes) into a true arborescence: a cheapest-path
    tree from the root over the union of its edges, then prune non-terminal leaves. Every node of the union is
    reachable from the root, and the tree uses only union edges, so its cost never exceeds the DP value
    (Theorem 12.1, achievability). Ties: smaller parent id."""
    out_adj: dict = {}
    for u, v in sorted(edges):
        out_adj.setdefault(u, []).append(v)
    dist = {g.root: 0}
    parent: dict = {}
    heap = [(0, g.root)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, INF):
            continue
        for v in out_adj.get(u, []):
            nd = d + g.cost[(u, v)]
            if nd < dist.get(v, INF) or (nd == dist.get(v, INF) and u < parent.get(v, INF)):
                dist[v], parent[v] = nd, u
                heapq.heappush(heap, (nd, v))
    kept = {(u, v) for v, u in parent.items()}
    terms = set(g.terminals)
    while True:
        heads = {u for u, _ in kept}
        leaves = {v for _, v in kept if v not in heads and v not in terms}
        if not leaves:
            return kept
        kept = {(u, v) for u, v in kept if v not in leaves}


def solve(g: Graph) -> tuple[float, set[tuple[int, int]]]:
    tval, back = dp_all(g, stop_at_root=True)
    full = (1 << len(g.terminals)) - 1
    if (g.root, full) not in tval:
        return INF, set()
    e = as_arborescence(edges_of(back, g.root, full), g)
    cost = sum(g.cost[x] for x in e)
    assert cost == tval[(g.root, full)], "the cleaned tree must cost exactly the DP optimum"
    return cost, e


def rivals(g: Graph, best_cost: float, window: int) -> list[dict]:
    """Lemma 11.2: for each entry r (a child of the root), the best explanation containing (root -> r):
    OPT_r = c(root, r) + min over non-empty X of [T_full(r, X) + T_{-r}(root, T \\ X)].
    Only entries whose lower bound (with T_full in place of T_{-r}) is within `window` are solved exactly."""
    tval, back = dp_all(g)
    k = len(g.terminals)
    full = (1 << k) - 1
    out = []
    entries = sorted(v for (u, v) in g.cost if u == g.root and v not in g.terminals)
    for r in entries:
        c0 = g.cost[(g.root, r)]
        lb = min((c0 + tval.get((r, X), INF) + (tval.get((g.root, full ^ X), INF) if X != full else 0)
                  for X in range(1, full + 1)), default=INF)
        if lb > best_cost + window:
            continue
        tv_r, back_r = dp_all(g, removed=r)
        best = (INF, None)
        for X in range(1, full + 1):
            a = tval.get((r, X), INF)
            b = 0 if X == full else tv_r.get((g.root, full ^ X), INF)
            if a + b < best[0]:
                best = (c0 + a + b, X)
        if best[1] is None or best[0] > best_cost + window:
            continue
        X = best[1]
        edges = {(g.root, r)} | edges_of(back, r, X)
        if X != full:
            edges |= edges_of(back_r, g.root, full ^ X)
        tree = as_arborescence(edges, g)
        out.append({"entry": r, "cost": sum(g.cost[e] for e in tree), "edges": sorted(tree)})
    return sorted(out, key=lambda d: (d["cost"], d["entry"]))
