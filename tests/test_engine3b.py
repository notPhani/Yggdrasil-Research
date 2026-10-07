from datetime import datetime, timezone

from ygg.verdicts.claims import Claim
from ygg.verdicts.engine3b import Hypothesis, facts_for, judge

TAU = datetime(2025, 1, 27, 8, 0, tzinfo=timezone.utc)


def rep(rid, src, tier, owner, group, when, claims=(), pre=True, copy=False):
    return {"id": rid, "source": src, "tier": tier, "owner": owner, "group": group, "first_seen": when, "pre": pre,
            "url": "u", "title": "t", "claims": list(claims), "copy": copy}


def test_supported_needs_signature_and_corroboration():
    h = Hypothesis("h_r1", "n1", "R1 release", [], 7, True, True, True)
    reps = {"h_r1": [rep("r1", "reuters.com", 2, "reuters.com", "g1", "2025-01-21T01:00:00+00:00"),
                     rep("r2", "blog.example", 3, "blog.example", "g2", "2025-01-21T02:00:00+00:00")]}
    out = judge([h], reps, TAU)
    assert out["P_pre"]["verdicts"]["h_r1"] == "SUPPORTED" and out["P_pre"]["tight"]


def test_copies_and_post_cutoff_reports_do_not_corroborate_before_tau():
    h = Hypothesis("h_x", "n1", "story", [], 3, True, True, True)
    reps = {"h_x": [rep("r1", "blog.a", 3, "blog.a", "g1", "2025-01-26T01:00:00+00:00"),
                    rep("r2", "blog.b", 3, "blog.b", "g1", "2025-01-26T02:00:00+00:00", copy=True),
                    rep("r3", "reuters.com", 2, "reuters.com", "g3", "2025-01-27T12:00:00+00:00", pre=False)]}
    out = judge([h], reps, TAU)
    assert out["P_pre"]["verdicts"]["h_x"] == "CONSISTENT-BUT-UNPROVEN"     # one tier-3 witness, its copy defeated
    assert out["P_all"]["verdicts"]["h_x"] == "SUPPORTED"                   # the post-cutoff tier-2 report counts for truth


def test_contrary_cost_scopes_refute_the_all_in_story():
    h = Hypothesis("h_cost", "n2", "cheap AI", [], 5, True, True, True)
    allin = Claim("deepseek_v3", "cost_of", "5.6e+06", "all_in", 1, "r1", "s", "rule")
    paper = Claim("deepseek_v3", "cost_of", "5.6e+06", "final_run_only", 1, "r2", "s", "rule")
    reps = {"h_cost": [rep("r1", "blog.a", 3, "blog.a", "g1", "2025-01-26T01:00:00+00:00", [allin]),
                       rep("r2", "arxiv.org", 1, "arxiv.org", "g2", "2024-12-27T01:00:00+00:00", [paper]),
                       rep("r3", "reuters.com", 2, "reuters.com", "g3", "2025-01-26T03:00:00+00:00")]}
    facts = facts_for([h], reps, TAU, pre_only=True)
    assert any(f.startswith("contrary(") for f in facts) and any(f.startswith("schema_refuter(") for f in facts)
    out = judge([h], reps, TAU)
    assert out["P_pre"]["verdicts"]["h_cost"] == "CONTRADICTED"
