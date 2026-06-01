import json
from pathlib import Path

from capsule.graph.builder import build_graph
from capsule.graph.serialize import graph_to_dict, graph_to_json
from capsule.spec.loader import load_project
from capsule.validate.rules import validate_project


EXAMPLE = Path("examples/refund-support-agent")


def test_example_project_validates():
    context = load_project(EXAMPLE)
    report = validate_project(context)

    assert report.ok, [error.format() for error in report.errors]


def test_example_project_builds_capsule_graph():
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    assert graph.name == "refund-support-agent"
    assert graph.start == "triage"
    assert graph.input_schema is not None
    assert graph.input_schema["required"] == ["message"]
    assert graph.output_schema is not None
    assert graph.output_schema["required"] == ["final_reply"]
    assert set(graph.nodes) == {"triage", "human_review", "responder"}
    assert graph.agents["triage"].tools == ["policy_search"]


def test_capsule_graph_serializes_to_json():
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    data = graph_to_dict(graph)
    text = graph_to_json(graph)

    assert data["name"] == "refund-support-agent"
    assert data["input_schema"]["properties"]["message"]["type"] == "string"
    assert data["nodes"]["triage"]["agent"] == "triage"
    assert json.loads(text)["start"] == "triage"
