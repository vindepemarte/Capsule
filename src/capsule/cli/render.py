from __future__ import annotations

from rich.console import Console
from rich.table import Table

from capsule.bundle.inspector import BundleInfo
from capsule.bundle.verifier import BundleVerificationReport
from capsule.history.models import RunRecord, RunSummary
from capsule.security.scan import SecurityFinding
from capsule.testing.models import TestRunReport
from capsule.validate.diagnostics import ValidationReport

console = Console()


def print_validation(report: ValidationReport) -> None:
    if report.ok:
        console.print("[green]Validation passed.[/green]")
    else:
        console.print("[red]Validation failed.[/red]")

    for warning in report.warnings:
        console.print(f"[yellow]warning[/yellow] {warning.format()}")
    for error in report.errors:
        console.print(f"[red]error[/red] {error.format()}")


def print_test_report(report: TestRunReport) -> None:
    table = Table(title="Capsule Tests")
    table.add_column("Test")
    table.add_column("Status")
    table.add_column("Failures")

    for result in report.results:
        status = "[green]pass[/green]" if result.passed else "[red]fail[/red]"
        failures = "\n".join(result.failures) if result.failures else ""
        table.add_row(result.name, status, failures)

    console.print(table)
    if report.passed:
        console.print("[green]All tests passed.[/green]")
    else:
        console.print("[red]Some tests failed.[/red]")


def print_bundle_info(info: BundleInfo) -> None:
    console.print(f"[bold]Bundle:[/bold] {info.path}")
    console.print(f"Name: {info.name or 'unknown'}")
    console.print(f"Version: {info.version or 'unknown'}")
    console.print(f"Format: {info.format or 'unknown'}")
    console.print(f"Manifest: {'yes' if info.has_manifest else 'no'}")
    console.print(f"Lockfile: {'yes' if info.has_lockfile else 'no'}")

    table = Table(title="Bundle Files")
    table.add_column("Path")
    for file_name in info.files:
        table.add_row(file_name)
    console.print(table)


def print_bundle_verification(report: BundleVerificationReport) -> None:
    if report.ok:
        console.print(f"[green]Bundle verified:[/green] {report.bundle}")
    else:
        console.print(f"[red]Bundle verification failed:[/red] {report.bundle}")

    for warning in report.warnings:
        console.print(f"[yellow]warning[/yellow] {warning}")
    for error in report.errors:
        console.print(f"[red]error[/red] {error}")

    if report.checked_files:
        table = Table(title="Verified Files")
        table.add_column("Path")
        for file_name in report.checked_files:
            table.add_row(file_name)
        console.print(table)


def print_run_history(runs: list[RunSummary]) -> None:
    if not runs:
        console.print("No runs recorded.")
        return

    console.print("[bold]Capsule Run History[/bold]")
    for run in runs:
        path = " -> ".join(run.path) if run.path else "n/a"
        console.print(
            f"{run.id} | {run.created_at} | {run.project_name}@{run.project_version} | "
            f"{run.source} | {run.status} | {path}"
        )


def print_run_record(record: RunRecord) -> None:
    console.print(f"[bold]Run:[/bold] {record.id}")
    console.print(f"Project: {record.project_name}@{record.project_version}")
    console.print(f"Source: {record.source}")
    console.print(f"Status: {record.status}")
    console.print(f"Created: {record.created_at}")
    console.print("[bold]Input[/bold]")
    console.print_json(data=record.input)
    console.print("[bold]Output[/bold]")
    console.print_json(data=record.output)
    console.print("[bold]Trace[/bold]")
    console.print_json(data=record.trace)


def print_security_findings(findings: list[SecurityFinding]) -> None:
    if not findings:
        console.print("[green]No security findings.[/green]")
        return

    table = Table(title="Capsule Security Scan")
    table.add_column("Severity")
    table.add_column("Code")
    table.add_column("Path")
    table.add_column("Message")
    for finding in findings:
        table.add_row(
            finding.severity,
            finding.code,
            finding.path or "",
            finding.message,
        )
    console.print(table)
