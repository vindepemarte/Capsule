import json
from pathlib import Path

from typer.testing import CliRunner

from capsule.cli.app import app


EXAMPLE = Path("examples/refund-support-agent")
runner = CliRunner()


def test_graph_command_prints_capsule_graph_json():
    result = runner.invoke(app, ["graph", str(EXAMPLE)])

    assert result.exit_code == 0, result.output
    graph = json.loads(result.output)
    assert graph["name"] == "refund-support-agent"
    assert graph["start"] == "triage"
    assert graph["nodes"]["responder"]["output"] == "final_reply"


def test_graph_command_writes_capsule_graph_json(tmp_path):
    output = tmp_path / "capsule-graph.json"

    result = runner.invoke(app, ["graph", str(EXAMPLE), "--output", str(output)])

    assert result.exit_code == 0, result.output
    graph = json.loads(output.read_text(encoding="utf-8"))
    assert graph["agents"]["triage"]["tools"] == ["policy_search"]
