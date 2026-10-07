import io
import zipfile

import pyarrow.parquet as pq

from ygg.determinism import WindowClock, parse_utc
from ygg.observation.canon import canon, url_key
from ygg.observation.engine1 import Engine1, _parse_job
from ygg.store.blobs import BlobStore

T0 = parse_utc("2024-12-16")


def gkg_line(rid, url, title="A title", ts="20241216000000"):
    c = [""] * 27
    c[0], c[1], c[2], c[3], c[4] = rid, ts, "1", "example.com", url
    c[7] = "ECON_STOCKMARKET;TAX_FNCACT;"
    c[9] = "1#United States#US#US#38#-97#US"
    c[11], c[13] = "jensen huang", "nvidia"
    c[15] = "-2.5,1,3.5,4.5,20,1,300"
    c[22] = "10|40|said|We will keep investing in compute"
    c[23] = "Jensen Huang,5;Nvidia,20"
    c[24] = "5600000,dollars to train,100;"
    c[26] = f"<PAGE_TITLE>{title} &amp; more</PAGE_TITLE><PAGE_PRECISEPUBTIMESTAMP>20241215235000</PAGE_PRECISEPUBTIMESTAMP>"
    return "\t".join(c)


def zip_blob(lines):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(zipfile.ZipInfo("x.gkg.csv", date_time=(2024, 12, 16, 0, 0, 0)), "\n".join(lines) + "\n")
    return buf.getvalue()


def setup(tmp_path, batches):
    """batches: {batch_ts: [lines] or None for a missing batch}"""
    store, status = BlobStore(tmp_path / "blobs"), {}
    for ts, lines in batches.items():
        if lines is None:
            status[(ts, "gkg")] = ("missing", "")
            continue
        sha = store.put(zip_blob(lines), ".zip")
        _parse_job((str(tmp_path), "gkg", sha))
        status[(ts, "gkg")] = ("ok", sha)
    return status


def run(tmp_path, status, n):
    eng = Engine1(tmp_path, WindowClock(T0), status)
    out = [eng.step(t) for t in range(n)]
    eng.finish()
    return out


def test_canon_rules_and_idempotence():
    u = "HTTP://WWW.Example.com//news/story/amp/?utm_source=x&b=2&a=1&fbclid=z#frag"
    assert canon(u) == "https://example.com/news/story?a=1&b=2"
    assert canon(canon(u)) == canon(u)
    assert url_key("https://example.com/a/") == url_key("http://www.example.com/a")
    assert url_key("https://example.com/a?id=1") != url_key("https://example.com/a?id=2")


def test_l1_dedup_clocks_and_missing_flag(tmp_path):
    status = setup(tmp_path, {
        "20241216000000": [gkg_line("r1", "https://example.com/story"), gkg_line("r2", "https://example.com/other")],
        "20241216001500": None,
        "20241216003000": [gkg_line("r3", "http://www.example.com/story/?utm_medium=rss"), gkg_line("r4", "https://example.com/new")],
    })
    out = run(tmp_path, status, 3)
    (new0, led0), (new1, led1), (new2, led2) = out
    assert len(new0) == 2 and led0["missing_batch"] is False
    assert new1 == [] and led1["missing_batch"] is True
    assert [r["native_id"] for r in new2] == ["r4"] and led2["l1_dups"] == 1
    r = new0[0]
    assert r["first_seen"] == parse_utc("20241216001500")          # D1: observed + 15 min
    assert r["title"] == "A title & more" and r["published_time"] == parse_utc("20241215235000")
    assert r["amounts"][0]["amount"] == 5600000.0 and r["quotations"][0]["verb"] == "said"
    dups = pq.read_table(tmp_path / "tables" / "dup_links" / "day=2024-12-16" / "part-0.parquet").to_pylist()
    assert dups[0]["matched_on"] == "url_key"


def test_engine1_is_deterministic(tmp_path):
    batches = {"20241216000000": [gkg_line(f"r{i}", f"https://example.com/{i % 7}") for i in range(30)]}
    a_dir, b_dir = tmp_path / "a", tmp_path / "b"
    for d in (a_dir, b_dir):
        run(d, setup(d, batches), 1)
    ta = pq.read_table(a_dir / "tables" / "obs_doc" / "day=2024-12-16" / "part-0.parquet")
    tb = pq.read_table(b_dir / "tables" / "obs_doc" / "day=2024-12-16" / "part-0.parquet")
    assert ta.equals(tb) and ta.num_rows == 7
