"""DuckDB views over the day-partitioned Parquet tables (decision 0.3)."""
from __future__ import annotations

from pathlib import Path

import duckdb

TABLES = ("obs_doc", "dup_links", "window_ledger", "obs_event", "obs_mention")


def connect(data_dir: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    for name in TABLES:
        root = Path(data_dir) / "tables" / name
        if any(root.glob("day=*/*.parquet")):
            con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{root}/day=*/*.parquet', hive_partitioning=true)")
    return con
