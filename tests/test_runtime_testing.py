from pathlib import Path

import pytest

from capsule.graph.builder import build_graph
from capsule.runtime.executor import RuntimeExecutionError, run_graph
from capsule.spec.loader import load_project
from capsule.testing.runner import run_capsule_tests


EXAMPLE = Path("examples/refund-support-agent")


def test_runtime_executes_example_input():
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    result = run_graph(
        graph,
        context.root,
        {"message": "I want a refund for my last order."},
        allow_all=True,
    )

    assert result.trace.path == ["triage", "responder"]
    assert "refund" in result.output["final_reply"].lower()


def test_runtime_rejects_input_that_does_not_match_schema():
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    with pytest.raises(RuntimeExecutionError, match="input does not match declared schema"):
        run_graph(graph, context.root, {})


def test_runtime_rejects_output_that_does_not_match_schema():
    context = load_project(EXAMPLE)
    graph = build_graph(context).model_copy(
        update={
            "output_schema": {
                "type": "object",
                "required": ["missing_field"],
                "properties": {"missing_field": {"type": "string"}},
            }
        }
    )

    with pytest.raises(RuntimeExecutionError, match="output does not match declared schema"):
        run_graph(
            graph, context.root, {"message": "I want a refund for my last order."}, allow_all=True
        )


def test_capsule_test_harness_runs_yaml_tests():
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    report = run_capsule_tests(graph, context.root)

    assert report.passed, report.model_dump()


def test_capsule_test_harness_reports_schema_failures():
    context = load_project(EXAMPLE)
    graph = build_graph(context).model_copy(
        update={
            "input_schema": {
                "type": "object",
                "required": ["missing_field"],
                "properties": {"missing_field": {"type": "string"}},
            }
        }
    )

    report = run_capsule_tests(graph, context.root)

    assert not report.passed
    assert "input does not match declared schema" in report.results[0].failures[0]
