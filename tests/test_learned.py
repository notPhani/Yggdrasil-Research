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


def test_birth_needs_fewer_stories_when_tighter():
    d = 64
    m = _model(d, kappa_s=60.0, log_alpha=-12.0, temp=1.0)

    def n_star(spread, ents=False):
        for n in range(2, 200):
            X, _ = _cluster(d, n, spread, f"c{spread}")
            if m.birth_evidence(X.sum(0), n, {"rare entity": n} if ents else {}) > 0:
                return n
        return 10 ** 9

    assert n_star(0.05) < n_star(0.25) < 200          # sharp stories nucleate earlier; vague ones still can
    assert n_star(1.0) == 10 ** 9                      # isotropic noise never does
    assert n_star(0.25, ents=True) < n_star(0.25)      # a shared rare entity is evidence too


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
