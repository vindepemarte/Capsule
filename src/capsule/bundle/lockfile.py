from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import yaml

from capsule.spec.loader import ProjectContext
from capsule.spec.paths import parse_python_entrypoint, resolve_project_path

SPEC_VERSION = "0.1"


def build_lock_data(context: ProjectContext) -> dict:
    manifest = context.manifest
    prompts = {
        name: _hash_file(resolve_project_path(context.root, agent.prompt, f"agents.{name}.prompt"))
        for name, agent in manifest.agents.items()
    }
    tools = {
        name: _hash_file(parse_python_entrypoint(context.root, tool.entrypoint or "").file)
        for name, tool in manifest.tools.items()
        if tool.type == "python"
    }
    tests = {
        test_path: _hash_file(resolve_project_path(context.root, test_path, "test"))
        for test_path in manifest.tests
    }

    return {
        "specVersion": SPEC_VERSION,
        "name": manifest.name,
        "version": manifest.version,
        "builtAt": datetime.now(UTC).isoformat(),
        "schemas": {
            "input": manifest.input_schema,
            "output": manifest.output_schema,
        },
        "models": {name: model.model_dump() for name, model in manifest.models.items()},
        "toolMetadata": {
            name: tool.model_dump(mode="json") for name, tool in manifest.tools.items()
        },
        "prompts": prompts,
        "tools": tools,
        "tests": tests,
    }


def write_lockfile(context: ProjectContext) -> Path:
    lock_path = context.root / "capsule.lock"
    lock_path.write_text(
        yaml.safe_dump(build_lock_data(context), sort_keys=True),
        encoding="utf-8",
    )
    return lock_path


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
