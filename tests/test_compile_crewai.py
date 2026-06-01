from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from capsule.adapters.crewai.compiler import compile_crewai
from capsule.graph.builder import build_graph
from capsule.spec.loader import load_project


EXAMPLE = Path("examples/refund-support-agent")


def test_crewai_compiler_generates_readable_project(tmp_path):
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    output = compile_crewai(context, graph, tmp_path / "crewai")

    assert (output / "main.py").exists()
    assert (output / "pyproject.toml").exists()
    assert (output / "capsule-graph.json").exists()
    assert (output / "prompts" / "triage.md").exists()
    assert (output / "tools" / "policy_search.py").exists()

    main_content = (output / "main.py").read_text(encoding="utf-8")
    assert "from crewai.flow.flow import Flow, listen, router, start" in main_content
    assert "class CapsuleFlow(Flow[State]):" in main_content
    assert "def triage(self)" in main_content
    assert "def route_triage(self, previous_result)" in main_content


def test_generated_crewai_project_structure(tmp_path, monkeypatch):
    context = load_project(EXAMPLE)
    graph = build_graph(context)
    output = compile_crewai(context, graph, tmp_path / "crewai")

    # Mock the crewai libraries so we don't import external dependencies in tests
    mock_crewai = types.ModuleType("crewai")
    mock_crewai.Agent = lambda **kwargs: None
    mock_crewai.Task = lambda **kwargs: None
    mock_crewai.Crew = lambda **kwargs: None

    mock_flow = types.ModuleType("crewai.flow.flow")

    class FakeFlow:
        @classmethod
        def __class_getitem__(cls, item):
            return cls

    mock_flow.Flow = FakeFlow
    mock_flow.start = lambda *args, **kwargs: lambda f: f
    mock_flow.listen = lambda *args, **kwargs: lambda f: f
    mock_flow.router = lambda *args, **kwargs: lambda f: f

    monkeypatch.setitem(sys.modules, "crewai", mock_crewai)
    monkeypatch.setitem(sys.modules, "crewai.flow.flow", mock_flow)

    # Dynamically load the generated main.py
    spec = importlib.util.spec_from_file_location("_generated_capsule_crewai", output / "main.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Check that flow state class exists
    assert hasattr(module, "State")
    assert issubclass(module.CapsuleFlow, FakeFlow)

    # Assert methods are defined
    assert hasattr(module.CapsuleFlow, "triage")
    assert hasattr(module.CapsuleFlow, "route_triage")
    assert hasattr(module.CapsuleFlow, "responder")
    assert hasattr(module.CapsuleFlow, "human_review")
