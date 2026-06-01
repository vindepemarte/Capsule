from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from capsule.graph.models import CapsuleGraph
from capsule.history.models import RunRecord, RunSummary, history_db_path
from capsule.runtime.trace import RunResult


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    project_version TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    input_json TEXT NOT NULL,
    output_json TEXT NOT NULL,
    trace_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
"""


class HistoryStoreError(RuntimeError):
    """Raised when run history cannot be read or written."""


def record_run(
    project_root: Path,
    graph: CapsuleGraph,
    input_data: dict[str, Any],
    result: RunResult,
    source: str = "local",
    status: str = "success",
) -> RunRecord:
    record = RunRecord(
        id=str(uuid.uuid4()),
        project_name=graph.name,
        project_version=graph.version,
        source=source,
        status=status,
        created_at=datetime.now(UTC).isoformat(),
        input=input_data,
        output=result.output,
        trace=result.trace.model_dump(mode="json"),
    )
    with _connect(project_root) as connection:
        _ensure_schema(connection)
        connection.execute(
            """
            INSERT INTO runs (
                id,
                project_name,
                project_version,
                source,
                status,
                created_at,
                input_json,
                output_json,
                trace_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.project_name,
                record.project_version,
                record.source,
                record.status,
                record.created_at,
                _dumps(record.input),
                _dumps(record.output),
                _dumps(record.trace),
            ),
        )
    return record


def list_runs(project_root: Path, limit: int = 20) -> list[RunSummary]:
    with _connect(project_root) as connection:
        _ensure_schema(connection)
        rows = connection.execute(
            """
            SELECT id, project_name, project_version, source, status, created_at, trace_json
            FROM runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_summary_from_row(row) for row in rows]


def get_run(project_root: Path, run_id: str) -> RunRecord:
    with _connect(project_root) as connection:
        _ensure_schema(connection)
        row = connection.execute(
            """
            SELECT id, project_name, project_version, source, status, created_at,
                   input_json, output_json, trace_json
            FROM runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
    if row is None:
        raise HistoryStoreError(f"Run not found: {run_id}")
    return _record_from_row(row)


def _connect(project_root: Path) -> sqlite3.Connection:
    db_path = history_db_path(project_root)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)


def _record_from_row(row: sqlite3.Row) -> RunRecord:
    return RunRecord(
        id=row["id"],
        project_name=row["project_name"],
        project_version=row["project_version"],
        source=row["source"],
        status=row["status"],
        created_at=row["created_at"],
        input=json.loads(row["input_json"]),
        output=json.loads(row["output_json"]),
        trace=json.loads(row["trace_json"]),
    )


def _summary_from_row(row: sqlite3.Row) -> RunSummary:
    trace = json.loads(row["trace_json"])
    return RunSummary(
        id=row["id"],
        project_name=row["project_name"],
        project_version=row["project_version"],
        source=row["source"],
        status=row["status"],
        created_at=row["created_at"],
        path=trace.get("path", []),
    )


def _dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True)
