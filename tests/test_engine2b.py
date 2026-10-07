import numpy as np

from ygg.attention.engine2b import B2Config, Engine2b
from ygg.attention.model import A_M, FitConfig, softplus
from ygg.determinism import WindowClock, parse_utc
from ygg.loop import digest

CLOCK = WindowClock(parse_utc("2024-12-16"))
IDS = ["n_a", "n_b", "n_c"]


def simulate(T=96 * 6, seed=0):
    rng = np.random.default_rng(seed)
    b0 = np.array([1.0, 0.5, 0.3])
    A = np.zeros((3, 3, 4)); A[1, 0, 0] = 0.5
    y = np.zeros((T, 3)); z = np.zeros((3, 4))
    for t in range(T):
        y[t] = rng.poisson(softplus(b0 + np.einsum("ijm,jm->i", A, z), 1.0))
        z = A_M * z + (1 - A_M) * y[t][:, None]
    return y


def run(y, perturb_from=None, alpha_floor=0.0):
    eng = Engine2b(CLOCK, B2Config(min_windows=96 * 2, min_mass=5, alpha_floor=alpha_floor, fit=FitConfig(iters=80)))
    cents = {n: v for n, v in zip(IDS, np.eye(3))}
    outs = []
    for t in range(len(y)):
        yy = y[t] if perturb_from is None or t < perturb_from else y[t] * 0 + 7
        if t == 1:
            eng.set_neighbors(cents)
        outs.append(eng.step(t, {n: float(v) for n, v in zip(IDS, yy)}, float(yy.sum()), False, []))
    return eng, outs


def test_alpha_is_a_probability_vector_lemma_7_1():
    eng, outs = run(simulate())
    sums = {}
    for o in outs:
        for a in o["alpha"]:
            sums[(a["target"], a["window"])] = sums.get((a["target"], a["window"]), 0.0) + a["alpha"]
    assert sums and all(abs(v - 1.0) < 1e-9 for v in sums.values())


def test_refits_run_and_respect_the_cap():
    eng, _ = run(simulate())
    assert eng.refits, "a refit should have happened"
    for info in eng.refits:
        assert info["omega"] in FitConfig().omega_grid
        if info["omega"] < 0.05:
            assert info["max_row_pos_sum"] <= FitConfig().rho_cap + 1e-9


def test_pit_in_unit_interval_and_roughly_centred():
    _, outs = run(simulate())
    u = np.array([r["pit"] for o in outs[96 * 3:] for r in o["series"] if r["pit"] is not None])
    assert ((u > 0) & (u < 1)).all() and 0.4 < u.mean() < 0.6


def test_future_perturbation_d7():
    y = simulate()
    _, a = run(y)
    _, b = run(y, perturb_from=400)
    assert [digest(x) for x in a[:400]] == [digest(x) for x in b[:400]]


def test_merge_conserves_traces_lemma_5_2():
    eng = Engine2b(CLOCK)
    eng._add("p", np.array([1.0, 2.0, 3.0, 4.0]), [])
    eng._add("q", np.array([0.5, 0.5, 0.5, 0.5]), [])
    eng.apply_lineage([{"kind": "merge", "parents": ["p", "q"], "children": ["c"], "shares": [1.0]}])
    assert np.allclose(eng.z["c"], [1.5, 2.5, 3.5, 4.5]) and "p" not in eng.z
    eng.apply_lineage([{"kind": "split", "parents": ["c"], "children": ["c1", "c2"], "shares": [0.25, 0.75]}])
    assert np.allclose(eng.z["c1"] + eng.z["c2"], [1.5, 2.5, 3.5, 4.5])
