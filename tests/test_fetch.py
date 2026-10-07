import hashlib

from ygg.observation import gdelt_fetch as gf
from ygg.store.blobs import BlobStore

LINES = """\
5560000 72bd7ab5659b60e78d41d5eed850ac85 http://data.gdeltproject.org/gdeltv2/20250127120000.gkg.csv.zip
151307 00bf83fc30470bb9d2555fc65f6aaf73 http://data.gdeltproject.org/gdeltv2/20250127120000.export.CSV.zip
110583 3497fdf2ae5388b176b3387796173a49 http://data.gdeltproject.org/gdeltv2/20250127120000.mentions.CSV.zip
99 aaaa http://data.gdeltproject.org/gdeltv2/20250127120000.translation.gkg.csv.zip
garbage line
100 bbbb http://data.gdeltproject.org/gdeltv2/20250131234500.gkg.csv.zip
100 cccc http://data.gdeltproject.org/gdeltv2/20250201000000.gkg.csv.zip
"""


def entries():
    return [e for e in (gf.parse_manifest_line(l) for l in LINES.splitlines()) if e]


def test_parse_keeps_english_stream_only_and_forces_https():
    es = entries()
    assert len(es) == 5 and {e.kind for e in es} == {"gkg", "export", "mentions"}
    assert all(e.url.startswith("https://") for e in es)


def test_plan_is_half_open_and_chronological():
    p = gf.plan(entries(), "20250127000000", "20250201000000")
    assert [e.batch_ts for e in p] == ["20250127120000"] * 3 + ["20250131234500"]
    assert [e.kind for e in p[:3]] == ["gkg", "export", "mentions"]


def test_blob_store_is_idempotent(tmp_path):
    s = BlobStore(tmp_path)
    h1, h2 = s.put(b"abc", ".zip"), s.put(b"abc", ".zip")
    assert h1 == h2 == hashlib.sha256(b"abc").hexdigest() and s.get(h1, ".zip") == b"abc"


def test_fetch_one_verifies_md5(tmp_path, monkeypatch):
    body = b"payload"
    good = gf.ManifestEntry(len(body), hashlib.md5(body).hexdigest(), "https://x/20250101000000.gkg.csv.zip", "20250101000000", "gkg")
    bad = gf.ManifestEntry(len(body), "0" * 32, good.url, good.batch_ts, "gkg")
    monkeypatch.setattr(gf, "http_get", lambda url, timeout=90.0: body)
    monkeypatch.setattr(gf.time, "sleep", lambda s: None)
    store = BlobStore(tmp_path)
    assert gf.fetch_one(good, store)[0] == "ok"
    outcome, rec = gf.fetch_one(bad, store, retries=2)
    assert outcome == "failed" and rec["status"] == "bad_md5"


def test_ledger_latest_record_wins(tmp_path):
    led = gf.Ledger(tmp_path / "l.jsonl")
    led.append({"url": "u", "status": "net_error"})
    led.append({"url": "u", "status": "ok"})
    assert led.load()["u"]["status"] == "ok"
