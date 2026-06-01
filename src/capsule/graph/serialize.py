from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from capsule.graph.models import CapsuleGraph


def graph_to_dict(graph: CapsuleGraph) -> dict[str, Any]:
    return graph.model_dump(mode="json")


def graph_to_json(graph: CapsuleGraph) -> str:
    return json.dumps(graph_to_dict(graph), indent=2, sort_keys=True) + "\n"


def write_graph_json(graph: CapsuleGraph, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(graph_to_json(graph), encoding="utf-8")
    return path
