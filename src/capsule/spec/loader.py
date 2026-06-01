from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from capsule.spec.models import CapsuleManifest


class CapsuleLoadError(ValueError):
    """Raised when a Capsule project cannot be loaded."""


@dataclass(frozen=True)
class ProjectContext:
    root: Path
    manifest_path: Path
    manifest: CapsuleManifest


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CapsuleLoadError(f"File not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise CapsuleLoadError(f"Invalid YAML in {path}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise CapsuleLoadError(f"YAML root must be an object: {path}")
    return data


def find_manifest(project_path: Path) -> Path:
    candidate = project_path / "capsule.yaml"
    if candidate.exists():
        return candidate
    raise CapsuleLoadError(f"No capsule.yaml found in {project_path}")


def load_project(project_path: Path | str = ".") -> ProjectContext:
    root = Path(project_path).resolve()
    if root.is_file():
        root = root.parent
    manifest_path = find_manifest(root)
    data = load_yaml(manifest_path)

    try:
        manifest = CapsuleManifest.model_validate(data)
    except ValidationError as exc:
        raise CapsuleLoadError(str(exc)) from exc

    return ProjectContext(root=root, manifest_path=manifest_path, manifest=manifest)
