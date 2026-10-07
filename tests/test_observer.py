from datetime import date, timedelta

import numpy as np

from ygg.observer.prices import adjusted_closes
from ygg.observer.trigger import build_case


def make_prices(shock_day_idx=300, n=320, seed=0):
    """Synthetic market: SPY, two correlated chip names, one power name, one ETF, one quiet name."""
    rng = np.random.default_rng(seed)
    days = []
    d = date(2023, 1, 2)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += timedelta(days=1)
    m = rng.normal(0.0004, 0.01, n)
    chip_factor = rng.normal(0, 0.012, n)
    power_factor = rng.normal(0, 0.012, n)
    rets = {
        "SPY": m,
        "AAA": 1.2 * m + chip_factor + rng.normal(0, 0.006, n),
        "BBB": 1.1 * m + chip_factor + rng.normal(0, 0.006, n),
        "ETF": 1.0 * m + 0.8 * chip_factor + rng.normal(0, 0.003, n),
        "PWR": 0.6 * m + power_factor + rng.normal(0, 0.006, n),
        "QUIET": 0.9 * m + rng.normal(0, 0.01, n),
    }
    shocks = {"AAA": -0.17, "BBB": -0.15, "ETF": -0.10, "PWR": -0.25}
    rows = []
    for sym, r in rets.items():
        price, vol0 = 100.0, 1e6
        for i, day in enumerate(days):
            ret = r[i] + (shocks.get(sym, 0.0) if i == shock_day_idx else 0.0)
            prev = price
            price = prev * (1 + ret)
            gap = 0.8 * ret if i == shock_day_idx else 0.2 * r[i]
            o = prev * (1 + gap)
            vol = vol0 * (4.0 if (i == shock_day_idx and sym in shocks) else float(np.exp(rng.normal(0, 0.2))))
            rows.append({"symbol": sym, "date": day, "open": round(o * 1e4), "high": round(max(o, price) * 1e4),
                         "low": round(min(o, price) * 1e4), "close": round(price * 1e4), "volume": int(vol)})
    return rows, days[shock_day_idx]


def test_trigger_finds_shocked_names_and_clusters_them():
    rows, day = make_prices()
    case = build_case(day, rows, [], etfs={"ETF"})
    assert set(case["fired"]) == {"AAA", "BBB", "ETF", "PWR"}
    assert ["AAA", "BBB", "ETF"] in case["clusters"] and ["PWR"] in case["clusters"]
    assert "QUIET" not in case["fired"]
    assert case["tau_star"].endswith("09:00:00+00:00")      # gap shocks count from the US pre-market print


def test_etf_only_cluster_is_not_a_terminal():
    rows, day = make_prices()
    case = build_case(day, rows, [], etfs={"ETF", "AAA", "BBB"})
    assert all(any(x not in {"ETF", "AAA", "BBB"} for x in g) for g in case["terminal_clusters"])


def test_dividends_adjust_but_splits_are_already_in_the_quotes():
    dates = ["2024-06-07", "2024-06-10", "2024-06-11"]
    close = np.array([1200000.0, 1210000.0, 1220000.0])
    adj = adjusted_closes(dates, close, [{"date": "2024-06-10", "kind": "split", "value": 10.0},
                                         {"date": "2024-06-11", "kind": "dividend", "value": 1.21}])
    assert adj[2] == close[2] and abs(adj[1] / close[1] - (1 - 12100 / 1210000)) < 1e-12
    assert adj[0] > 1000000                                    # no second division by the split ratio
