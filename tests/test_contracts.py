import pytest

from ygg.contracts import (OBSERVATION_SCHEMA, TARGETED_PAGE_SCHEMA, ObservationRecord, SnapshotManifest,
                           TargetedPage, schema_fields_match, snapshot_id)
from ygg.determinism import parse_utc

T = parse_utc("20250127074500")


def _rec(**kw):
    base = dict(observation_id="o1", source_type="gdelt_gkg", source_name="reuters.com", url="https://reuters.com/a",
                url_key="k", native_id="n", observed_time=T, ingested_time=T, first_seen=T, window=1)
    base.update(kw)
    return ObservationRecord(**base)


def test_c1_is_broad_only_a1():
    assert _rec().origin == "broad"
    with pytest.raises(ValueError):
        _rec(origin="targeted")


def test_targeted_pages_are_a_different_type_a1():
    page = TargetedPage(page_id="p", case_id="c", query="q", url="u", url_key="k", fetched_time=T, first_seen=T)
    assert not isinstance(page, ObservationRecord)


def test_records_are_frozen():
    r = _rec()
    with pytest.raises(Exception):
        r.window = 2


def test_schemas_match_dataclasses():
    assert schema_fields_match(ObservationRecord, OBSERVATION_SCHEMA)
    assert schema_fields_match(TargetedPage, TARGETED_PAGE_SCHEMA)


def test_snapshot_id_is_content_derived():
    m = SnapshotManifest(t=5, cfg_hash="c", parent_snapshot_id="p", inputs_hash="i", tables=(("y", "h"),))
    assert m.snapshot_id == snapshot_id("c", 5, "p", "i")
    with pytest.raises(ValueError):
        SnapshotManifest(t=5, cfg_hash="c", parent_snapshot_id="p", inputs_hash="i", tables=(), snapshot_id="forged")
