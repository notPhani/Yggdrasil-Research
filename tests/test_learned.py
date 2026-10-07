"""2a-L: the high-dimensional vMF normalizer, the closed-form evidences, and behaviour on synthetic topics."""
import math

import numpy as np
from scipy.special import ive

from ygg.determinism import keyed_rng
from ygg.narratives.learned import LearnedConfig, LearnedNarrativeModel, log_cd, log_iv


def test_debye_log_bessel_matches_scipy_at_d384():
    nu = 191.0
    for x in (150.0, 191.0, 400.0, 2000.0, 9000.0):
        exact = math.log(ive(nu, x)) + x
        assert abs(log_iv(nu, x) - exact) < 1e-6 * max(1.0, abs(exact))


def test_log_cd_small_kappa_tends_to_uniform_and_no_underflow():
    d = 384
    assert abs(log_cd(1e-6, d) - log_cd(0.0, d)) < 1e-3
    assert math.isfinite(log_cd(1.0, d))                    # scipy's ive(191, 1) underflows to 0


def _model(d=64, **kw):
    rng = keyed_rng("bg")
    m = LearnedNarrativeModel(d, LearnedConfig(**kw))
    for i in range(400):                                     # a broad background
        v = rng.standard_normal(d)
        m.background_add(10_000 + i, v / np.linalg.norm(v), 0.0)
    m.set_background_counts({f"common{i}": 50 for i in range(20)}, 20, 1000)
    return m


def _cluster(d, n, spread, seed):
    rng = keyed_rng(seed)
    c = rng.standard_normal(d)
    c /= np.linalg.norm(c)
    X = c + spread * rng.standard_normal((n, d))
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    return X, c


def test_group_evidence_favours_related_events_over_unrelated_or_noise():
    d = 64
    m = _model(d, kappa_s=60.0, log_alpha=-12.0, temp=1.0)
    X, _ = _cluster(d, 4, 0.08, "story")                    # four distinct events of one storyline
    Y = np.stack([_cluster(d, 1, 0.0, f"u{i}")[0][0] for i in range(4)])   # four unrelated events
    w_shared = [{"rare entity": 1.0}] * 4
    w_none = [{}] * 4
    related = m.group_evidence(X, w_shared)
    assert related + m.cfg.log_alpha > 0
    assert m.group_evidence(X[:2], w_none) < m.group_evidence(X, w_none)            # more events, more evidence
    assert m.group_evidence(Y, w_none) < 0 < m.group_evidence(X, w_none)
    assert m.group_evidence(X, w_shared) > m.group_evidence(X, w_none)              # a shared rare entity is evidence


def test_birth_needs_two_events_and_moves_them_out_of_the_background():
    d = 64
    m = _model(d, kappa_s=60.0, log_alpha=-12.0, temp=1.0)
    X, _ = _cluster(d, 3, 0.08, "story")

    class Ev:
        def __init__(self, cid, x):
            self.cid, self.centroid, self.n, self.cnt = cid, x, 3, {"rare entity": 3}

    clusters = {i: Ev(i, X[i]) for i in range(3)}
    w = {"rare entity": 1.0}
    assert m.try_birth(0, X[0], w, clusters, 1.0, 1, {}) is None                 # empty pool: one event alone never starts one
    for i in (1, 2):
        m.background_add(i, X[i], 1.0)
        m.pool_upsert(i, X[i], 1.0)
    n0 = m.N0
    nid = m.try_birth(0, X[0], w, clusters, 1.0, 1, {})
    assert nid is not None and len(m.narratives[nid].events) == 3
    assert m.N0 < n0 and not m.pool


def test_merge_evidence_sign():
    d = 64
    m = _model(d, kappa_s=60.0, log_alpha=-10.0, temp=1.0)
    X, c = _cluster(d, 12, 0.05, "a")
    Y, _ = _cluster(d, 12, 0.05, "b")                       # an unrelated direction
    na = m.emerge(1, X[0], {"x": 1.0}, 0.0, 0, "a")
    for i, x in enumerate(X[1:]):
        m.route(100 + i, na, x, {"x": 1.0}, 1.0, 0.0, 0)
    nb = m.emerge(2, Y[0], {"y": 1.0}, 0.0, 0, "b")
    for i, y in enumerate(Y[1:]):
        m.route(200 + i, nb, y, {"y": 1.0}, 1.0, 0.0, 0)
    X2, _ = _cluster(d, 12, 0.05, "a")                      # same direction as a, same entity
    nc = m.emerge(3, X2[0], {"x": 1.0}, 0.0, 0, "a2")
    for i, x in enumerate(X2[1:]):
        m.route(300 + i, nc, x, {"x": 1.0}, 1.0, 0.0, 0)
    N = m.narratives
    assert m.merge_evidence(N[na], N[nc], 0.0) > 0
    assert m.merge_evidence(N[na], N[nb], 0.0) < 0


def test_engine_separates_topics_from_noise_and_scores_prequentially():
    import sys
    sys.path.insert(0, "tests")
    from test_engine2a import synth

    from ygg.determinism import WindowClock, parse_utc
    from ygg.narratives.engine2a import Engine2a
    from ygg.narratives.events import EventConfig

    windows, vecs = synth(n_windows=80)
    eng = Engine2a(WindowClock(parse_utc("2024-12-16")), 32, EventConfig(lsh_tables=4, lsh_bits=6, tau_event=0.5),
                   lr_cfg=LearnedConfig(kappa_s=40.0, log_alpha=-5.0, temp=1.0, check_every_windows=8))
    none_topic, none_noise = [], []
    for t in range(80):
        r = eng.step(t, windows[t], vecs)
        if t < 40:
            continue
        titles = {d["observation_id"]: d["title"] for d in windows[t]}
        for row in r["memberships"]:
            (none_noise if titles[row["observation_id"]].startswith("t3") else none_topic).append(row["p0"] / 255)
    assert np.mean(none_topic) < 0.5 < np.mean(none_noise)
    assert eng.model.preq["n"] > 0 and math.isfinite(eng.model.preq["sum"])
    assert 2 <= len(eng.model.narratives) <= 12
