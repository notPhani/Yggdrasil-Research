"""GDELT 2.0 English-stream downloader.

The master manifest is turned into a chronological plan. Files are fetched in parallel, each one
checked against the manifest md5 and stored in the content-addressed blob store. Every outcome
goes into an append-only ledger, so a run can be interrupted and resumed. Progress is written
to status.json for `ygg fetch-status`, and milestone lines go to progress.log.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ygg.store.blobs import BlobStore

MASTER_URL = "https://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
SUFFIX_TO_KIND = {"export.CSV.zip": "export", "mentions.CSV.zip": "mentions", "gkg.csv.zip": "gkg"}
KIND_ORDER = {"gkg": 0, "export": 1, "mentions": 2}
USER_AGENT = "yggdrasil-research/0.1 (+https://github.com/notPhani/Yggdrasil-Research)"


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    size: int
    md5: str
    url: str
    batch_ts: str  # YYYYMMDDHHMMSS, UTC
    kind: str      # gkg | export | mentions


def parse_manifest_line(line: str) -> ManifestEntry | None:
    """Parse '<size> <md5> <url>'; return None for malformed or non-English-stream lines."""
    parts = line.split()
    if len(parts) != 3:
        return None
    size, md5, url = parts
    name = url.rsplit("/", 1)[-1]
    ts, _, suffix = name.partition(".")
    kind = SUFFIX_TO_KIND.get(suffix)
    if kind is None or len(ts) != 14 or not ts.isdigit() or not size.isdigit():
        return None
    return ManifestEntry(int(size), md5.lower(), url.replace("http://", "https://", 1), ts, kind)


def plan(entries: list[ManifestEntry], start: str, end: str, kinds: tuple[str, ...] = ("gkg", "export", "mentions")) -> list[ManifestEntry]:
    """Entries with start <= batch_ts < end (YYYYMMDDHHMMSS strings), in chronological order."""
    chosen = {(e.batch_ts, e.kind): e for e in entries if start <= e.batch_ts < end and e.kind in kinds}
    return [chosen[k] for k in sorted(chosen, key=lambda k: (k[0], KIND_ORDER[k[1]]))]


def http_get(url: str, timeout: float = 90.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


class Ledger:
    """Append-only JSONL record of every fetch outcome; the latest record per url wins."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def load(self) -> dict[str, dict]:
        latest: dict[str, dict] = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    rec = json.loads(line)
                    latest[rec["url"]] = rec
        return latest

    def append(self, rec: dict) -> None:
        line = json.dumps(rec, sort_keys=True)
        with self._lock, self.path.open("a") as f:
            f.write(line + "\n")


class Progress:
    """Thread-safe counters, a status.json writer and milestone lines for progress.log."""

    def __init__(self, status_path: Path, log_path: Path, files_total: int, bytes_total: int, step_pct: float = 5.0):
        self.status_path, self.log_path = status_path, log_path
        self.files_total, self.bytes_total = files_total, bytes_total
        self.files_done = self.ok = self.missing = self.failed = self.skipped = 0
        self.bytes_done = 0
        self.skipped_bytes = 0
        self.latest_ts = ""
        self.t0 = time.monotonic()
        self.started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._window: list[tuple[float, int]] = []
        self._lock = threading.Lock()
        self._next_pct = step_pct
        self._step = step_pct
        self.state = "running"

    def add(self, entry: ManifestEntry, outcome: str, nbytes: int) -> None:
        with self._lock:
            self.files_done += 1
            setattr(self, outcome, getattr(self, outcome) + 1)
            self.bytes_done += nbytes
            if outcome == "skipped":
                self.skipped_bytes += nbytes
            self.latest_ts = max(self.latest_ts, entry.batch_ts)
            now = time.monotonic()
            if outcome != "skipped":
                self._window.append((now, self.bytes_done))
            self._window = [(t, b) for t, b in self._window if now - t <= 30.0]
            pct = 100.0 * self.bytes_done / max(1, self.bytes_total)
            if outcome in ("missing", "failed"):
                self._log(f"WARN {outcome} {entry.url.rsplit('/', 1)[-1]}")
            while pct >= self._next_pct:
                self._log(self.line())
                self._next_pct += self._step

    def rate(self) -> float:
        if len(self._window) < 2:
            el = time.monotonic() - self.t0
            return (self.bytes_done - self.skipped_bytes) / el if el > 0 else 0.0
        (t0, b0), (t1, b1) = self._window[0], self._window[-1]
        return (b1 - b0) / (t1 - t0) if t1 > t0 else 0.0

    def snapshot(self) -> dict:
        r = self.rate()
        left = max(0, self.bytes_total - self.bytes_done)
        return {
            "state": self.state, "started_utc": self.started, "elapsed_s": round(time.monotonic() - self.t0, 1),
            "files_total": self.files_total, "files_done": self.files_done, "ok": self.ok, "skipped_already_had": self.skipped,
            "missing": self.missing, "failed": self.failed, "bytes_total": self.bytes_total, "bytes_done": self.bytes_done,
            "rate_bps": round(r), "eta_s": round(left / r) if r > 0 else None, "latest_batch": self.latest_ts,
        }

    def line(self) -> str:
        s = self.snapshot()
        return format_status(s)

    def _log(self, msg: str) -> None:
        stamp = datetime.now(timezone.utc).strftime("%H:%M:%SZ")
        with self.log_path.open("a") as f:
            f.write(f"[fetch {stamp}] {msg}\n")

    def write_status(self) -> None:
        with self._lock:
            snap = self.snapshot()
        tmp = self.status_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap, indent=1))
        tmp.replace(self.status_path)

    def finish(self, state: str) -> None:
        with self._lock:
            self.state = state
            self._log(f"{state.upper()} " + self.line())
        self.write_status()


def format_status(s: dict, width: int = 30) -> str:
    frac = s["bytes_done"] / max(1, s["bytes_total"])
    bar = "#" * int(round(frac * width)) + "-" * (width - int(round(frac * width)))
    eta = s.get("eta_s")
    eta_txt = "--:--" if eta is None else f"{eta // 3600:d}:{(eta % 3600) // 60:02d}:{eta % 60:02d}"
    batch = s.get("latest_batch") or "--------"
    return (f"[{bar}] {100 * frac:5.1f}%  {s['bytes_done'] / 1e9:5.2f}/{s['bytes_total'] / 1e9:.2f} GB  "
            f"{s['rate_bps'] / 1e6:5.1f} MB/s  ETA {eta_txt}  files {s['files_done']}/{s['files_total']}  "
            f"missing {s['missing']} failed {s['failed']}  at {batch[:4]}-{batch[4:6]}-{batch[6:8]}")


def fetch_one(entry: ManifestEntry, store: BlobStore, retries: int = 4) -> tuple[str, dict]:
    """Download one file with md5 verification and backoff. Returns (outcome, ledger record)."""
    rec = {**asdict(entry), "sha256": None, "attempts": 0, "status": None, "error": None}
    for attempt in range(1, retries + 1):
        rec["attempts"] = attempt
        try:
            body = http_get(entry.url)
            if hashlib.md5(body).hexdigest() != entry.md5:
                rec["status"], rec["error"] = "bad_md5", f"got {len(body)} bytes"
            else:
                rec["sha256"] = store.put(body, suffix=".zip")
                rec["status"], rec["error"] = "ok", None
                return "ok", rec
        except urllib.error.HTTPError as e:
            rec["status"], rec["error"] = ("missing" if e.code == 404 else "http_error"), f"HTTP {e.code}"
            if e.code == 404 and attempt >= 2:
                break
        except Exception as e:  # network errors: retry
            rec["status"], rec["error"] = "net_error", repr(e)[:200]
        time.sleep(min(30, 2 ** attempt))
    return ("missing" if rec["status"] == "missing" else "failed"), rec


def load_manifest(data_dir: Path, refresh: bool = False) -> tuple[list[ManifestEntry], str]:
    """Download (or reuse) the master manifest; returns entries and the manifest's sha256."""
    path = data_dir / "manifests" / "masterfilelist.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    if refresh or not path.exists():
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(http_get(MASTER_URL, timeout=600))
        tmp.replace(path)
    raw = path.read_bytes()
    entries = [e for e in (parse_manifest_line(l) for l in raw.decode("utf-8", "replace").splitlines()) if e]
    return entries, hashlib.sha256(raw).hexdigest()


def run_fetch(data_dir: Path, start: str, end: str, workers: int = 8, refresh_manifest: bool = False) -> dict:
    fetch_dir = data_dir / "fetch"
    fetch_dir.mkdir(parents=True, exist_ok=True)
    log_path, status_path = fetch_dir / "progress.log", fetch_dir / "status.json"
    entries, manifest_sha = load_manifest(data_dir, refresh_manifest)
    todo_all = plan(entries, start, end)
    store, ledger = BlobStore(data_dir / "blobs"), Ledger(fetch_dir / "ledger.jsonl")
    done = {u for u, r in ledger.load().items() if r["status"] == "ok" and r.get("sha256") and store.has(r["sha256"], ".zip")}
    todo = [e for e in todo_all if e.url not in done]
    prog = Progress(status_path, log_path, len(todo_all), sum(e.size for e in todo_all))
    for e in todo_all:
        if e.url in done:
            prog.add(e, "skipped", e.size)
    prog._log(f"START plan {start}..{end}: {len(todo_all)} files, {prog.bytes_total / 1e9:.2f} GB "
              f"({len(todo_all) - len(todo)} already present), manifest sha256 {manifest_sha[:12]}, workers {workers}")
    stop = threading.Event()

    def writer():
        while not stop.wait(2.0):
            prog.write_status()

    wt = threading.Thread(target=writer, daemon=True)
    wt.start()

    def task(e: ManifestEntry):
        outcome, rec = fetch_one(e, store)
        rec["fetched_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        ledger.append(rec)
        prog.add(e, outcome, e.size if outcome == "ok" else 0)

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(task, todo))
        prog.finish("done" if prog.failed == 0 else "done_with_failures")
    except BaseException:
        prog.finish("interrupted")
        raise
    finally:
        stop.set()
    return prog.snapshot()
