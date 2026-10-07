"""DuckDB views over the day-partitioned Parquet tables (decision 0.3). Every table directory is registered."""
from __future__ import annotations

from pathlib import Path

import duckdb


def connect(data_dir: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    root = Path(data_dir) / "tables"
    for d in sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []:
        if any(d.glob("day=*/*.parquet")):
            con.execute(f"CREATE VIEW {d.name} AS SELECT * FROM read_parquet('{d}/day=*/*.parquet', hive_partitioning=true)")
    return con
