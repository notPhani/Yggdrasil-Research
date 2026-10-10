"""The placebo memo returns exactly what the search computed, and does not search again on a hit."""
import json

from ygg.search import case


class _Clock:
    def start(self, t):
        from datetime import datetime, timedelta, timezone
        return datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * t)


def test_placebo_cache_hit_equals_miss(tmp_path, monkeypatch):
    snap = tmp_path / "snapshots" / "t=7"
    snap.mkdir(parents=True)
    (snap / "manifest.json").write_text(json.dumps({"snapshot_id": "abc"}))
    monkeypatch.setattr("ygg.search.placebo.placebo_terminals", lambda *a: [["X"]])
    from types import SimpleNamespace
    monkeypatch.setattr("ygg.search.graph.build_terminals", lambda clusters, u: [SimpleNamespace(name="X")])
    calls = []

    def fake_explain(data_dir, clock, t, terms, cfg):
        calls.append(t)
        return {"groups": [{"terminals": ["X"], "best": {"cost_mnats": 4321, "abstained_on": []}, "used_narratives": ["n1"]}]}

    monkeypatch.setattr(case, "explain", fake_explain)
    args = (tmp_path, _Clock(), 7, [], [], {"etfs": []}, 1, case.SearchConfig(), "h")
    a = case.placebo_one(*args)
    b = case.placebo_one(*args)
    assert a == b and calls == [7]
    assert a["groups"][0]["cost_mnats"] == 4321
    (snap / "manifest.json").write_text(json.dumps({"snapshot_id": "changed"}))
    case.placebo_one(*args)
    assert calls == [7, 7]                      # a different snapshot is a different key
