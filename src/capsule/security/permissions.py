from __future__ import annotations

from capsule.graph.models import CapsuleGraph


class PermissionError(RuntimeError):
    """Raised when a workflow tries to use an undeclared capability."""


def require_tool_permission(graph: CapsuleGraph, tool_name: str) -> str:
    if tool_name not in graph.tools:
        raise PermissionError(f"Tool '{tool_name}' is not declared")

    declared = graph.permissions.get(tool_name)
    if declared is None:
        raise PermissionError(f"Tool '{tool_name}' is missing a permissions.tools declaration")

    expected = graph.tools[tool_name].permission
    if declared != expected:
        raise PermissionError(
            f"Tool '{tool_name}' requires permission '{expected}' but declares '{declared}'"
        )

    return declared
