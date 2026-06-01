from __future__ import annotations

import json
import zipfile
from pathlib import Path

from capsule.bundle.lockfile import write_lockfile
from capsule.spec.loader import ProjectContext
from capsule.spec.paths import parse_python_entrypoint, resolve_project_path


def build_bundle(context: ProjectContext, output_dir: Path | None = None) -> Path:
    lock_path = write_lockfile(context)
    out_dir = output_dir or context.root / "dist"
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = out_dir / f"{context.manifest.name}-{context.manifest.version}.capsule"

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _write_file(archive, context.manifest_path, context.root)
        _write_file(archive, lock_path, context.root)
        for path in _asset_paths(context):
            _write_file(archive, path, context.root)
        archive.writestr(
            "capsule.bundle.json",
            json.dumps(
                {
                    "name": context.manifest.name,
                    "version": context.manifest.version,
                    "format": "capsule.zip.v1",
                },
                indent=2,
            ),
        )

    return bundle_path


def _asset_paths(context: ProjectContext) -> list[Path]:
    paths: list[Path] = []
    for agent in context.manifest.agents.values():
        paths.append(resolve_project_path(context.root, agent.prompt, "agent prompt"))
    for tool in context.manifest.tools.values():
        if tool.type == "python":
            paths.append(parse_python_entrypoint(context.root, tool.entrypoint or "").file)
    for test_path in context.manifest.tests:
        paths.append(resolve_project_path(context.root, test_path, "test"))
    return paths


def _write_file(archive: zipfile.ZipFile, path: Path, root: Path) -> None:
    archive.write(path, path.resolve().relative_to(root.resolve()).as_posix())
