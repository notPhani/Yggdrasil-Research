"""Placebo calibration (decision 5.13, K = 20 in the cut): run the identical search where nothing happened.

Cutoffs are drawn with a keyed Philox stream (D2) from trading-hour windows on days where the US market was
open and the trigger fired on nothing. Each placebo gets the same number of terminals as the real case,
built from instruments that did not move abnormally that day (|SAR| < 1). The outputs:
  FER         share of placebo terminals given a non-abstention explanation (target <= 5%)
  hub freq    share of placebo explanations containing each narrative
  p_emp       (1 + #placebo best costs <= real best cost) / (1 + K)
"""
from __future__ import annotations

from datetime import datetime, timezone

from ygg.determinism import WindowClock, keyed_rng
from ygg.observer.trigger import build_case


def placebo_days(prices: list[dict], actions: list[dict], etfs: set[str], start: str, end: str) -> tuple[list[str], dict]:
    spy_days = sorted({r["date"] for r in prices if r["symbol"] == "SPY" and start <= r["date"] < end})
    quiet, cases = [], {}
    for d in spy_days:
        c = build_case(d, prices, actions, etfs)
        if c["fired"]:
            cases[d] = c
        else:
            quiet.append(d)
    return quiet, cases


def placebo_cutoffs(days: list[str], clock: WindowClock, k: int, cfg_hash: str) -> list[int]:
    """k distinct windows inside 08:00-21:00 UTC on the given days, drawn with Philox (D2)."""
    pool = []
    for d in days:
        base = clock.window_of(datetime.fromisoformat(d + "T00:00:00+00:00"))
        pool += [base + w for w in range(32, 84)]            # 08:00 .. 20:45 UTC
    rng = keyed_rng(cfg_hash, "placebo-cutoffs", ",".join(days))
    pick = rng.choice(len(pool), size=min(k, len(pool)), replace=False)
    return sorted(int(pool[i]) for i in pick)


def placebo_terminals(day: str, prices: list[dict], actions: list[dict], etfs: set[str], k: int, cfg_hash: str, t: int) -> list[list[str]]:
    c = build_case(day, prices, actions, etfs)
    calm = sorted(s["symbol"] for s in c["stats"] if abs(s["SAR"]) < 1.0 and s["symbol"] not in etfs)
    rng = keyed_rng(cfg_hash, "placebo-terminals", day, str(t))
    pick = rng.choice(len(calm), size=min(k, len(calm)), replace=False)
    return [[calm[i]] for i in sorted(int(x) for x in pick)]


def empirical_p(real_cost: float, placebo_costs: list[float]) -> float:
    return (1 + sum(1 for c in placebo_costs if c <= real_cost)) / (1 + len(placebo_costs))
