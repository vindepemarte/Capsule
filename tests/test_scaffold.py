from typer.testing import CliRunner

from capsule.cli.app import app
from capsule.project.scaffold import create_project
from capsule.spec.loader import load_project
from capsule.validate.rules import validate_project

runner = CliRunner()


def test_scaffolded_project_validates(tmp_path):
    project = create_project("demo-agent", tmp_path / "demo-agent")
    context = load_project(project)
    report = validate_project(context)

    assert report.ok, [error.format() for error in report.errors]
    assert ".capsule/" in (project / ".gitignore").read_text(encoding="utf-8")


def test_init_command_creates_valid_project(tmp_path):
    project = tmp_path / "demo-agent"
    result = runner.invoke(app, ["init", "demo-agent", "--output", str(project)])

    assert result.exit_code == 0, result.output
    context = load_project(project)
    report = validate_project(context)
    assert report.ok, [error.format() for error in report.errors]
