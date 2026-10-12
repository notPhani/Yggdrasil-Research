"""Build fixtures/replay/ from a full data directory: the recorded investigations plus exactly what `ygg verify`
and `ygg ui` need to inspect them offline. SerpApi responses are reduced to the fields the code reads
(position, title, link); credential-bearing fields never exist in the archive and are dropped again here.

    python scripts/make_fixture.py [DATA_DIR] [OUT_DIR]      (defaults: data fixtures/replay)
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

src = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
out = Path(sys.argv[2] if len(sys.argv) > 2 else "fixtures/replay")
days = ["2025-01-13", "2025-01-27"]
if out.exists():
    shutil.rmtree(out)
for sub in ("cases", "prices", "universe", "fetch/serpapi"):
    (out / sub).mkdir(parents=True)
for day in days:
    for ext in (".json", ".md"):
        shutil.copy2(src / "cases" / f"{day}{ext}", out / "cases" / f"{day}{ext}")
for f in ("daily.parquet", "actions.parquet"):
    shutil.copy2(src / "prices" / f, out / "prices" / f)
shutil.copy2(src / "universe" / "universe.json", out / "universe" / "universe.json")

sys.path.insert(0, "src")
from ygg.verdicts.serpapi import Sensor  # noqa: E402

keep = ("position", "title", "link")
n = 0
for day in days:
    d = json.loads((src / "cases" / f"{day}.json").read_text())
    tau = datetime.fromisoformat(d["case"]["tau_star"])
    s = Sensor(src, api_key="")
    for o in d["verdicts"].get("searches", []):
        if o["status"] not in ("DONE", "CACHED"):
            continue
        params = s._params(o["query"], tau, o["bounded"])
        ck = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
        rec = json.loads((s.cache / f"{ck}.json").read_text())
        slim = {"params": params, "organic_results": [{k: r[k] for k in keep if k in r} for r in rec.get("organic_results", [])]}
        (out / "fetch" / "serpapi" / f"{ck}.json").write_text(json.dumps(slim, indent=1, sort_keys=True))
        n += 1
files = sorted(p for p in out.rglob("*") if p.is_file())
(out / "MANIFEST.sha256").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}\n" for p in files))
size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
print(f"{out}: {len(files)} files, {n} SerpApi responses, {size / 1e6:.1f} MB")
