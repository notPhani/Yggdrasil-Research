import random
from datetime import timedelta

from ygg.determinism import WindowClock, exact_sum, keyed_rng, parse_utc, stable_hash, tie_key


def test_window_clock_maps_batches_to_windows():
    clk = WindowClock(parse_utc("2024-12-16"))
    assert clk.window_of(parse_utc("20241216000000")) == 0
    assert clk.window_of(parse_utc("20241216001459")) == 0
    assert clk.window_of(parse_utc("20241216001500")) == 1
    assert clk.window_of(parse_utc("20250127080000")) == 42 * 96 + 32
    assert clk.end(5) - clk.start(5) == timedelta(minutes=15)


def test_d1_ingested_time_is_observed_plus_lag():
    clk = WindowClock(parse_utc("2024-12-16"))
    obs = parse_utc("20250127074500")
    assert clk.ingested_time(obs) == parse_utc("20250127080000")


def test_d7_fit_cutoff_is_start_of_day():
    clk = WindowClock(parse_utc("2024-12-16"))
    t = clk.window_of(parse_utc("20250127153000"))
    assert clk.fit_cutoff(t) == parse_utc("2025-01-27")


def test_d2_keyed_rng_reproducible_and_key_sensitive():
    a = keyed_rng("cfg", "r1").random(5)
    b = keyed_rng("cfg", "r1").random(5)
    c = keyed_rng("cfg", "r2").random(5)
    d = keyed_rng("cfg2", "r1").random(5)
    assert (a == b).all() and not (a == c).all() and not (a == d).all()


def test_d3_exact_sum_is_order_independent():
    vals = [1e16, 1.0, -1e16, 3.14159, 2.5e-9] * 50
    shuffled = vals[:]
    random.Random(0).shuffle(shuffled)
    assert exact_sum(vals) == exact_sum(shuffled)


def test_d4_tie_key_orders_totally():
    t = parse_utc("20250127080000")
    recs = [tie_key(t, 1, "b", "x"), tie_key(t, 0, "z", "y"), tie_key(t, 1, "a", "z")]
    assert sorted(recs)[0][1] == 0 and sorted(recs)[1][2] == "a"


def test_stable_hash_is_length_prefixed():
    assert stable_hash("ab", "c") != stable_hash("a", "bc")
