"""Title embeddings, computed once per day and cached (decision 3.2; model chosen at build time).

Two models, one per job:
  Engine 1 near-duplicate step: minishlab/potion-base-8M (static embeddings, MIT). ~11k titles/s on this
    CPU, bit-identical across runs; theta_a is calibrated on it.
  Narratives (Engine 2a): sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0), same-event AUC 0.854 vs
    0.832 for potion. Run as the model's own fp32 ONNX file with 2 intra-op threads (fixed, so reductions
    are reproducible) and a 64-token cap (0.6% of titles are longer; median 15, p99 45). ~121 titles/s here.
    Its int8 ONNX file was 1.37x faster but moved pairwise similarities by up to 0.076, so it is not used.
Identical titles get identical vectors, so each distinct title is encoded once (~11% of root titles repeat).
Vectors are L2-normalized and stored as int8 (2.7b), which moves any cosine by at most ~0.017.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

DEFAULT_MODEL = "minishlab/potion-base-8M"
ONNX_THREADS = 2
MAX_TOKENS = 64
DIMS = {"minishlab/potion-base-8M": 256, "sentence-transformers/all-MiniLM-L6-v2": 384}


@lru_cache(maxsize=2)
def _model(name: str):
    if name.startswith("minishlab/"):
        from model2vec import StaticModel

        return StaticModel.from_pretrained(name)
    import onnxruntime as ort
    from sentence_transformers import SentenceTransformer

    so = ort.SessionOptions()
    so.intra_op_num_threads, so.inter_op_num_threads = ONNX_THREADS, 1
    m = SentenceTransformer(name, backend="onnx", device="cpu",
                            model_kwargs={"file_name": "onnx/model.onnx", "session_options": so})
    m.max_seq_length = MAX_TOKENS
    return m


def _encode_raw(titles: list[str], model: str) -> np.ndarray:
    m = _model(model)
    if model.startswith("minishlab/"):
        return np.asarray(m.encode(titles), dtype=np.float32)
    return np.asarray(m.encode(titles, batch_size=128, convert_to_numpy=True), dtype=np.float32)


def encode(titles: list[str], model: str = DEFAULT_MODEL) -> np.ndarray:
    if not titles:
        return np.zeros((0, DIMS.get(model, 256)), np.float32)
    uniq = sorted(set(titles))
    pos = {t: i for i, t in enumerate(uniq)}
    e = _encode_raw(uniq, model)
    n = np.linalg.norm(e, axis=1, keepdims=True)
    e = e / np.where(n == 0, 1.0, n)
    return e[[pos[t] for t in titles]]


def to_int8(e: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(e * 127.0), -127, 127).astype(np.int8)


def from_int8(q: np.ndarray) -> np.ndarray:
    e = q.astype(np.float32) / 127.0
    n = np.linalg.norm(e, axis=1, keepdims=True)
    return e / np.where(n == 0, 1.0, n)


def cache_path(data_dir: Path, model: str, day: str) -> Path:
    return Path(data_dir) / "embeddings" / model.replace("/", "__") / f"day={day}.parquet"


def write_day(path: Path, ids: list[str], e: np.ndarray) -> None:
    q = to_int8(e)
    tab = pa.table({"observation_id": pa.array(ids, pa.string()),
                    "vec": pa.FixedSizeListArray.from_arrays(pa.array(q.reshape(-1), pa.int8()), q.shape[1])})
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tab, path, compression="zstd")


def cached_dim(data_dir: Path, model: str) -> int:
    files = sorted((Path(data_dir) / "embeddings" / model.replace("/", "__")).glob("day=*.parquet"))
    return pq.read_schema(files[0]).field("vec").type.list_size if files else DIMS[model]


def embed_roots(data_dir: Path, days: list[str], model: str, log=print) -> dict:
    """Embed the root documents of each day (copies inherit their root's narrative), resumable per day.
    Progress goes to data/embeddings/<model>/status.json and one log line per day."""
    import json
    import time

    data_dir = Path(data_dir)
    status_path = data_dir / "embeddings" / model.replace("/", "__") / "status.json"
    todo = [d for d in days if not cache_path(data_dir, model, d).exists()]
    done_before, n_total, t0 = len(days) - len(todo), 0, time.monotonic()
    for i, day in enumerate(todo):
        tab = pq.read_table(Path(data_dir) / "tables" / "obs_doc" / f"day={day}" / "part-0.parquet",
                            columns=["observation_id", "copy_group", "title"]).to_pylist()
        roots = [r for r in tab if r["copy_group"] == r["observation_id"]]
        e = encode([r["title"] or "" for r in roots], model)
        write_day(cache_path(data_dir, model, day), [r["observation_id"] for r in roots], e)
        n_total += len(roots)
        el = time.monotonic() - t0
        eta_s = el / (i + 1) * (len(todo) - i - 1)
        snap = {"model": model, "days_done": done_before + i + 1, "days": len(days), "last_day": day, "titles": n_total,
                "rate": round(n_total / el, 1), "elapsed_s": round(el), "eta_s": round(eta_s)}
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(snap))
        k = done_before + i + 1
        bar = "#" * (20 * k // len(days)) + "." * (20 - 20 * k // len(days))
        log(f"embed [{bar}] {k}/{len(days)} days  {day}: {len(roots)} roots  {snap['rate']:.0f}/s  "
            f"elapsed {el / 3600:.1f} h  eta {eta_s / 3600:.1f} h")
    return {"days": len(days), "embedded_now": len(todo), "titles": n_total}


def read_day(path: Path) -> dict[str, np.ndarray]:
    tab = pq.read_table(path)
    dim = tab.schema.field("vec").type.list_size
    q = tab.column("vec").combine_chunks().flatten().to_numpy(zero_copy_only=False).reshape(-1, dim)
    e = from_int8(q)
    return dict(zip(tab.column("observation_id").to_pylist(), e))
