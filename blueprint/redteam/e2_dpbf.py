"""E2: directed DPBF (as in the blueprint) vs brute-force enumeration of arborescences."""
import heapq, itertools, random, sys
def dpbf(n, edges, root, T):
    par = {v: [] for v in range(n)}
    for (u, v), c in edges.items(): par[v].append((u, c))
    full = frozenset(T); heap = []; done = {}; byv = {v: [] for v in range(n)}
    for x in T: heapq.heappush(heap, (0, x, tuple(sorted([x]))))
    while heap:
        val, v, Xt = heapq.heappop(heap); X = frozenset(Xt)
        if (v, X) in done: continue
        done[(v, X)] = val; byv[v].append(X)
        if v == root and X == full: return val
        for u, c in par[v]:
            if (u, X) not in done: heapq.heappush(heap, (val + c, u, Xt))
        for Y in byv[v]:
            if not (X & Y): heapq.heappush(heap, (val + done[(v, Y)], v, tuple(sorted(X | Y))))
    return None
def brute(n, edges, root, T):
    E = list(edges); best = None
    for s in range(1, n):
        for sub in itertools.combinations(E, s):
            indeg = {}; ok = True
            for u, v in sub:
                if v == root or v in indeg: ok = False; break
                indeg[v] = u
            if not ok: continue
            nodes = set(indeg) | {root}
            if not set(T) <= nodes: continue
            if any(u not in nodes for u in indeg.values()): continue
            # every node must reach root through parents (no cycles)
            good = True
            for v in indeg:
                seen = set(); w = v
                while w != root:
                    if w in seen: good = False; break
                    seen.add(w); w = indeg[w]
                if not good: break
            if not good: continue
            c = sum(edges[e] for e in sub)
            if best is None or c < best: best = c
    return best
rng = random.Random(11); N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
mism = feasible = 0
for it in range(N):
    n = rng.randint(3, 7); root = 0; k = rng.randint(1, min(3, n - 1)); T = rng.sample(range(1, n), k)
    p = rng.uniform(0.25, 0.6); edges = {}
    for u in range(n):
        for v in range(n):
            if u != v and v != root and rng.random() < p and len(edges) < 14: edges[(u, v)] = rng.randint(0, 9)
    a, b = dpbf(n, edges, root, T), brute(n, edges, root, T)
    feasible += b is not None; mism += a != b
print(f"E2 directed instances: {N} (3-7 nodes, 1-3 terminals, integer costs 0-9 incl. zero, random directions)")
print(f"   feasible: {feasible}   DPBF != brute force: {mism}")
