"""SerpApi sensor (C4): archived responses replay offline, canonical-URL matches inherit first_seen, unmatched
results are truth-only, results never witness the trigger event, and no key means UNAVAILABLE, never invented."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import duckdb

from ygg.observation.canon import url_key
from ygg.verdicts.serpapi import Sensor, queries

TAU = datetime(2025, 1, 27, 8, 0, tzinfo=timezone.utc)


def _con(rows):
    con = duckdb.connect()
    con.execute("CREATE TABLE obs_doc (url_key VARCHAR, first_seen TIMESTAMP, observation_id VARCHAR, copy_group VARCHAR)")
    for r in rows:
        con.execute("INSERT INTO obs_doc VALUES (?, ?, ?, ?)", r)
    return con


def test_three_queries_one_confirming_two_disconfirming():
    q = queries("deepseek", "DeepSeek releases R1 reasoning model")
    assert [k for k, _, _ in q] == ["confirm", "disconfirm", "disconfirm"]
    assert q[0][2] and q[1][2] and not q[2][2]


def test_no_key_is_unavailable_and_sends_nothing(tmp_path):
    s = Sensor(tmp_path, api_key="")
    h = SimpleNamespace(hid="h1", entry_label="DeepSeek releases R1")
    ops, extra = s.run_case([h], TAU, _con([]), {}, lambda h: "deepseek")
    assert {o["status"] for o in ops} == {"UNAVAILABLE"} and extra == {"h1": []}


def test_cached_response_matches_inherit_first_seen_and_unmatched_are_truth_only(tmp_path):
    s = Sensor(tmp_path, api_key="")
    h = SimpleNamespace(hid="h1", entry_label="DeepSeek releases R1")
    q0 = queries("deepseek", h.entry_label)[0]
    params = s._params(q0[1], TAU, q0[2])
    import hashlib
    ck = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
    seen, unseen = "https://www.reuters.com/tech/deepseek-r1?utm_source=x", "https://blog.example.net/r1"
    (tmp_path / "fetch" / "serpapi" / f"{ck}.json").write_text(json.dumps({"params": params, "organic_results": [
        {"link": seen, "title": "DeepSeek releases R1"}, {"link": unseen, "title": "R1 explained"}]}))
    con = _con([(url_key("https://reuters.com/tech/deepseek-r1"), datetime(2025, 1, 21, 9, 15), "o1", "o1")])
    ops, extra = s.run_case([h], TAU, con, {}, lambda h: "deepseek")
    assert ops[0]["status"] == "CACHED" and ops[0]["matched"] == 1 and ops[0]["unmatched"] == 1
    by = {r["url"]: r for r in extra["h1"]}
    assert by[seen]["first_seen"].startswith("2025-01-21") and by[seen]["pre"] is True
    assert by[unseen]["first_seen"] is None and by[unseen]["pre"] is False
    assert all(r["witness"] is False and r["origin"] == "targeted" for r in extra["h1"])
