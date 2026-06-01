from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class CapsulePathError(ValueError):
    """Raised when a project path is unsafe or invalid."""


@dataclass(frozen=True)
class Entrypoint:
    file: Path
    function: str


def resolve_project_path(root: Path, raw_path: str, label: str) -> Path:
    if not raw_path:
        raise CapsulePathError(f"{label} path cannot be empty")

    path = Path(raw_path)
    if path.is_absolute():
        raise CapsulePathError(f"{label} must be relative to the Capsule project")

    project_root = root.resolve()
    resolved = (project_root / path).resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise CapsulePathError(f"{label} escapes the Capsule project: {raw_path}") from exc

    return resolved


def parse_python_entrypoint(root: Path, value: str) -> Entrypoint:
    if ":" not in value:
        raise CapsulePathError(f"Python tool entrypoint must use 'file.py:function': {value}")

    file_part, function = value.split(":", 1)
    if not function.strip():
        raise CapsulePathError(f"Python tool entrypoint is missing a function: {value}")

    return Entrypoint(
        file=resolve_project_path(root, file_part.strip(), "tool entrypoint"),
        function=function.strip(),
    )
