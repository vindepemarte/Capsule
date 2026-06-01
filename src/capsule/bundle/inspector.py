from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class BundleInspectError(RuntimeError):
    """Raised when a .capsule bundle cannot be inspected."""


class BundleInfo(BaseModel):
    path: Path
    name: str | None = None
    version: str | None = None
    format: str | None = None
    files: list[str] = Field(default_factory=list)
    has_manifest: bool = False
    has_lockfile: bool = False
    lock: dict[str, Any] = Field(default_factory=dict)


def inspect_bundle(path: Path) -> BundleInfo:
    if not path.exists():
        raise BundleInspectError(f"Bundle not found: {path}")
    if not zipfile.is_zipfile(path):
        raise BundleInspectError(f"Bundle is not a valid .capsule zip archive: {path}")

    with zipfile.ZipFile(path) as archive:
        files = sorted(archive.namelist())
        metadata = _read_json(archive, "capsule.bundle.json")
        lock = _read_yaml(archive, "capsule.lock")

    return BundleInfo(
        path=path,
        name=metadata.get("name") or lock.get("name"),
        version=metadata.get("version") or lock.get("version"),
        format=metadata.get("format"),
        files=files,
        has_manifest="capsule.yaml" in files,
        has_lockfile="capsule.lock" in files,
        lock=lock,
    )


def _read_json(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    if name not in archive.namelist():
        return {}
    return json.loads(archive.read(name).decode("utf-8"))


def _read_yaml(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    if name not in archive.namelist():
        return {}
    data = yaml.safe_load(archive.read(name).decode("utf-8"))
    return data if isinstance(data, dict) else {}
