"""Embed Yggdrasil's root titles with all-MiniLM-L6-v2 on a CUDA GPU.

Reproduces ygg.observation.embed exactly: each distinct title of a day is encoded once (64-token cap),
L2-normalized, mapped back to every root in input order, quantized to int8 (round(x * 127), clipped to
[-127, 127]) and written as day=D.parquet with columns observation_id (string) and vec (int8[384]).
Strict fp32 (TF32 off) and deterministic cuBLAS, so a rerun on the same machine is bit-identical.
The main box verifies the result with a CPU parity sample before using it (ygg embed-import).

  python embed_gpu.py --days 2024-12-16      # smoke test: one day
  python embed_gpu.py                        # everything in inputs/ (resumable)
  python embed_gpu.py --upload               # attach out/ to a GitHub release (needs the gh CLI, logged in)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")      # required for deterministic cuBLAS

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"             # the snapshot the main box uses
MAX_TOKENS = 64
DIM = 384
REPO = "notPhani/Yggdrasil-Research"
TAG = "embeddings-minilm-v1"
HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_model(device: str):
    import torch
    from sentence_transformers import SentenceTransformer

    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)
    m = SentenceTransformer(MODEL, revision=REVISION, device=device)
    m.max_seq_length = MAX_TOKENS
    m.eval()
    return m


def encode_unique(model, titles: list[str], batch: int, bar: tqdm) -> tuple[np.ndarray, int]:
    """Encode in length-sorted batches (less padding); on CUDA out-of-memory, halve the batch and retry."""
    import torch

    order = sorted(range(len(titles)), key=lambda i: (len(titles[i]), i))
    out = np.empty((len(titles), DIM), np.float32)
    i = 0
    while i < len(order):
        idx = order[i:i + batch]
        try:
            with torch.inference_mode():
                e = model.encode([titles[j] for j in idx], batch_size=len(idx), convert_to_numpy=True,
                                 show_progress_bar=False, normalize_embeddings=False)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            if batch <= 16:
                raise
            batch //= 2
            bar.write(f"CUDA out of memory: batch size -> {batch}")
            continue
        out[idx] = e
        i += len(idx)
        bar.update(len(idx))
        bar.set_postfix(batch=batch)
    return out, batch


def embed_day(model, inp: Path, out: Path, batch: int, bar: tqdm) -> tuple[dict, int]:
    tab = pq.read_table(inp)
    ids = tab.column("observation_id").to_pylist()
    titles = tab.column("title").to_pylist()
    uniq = sorted(set(titles))
    pos = {t: i for i, t in enumerate(uniq)}
    e, batch = encode_unique(model, uniq, batch, bar)
    n = np.linalg.norm(e, axis=1, keepdims=True)
    e = e / np.where(n == 0, 1.0, n)
    q = np.clip(np.rint(e[[pos[t] for t in titles]] * 127.0), -127, 127).astype(np.int8)
    table = pa.table({"observation_id": pa.array(ids, pa.string()),
                      "vec": pa.FixedSizeListArray.from_arrays(pa.array(q.reshape(-1), pa.int8()), DIM)})
    tmp = out.with_suffix(".tmp")
    pq.write_table(table, tmp, compression="zstd")
    tmp.replace(out)
    return {"rows": len(ids), "unique_titles": len(uniq), "sha256": sha256(out)}, batch


def upload(out_dir: Path) -> None:
    files = sorted(str(p) for p in out_dir.glob("day=*.parquet")) + [str(out_dir / "manifest.json")]
    notes = ("all-MiniLM-L6-v2 title embeddings (int8[384]) of every root story in the Yggdrasil replay, "
             "Dec 16 2024 - Jan 31 2025, computed from the GDELT 2.0 English stream. Produced by embed_gpu.py "
             "on the gpu-embed branch; verified on import with a CPU parity sample.")
    cmd = ["gh", "release", "create", TAG, *files, "--repo", REPO, "--title", "MiniLM title embeddings (replay)", "--notes", notes]
    print("running:", " ".join(cmd[:4]), f"... ({len(files)} files)")
    subprocess.run(cmd, check=True)
    print(f"done: https://github.com/{REPO}/releases/tag/{TAG}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", default=str(HERE / "inputs"))
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--days", nargs="*", help="only these days (YYYY-MM-DD); default: all")
    ap.add_argument("--batch-size", type=int, default=1024)
    ap.add_argument("--allow-cpu", action="store_true", help="run without CUDA (slow; for testing only)")
    ap.add_argument("--upload", action="store_true", help="attach out/ to the GitHub release and exit")
    args = ap.parse_args()
    inp, out = Path(args.inputs), Path(args.out)
    if args.upload:
        upload(out)
        return 0

    import sentence_transformers
    import torch
    import transformers

    if torch.cuda.is_available():
        device = "cuda"
    elif args.allow_cpu:
        device = "cpu"
    else:
        sys.exit("CUDA is not available to PyTorch. Install a CUDA build of torch (see README), or pass --allow-cpu to test.")

    man_in = json.loads((inp / "manifest.json").read_text())
    names = sorted(man_in["files"])
    if args.days:
        names = [n for n in names if n[len("day="):-len(".parquet")] in set(args.days)]
    for name in names:
        if sha256(inp / name) != man_in["files"][name]["sha256"]:
            sys.exit(f"{name}: input sha256 mismatch (incomplete clone?)")

    out.mkdir(parents=True, exist_ok=True)
    man_path = out / "manifest.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {"files": {}}
    man.update({"model": MODEL, "revision": REVISION, "max_tokens": MAX_TOKENS, "dtype": "fp32", "tf32": False,
                "device": torch.cuda.get_device_name(0) if device == "cuda" else platform.processor(),
                "torch": torch.__version__, "cuda": torch.version.cuda, "sentence_transformers": sentence_transformers.__version__,
                "transformers": transformers.__version__, "python": platform.python_version(), "platform": platform.platform()})
    todo = [n for n in names if not ((out / n).exists() and man["files"].get(n, {}).get("sha256") == sha256(out / n))]
    print(f"device: {man['device']}  torch {torch.__version__} (CUDA {torch.version.cuda})  days: {len(todo)} to do, "
          f"{len(names) - len(todo)} already done")
    model = load_model(device)
    total = sum(man_in["files"][n]["unique_titles"] for n in todo)
    batch, t0 = args.batch_size, time.monotonic()
    with tqdm(total=total, unit="title", unit_scale=True, dynamic_ncols=True, smoothing=0.05) as bar:
        for name in todo:
            bar.set_description(name[len("day="):-len(".parquet")])
            meta, batch = embed_day(model, inp / name, out / name, batch, bar)
            if meta["rows"] != man_in["files"][name]["rows"]:
                sys.exit(f"{name}: wrote {meta['rows']} rows, expected {man_in['files'][name]['rows']}")
            man["files"][name] = meta
            man_path.write_text(json.dumps(man, indent=1, sort_keys=True))
    el = time.monotonic() - t0
    print(f"done: {len(todo)} days, {total} distinct titles in {el / 60:.1f} min ({total / max(el, 1e-9):.0f} titles/s)")
    if len(man["files"]) == len(man_in["files"]):
        print("all days present. Next: python embed_gpu.py --upload   (or attach out/* to the release by hand; see README)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
