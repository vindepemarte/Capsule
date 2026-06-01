from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ModelSpec(StrictModel):
    provider: str
    model: str


class AgentSpec(StrictModel):
    prompt: str
    model: str
    tools: list[str] = Field(default_factory=list)


class ToolSpec(StrictModel):
    type: Literal["python", "mcp"] = "python"
    entrypoint: str | None = None
    server: str | None = None
    tool: str | None = None
    permission: str

    @model_validator(mode="after")
    def validate_tool_shape(self) -> "ToolSpec":
        if self.type == "python":
            if not self.entrypoint:
                raise ValueError("Python tools must declare entrypoint")
            if self.server or self.tool:
                raise ValueError("Python tools cannot declare server or tool")
        elif self.type == "mcp":
            if not self.server:
                raise ValueError("MCP tools must declare server")
            if not self.tool:
                raise ValueError("MCP tools must declare tool")
            if self.entrypoint:
                raise ValueError("MCP tools cannot declare entrypoint")
        return self


class WorkflowStepSpec(StrictModel):
    id: str
    type: Literal["agent", "human_gate"] = "agent"
    agent: str | None = None
    next: str | dict[str, str] | None = None
    output: str | None = None


class WorkflowSpec(StrictModel):
    start: str
    steps: list[WorkflowStepSpec]


class PermissionsSpec(StrictModel):
    tools: dict[str, str] = Field(default_factory=dict)


class CapsuleManifest(StrictModel):
    name: str
    version: str
    description: str = ""
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    models: dict[str, ModelSpec]
    agents: dict[str, AgentSpec]
    tools: dict[str, ToolSpec] = Field(default_factory=dict)
    workflow: WorkflowSpec
    permissions: PermissionsSpec = Field(default_factory=PermissionsSpec)
    tests: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name cannot be empty")
        return cleaned


ManifestData = dict[str, Any]
