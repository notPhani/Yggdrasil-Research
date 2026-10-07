import pickle

import numpy as np

from ygg.determinism import WindowClock, keyed_rng, parse_utc
from ygg.narratives.engine2a import NONE, Engine2a
from ygg.narratives.narratives import largest_remainder_uint8
from ygg.loop import digest

CLOCK = WindowClock(parse_utc("2024-12-16"))
DIM = 32


def synth(n_windows=60, seed="synth"):
    """Three topics with their own entities, plus unrelated noise documents."""
    rng = keyed_rng(seed)
    centers = rng.standard_normal((3, DIM))
    centers /= np.linalg.norm(centers, axis=1, keepdims=True)
    ents = [["deepseek", "liang wenfeng", "hangzhou"], ["nvidia", "jensen huang", "santa clara"], ["vistra", "constellation", "texas grid"]]
    windows, vecs = {}, {}
    k = 0
    for t in range(n_windows):
        docs = []
        for _ in range(12):
            k += 1
            oid = f"{seed}-{k:05d}"
            topic = int(rng.integers(0, 4))
            if topic < 3:
                v = centers[topic] + 0.15 * rng.standard_normal(DIM)
                names = ents[topic] + [f"x{int(rng.integers(0, 50))}"]
            else:
                v = rng.standard_normal(DIM)
                names = [f"noise{k}"]
            v /= np.linalg.norm(v)
            root = oid if rng.random() > 0.2 or not docs else docs[-1]["copy_group"]
            docs.append({"observation_id": oid, "copy_group": root, "title": f"t{topic} {k}", "persons": [], "orgs": [],
                         "all_names": names, "url_key": oid})
            vecs[oid] = v.astype(np.float32)
        windows[t] = docs
    return windows, vecs


def make():
    from ygg.narratives.events import EventConfig
    from ygg.narratives.narratives import NarrativeConfig
    return Engine2a(CLOCK, DIM, EventConfig(lsh_tables=4, lsh_bits=6, tau_event=0.5),
                    NarrativeConfig(kappa0=20.0, m_emerge=4, check_every_windows=8))


def test_largest_remainder_sums_to_255():
    for p in ([1 / 3, 1 / 3, 1 / 3], [0.5, 0.25, 0.25, 0.0], [0.999, 0.001]):
        q = largest_remainder_uint8(np.array(p))
        assert int(q.sum()) == 255


def test_lemma_5_1_exact_and_narratives_emerge():
    windows, vecs = synth()
    eng = make()
    for t in range(60):
        r = eng.step(t, windows[t], vecs)
        led = r["ledger"]
        assert sum(s["y255"] for s in r["series"]) + led["y0_255"] == 255 * led["roots"]
    assert len([n for n in eng.model.narratives.values() if n.state == "alive"]) >= 2


def test_t1_exact_resume_and_determinism():
    windows, vecs = synth()
    a = make()
    out_a = [a.step(t, windows[t], vecs) for t in range(60)]
    b = make()
    out_b = [b.step(t, windows[t], vecs) for t in range(30)]
    b = pickle.loads(pickle.dumps(b))                  # snapshot at t = 30, then resume
    out_b += [b.step(t, windows[t], vecs) for t in range(30, 60)]
    assert [digest(x) for x in out_a] == [digest(x) for x in out_b]
    assert a.state_hash() == b.state_hash()


def test_future_perturbation_leaves_past_untouched():
    windows, vecs = synth()
    pert, pvecs = synth(seed="other")
    a = make()
    out_a = [a.step(t, windows[t], vecs) for t in range(60)]
    b = make()
    mixed = {t: (windows[t] if t < 40 else pert[t]) for t in range(60)}
    allv = {**vecs, **pvecs}
    out_b = [b.step(t, mixed[t], allv) for t in range(60)]
    assert [digest(x) for x in out_a[:40]] == [digest(x) for x in out_b[:40]]
