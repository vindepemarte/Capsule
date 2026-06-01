import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from capsule.cli.app import app
from capsule.security.scan import scan_project
from capsule.spec.loader import load_project
from capsule.validate.rules import validate_project


EXAMPLE = Path("examples/refund-support-agent")
runner = CliRunner()


def test_validate_warns_for_risky_write_permission():
    context = load_project(EXAMPLE)

    report = validate_project(context)

    assert report.ok
    assert any(warning.code == "security.risky_permission" for warning in report.warnings)


def test_security_scan_flags_risky_tool_source(tmp_path):
    project = _copy_example(tmp_path)
    tool_path = project / "tools" / "danger.py"
    tool_path.write_text(
        """
import os
import subprocess

def danger(state):
    token = os.getenv("TOKEN")
    subprocess.run(["echo", token or "missing"], check=False)
    return {"route": "approved"}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    data = _read_manifest(project)
    data["tools"]["danger"] = {
        "type": "python",
        "entrypoint": "tools/danger.py:danger",
        "permission": "shell_exec",
    }
    data["agents"]["triage"]["tools"].append("danger")
    data["permissions"]["tools"]["danger"] = "shell_exec"
    _write_manifest(project, data)

    findings = scan_project(load_project(project))
    codes = {finding.code for finding in findings}

    assert "risky_permission" in codes
    assert "risky_import" in codes
    assert "environment_access" in codes


def test_scan_command_prints_security_findings():
    result = runner.invoke(app, ["scan", str(EXAMPLE)])

    assert result.exit_code == 0, result.output
    assert "Capsule Security Scan" in result.output
    assert "write_draft" in result.output


def _copy_example(tmp_path) -> Path:
    project = tmp_path / "refund-support-agent"
    shutil.copytree(
        EXAMPLE, project, ignore=shutil.ignore_patterns("dist", "capsule.lock", ".capsule")
    )
    return project


def _read_manifest(project: Path) -> dict:
    return yaml.safe_load((project / "capsule.yaml").read_text(encoding="utf-8"))


def _write_manifest(project: Path, data: dict) -> None:
    (project / "capsule.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
