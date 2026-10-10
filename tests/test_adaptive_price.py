"""2a-L adaptive price of a narrative: volume term, capacity ramp, burst tilt, and determinism of the state digest."""
import math

import numpy as np

from ygg.determinism import keyed_rng
from ygg.narratives.learned import LearnedConfig, LearnedNarrativeModel, learned_config_from


def _model(d=32, **kw):
    m = LearnedNarrativeModel(d, LearnedConfig(**kw))
    rng = keyed_rng("bg-adaptive")
    for i in range(200):
        v = rng.standard_normal(d)
        m.background_add(10_000 + i, v / np.linalg.norm(v), 0.0)
    m.set_background_counts({f"c{i}": 50 for i in range(10)}, 10, 500)
    return m


def test_volume_term_is_zero_until_six_hours_then_log_ratio_clipped():
    m = _model(log_alpha=-10.0)
    assert m.vol_term() == 0.0 and m.log_alpha_now() == -10.0
    for _ in range(672 - 24):
        m.record_volume(3000)                        # a week at 3000 roots per window
    for _ in range(24):
        m.record_volume(1000)                        # a quiet night: 6 h at a third of the volume
    v6, v7 = 1000.0, (648 * 3000 + 24 * 1000) / 672
    assert abs(m.vol_term() - math.log(v6 / v7)) < 1e-9
    assert m.log_alpha_now() > -10.0                 # fewer proposals at night: a narrative is cheaper
    for _ in range(24):
        m.record_volume(3000 * 50)                   # an absurd surge is clipped
    assert m.vol_term() == LearnedConfig().vol_clip
    m.cfg.beta_tail = 30.0                           # in rate units: the same factor is worth 30 nats per e-fold
    assert m.vol_term() == 30.0 * LearnedConfig().vol_clip


def test_capacity_ramp_suppresses_births_by_e_to_minus_cap_rate_and_refunds_merges():
    m = _model(log_alpha=-10.0, k_soft=200, k_max=300, cap_rate=3.0, beta_tail=20.0)
    assert m.cap_term(150) == 0.0
    assert abs(m.cap_term(250) - 30.0) < 1e-12       # half way: e^-1.5 in rate, 1.5 x 20 nats
    assert abs(m.cap_term(300) - 60.0) < 1e-12 and abs(m.cap_term(1000) - 60.0) < 1e-12
    assert m.log_alpha_now(300) == -70.0             # births and splits pay it ...
    assert -m.log_alpha_now(300) == 70.0             # ... merges earn exactly the same amount back


def test_burst_bonus_rewards_fast_arrivals_only():
    m = _model(gamma_burst=1.0, v_ref_per_h=1.0, burst_cap=3.0)
    assert abs(m.burst_bonus(4, 0.5) - math.log(6.0)) < 1e-12     # 3 inter-arrivals in half an hour
    assert m.burst_bonus(4, 20.0) == 0.0                           # the same four events over 20 h
    assert m.burst_bonus(1, 0.0) == 0.0
    assert m.burst_bonus(50, 0.1) == 3.0                           # capped
    off = _model(adaptive=False)
    assert off.burst_bonus(4, 0.5) == 0.0 and off.vol_term() == 0.0 and off.cap_term(1000) == 0.0


def test_adaptive_off_reproduces_locked_price():
    m = _model(adaptive=False, log_alpha=-7.5)
    for _ in range(700):
        m.record_volume(5)
    assert m.log_alpha_now(400) == -7.5


def test_volume_history_is_part_of_the_state_digest():
    a, b = _model(), _model()
    assert a.canon() == b.canon()
    a.record_volume(10)
    assert a.canon() != b.canon()
    b.record_volume(10)
    assert a.canon() == b.canon()


def test_config_from_toml_table_ignores_foreign_keys():
    cfg = learned_config_from({"narratives": {"embed_model": "x", "adaptive": False, "rho_vol": 0.5, "k_max": 250}})
    assert cfg.adaptive is False and cfg.rho_vol == 0.5 and cfg.k_max == 250 and cfg.kappa_s == LearnedConfig().kappa_s


def test_split_needs_three_consecutive_winning_checks():
    """Locked 3.5: a narrative whose events form two clear groups splits only at the third consecutive check."""
    d = 32
    m = _model(d, kappa_s=40.0, log_alpha=-5.0, temp=1.0, split_min_events=4)
    from types import SimpleNamespace
    rng = keyed_rng("two-topics")
    a, b = rng.standard_normal(d), rng.standard_normal(d)
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    clusters = {}
    for i in range(12):
        c = (a if i % 2 else b) + 0.05 * rng.standard_normal(d)
        c /= np.linalg.norm(c)
        clusters[i] = SimpleNamespace(centroid=c, cnt={f"e{i % 2}": 3}, n=3)
    nid = m.emerge(0, clusters[0].centroid, {"e0": 1.0}, 1.0, 1, "x")
    for i in range(1, 12):
        m.route(i, nid, clusters[i].centroid, {f"e{i % 2}": 1.0}, 1.0, 1.0 + i * 0.1, 1)
    kinds = []
    for check in range(3):
        kinds.append([ev["kind"] for ev in m._splits(3.0 + check * 6, 10 + check, clusters)])
    assert kinds[0] == [] and kinds[1] == [] and kinds[2] == ["split"]


def test_hard_ceiling_evicts_least_recently_active_and_pauses_splits():
    d = 16
    m = _model(d, k_max=3, k_soft=2)
    rng = keyed_rng("cap")
    ids = []
    for i in range(3):
        v = rng.standard_normal(d); v /= np.linalg.norm(v)
        ids.append(m.emerge(100 + i, v, {f"e{i}": 1.0}, float(i), i, f"n{i}"))
    assert m.n_alive() == 3 and m.at_capacity()
    out = m.evict(window=9)                                   # oldest last activity: the first one
    assert out == ids[0] and m.narratives[ids[0]].state == "dormant" and m.n_alive() == 2
    v = rng.standard_normal(d); v /= np.linalg.norm(v)
    m.emerge(200, v, {"x": 1.0}, 5.0, 5, "n3")                # full again
    m.route(300, ids[0], v, {"x": 1.0}, 1.0, 6.0, 6)          # reactivation at capacity evicts the next oldest
    assert m.narratives[ids[0]].state == "alive" and m.narratives[ids[1]].state == "dormant" and m.n_alive() == 3
    assert m._splits(7.0, 7, {}) == []                        # at capacity: no splits
    assert any(ev.get("reason") == "capacity" for ev in m.lineage)
