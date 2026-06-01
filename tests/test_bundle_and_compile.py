import importlib.util
import sys
import types
from pathlib import Path
from zipfile import ZipFile

from typer.testing import CliRunner

from capsule.adapters.langgraph.compiler import compile_langgraph
from capsule.bundle.builder import build_bundle
from capsule.bundle.inspector import inspect_bundle
from capsule.bundle.verifier import verify_bundle
from capsule.cli.app import app
from capsule.graph.builder import build_graph
from capsule.spec.loader import load_project


EXAMPLE = Path("examples/refund-support-agent")
runner = CliRunner()


def test_build_bundle_creates_capsule_archive(tmp_path):
    context = load_project(EXAMPLE)

    bundle_path = build_bundle(context, tmp_path)

    assert bundle_path.name == "refund-support-agent-0.1.0.capsule"
    with ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
    assert "capsule.yaml" in names
    assert "capsule.lock" in names
    assert "agents/triage.md" in names
    assert "tools/policy_search.py" in names


def test_inspect_bundle_reads_metadata_and_file_list(tmp_path):
    context = load_project(EXAMPLE)
    bundle_path = build_bundle(context, tmp_path)

    info = inspect_bundle(bundle_path)

    assert info.name == "refund-support-agent"
    assert info.version == "0.1.0"
    assert info.has_manifest
    assert info.has_lockfile
    assert "capsule.yaml" in info.files
    assert info.lock["name"] == "refund-support-agent"
    assert info.lock["schemas"]["input"]["required"] == ["message"]


def test_inspect_bundle_command_prints_metadata(tmp_path):
    context = load_project(EXAMPLE)
    bundle_path = build_bundle(context, tmp_path)

    result = runner.invoke(app, ["inspect-bundle", str(bundle_path)])

    assert result.exit_code == 0, result.output
    assert "refund-support-agent" in result.output
    assert "capsule.yaml" in result.output


def test_verify_bundle_accepts_valid_bundle(tmp_path):
    context = load_project(EXAMPLE)
    bundle_path = build_bundle(context, tmp_path)

    report = verify_bundle(bundle_path)

    assert report.ok, report.errors
    assert "agents/triage.md" in report.checked_files
    assert "tools/policy_search.py" in report.checked_files


def test_verify_bundle_command_prints_success(tmp_path):
    context = load_project(EXAMPLE)
    bundle_path = build_bundle(context, tmp_path)

    result = runner.invoke(app, ["verify-bundle", str(bundle_path)])

    assert result.exit_code == 0, result.output
    assert "Bundle verified" in result.output
    assert "agents/triage.md" in result.output


def test_verify_bundle_rejects_tampered_file(tmp_path):
    context = load_project(EXAMPLE)
    bundle_path = build_bundle(context, tmp_path)
    tampered = tmp_path / "tampered.capsule"
    _copy_bundle_with_replacement(bundle_path, tampered, "agents/triage.md", b"tampered")

    report = verify_bundle(tampered)

    assert not report.ok
    assert any("Hash mismatch" in error for error in report.errors)


def test_verify_bundle_rejects_schema_lock_mismatch(tmp_path):
    context = load_project(EXAMPLE)
    bundle_path = build_bundle(context, tmp_path)
    tampered = tmp_path / "tampered-schema.capsule"
    _copy_bundle_with_replacement(
        bundle_path, tampered, "capsule.lock", b"name: refund-support-agent\n"
    )

    report = verify_bundle(tampered)

    assert not report.ok
    assert any("schemas metadata" in error for error in report.errors)


def test_langgraph_compiler_generates_readable_project(tmp_path):
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    output = compile_langgraph(context, graph, tmp_path / "langgraph")

    assert (output / "main.py").exists()
    assert (output / "pyproject.toml").exists()
    assert (output / "capsule-graph.json").exists()
    assert "StateGraph" in (output / "main.py").read_text(encoding="utf-8")


def test_generated_langgraph_project_preserves_tool_behavior(tmp_path, monkeypatch):
    context = load_project(EXAMPLE)
    graph = build_graph(context)
    output = compile_langgraph(context, graph, tmp_path / "langgraph")

    module = _load_generated_main(output / "main.py", monkeypatch)
    result = module.build_graph().invoke({"message": "I want a refund for my last order."})

    assert result["route"] == "approved"
    assert "refund" in result["final_reply"].lower()
    assert "Refunds are available within 30 days" in result["final_reply"]


def _load_generated_main(path: Path, monkeypatch):
    graph_module = types.ModuleType("langgraph.graph")
    graph_module.START = "__start__"
    graph_module.END = "__end__"
    graph_module.StateGraph = _FakeStateGraph
    langgraph_module = types.ModuleType("langgraph")
    langgraph_module.graph = graph_module
    monkeypatch.setitem(sys.modules, "langgraph", langgraph_module)
    monkeypatch.setitem(sys.modules, "langgraph.graph", graph_module)

    spec = importlib.util.spec_from_file_location("_generated_capsule_langgraph", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeStateGraph:
    def __init__(self, state_type):
        self.state_type = state_type
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}

    def add_node(self, name, function):
        self.nodes[name] = function

    def add_edge(self, source, target):
        self.edges[source] = target

    def add_conditional_edges(self, source, route_function, mapping):
        self.conditional_edges[source] = (route_function, mapping)

    def compile(self):
        return _FakeCompiledGraph(self.nodes, self.edges, self.conditional_edges)


class _FakeCompiledGraph:
    def __init__(self, nodes, edges, conditional_edges):
        self.nodes = nodes
        self.edges = edges
        self.conditional_edges = conditional_edges

    def invoke(self, input_data):
        state = dict(input_data)
        current = self.edges["__start__"]
        while current != "__end__":
            state.update(self.nodes[current](state))
            if current in self.conditional_edges:
                route_function, mapping = self.conditional_edges[current]
                current = mapping[route_function(state)]
            else:
                current = self.edges[current]
        return state


def _copy_bundle_with_replacement(source: Path, target: Path, name: str, content: bytes) -> None:
    with ZipFile(source) as original, ZipFile(target, "w") as replacement:
        for item in original.infolist():
            if item.filename == name:
                replacement.writestr(item.filename, content)
            else:
                replacement.writestr(item, original.read(item.filename))
