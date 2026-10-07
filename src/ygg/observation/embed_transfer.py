"""Off-box embedding: export the root titles, embed them on a GPU elsewhere, import and verify the vectors.

  export   data/tables/obs_doc -> DIR/inputs/day=D.parquet (observation_id, title; roots only, in the same order
           and with the same title rule as embed_roots) + DIR/inputs/manifest.json (rows and sha256 per file)
  import   DIR/day=D.parquet (observation_id, vec int8[384]) + DIR/manifest.json from the GPU run:
           1. sha256 and row counts match the GPU manifest
           2. ids and order match this box's roots exactly
           3. parity: a sample of titles per day is re-embedded here on the CPU (fp32 ONNX); every sampled
              vector must agree with the GPU one (cosine >= 0.999 after int8; quantization alone allows ~0.9999)
           then the files are installed into data/embeddings/<model>/ (CPU-made days are kept aside for audit)
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ygg.observation import embed as emb

INPUT_SCHEMA = pa.schema([("observation_id", pa.string()), ("title", pa.string())])


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def roots_of_day(data_dir: Path, day: str) -> tuple[list[str], list[str]]:
    tab = pq.read_table(Path(data_dir) / "tables" / "obs_doc" / f"day={day}" / "part-0.parquet",
                        columns=["observation_id", "copy_group", "title"]).to_pylist()
    roots = [r for r in tab if r["copy_group"] == r["observation_id"]]
    return [r["observation_id"] for r in roots], [r["title"] or "" for r in roots]


def export_inputs(data_dir: Path, days: list[str], out_dir: Path, model: str, log=print) -> dict:
    out = Path(out_dir) / "inputs"
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for day in days:
        ids, titles = roots_of_day(data_dir, day)
        path = out / f"day={day}.parquet"
        pq.write_table(pa.Table.from_pydict({"observation_id": ids, "title": titles}, schema=INPUT_SCHEMA), path,
                       compression="zstd", compression_level=9)
        files[path.name] = {"rows": len(ids), "unique_titles": len(set(titles)), "sha256": _sha256(path)}
        log(f"export {day}: {len(ids)} roots, {path.stat().st_size / 1e6:.1f} MB")
    man = {"model": model, "max_tokens": emb.MAX_TOKENS, "normalize": True, "int8_scale": 127, "files": files}
    (out / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True))
    return man


def _read_vecs(path: Path) -> tuple[list[str], np.ndarray]:
    tab = pq.read_table(path)
    dim = tab.schema.field("vec").type.list_size
    q = tab.column("vec").combine_chunks().flatten().to_numpy(zero_copy_only=False).reshape(-1, dim)
    return tab.column("observation_id").to_pylist(), q


def import_outputs(data_dir: Path, src: Path, days: list[str], model: str, sample_per_day: int = 200, log=print) -> dict:
    src = Path(src)
    man = json.loads((src / "manifest.json").read_text())
    dest = Path(data_dir) / "embeddings" / model.replace("/", "__")
    aside = Path(data_dir) / "embeddings" / (model.replace("/", "__") + "__cpu_audit")
    report, worst = {}, 1.0
    for day in days:
        name = f"day={day}.parquet"
        path = src / name
        meta = man["files"].get(name)
        if meta is None or not path.exists():
            raise FileNotFoundError(f"{name}: missing from the GPU output")
        if _sha256(path) != meta["sha256"]:
            raise ValueError(f"{name}: sha256 differs from the GPU manifest (corrupt download?)")
        ids_gpu, q = _read_vecs(path)
        ids, titles = roots_of_day(data_dir, day)
        if ids_gpu != ids:
            raise ValueError(f"{name}: observation ids or order differ from this box's roots")
        if q.shape[1] != emb.DIMS[model]:
            raise ValueError(f"{name}: dimension {q.shape[1]}, expected {emb.DIMS[model]}")
        rng = np.random.default_rng(int(hashlib.sha256(day.encode()).hexdigest()[:8], 16))
        idx = np.sort(rng.choice(len(ids), size=min(sample_per_day, len(ids)), replace=False))
        cpu = emb.from_int8(emb.to_int8(emb.encode([titles[i] for i in idx], model)))
        gpu = emb.from_int8(q[idx])
        cos = (cpu * gpu).sum(1)
        worst = min(worst, float(cos.min()))
        report[day] = {"rows": len(ids), "parity_min_cos": round(float(cos.min()), 6), "parity_mean_cos": round(float(cos.mean()), 6),
                       "int8_max_abs_diff": int(np.abs(emb.to_int8(cpu).astype(int) - q[idx].astype(int)).max())}
        if cos.min() < 0.999:
            raise ValueError(f"{name}: parity check failed (min cosine {cos.min():.5f} < 0.999)")
        log(f"import {day}: ids match, parity min cos {cos.min():.5f} mean {cos.mean():.6f}")
    for day in days:                                         # install only after every day has passed
        name = f"day={day}.parquet"
        if (dest / name).exists():
            aside.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dest / name), str(aside / name))
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / name, dest / name)
    (dest / "provenance.json").write_text(json.dumps({"source": "gpu", "gpu_manifest": {k: v for k, v in man.items() if k != "files"},
                                                      "parity": report, "worst_min_cos": worst}, indent=1, sort_keys=True))
    return {"days": len(days), "worst_min_cos": worst}
