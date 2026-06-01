from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TestExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: list[str] | None = None
    output_contains: dict[str, str] = Field(default_factory=dict)
    tool_calls: list[str] | None = None


class CapsuleTestCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    input: dict[str, Any]
    mock_tools: dict[str, Any] = Field(default_factory=dict)
    expect: TestExpectation = Field(default_factory=TestExpectation)


class TestCaseResult(BaseModel):
    name: str
    passed: bool
    failures: list[str] = Field(default_factory=list)


class TestRunReport(BaseModel):
    results: list[TestCaseResult]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)
