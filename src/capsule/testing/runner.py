from __future__ import annotations

from pathlib import Path

import yaml

from capsule.graph.models import CapsuleGraph
from capsule.runtime.executor import RuntimeExecutionError, run_graph
from capsule.spec.paths import resolve_project_path
from capsule.testing.models import CapsuleTestCase, TestCaseResult, TestRunReport


def run_capsule_tests(graph: CapsuleGraph, project_root: Path) -> TestRunReport:
    results = []
    for raw_path in graph.tests:
        test_path = resolve_project_path(project_root, raw_path, "test")
        test_case = _load_test_case(test_path)
        results.append(_run_test_case(graph, project_root, test_case))
    return TestRunReport(results=results)


def _load_test_case(path: Path) -> CapsuleTestCase:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return CapsuleTestCase.model_validate(data)


def _run_test_case(
    graph: CapsuleGraph,
    project_root: Path,
    test_case: CapsuleTestCase,
) -> TestCaseResult:
    failures: list[str] = []
    try:
        result = run_graph(
            graph, project_root, test_case.input, test_case.mock_tools, allow_all=True
        )
    except RuntimeExecutionError as exc:
        return TestCaseResult(name=test_case.name, passed=False, failures=[str(exc)])

    expected = test_case.expect

    if expected.path is not None and result.trace.path != expected.path:
        failures.append(f"Expected path {expected.path}, got {result.trace.path}")

    for field, expected_text in expected.output_contains.items():
        actual = result.output.get(field)
        if expected_text.lower() not in str(actual).lower():
            failures.append(f"Expected output.{field} to contain '{expected_text}', got '{actual}'")

    if expected.tool_calls is not None:
        calls = [tool.name for step in result.trace.steps for tool in step.tools]
        if calls != expected.tool_calls:
            failures.append(f"Expected tool calls {expected.tool_calls}, got {calls}")

    return TestCaseResult(name=test_case.name, passed=not failures, failures=failures)
