"""Title embeddings, computed once per day and cached (decision 3.2; model chosen at build time).

Default: minishlab/potion-base-8M (static embeddings, MIT). On the GDELT same-event referee it scores
AUC 0.832 against 0.854 for all-MiniLM-L6-v2, it runs ~11k titles/s on this CPU (MiniLM: ~150/s), and
its output is bit-identical across runs. Vectors are L2-normalized and stored as int8 (2.7b), which
moves any cosine by at most ~0.017.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

DEFAULT_MODEL = "minishlab/potion-base-8M"


@lru_cache(maxsize=2)
def _model(name: str):
    from model2vec import StaticModel

    return StaticModel.from_pretrained(name)


def encode(titles: list[str], model: str = DEFAULT_MODEL) -> np.ndarray:
    if not titles:
        return np.zeros((0, 256), np.float32)
    e = np.asarray(_model(model).encode(titles), dtype=np.float32)
    n = np.linalg.norm(e, axis=1, keepdims=True)
    return e / np.where(n == 0, 1.0, n)


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


def read_day(path: Path) -> dict[str, np.ndarray]:
    tab = pq.read_table(path)
    dim = tab.schema.field("vec").type.list_size
    q = tab.column("vec").combine_chunks().flatten().to_numpy(zero_copy_only=False).reshape(-1, dim)
    e = from_int8(q)
    return dict(zip(tab.column("observation_id").to_pylist(), e))
