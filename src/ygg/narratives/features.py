"""Grouping features (decision 3.2): the reused title embedding plus cleaned, IDF-weighted entities.

IDF is causal (D7): the weights used in window t come only from documents in earlier windows, over a
trailing 7-day horizon.
"""
from __future__ import annotations

import math
from collections import Counter, deque

# known GKG misfiles: places tagged as persons (measured: "los angeles" as a person in 26 docs of one batch)
MISFILED_PERSONS = frozenset({"los angeles", "new york", "san francisco", "hong kong", "new delhi", "las vegas", "tel aviv",
                              "abu dhabi", "rio de janeiro", "buenos aires", "kuala lumpur", "sri lanka", "costa rica"})


def entities(doc: dict) -> frozenset[str]:
    persons = {p.casefold().strip() for p in (doc.get("persons") or []) if p.casefold().strip() not in MISFILED_PERSONS}
    orgs = {o.casefold().strip() for o in (doc.get("orgs") or []) if o.casefold().strip() not in MISFILED_PERSONS}
    names = {n.casefold().strip() for n in (doc.get("all_names") or []) if n.casefold().strip() not in MISFILED_PERSONS}
    return frozenset(x for x in persons | orgs | names if len(x) > 2)


class CausalIDF:
    """Document frequencies over the trailing `horizon_windows`, updated only after a window closes."""

    def __init__(self, horizon_windows: int = 7 * 96):
        self.horizon = horizon_windows
        self.df: Counter = Counter()
        self.total = 0                         # sum of df over entities
        self.n_docs = 0
        self.history: deque = deque()          # (window, Counter, n)

    def idf(self, x: str) -> float:
        return math.log((self.n_docs + 1.0) / (self.df.get(x, 0) + 1.0)) + 1.0

    def weights(self, ents: frozenset[str]) -> dict[str, float]:
        return {e: self.idf(e) for e in ents}

    def close_window(self, t: int, docs_entities: list[frozenset[str]]) -> None:
        c = Counter()
        for ents in docs_entities:
            c.update(ents)
        self.history.append((t, c, len(docs_entities)))
        self.df.update(c)
        self.total += sum(c.values())
        self.n_docs += len(docs_entities)
        while self.history and self.history[0][0] <= t - self.horizon:
            _, old, n = self.history.popleft()
            self.df.subtract(old)
            self.total -= sum(old.values())
            self.n_docs -= n
            for k in [k for k, v in old.items() if self.df[k] <= 0]:
                del self.df[k]


def weighted_jaccard(a: dict[str, float], b: dict[str, float], sum_a: float | None = None, sum_b: float | None = None) -> float:
    """sum over shared keys of min weight / sum over the union of max weight.
    Uses sum(max) = sum(a) + sum(b) - sum(min over shared keys), so the cost is O(min(|a|, |b|))."""
    if not a or not b:
        return 0.0
    small, big = (a, b) if len(a) <= len(b) else (b, a)
    num = 0.0
    for k, v in small.items():
        w = big.get(k)
        if w is not None:
            num += v if v < w else w
    sa = sum(a.values()) if sum_a is None else sum_a
    sb = sum(b.values()) if sum_b is None else sum_b
    den = sa + sb - num
    return num / den if den > 0 else 0.0
