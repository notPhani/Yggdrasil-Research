"""Frozen configuration and its hash (rule D6: every artifact is stamped with cfg_hash)."""
from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "default.toml"


def load_config(path: str | Path | None = None) -> dict:
    with open(path or DEFAULT_CONFIG, "rb") as f:
        cfg = tomllib.load(f)
    data_dir = Path(cfg["paths"]["data_dir"])
    if not data_dir.is_absolute():
        cfg["paths"]["data_dir"] = str(REPO_ROOT / data_dir)
    return cfg


def cfg_hash(cfg: dict) -> str:
    """sha256 of the canonical JSON form; paths are excluded so the hash is machine-independent."""
    canon = {k: v for k, v in cfg.items() if k != "paths"}
    return hashlib.sha256(json.dumps(canon, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
