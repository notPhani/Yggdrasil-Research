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


def cmd_embed(args: argparse.Namespace) -> int:
    """Narrative-layer title embeddings for every root document, one cached file per day (resumable)."""
    from datetime import date, timedelta

    from ygg.observation.embed import embed_roots

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    d0 = date.fromisoformat(args.start or cfg["replay"]["start"])
    d1 = date.fromisoformat(args.end or cfg["replay"]["end_exclusive"])
    days = [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days)]
    days = [d for d in days if (data_dir / "tables" / "obs_doc" / f"day={d}" / "part-0.parquet").exists()]
    print(json.dumps(embed_roots(data_dir, days, args.model or cfg["narratives"]["embed_model"], log=lambda m: print(m, flush=True))))
    return 0


def _replay_days(cfg, data_dir: Path, start: str | None, end: str | None) -> list[str]:
    from datetime import date, timedelta

    d0 = date.fromisoformat(start or cfg["replay"]["start"])
    d1 = date.fromisoformat(end or cfg["replay"]["end_exclusive"])
    days = [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days)]
    return [d for d in days if (data_dir / "tables" / "obs_doc" / f"day={d}" / "part-0.parquet").exists()]


def cmd_embed_export(args: argparse.Namespace) -> int:
    """Root titles for an off-box GPU embedding run (see ygg.observation.embed_transfer)."""
    from ygg.observation.embed_transfer import export_inputs

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    export_inputs(data_dir, _replay_days(cfg, data_dir, args.start, args.end), Path(args.out), cfg["narratives"]["embed_model"],
                  log=lambda m: print(m, flush=True))
    return 0


def cmd_embed_import(args: argparse.Namespace) -> int:
    """Verify (sha256, ids, CPU parity sample) and install embeddings produced off-box."""
    from ygg.observation.embed_transfer import import_outputs

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    if args.release:
        from ygg.observation.embed_transfer import download_release

        download_release(args.repo, args.release, Path(args.src), log=lambda m: print(m, flush=True))
    out = import_outputs(data_dir, Path(args.src), _replay_days(cfg, data_dir, args.start, args.end), cfg["narratives"]["embed_model"],
                         sample_per_day=args.sample, log=lambda m: print(m, flush=True))
    print(json.dumps(out))
    return 0


def cmd_fit_narratives(args: argparse.Namespace) -> int:
    """2a-L: fit kappa_s, alpha and the entity temperature on the warmup only (prequential score)."""
    from ygg.determinism import WindowClock, parse_utc
    from ygg.narratives.fit import _days, build_cache, grid
    from ygg.observation import embed as emb

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    clock = WindowClock(parse_utc(cfg["replay"]["start"]), cfg["replay"]["window_seconds"], cfg["replay"]["ingest_lag_seconds"])
    model = cfg["narratives"]["embed_model"]
    end = args.end or cfg["replay"]["warmup_end"]
    log = lambda m: print(m, flush=True)
    if args.cache:
        build_cache(data_dir, clock, cfg["replay"]["start"], end, model, log=log)
    if args.grid:
        f = lambda s, typ: [typ(x) for x in s.split(",")]
        from ygg.narratives.learned import learned_config_from

        grid(data_dir, clock, _days(cfg["replay"]["start"], end), args.burn_in, emb.cached_dim(data_dir, model),
             f(args.kappas, float), f(args.log_alphas, float), f(args.temps, float), log=log, base=learned_config_from(cfg))
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    """Engines 2a + 2b over the replay, with snapshots at every case cutoff and placebo cutoff in data/cases/plan.json."""
    from ygg.config import cfg_hash
    from ygg.determinism import WindowClock, parse_utc
    from ygg.replay import run_replay

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    plan = json.loads((data_dir / "cases" / "plan.json").read_text()) if (data_dir / "cases" / "plan.json").exists() else {}
    snaps = set(plan.get("placebo_windows", [])) | set(plan.get("case_snapshot_windows", {}).values())
    clock = WindowClock(parse_utc(cfg["replay"]["start"]), cfg["replay"]["window_seconds"], cfg["replay"]["ingest_lag_seconds"])
    log_path = data_dir / "tables" / "replay.log"

    def log(msg: str) -> None:
        print(msg, flush=True)
        with log_path.open("a") as f:
            f.write(msg + "\n")

    from ygg.narratives.learned import learned_config_from

    start, state = cfg["replay"].get("process_start", cfg["replay"]["start"]), {}
    ck = data_dir / "checkpoint" / "latest.pkl"
    if args.resume and ck.exists():                 # T1: full-state resume from the last checkpoint (bit-identical)
        import pickle
        from datetime import date, timedelta

        state = pickle.loads(ck.read_bytes())
        start = (date.fromisoformat(state["day"]) + timedelta(days=1)).isoformat()
        log(f"resume after {state['day']} from {ck}")
    out = run_replay(data_dir, clock, start, args.end or cfg["replay"]["end_exclusive"], cfg["narratives"]["embed_model"],
                     cfg_hash(cfg), snapshot_windows=snaps, log=log, lr_cfg=learned_config_from(cfg), checkpoint_every=3,
                     e2a=state.get("e2a"), e2b=state.get("e2b"), parent=state.get("parent", ""), made=state.get("made"))
    (data_dir / "tables" / "replay_summary.json").write_text(json.dumps(out, indent=1, default=str))
    log(f"replay done: {len(out['snapshots'])} snapshots")
    return 0


def cmd_case(args: argparse.Namespace) -> int:
    """Engine 3a for one case day: trigger -> clusters -> tau* -> explanation trees, rivals, abstention."""
    import pyarrow.parquet as pq

    from ygg.determinism import WindowClock, parse_utc
    from ygg.observer.trigger import build_case
    from ygg.observer.universe import load_universe
    from ygg.search.case import explain
    from ygg.search.graph import SearchConfig, build_terminals

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    u = load_universe(data_dir)
    prices = pq.read_table(data_dir / "prices" / "daily.parquet").to_pylist()
    actions = pq.read_table(data_dir / "prices" / "actions.parquet").to_pylist()
    case = build_case(args.day, prices, actions, set(u["etfs"]))
    clock = WindowClock(parse_utc(cfg["replay"]["start"]), cfg["replay"]["window_seconds"], cfg["replay"]["ingest_lag_seconds"])
    t_snap = clock.window_of(parse_utc(case["tau_star"][:19])) - 1
    terminals = build_terminals(case["clusters"], u)
    scfg = SearchConfig()
    res = explain(data_dir, clock, t_snap, terminals, scfg)
    out = {"case": {k: v for k, v in case.items() if k != "stats"}, "search": res}
    plan_path = data_dir / "cases" / "plan.json"
    if not args.no_placebo and plan_path.exists():
        from ygg.search.case import run_placebos

        plan = json.loads(plan_path.read_text())
        real = res["groups"][0]["best"]["cost_mnats"]
        out["placebo"] = run_placebos(data_dir, clock, plan, prices, actions, u, len(terminals), scfg, real)
    path = data_dir / "cases" / f"{args.day}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str)[:6000])
    return 0


def cmd_verdict(args: argparse.Namespace) -> int:
    """Engine 3b on a case produced by 'ygg case': hypotheses, evidence, claims, four-bit verdicts, dossier."""
    from datetime import datetime

    from ygg.dossier import render_markdown, render_terminal
    from ygg.observation.pages import PageFetcher
    from ygg.store.tables import connect
    from ygg.verdicts.engine3b import build_hypotheses, evidence, judge

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    d = json.loads((data_dir / "cases" / f"{args.day}.json").read_text())
    tau = datetime.fromisoformat(d["case"]["tau_star"])
    con = connect(data_dir)
    hyps = build_hypotheses(con, d["search"], d["search"]["t_snap"])
    fetcher = None if args.no_fetch else PageFetcher(data_dir)
    reps = {h.hid: evidence(h, tau, fetcher, fetch_top=args.fetch_top) for h in hyps}
    v = judge(hyps, reps, tau)
    d["verdicts"] = {**v, "hypotheses": [{"hid": h.hid, "label": h.entry_label, "event": h.event, "signature_ok": h.signature_ok,
                                          "burst": h.burst, "surprise_ok": h.edges_surprise_ok,
                                          "reports": [{k: (x if k != "claims" else [c.__dict__ for c in x]) for k, x in r.items()} for r in reps[h.hid]]}
                                         for h in hyps]}
    (data_dir / "cases" / f"{args.day}.json").write_text(json.dumps(d, indent=1, default=str))
    md = render_markdown(d)
    (data_dir / "cases" / f"{args.day}.md").write_text(md)
    render_terminal(d)
    return 0


def cmd_tui(args: argparse.Namespace) -> int:
    """Launch the Rich-powered Terminal User Interface (TUI) for a forensic case."""
    from ygg.tui import ForensicsTUI

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir or cfg["paths"]["data_dir"])
    tui = ForensicsTUI(data_dir, day=args.day)
    tui.render_full_dashboard()
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

    e = sub.add_parser("embed", help="narrative-layer title embeddings for root documents (after 'ygg ingest'; resumable)")
    e.add_argument("--model", default=None, help="default: [narratives] embed_model")
    e.add_argument("--from", dest="start", default=None)
    e.add_argument("--to", dest="end", default=None)
    e.add_argument("--data-dir", default=None)
    e.set_defaults(func=cmd_embed)

    x = sub.add_parser("embed-export", help="export root titles for an off-box GPU embedding run")
    x.add_argument("out", help="output directory (inputs/ is created inside)")
    x.add_argument("--from", dest="start", default=None)
    x.add_argument("--to", dest="end", default=None)
    x.add_argument("--data-dir", default=None)
    x.set_defaults(func=cmd_embed_export)

    i = sub.add_parser("embed-import", help="verify and install embeddings produced off-box")
    i.add_argument("src", help="directory with day=*.parquet and manifest.json from the GPU run")
    i.add_argument("--from", dest="start", default=None)
    i.add_argument("--to", dest="end", default=None)
    i.add_argument("--sample", type=int, default=200, help="titles per day re-embedded here for the parity check")
    i.add_argument("--release", default=None, help="download this GitHub release tag into SRC first (e.g. embeddings-minilm-v1)")
    i.add_argument("--repo", default="notPhani/Yggdrasil-Research")
    i.add_argument("--data-dir", default=None)
    i.set_defaults(func=cmd_embed_import)

    n = sub.add_parser("fit-narratives", help="2a-L: fit kappa_s, alpha, T on the warmup (prequential score)")
    n.add_argument("--cache", action="store_true", help="stage 1: cache the warmup's event clusters")
    n.add_argument("--grid", action="store_true", help="stage 2: score each setting (resumable)")
    n.add_argument("--to", dest="end", default=None, help="end day, exclusive (default: warmup_end)")
    n.add_argument("--burn-in", type=int, default=7)
    n.add_argument("--kappas", default="100,200,400")
    n.add_argument("--log-alphas", default="-10,-40,-160")
    n.add_argument("--temps", default="1,3")
    n.add_argument("--data-dir", default=None)
    n.set_defaults(func=cmd_fit_narratives)

    r = sub.add_parser("replay", help="Engines 2a + 2b over the replay window (needs 'ygg ingest' first)")
    r.add_argument("--to", dest="end", help="end day, exclusive (default: replay end)")
    r.add_argument("--resume", action="store_true", help="continue after the last full-state checkpoint (data/checkpoint)")
    r.add_argument("--data-dir", default=None)
    r.set_defaults(func=cmd_replay)

    c = sub.add_parser("case", help="Engine 3a for one trading day: trigger, clusters, tau*, explanations")
    c.add_argument("day", help="YYYY-MM-DD")
    c.add_argument("--no-placebo", action="store_true")
    c.add_argument("--data-dir", default=None)
    c.set_defaults(func=cmd_case)

    v = sub.add_parser("verdict", help="Engine 3b on a case: hypotheses, evidence, four-bit verdicts, dossier")
    v.add_argument("day", help="YYYY-MM-DD (run 'ygg case DAY' first)")
    v.add_argument("--no-fetch", action="store_true", help="deterministic-only, no page fetches (claims then need GDELT text only)")
    v.add_argument("--fetch-top", type=int, default=6)
    v.add_argument("--data-dir", default=None)
    v.set_defaults(func=cmd_verdict)

    t = sub.add_parser("tui", help="Rich Terminal User Interface (TUI): view explanation tree, evidence, and verdicts")
    t.add_argument("day", nargs="?", default="2025-01-27", help="case day (YYYY-MM-DD, default: 2025-01-27)")
    t.add_argument("--data-dir", default=None)
    t.set_defaults(func=cmd_tui)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
