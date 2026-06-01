import shutil
from pathlib import Path

import yaml

from capsule.spec.loader import load_project
from capsule.validate.rules import validate_project


EXAMPLE = Path("examples/refund-support-agent")


def test_validation_reports_missing_prompt(tmp_path):
    project = _copy_example(tmp_path)
    (project / "agents" / "triage.md").unlink()

    report = validate_project(load_project(project))

    assert _has_error(report, "path.missing")


def test_validation_reports_unknown_tool(tmp_path):
    project = _copy_example(tmp_path)
    data = _read_manifest(project)
    data["agents"]["triage"]["tools"].append("missing_tool")
    _write_manifest(project, data)

    report = validate_project(load_project(project))

    assert _has_error(report, "agent.unknown_tool")


def test_validation_reports_invalid_workflow_edge(tmp_path):
    project = _copy_example(tmp_path)
    data = _read_manifest(project)
    data["workflow"]["steps"][0]["next"]["approved"] = "missing_step"
    _write_manifest(project, data)

    report = validate_project(load_project(project))

    assert _has_error(report, "workflow.invalid_edge")


def test_validation_reports_undeclared_tool_permission(tmp_path):
    project = _copy_example(tmp_path)
    data = _read_manifest(project)
    del data["permissions"]["tools"]["draft_reply"]
    _write_manifest(project, data)

    report = validate_project(load_project(project))

    assert _has_error(report, "tool.missing_permission")


def test_validation_reports_invalid_payload_schema(tmp_path):
    project = _copy_example(tmp_path)
    data = _read_manifest(project)
    data["input_schema"]["type"] = "invalid-json-schema-type"
    _write_manifest(project, data)

    report = validate_project(load_project(project))

    assert _has_error(report, "schema.invalid")


def _copy_example(tmp_path) -> Path:
    project = tmp_path / "refund-support-agent"
    shutil.copytree(EXAMPLE, project, ignore=shutil.ignore_patterns("dist", "capsule.lock"))
    return project


def _read_manifest(project: Path) -> dict:
    return yaml.safe_load((project / "capsule.yaml").read_text(encoding="utf-8"))


def _write_manifest(project: Path, data: dict) -> None:
    (project / "capsule.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _has_error(report, code: str) -> bool:
    return any(error.code == code for error in report.errors)
