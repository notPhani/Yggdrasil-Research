from datetime import timedelta

import numpy as np

from ygg.determinism import parse_utc
from ygg.observation.dedup_l2 import L2Config, L2Dedup, norm_title

T = parse_utc("20250127080000")


def doc(oid, title, source, *, image="", authors=(), names=(), amounts=(), dt_h=0.0, url=None):
    return {"observation_id": oid, "observed_time": T + timedelta(hours=dt_h), "title": title, "source_name": source,
            "url_key": url or f"u-{oid}", "sharing_image": image, "authors": list(authors), "all_names": list(names),
            "persons": [], "orgs": [], "amounts": [{"amount": a, "object": ""} for a in amounts]}


def test_norm_title_strips_site_suffix():
    assert norm_title("London City Airport seeks leisure growth with Airbus | Bournemouth Echo") == \
        norm_title("London City Airport seeks leisure growth with Airbus - Oxford Mail")


def test_wire_copies_merge_on_title_plus_image():
    l2 = L2Dedup()
    t = "London City Airport seeks leisure growth with Airbus"
    root, ev = l2.assign(doc("a", t + " | Echo", "echo.co.uk", image="img/pa1.jpg"), None)
    assert ev == "root"
    for i, src in enumerate(["oxfordmail.co.uk", "dailyecho.co.uk", "theargus.co.uk"]):
        r, ev = l2.assign(doc(f"b{i}", t + " | Paper", src, image="img/pa1.jpg"), None)
        assert r == "a" and ev == "L2:s1:image"


def test_template_titles_from_one_site_never_merge():
    l2 = L2Dedup()
    roots = set()
    for i in range(14):
        r, _ = l2.assign(doc(f"g{i}", "Gearing announcement | company announcement", "investegate.co.uk",
                             image="img/logo.png", names=[f"Company {i} plc"]), None)
        roots.add(r)
    assert len(roots) == 14


def test_site_logo_image_is_not_evidence():
    l2 = L2Dedup(L2Config(logo_titles=3))
    for i in range(3):
        l2.assign(doc(f"x{i}", f"Unrelated story number {i} about things", "site.com", image="img/logo.png"), None)
    r, ev = l2.assign(doc("y", "Unrelated story number 0 about things", "other.com", image="img/logo.png"), None)
    assert ev == "root"          # same title, but the only shared signal is a site logo


def test_independent_coverage_is_never_merged():
    l2 = L2Dedup()
    l2.assign(doc("reuters", "Nvidia shares tumble as DeepSeek rattles AI trade", "reuters.com", names=["Nvidia", "DeepSeek"]), None)
    r, ev = l2.assign(doc("bloomberg", "Nvidia loses $590 billion in record wipeout", "bloomberg.com", names=["Nvidia", "DeepSeek"]), None)
    assert r == "bloomberg" and ev == "root"


def test_fallback_a_needs_embedding_and_entities():
    l2 = L2Dedup()
    v = np.ones(4, np.float32) / 2.0
    l2.assign(doc("a", "DeepSeek's AI model tops App Store", "a.com", image="img/ds.jpg", names=["DeepSeek", "Apple"]), v)
    r, ev = l2.assign(doc("b", "DeepSeek AI app tops Apple App Store chart", "b.com", image="img/ds.jpg", names=["DeepSeek", "Apple"]), v)
    assert r == "a" and ev == "L2:A:image+embedding"
    r, ev = l2.assign(doc("c", "Totally different headline on the same photo", "c.com", image="img/ds.jpg", names=["Paris"]), v)
    assert ev == "root"


def test_horizon_expires_roots_after_72h():
    l2 = L2Dedup()
    l2.assign(doc("a", "Same exact headline for the test", "a.com", image="img/1.jpg"), None)
    r, ev = l2.assign(doc("b", "Same exact headline for the test", "b.com", image="img/1.jpg", dt_h=73), None)
    assert r == "b" and ev == "root"


def test_generic_site_title_with_overlapping_names_is_a_template():
    l2 = L2Dedup()
    roots = set()
    for i in range(6):
        r, _ = l2.assign(doc(f"cd{i}", "China Daily Website - Connecting China Connecting the World", "chinadaily.com.cn",
                             names=["China", f"Topic {i}"]), None)
        roots.add(r)
    assert len(roots) == 6


def test_short_generic_titles_need_an_image():
    l2 = L2Dedup()
    l2.assign(doc("w1", "Weather forecast", "a.com", names=["London"]), None)
    r, ev = l2.assign(doc("w2", "Weather forecast", "b.com", names=["London"]), None)
    assert ev == "root"
