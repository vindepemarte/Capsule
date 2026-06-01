from __future__ import annotations

import sys
from rich.prompt import Confirm

from capsule.graph.models import CapsuleGraph


class CapsulePermissionError(RuntimeError):
    """Raised when a workflow tries to use an undeclared capability."""


def require_tool_permission(graph: CapsuleGraph, tool_name: str) -> str:
    if tool_name not in graph.tools:
        raise CapsulePermissionError(f"Tool '{tool_name}' is not declared")

    declared = graph.permissions.get(tool_name)
    if declared is None:
        raise CapsulePermissionError(
            f"Tool '{tool_name}' is missing a permissions.tools declaration"
        )

    expected = graph.tools[tool_name].permission
    if declared != expected:
        raise CapsulePermissionError(
            f"Tool '{tool_name}' requires permission '{expected}' but declares '{declared}'"
        )

    return declared


def authorize_tool_permission(
    graph: CapsuleGraph,
    tool_name: str,
    allowed: list[str],
    allow_all: bool = False,
) -> None:
    declared = require_tool_permission(graph, tool_name)

    # 'read' is always allowed by default in local runtime, others need authorization
    if declared == "read" or allow_all or (declared in allowed):
        return

    # Check if we can prompt interactive user
    if sys.stdin.isatty():
        approved = Confirm.ask(
            f"[yellow]Tool '{tool_name}' requires permission '{declared}'. Authorize execution?[/yellow]",
            default=False,
        )
        if approved:
            allowed.append(declared)
            return

    raise CapsulePermissionError(
        f"Execution of tool '{tool_name}' blocked: permission '{declared}' is not authorized. "
        "Run with --allow-permission or --allow-all to override."
    )
