from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from capsule.spec.models import CapsuleManifest


def manifest_json_schema() -> dict[str, Any]:
    schema = CapsuleManifest.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Capsule Manifest"
    return schema


def manifest_json_schema_text() -> str:
    return json.dumps(manifest_json_schema(), indent=2, sort_keys=True) + "\n"


def write_manifest_schema(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest_json_schema_text(), encoding="utf-8")
    return path
