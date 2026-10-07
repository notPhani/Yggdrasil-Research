"""Verdict logic: the verified four-bit example, E1 (stable-model existence + tightness fuzz), A4 control."""
import random

from ygg.verdicts.program import decide

EXAMPLE = """
reported(m1, ygg, occurred(ev_r1), d0120).   reported(m2, ygg, occurred(ev_surge), d0126).
reported(r02, arxiv_v3, excludes_prior(v3), d1227).  reported(r31, outlet_a, all_in_cost_5m(v3), d0126).
reported(r40, outlet_b, smuggled_chips(deepseek), d0126). reported(r41, outlet_c, no_diversion(deepseek), d0126).
contrary(all_in_cost_5m(v3), excludes_prior(v3)).  contrary(smuggled_chips(deepseek), no_diversion(deepseek)).
tier(ygg, 0). tier(arxiv_v3, 1). tier(outlet_a, 2). tier(outlet_b, 2). tier(outlet_c, 2).
owner(ygg, ygg). owner(arxiv_v3, arxiv). owner(outlet_a, oa). owner(outlet_b, ob). owner(outlet_c, oc).
group(m1, g1). group(m2, g2). group(r02, g3). group(r31, g4). group(r40, g5). group(r41, g6).
trigger(h1, ev_r1).  before(ev_r1, move).
trigger(h3, ev_r1).  schema_refuter(h3, excludes_prior(v3)).
trigger(h4, ev_chips). before(ev_chips, move). signature_ok(h4).
holds(occurred(ev_chips)) :- holds(smuggled_chips(deepseek)).
schema_refuter(h4, no_diversion(deepseek)).
trigger(h6, ev_surge). before(ev_surge, move). signature_ok(h6).
"""


def test_verified_example_four_verdicts():
    v = decide(EXAMPLE)
    assert v.n_models == 2 and v.tight and not v.incoherent
    assert v.verdict == {"h1": "CONSISTENT-BUT-UNPROVEN", "h3": "CONTRADICTED", "h4": "UNRESOLVED", "h6": "SUPPORTED"}
    assert v.bits["h6"] == (1, 1, 0, 0) and v.bits["h3"] == (0, 0, 1, 1)


def test_a6_corroboration_needs_tier2_or_two_owners():
    base = """trigger(h, e). before(e, move). signature_ok(h).
    reported(r1, blog, occurred(e), d). tier(blog, 3). owner(blog, ob). group(r1, g1)."""
    assert decide(base).verdict["h"] == "CONSISTENT-BUT-UNPROVEN"
    two = base + "\nreported(r2, blog2, occurred(e), d). tier(blog2, 3). owner(blog2, ob2). group(r2, g2)."
    assert decide(two).verdict["h"] == "SUPPORTED"
    same_owner = base + "\nreported(r2, blog2, occurred(e), d). tier(blog2, 3). owner(blog2, ob). group(r2, g2)."
    assert decide(same_owner).verdict["h"] == "CONSISTENT-BUT-UNPROVEN"


def test_e1_template_always_has_a_stable_model_and_is_tight():
    rng = random.Random(7)
    for _ in range(300):
        nl, ns, nr = rng.randint(2, 7), rng.randint(2, 5), rng.randint(2, 12)
        f = []
        for s in range(ns):
            f += [f"tier(s{s},{rng.randint(0, 3)}).", f"owner(s{s},o{rng.randint(0, ns - 1)})."]
        for a in range(nl):
            for b in range(a + 1, nl):
                if rng.random() < 0.45:
                    f.append(f"contrary(l{a},l{b}).")
        for r in range(nr):
            f += [f"reported(r{r},s{rng.randrange(ns)},l{rng.randrange(nl)},t).", f"group(r{r},g{rng.randrange(nr)})."]
            if rng.random() < 0.08:
                f.append(f"retracted(r{r}).")
            if r and rng.random() < 0.1:
                f.append(f"copy_of(r{r},r{rng.randrange(r)}).")
        f += ["trigger(h, ev).", "before(ev, move).", "signature_ok(h).", "schema_refuter(h, l0)."]
        v = decide("\n".join(f))
        assert not v.incoherent and v.tight and v.n_models >= 1


def test_a4_flags_a_bridge_rule_loop():
    v = decide("reported(r1,s1,a,t). tier(s1,1). owner(s1,o1). group(r1,g1).\nholds(b) :- holds(a).\nholds(a) :- holds(b).\ntrigger(h,e).")
    assert v.tight is False
