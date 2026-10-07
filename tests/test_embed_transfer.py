"""Off-box embedding: export -> (simulated GPU run) -> import verifies sha256, ids and CPU parity."""
import hashlib
import json

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from ygg.observation import embed as emb
from ygg.observation import embed_transfer as et

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _fake(titles, model):
    return np.stack([np.frombuffer(hashlib.sha256(t.encode()).digest() * 12, np.uint8)[:384].astype(np.float32) - 127.5
                     for t in titles])


def _setup(tmp_path, monkeypatch):
    monkeypatch.setattr(emb, "_encode_raw", _fake)
    d = tmp_path / "data" / "tables" / "obs_doc" / "day=2024-12-16"
    d.mkdir(parents=True)
    rows = [{"observation_id": f"o{i}", "copy_group": f"o{i}" if i % 4 else f"o{i - 1}", "title": f"title {i % 7}"} for i in range(1, 40)]
    pq.write_table(pa.Table.from_pylist(rows), d / "part-0.parquet")
    data = tmp_path / "data"
    et.export_inputs(data, ["2024-12-16"], tmp_path / "x", MODEL)
    src = tmp_path / "gpu"
    src.mkdir()
    ids, titles = et.roots_of_day(data, "2024-12-16")
    emb.write_day(src / "day=2024-12-16.parquet", ids, emb.encode(titles, MODEL))
    man = {"files": {"day=2024-12-16.parquet": {"rows": len(ids), "sha256": et._sha256(src / "day=2024-12-16.parquet")}}}
    (src / "manifest.json").write_text(json.dumps(man))
    return data, src, ids


def test_export_import_roundtrip_installs_and_keeps_cpu_days_aside(tmp_path, monkeypatch):
    data, src, ids = _setup(tmp_path, monkeypatch)
    inp = pq.read_table(tmp_path / "x" / "inputs" / "day=2024-12-16.parquet")
    assert inp.column("observation_id").to_pylist() == ids
    cache = emb.cache_path(data, MODEL, "2024-12-16")
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"cpu-made")
    out = et.import_outputs(data, src, ["2024-12-16"], MODEL, sample_per_day=10)
    assert out["worst_min_cos"] > 0.9999
    assert set(emb.read_day(cache)) == set(ids)
    assert (data / "embeddings" / (MODEL.replace("/", "__") + "__cpu_audit") / "day=2024-12-16.parquet").read_bytes() == b"cpu-made"


def test_import_rejects_tampered_vectors(tmp_path, monkeypatch):
    data, src, ids = _setup(tmp_path, monkeypatch)
    _, titles = et.roots_of_day(data, "2024-12-16")
    bad = emb.encode(titles, MODEL)[::-1].copy()          # vectors shuffled against their ids
    emb.write_day(src / "day=2024-12-16.parquet", ids, bad)
    man = json.loads((src / "manifest.json").read_text())
    man["files"]["day=2024-12-16.parquet"]["sha256"] = et._sha256(src / "day=2024-12-16.parquet")
    (src / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(ValueError, match="parity"):
        et.import_outputs(data, src, ["2024-12-16"], MODEL, sample_per_day=10)


def test_import_rejects_corrupt_download(tmp_path, monkeypatch):
    data, src, _ = _setup(tmp_path, monkeypatch)
    with (src / "day=2024-12-16.parquet").open("ab") as f:
        f.write(b"x")
    with pytest.raises(ValueError, match="sha256"):
        et.import_outputs(data, src, ["2024-12-16"], MODEL, sample_per_day=10)
