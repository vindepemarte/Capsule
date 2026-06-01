from __future__ import annotations

from collections import Counter

from capsule.security.scan import scan_project
from capsule.spec.loader import ProjectContext
from capsule.spec.paths import CapsulePathError, parse_python_entrypoint, resolve_project_path
from capsule.spec.payload_schema import schema_definition_errors
from capsule.validate.diagnostics import ValidationReport


def validate_project(context: ProjectContext) -> ValidationReport:
    report = ValidationReport()
    manifest = context.manifest
    root = context.root

    _validate_payload_schemas(context, report)

    for agent_name, agent in manifest.agents.items():
        if agent.model not in manifest.models:
            report.add_error(
                "agent.unknown_model", f"Agent '{agent_name}' uses unknown model '{agent.model}'"
            )
        _check_file(report, root, agent.prompt, f"agents.{agent_name}.prompt")
        for tool_name in agent.tools:
            if tool_name not in manifest.tools:
                report.add_error(
                    "agent.unknown_tool",
                    f"Agent '{agent_name}' uses unknown tool '{tool_name}'",
                    f"agents.{agent_name}.tools",
                )

    for tool_name, tool in manifest.tools.items():
        if tool.type == "python":
            try:
                entrypoint = parse_python_entrypoint(root, tool.entrypoint or "")
                if not entrypoint.file.exists():
                    report.add_error(
                        "tool.missing_file",
                        f"Tool '{tool_name}' entrypoint file does not exist",
                        tool.entrypoint,
                    )
            except CapsulePathError as exc:
                report.add_error("tool.invalid_entrypoint", str(exc), tool.entrypoint)

        declared_permission = manifest.permissions.tools.get(tool_name)
        if declared_permission is None:
            report.add_error(
                "tool.missing_permission",
                f"Tool '{tool_name}' must be declared in permissions.tools",
                f"tools.{tool_name}",
            )
        elif declared_permission != tool.permission:
            report.add_error(
                "tool.permission_mismatch",
                f"Tool '{tool_name}' permission is '{tool.permission}' but permissions.tools declares '{declared_permission}'",
                f"tools.{tool_name}",
            )

    _validate_workflow(context, report)

    for test_path in manifest.tests:
        _check_file(report, root, test_path, "tests")

    for finding in scan_project(context):
        report.add_warning(
            f"security.{finding.code}",
            f"[{finding.severity}] {finding.message}",
            finding.path,
        )

    return report


def _validate_payload_schemas(context: ProjectContext, report: ValidationReport) -> None:
    manifest = context.manifest
    for field_name, schema in (
        ("input_schema", manifest.input_schema),
        ("output_schema", manifest.output_schema),
    ):
        for message in schema_definition_errors(schema, field_name):
            report.add_error("schema.invalid", message, field_name)


def _validate_workflow(context: ProjectContext, report: ValidationReport) -> None:
    manifest = context.manifest
    steps = manifest.workflow.steps
    ids = [step.id for step in steps]
    counts = Counter(ids)

    for step_id, count in counts.items():
        if count > 1:
            report.add_error(
                "workflow.duplicate_step", f"Workflow step '{step_id}' appears {count} times"
            )

    step_ids = set(ids)
    if manifest.workflow.start not in step_ids:
        report.add_error(
            "workflow.invalid_start",
            f"Workflow start '{manifest.workflow.start}' is not a defined step",
            "workflow.start",
        )

    for step in steps:
        if step.type == "agent":
            if not step.agent:
                report.add_error(
                    "workflow.missing_agent", f"Step '{step.id}' must declare an agent"
                )
            elif step.agent not in manifest.agents:
                report.add_error(
                    "workflow.unknown_agent",
                    f"Step '{step.id}' references unknown agent '{step.agent}'",
                )

        for target in _next_targets(step.next):
            if target not in step_ids:
                report.add_error(
                    "workflow.invalid_edge",
                    f"Step '{step.id}' points to missing step '{target}'",
                    f"workflow.steps.{step.id}.next",
                )


def _check_file(report: ValidationReport, root, raw_path: str, label: str) -> None:
    try:
        path = resolve_project_path(root, raw_path, label)
    except CapsulePathError as exc:
        report.add_error("path.invalid", str(exc), raw_path)
        return

    if not path.exists():
        report.add_error("path.missing", f"{label} file does not exist", raw_path)


def _next_targets(value: str | dict[str, str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value.values())
