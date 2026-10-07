"""Command line: python -m ygg <command>."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ygg.config import load_config


def _ts(day: str) -> str:
    """'2024-12-16' -> '20241216000000'."""
    return day.replace("-", "") + "000000"


def cmd_fetch(args: argparse.Namespace) -> int:
    from ygg.observation.gdelt_fetch import format_status, run_fetch

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    start = _ts(args.start or cfg["replay"]["start"])
    end = _ts(args.end or cfg["replay"]["end_exclusive"])
    snap = run_fetch(data_dir, start, end, workers=args.workers or cfg["fetch"]["workers"], refresh_manifest=args.refresh_manifest)
    print(format_status(snap))
    return 0 if snap["failed"] == 0 else 1


def cmd_fetch_status(args: argparse.Namespace) -> int:
    from ygg.observation.gdelt_fetch import format_status

    cfg = load_config(args.config)
    path = Path(args.data_dir or cfg["paths"]["data_dir"]) / "fetch" / "status.json"
    if not path.exists():
        print("no fetch has run yet")
        return 1
    snap = json.loads(path.read_text())
    print(f"{snap['state']}: " + format_status(snap))
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    from ygg.observation.engine1 import run_ingest

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    log_path = data_dir / "tables" / "ingest.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)
        with log_path.open("a") as f:
            f.write(msg + "\n")

    from ygg.observation.dedup_l2 import L2Config

    d = cfg["dedup"]
    l2 = L2Config(horizon_h=d["horizon_h"], j0=d["j0"], theta_a=d["theta_a"], logo_titles=d["logo_titles"])
    summary = run_ingest(data_dir, cfg["replay"]["start"], args.end or cfg["replay"]["end_exclusive"],
                         cfg["replay"]["window_seconds"], cfg["replay"]["ingest_lag_seconds"], workers=args.workers, log=log,
                         l2=l2, embed_model=d["embed_model"])
    log(json.dumps(summary))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ygg", description="Yggdrasil: market event forensics")
    p.add_argument("--config", default=None, help="TOML config (default: config/default.toml)")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download GDELT 2.0 English-stream batches (resumable, md5-verified)")
    f.add_argument("--from", dest="start", help="first day, YYYY-MM-DD (default: replay start)")
    f.add_argument("--to", dest="end", help="end day, exclusive, YYYY-MM-DD (default: replay end)")
    f.add_argument("--workers", type=int, default=None)
    f.add_argument("--data-dir", default=None)
    f.add_argument("--refresh-manifest", action="store_true")
    f.set_defaults(func=cmd_fetch)

    s = sub.add_parser("fetch-status", help="show download progress")
    s.add_argument("--data-dir", default=None)
    s.set_defaults(func=cmd_fetch_status)

    g = sub.add_parser("ingest", help="Engine 1: parse downloaded batches, exact dedup, clocks, day-partitioned tables")
    g.add_argument("--to", dest="end", help="end day, exclusive (default: replay end); stops at the last fully downloaded day")
    g.add_argument("--workers", type=int, default=4)
    g.add_argument("--data-dir", default=None)
    g.set_defaults(func=cmd_ingest)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
