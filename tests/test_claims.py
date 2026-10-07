from ygg.verdicts.claims import Claim, contrary, from_amounts, from_quotes, from_title, grounded, scope_of
from ygg.verdicts.sources import owner, tier


def test_negex_scope_cues_settle_the_v3_cost_claim():
    paper = ("Note that the aforementioned costs include only the official training of DeepSeek-V3, "
             "excluding the costs associated with prior research and ablation experiments on architectures.")
    assert scope_of(paper) == "final_run_only"
    assert scope_of("DeepSeek built its model for a total cost of just $5.6 million") == "all_in"


def test_cost_claims_with_incompatible_scope_are_contrary():
    a = Claim("deepseek_v3", "cost_of", "5.6e+06", "all_in", 1, "r1", "x", "gdelt")
    b = Claim("deepseek_v3", "cost_of", "5.6e+06", "final_run_only", 1, "r2", "y", "rule")
    c = Claim("deepseek_v3", "cost_of", "5.6e+06", "unspecified", 1, "r3", "z", "rule")
    assert contrary(a, b) and not contrary(a, c)


def test_amounts_and_quotes_and_titles():
    text = "DeepSeek said training V3 took 2.788 million GPU hours, excluding prior research. It cost about $5.6 million in dollars to train."
    cl = from_amounts("r1", [{"amount": 5600000.0, "object": "dollars to train"}], text, "deepseek_v3")
    assert cl and cl[0].predicate == "cost_of" and cl[0].extractor == "gdelt"
    q = from_quotes("r2", [{"verb": "denied", "quote": "we did not use smuggled chips"}], "deepseek")
    assert q[0].predicate == "denies" and q[0].value == "smuggl"
    t = from_title("r3", "DeepSeek releases R1 reasoning model that rivals OpenAI o1", "deepseek")
    assert {c.predicate for c in t} >= {"released", "capability_parity"}


def test_a5_span_grounding():
    c = Claim("s", "released", "model", "unspecified", 1, "r", "DeepSeek open-sources its R1", "rule")
    assert grounded(c, "Header\nDeepSeek  open-sources its   R1 reasoning model series\nBody")
    assert not grounded(c, "unrelated page")


def test_tiers_and_owners():
    assert tier("www.reuters.com") == 2 and tier("arxiv.org") == 1 and tier("bls.gov") == 1 and tier("someblog.net") == 3
    assert owner("kiis.iheart.com") == owner("www.iheart.com")
