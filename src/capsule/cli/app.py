from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from capsule.adapters.langgraph.compiler import compile_langgraph
from capsule.bundle.builder import build_bundle
from capsule.bundle.inspector import BundleInspectError, inspect_bundle
from capsule.bundle.verifier import verify_bundle
from capsule.cli.render import (
    console,
    print_bundle_info,
    print_bundle_verification,
    print_run_history,
    print_run_record,
    print_security_findings,
    print_test_report,
    print_validation,
)
from capsule.graph.builder import build_graph
from capsule.graph.inspect import graph_summary
from capsule.graph.serialize import graph_to_dict, write_graph_json
from capsule.history.store import HistoryStoreError, get_run, list_runs, record_run
from capsule.project.scaffold import ScaffoldError, create_project
from capsule.runtime.executor import RuntimeExecutionError, run_graph
from capsule.security.scan import scan_project
from capsule.spec.loader import CapsuleLoadError, ProjectContext, load_project
from capsule.spec.schema import manifest_json_schema, write_manifest_schema
from capsule.testing.runner import run_capsule_tests
from capsule.validate.rules import validate_project

app = typer.Typer(help="Package, test, and compile portable AI agent workflows.")


@app.command()
def init(
    name: str = typer.Argument(..., help="Name of the Capsule project to create."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Destination folder."),
) -> None:
    """Create a starter Capsule project."""
    try:
        project_path = create_project(name, output)
    except ScaffoldError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]Created Capsule project:[/green] {project_path}")


@app.command()
def validate(path: Path = typer.Argument(Path("."), help="Capsule project folder.")) -> None:
    """Validate capsule.yaml and referenced project files."""
    context = _load_context(path)
    report = validate_project(context)
    print_validation(report)
    if not report.ok:
        raise typer.Exit(1)


@app.command()
def scan(path: Path = typer.Argument(Path("."), help="Capsule project folder.")) -> None:
    """Scan a Capsule project for security-sensitive tool behavior."""
    context = _load_context(path)
    report = validate_project(context)
    if report.errors:
        print_validation(report)
        raise typer.Exit(1)
    print_security_findings(scan_project(context))


@app.command()
def schema(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write schema to a file."),
) -> None:
    """Print or write the capsule.yaml JSON Schema."""
    if output:
        schema_path = write_manifest_schema(output)
        console.print(f"[green]Wrote Capsule manifest schema:[/green] {schema_path}")
        return
    console.print_json(data=manifest_json_schema())


@app.command()
def inspect(path: Path = typer.Argument(Path("."), help="Capsule project folder.")) -> None:
    """Print a readable summary of a Capsule workflow."""
    context, graph = _load_valid_graph(path)
    console.print(graph_summary(graph))
    _ = context


@app.command("graph")
def graph_cmd(
    path: Path = typer.Argument(Path("."), help="Capsule project folder."),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Write graph JSON to a file."
    ),
) -> None:
    """Print or write the framework-neutral Capsule Graph as JSON."""
    _context, graph = _load_valid_graph(path)
    if output:
        graph_path = write_graph_json(graph, output)
        console.print(f"[green]Wrote Capsule Graph:[/green] {graph_path}")
        return
    console.print_json(data=graph_to_dict(graph))


@app.command()
def run(
    path: Path = typer.Argument(Path("."), help="Capsule project folder."),
    input_file: Path = typer.Option(..., "--input", "-i", help="JSON input file."),
    history: bool = typer.Option(True, "--history/--no-history", help="Persist this run locally."),
    allow_permission: Optional[list[str]] = typer.Option(
        None, "--allow-permission", "-p", help="Permissions to authorize at runtime."
    ),
    allow_all: bool = typer.Option(
        False, "--allow-all", help="Authorize all permissions at runtime."
    ),
) -> None:
    """Run a Capsule workflow locally."""
    context, graph = _load_valid_graph(path)
    input_data = json.loads(input_file.read_text(encoding="utf-8"))
    try:
        result = run_graph(
            graph,
            context.root,
            input_data,
            allowed_permissions=allow_permission,
            allow_all=allow_all,
        )
    except (RuntimeExecutionError, PermissionError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    if history:
        record = record_run(context.root, graph, input_data, result)
        console.print(f"[green]Recorded run:[/green] {record.id}")
    console.print_json(data=result.model_dump(mode="json"))


@app.command(name="test")
def test_cmd(path: Path = typer.Argument(Path("."), help="Capsule project folder.")) -> None:
    """Run Capsule workflow tests."""
    context, graph = _load_valid_graph(path)
    report = run_capsule_tests(graph, context.root)
    print_test_report(report)
    if not report.passed:
        raise typer.Exit(1)


@app.command()
def compile(
    path: Path = typer.Argument(Path("."), help="Capsule project folder."),
    target: str = typer.Option("langgraph", "--target", "-t", help="Compiler target."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output folder."),
) -> None:
    if target not in ("langgraph", "openai-agents", "crewai"):
        console.print(f"[red]Unsupported target:[/red] {target}")
        raise typer.Exit(1)
    context, graph = _load_valid_graph(path)
    if target == "langgraph":
        output_path = compile_langgraph(context, graph, output)
        console.print(f"[green]Generated LangGraph project:[/green] {output_path}")
    elif target == "openai-agents":
        from capsule.adapters.openai_agents.compiler import compile_openai_agents

        output_path = compile_openai_agents(context, graph, output)
        console.print(f"[green]Generated OpenAI Agents project:[/green] {output_path}")
    else:
        from capsule.adapters.crewai.compiler import compile_crewai

        output_path = compile_crewai(context, graph, output)
        console.print(f"[green]Generated CrewAI Flow project:[/green] {output_path}")


@app.command()
def build(
    path: Path = typer.Argument(Path("."), help="Capsule project folder."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Bundle output folder."),
) -> None:
    """Build a .capsule bundle and capsule.lock."""
    context, _graph = _load_valid_graph(path)
    bundle_path = build_bundle(context, output)
    console.print(f"[green]Built Capsule bundle:[/green] {bundle_path}")


@app.command("inspect-bundle")
def inspect_bundle_cmd(path: Path = typer.Argument(..., help=".capsule bundle path.")) -> None:
    """Inspect a built .capsule bundle."""
    try:
        info = inspect_bundle(path)
    except BundleInspectError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    print_bundle_info(info)


@app.command("verify-bundle")
def verify_bundle_cmd(path: Path = typer.Argument(..., help=".capsule bundle path.")) -> None:
    """Verify a .capsule bundle against capsule.lock hashes."""
    report = verify_bundle(path)
    print_bundle_verification(report)
    if not report.ok:
        raise typer.Exit(1)


@app.command("history")
def history_cmd(
    path: Path = typer.Argument(Path("."), help="Capsule project folder."),
    limit: int = typer.Option(20, "--limit", "-n", min=1, help="Maximum runs to list."),
) -> None:
    """List persisted local workflow runs."""
    context = _load_context(path)
    print_run_history(list_runs(context.root, limit))


@app.command("show-run")
def show_run_cmd(
    run_id: str = typer.Argument(..., help="Run ID to show."),
    path: Path = typer.Option(Path("."), "--path", "-p", help="Capsule project folder."),
) -> None:
    """Show a persisted run with input, output, and trace."""
    context = _load_context(path)
    try:
        record = get_run(context.root, run_id)
    except HistoryStoreError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    print_run_record(record)


def _load_context(path: Path) -> ProjectContext:
    try:
        return load_project(path)
    except CapsuleLoadError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


def _load_valid_graph(path: Path) -> tuple[ProjectContext, object]:
    context = _load_context(path)
    report = validate_project(context)
    if not report.ok:
        print_validation(report)
        raise typer.Exit(1)
    return context, build_graph(context)


def main() -> None:
    app()
