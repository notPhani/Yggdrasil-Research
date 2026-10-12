"""The event cutoff tau* is a session start derived from daily bars, never an observed intraday print.
Amsterdam opens 09:00 local: 08:00 UTC in winter, 07:00 UTC in summer. US: 04:00 ET pre-market for a gap
shock, otherwise the 09:30 ET regular open, both DST-aware."""
from ygg.observer.trigger import Thresholds, first_abnormal_utc

TH = Thresholds()


def _utc(st, day):
    t = first_abnormal_utc(st, day, TH)
    return t.hour, t.minute


def test_amsterdam_open_follows_dst():
    assert _utc({"symbol": "ASM.AS", "Mg": 0.0}, "2025-01-27") == (8, 0)     # CET: unchanged for the recorded case
    assert _utc({"symbol": "ASM.AS", "Mg": 0.0}, "2025-07-14") == (7, 0)     # CEST


def test_us_cutoff_is_premarket_for_a_gap_shock_else_the_regular_open():
    assert _utc({"symbol": "EIX", "Mg": 0.0}, "2025-01-13") == (14, 30)      # the recorded 13 Jan cutoff
    assert _utc({"symbol": "EIX", "Mg": -9.0}, "2025-01-13") == (9, 0)
    assert _utc({"symbol": "EIX", "Mg": 0.0}, "2025-07-14") == (13, 30)
