# gpu-embed: MiniLM title embeddings on a local GPU

This branch holds only data and one script. It is not part of the Yggdrasil code history.

It embeds the 4,009,947 root story titles of the replay (Dec 16 2024 to Jan 31 2025, 47 days, 3,527,506
distinct titles per day summed) with `sentence-transformers/all-MiniLM-L6-v2` on a CUDA GPU. The same job
on the main box's 2 CPU cores runs at about 145 titles/s, roughly 8 hours.

The output reproduces `ygg.observation.embed` exactly:
- each distinct title of a day is encoded once, with a 64-token cap;
- vectors are L2-normalized, mapped back to every root in input order, and quantized to int8;
- each day is written as `out/day=D.parquet` with columns `observation_id` and `vec int8[384]`;
- inference runs in strict fp32 (TF32 off) with deterministic cuBLAS.

A CPU run of this script on 500 titles matched the main box's own embeddings: 99.8% of vectors were
bit-identical, the rest differed by one int8 step, and the minimum cosine was 0.99997.

## What's here

| path | what |
|---|---|
| `inputs/day=D.parquet` | root `observation_id` and `title` per day, in the exact order the main box expects (240 MB total) |
| `inputs/manifest.json` | rows, distinct titles and sha256 per input file |
| `embed_gpu.py` | the embedding script (batched, tqdm progress, CUDA, resumable) |
| `requirements.txt` | pinned to the main box's versions |

## Run it

**1. Get the branch.** `--single-branch` keeps the clone to this branch only.

```
git clone --branch gpu-embed --single-branch https://github.com/notPhani/Yggdrasil-Research.git ygg-gpu-embed
cd ygg-gpu-embed
```

**2. Create a Python environment** (Python 3.10 to 3.12).

Windows (PowerShell):
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```
Linux:
```
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install a CUDA build of PyTorch, then the rest.** Take the install command from
https://pytorch.org/get-started/locally/ (Stable, your OS, Pip, Python, a CUDA version your driver
supports; `nvidia-smi` shows the driver's highest CUDA version). It is a `pip install torch --index-url
https://download.pytorch.org/whl/cuXXX` line. Then:

```
pip install -r requirements.txt
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

The check must print `True` and the GPU name, e.g. `NVIDIA GeForce RTX 4050 Laptop GPU`.

**4. Smoke test: one day.** About 95k titles; this also downloads the model, about 90 MB.

```
python embed_gpu.py --days 2024-12-16
```

**5. Everything.** The run is resumable: finished days are skipped, so rerun after an interruption.

```
python embed_gpu.py
```

The bar counts distinct titles. On CUDA out-of-memory the batch size halves itself and the run
continues. The default is `--batch-size 1024`, which suits a 6 GB laptop GPU.

**6. Post the results to a GitHub release.** Tag `embeddings-minilm-v1` on `notPhani/Yggdrasil-Research`.

With the GitHub CLI (run `gh auth login` once first):
```
python embed_gpu.py --upload
```

By hand, if you don't have the CLI:
- open github.com/notPhani/Yggdrasil-Research, then Releases, then Draft a new release;
- create the tag `embeddings-minilm-v1` and give it any title;
- attach every file in `out/`: 47 `day=*.parquet` files plus `manifest.json`, about 1.5 GB in total, each well under the 2 GiB limit;
- **Publish** it. A draft release is not downloadable.

**7. Tell the main session.** It downloads the release and runs `ygg embed-import`, which checks:
- each file's sha256 against `out/manifest.json`;
- that observation ids and order match its roots exactly;
- a CPU re-embedding of 200 titles per day, which must reach cosine >= 0.999 with your vectors.

Only if all 47 days pass are the vectors installed.

## Notes
- **The release is public, like the repo.** The vectors derive from public GDELT titles. Delete the
  release after the import, or keep it as a reproducibility artifact so anyone rerunning the replay can
  skip the 8-hour embedding step.
- **Without CUDA the script refuses to run.** `--allow-cpu` exists only for testing.
- **Delete this branch after the import.** It only exists to move data.
