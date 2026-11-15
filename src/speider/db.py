"""Local DuckDB database: connect and create the schema."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import duckdb

DEFAULT_PATH = Path("data") / "speider.duckdb"


def connect(path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open the database (":memory:" for tests) and make sure the schema exists."""
    if path is None:
        path = DEFAULT_PATH
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute(resources.files("speider").joinpath("schema.sql").read_text(encoding="utf-8"))
    return con


def upsert(con: duckdb.DuckDBPyConnection, table: str, rows: list[dict]) -> int:
    """Insert rows, replacing any that share a primary key. Returns the row count."""
    if not rows:
        return 0
    columns = list(rows[0])
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    con.executemany(sql, [[row.get(c) for c in columns] for row in rows])
    return len(rows)
