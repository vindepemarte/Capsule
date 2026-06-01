from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from capsule.spec.models import ModelSpec, ToolSpec


class GraphModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class GraphAgent(GraphModel):
    name: str
    prompt_path: str
    prompt: str
    model: str
    tools: list[str] = Field(default_factory=list)


class GraphNode(GraphModel):
    id: str
    type: str
    agent: str | None = None
    next: str | dict[str, str] | None = None
    output: str | None = None


class CapsuleGraph(GraphModel):
    name: str
    version: str
    description: str
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    models: dict[str, ModelSpec]
    agents: dict[str, GraphAgent]
    tools: dict[str, ToolSpec]
    start: str
    nodes: dict[str, GraphNode]
    permissions: dict[str, str]
    tests: list[str]
