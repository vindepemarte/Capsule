import json
import shutil
from pathlib import Path
from zipfile import ZipFile

import pytest
import yaml

from capsule.adapters.langgraph.compiler import compile_langgraph
from capsule.bundle.builder import build_bundle
from capsule.bundle.inspector import inspect_bundle
from capsule.bundle.verifier import verify_bundle
from capsule.graph.builder import build_graph
from capsule.runtime.executor import RuntimeExecutionError, run_graph
from capsule.security.scan import scan_project
from capsule.spec.loader import CapsuleLoadError, load_project
from capsule.testing.runner import run_capsule_tests
from capsule.validate.rules import validate_project


MCP_EXAMPLE = Path("examples/mcp-research-agent")


def test_mcp_example_validates_and_builds_graph():
    context = load_project(MCP_EXAMPLE)
    report = validate_project(context)
    graph = build_graph(context)

    assert report.ok, [error.format() for error in report.errors]
    assert graph.tools["web_lookup"].type == "mcp"
    assert graph.tools["web_lookup"].server == "browser"
    assert graph.tools["web_lookup"].tool == "search"


def test_mcp_tool_can_run_when_mocked():
    context = load_project(MCP_EXAMPLE)
    graph = build_graph(context)

    report = run_capsule_tests(graph, context.root)

    assert report.passed, report.model_dump()


def test_mcp_tool_requires_mock_for_local_runtime():
    context = load_project(MCP_EXAMPLE)
    graph = build_graph(context)

    with pytest.raises(RuntimeExecutionError, match="requires a mocked tool result"):
        run_graph(
            graph,
            context.root,
            {"topic": "portable agent workflow packaging"},
            allow_all=True,
        )


def test_mcp_declaration_is_security_visible():
    context = load_project(MCP_EXAMPLE)
    findings = scan_project(context)

    assert any(finding.code == "mcp_tool_declared" for finding in findings)


def test_mcp_bundle_contains_metadata_without_python_tool_source(tmp_path):
    context = load_project(MCP_EXAMPLE)

    bundle_path = build_bundle(context, tmp_path)
    info = inspect_bundle(bundle_path)
    report = verify_bundle(bundle_path)

    assert report.ok, report.errors
    assert info.lock["toolMetadata"]["web_lookup"]["type"] == "mcp"
    assert "tools/web_lookup.py" not in info.files
    with ZipFile(bundle_path) as archive:
        assert "tools/web_lookup.py" not in archive.namelist()


def test_mcp_langgraph_compile_preserves_declaration(tmp_path):
    context = load_project(MCP_EXAMPLE)
    graph = build_graph(context)

    output = compile_langgraph(context, graph, tmp_path / "langgraph")

    data = json.loads((output / "capsule-graph.json").read_text(encoding="utf-8"))
    main = (output / "main.py").read_text(encoding="utf-8")
    assert data["tools"]["web_lookup"]["type"] == "mcp"
    assert "MCP tool" in main


def test_mcp_tool_requires_server_and_tool(tmp_path):
    project = tmp_path / "mcp-research-agent"
    shutil.copytree(MCP_EXAMPLE, project)
    manifest_path = project / "capsule.yaml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    del data["tools"]["web_lookup"]["server"]
    manifest_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(CapsuleLoadError, match="MCP tools must declare server"):
        load_project(project)
