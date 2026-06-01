from __future__ import annotations

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    name: str
    permission: str
    mocked: bool = False
    result: object | None = None


class TraceStep(BaseModel):
    node: str
    type: str
    agent: str | None = None
    tools: list[ToolCall] = Field(default_factory=list)
    selected_next: str | None = None


class RunTrace(BaseModel):
    path: list[str] = Field(default_factory=list)
    steps: list[TraceStep] = Field(default_factory=list)


class RunResult(BaseModel):
    output: dict
    trace: RunTrace
