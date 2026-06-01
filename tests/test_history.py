import re
import shutil
from pathlib import Path

from typer.testing import CliRunner

from capsule.cli.app import app
from capsule.graph.builder import build_graph
from capsule.history.models import history_db_path
from capsule.history.store import get_run, list_runs, record_run
from capsule.runtime.executor import run_graph
from capsule.spec.loader import load_project


EXAMPLE = Path("examples/refund-support-agent")
runner = CliRunner()


def test_record_and_read_run_history(tmp_path):
    project = _copy_example(tmp_path)
    context = load_project(project)
    graph = build_graph(context)
    input_data = {"message": "I want a refund for my last order."}
    result = run_graph(graph, context.root, input_data, allow_all=True)

    record = record_run(context.root, graph, input_data, result)
    runs = list_runs(context.root)
    fetched = get_run(context.root, record.id)

    assert history_db_path(context.root).exists()
    assert runs[0].id == record.id
    assert runs[0].path == ["triage", "responder"]
    assert fetched.output["final_reply"] == result.output["final_reply"]


def test_run_command_records_history_and_show_run(tmp_path):
    project = _copy_example(tmp_path)
    input_file = project / "examples" / "refund-request.json"

    result = runner.invoke(app, ["run", str(project), "--input", str(input_file), "--allow-all"])

    assert result.exit_code == 0, result.output
    run_id = _extract_run_id(result.output)

    history_result = runner.invoke(app, ["history", str(project)])
    assert history_result.exit_code == 0, history_result.output
    assert run_id in history_result.output
    assert "triage -> responder" in history_result.output

    show_result = runner.invoke(app, ["show-run", run_id, "--path", str(project)])
    assert show_result.exit_code == 0, show_result.output
    assert "final_reply" in show_result.output
    assert "refund" in show_result.output.lower()


def test_run_command_can_skip_history(tmp_path):
    project = _copy_example(tmp_path)
    input_file = project / "examples" / "refund-request.json"

    result = runner.invoke(
        app, ["run", str(project), "--input", str(input_file), "--no-history", "--allow-all"]
    )

    assert result.exit_code == 0, result.output
    assert "Recorded run" not in result.output
    assert not history_db_path(project).exists()


def _copy_example(tmp_path) -> Path:
    project = tmp_path / "refund-support-agent"
    shutil.copytree(
        EXAMPLE, project, ignore=shutil.ignore_patterns("dist", "capsule.lock", ".capsule")
    )
    return project


def _extract_run_id(output: str) -> str:
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        output,
    )
    assert match, output
    return match.group(0)
