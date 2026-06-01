from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RunRecord(BaseModel):
    id: str
    project_name: str
    project_version: str
    source: str
    status: str
    created_at: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    trace: dict[str, Any] = Field(default_factory=dict)


class RunSummary(BaseModel):
    id: str
    project_name: str
    project_version: str
    source: str
    status: str
    created_at: str
    path: list[str] = Field(default_factory=list)


def history_db_path(project_root: Path) -> Path:
    return project_root / ".capsule" / "runs.sqlite"
