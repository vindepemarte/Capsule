from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from capsule.adapters.openai_agents.compiler import compile_openai_agents
from capsule.graph.builder import build_graph
from capsule.spec.loader import load_project


EXAMPLE = Path("examples/refund-support-agent")


def test_openai_agents_compiler_generates_readable_project(tmp_path):
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    output = compile_openai_agents(context, graph, tmp_path / "openai-agents")

    assert (output / "main.py").exists()
    assert (output / "pyproject.toml").exists()
    assert (output / "capsule-graph.json").exists()
    assert (output / "prompts" / "triage.md").exists()
    assert (output / "tools" / "policy_search.py").exists()

    main_content = (output / "main.py").read_text(encoding="utf-8")
    assert "from agents import Agent, Runner, handoff" in main_content
    assert "triage_agent = Agent(" in main_content
    assert "triage_agent.handoffs = [" in main_content


def test_generated_openai_agents_project_structure(tmp_path, monkeypatch):
    context = load_project(EXAMPLE)
    graph = build_graph(context)
    output = compile_openai_agents(context, graph, tmp_path / "openai-agents")

    # Mock the agents library so it doesn't try to import external openai-agents dependency
    mock_agents = types.ModuleType("agents")

    class FakeAgent:
        def __init__(self, name, instructions, tools=None, handoffs=None):
            self.name = name
            self.instructions = instructions
            self.tools = tools or []
            self.handoffs = handoffs or []

    mock_agents.Agent = FakeAgent
    mock_agents.handoff = lambda agent: agent
    mock_agents.Runner = None

    monkeypatch.setitem(sys.modules, "agents", mock_agents)

    # Dynamically load the generated main.py
    spec = importlib.util.spec_from_file_location(
        "_generated_capsule_openai_agents", output / "main.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Check that agents are configured correctly in the generated module
    assert isinstance(module.triage_agent, FakeAgent)
    assert module.triage_agent.name == "triage"
    assert len(module.triage_agent.tools) == 1
    assert (
        len(module.triage_agent.handoffs) == 2
    )  # approved -> responder, needs_human -> human_review

    assert isinstance(module.responder_agent, FakeAgent)
    assert module.responder_agent.name == "responder"
    assert len(module.responder_agent.tools) == 1
