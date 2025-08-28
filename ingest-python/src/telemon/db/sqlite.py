from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from telemon.models import Observation

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY,
    ts_utc TEXT NOT NULL,
    service_id TEXT NOT NULL,
    iso2 TEXT NOT NULL,
    metric TEXT NOT NULL,
    value INTEGER NOT NULL,
    source TEXT NOT NULL,
    confidence REAL NOT NULL,
    raw TEXT
);
CREATE INDEX IF NOT EXISTS idx_observations_ts ON observations(ts_utc);
CREATE INDEX IF NOT EXISTS idx_observations_svc_cc ON observations(service_id, iso2);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con


def init_db(db_path: str | Path) -> None:
    con = connect(db_path)
    with con:
        for stmt in SCHEMA.strip().split(";\n"):
            if stmt.strip():
                con.execute(stmt)


def insert_observations(
    db_path: str | Path,
    observations: Iterable[Observation],
) -> int:
    con = connect(db_path)
    with con:
        cur = con.executemany(
            """
            INSERT INTO observations
            (ts_utc, service_id, iso2, metric, value, source, confidence, raw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    o.ts_utc,
                    o.service_id,
                    o.iso2.upper(),
                    o.metric,
                    int(o.value),
                    o.source,
                    float(o.confidence),
                    json.dumps(o.raw) if o.raw is not None else None,
                )
                for o in observations
            ],
        )
        return cur.rowcount or 0
