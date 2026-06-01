from __future__ import annotations

from pathlib import Path
from typing import Any

from capsule.graph.models import CapsuleGraph, GraphNode
from capsule.runtime.tool_loader import call_tool, load_python_tool
from capsule.runtime.trace import RunResult, RunTrace, ToolCall, TraceStep
from capsule.security.permissions import require_tool_permission
from capsule.spec.payload_schema import PayloadSchemaError, validate_payload


class RuntimeExecutionError(RuntimeError):
    """Raised when a Capsule workflow cannot be executed locally."""


def run_graph(
    graph: CapsuleGraph,
    project_root: Path,
    input_data: dict[str, Any],
    mock_tools: dict[str, Any] | None = None,
) -> RunResult:
    _validate_runtime_payload(graph.input_schema, input_data, "input")
    state = dict(input_data)
    trace = RunTrace()
    current = graph.start
    visited = 0
    mocks = mock_tools or {}

    while current:
        visited += 1
        if visited > len(graph.nodes) + 10:
            raise RuntimeExecutionError("Workflow exceeded safe step limit")

        node = graph.nodes[current]
        trace.path.append(node.id)
        step_trace = TraceStep(node=node.id, type=node.type, agent=node.agent)

        if node.type == "agent":
            _run_agent_node(graph, project_root, node, state, mocks, step_trace)
        elif node.type == "human_gate":
            state.setdefault("human_gate", "approved")
            state.setdefault("route", "approved")
        else:
            raise RuntimeExecutionError(f"Unsupported node type: {node.type}")

        next_node = _select_next(node.next, state)
        step_trace.selected_next = next_node
        trace.steps.append(step_trace)
        current = next_node

    _validate_runtime_payload(graph.output_schema, state, "output")
    return RunResult(output=state, trace=trace)


def _validate_runtime_payload(schema: dict[str, Any] | None, payload: Any, label: str) -> None:
    try:
        validate_payload(schema, payload, label)
    except PayloadSchemaError as exc:
        raise RuntimeExecutionError(str(exc)) from exc


def _run_agent_node(
    graph: CapsuleGraph,
    project_root: Path,
    node: GraphNode,
    state: dict[str, Any],
    mock_tools: dict[str, Any],
    trace: TraceStep,
) -> None:
    if not node.agent:
        raise RuntimeExecutionError(f"Agent node '{node.id}' has no agent")

    agent = graph.agents[node.agent]
    state["current_agent"] = node.agent
    state["current_prompt"] = agent.prompt

    for tool_name in agent.tools:
        permission = require_tool_permission(graph, tool_name)
        if tool_name in mock_tools:
            result = _normalize_mock_result(mock_tools[tool_name])
            mocked = True
        else:
            tool = graph.tools[tool_name]
            if tool.type != "python":
                raise RuntimeExecutionError(
                    f"Tool '{tool_name}' is an MCP tool. Local runtime requires a mocked "
                    "tool result until MCP execution is implemented."
                )
            callable_tool = load_python_tool(project_root, tool.entrypoint or "")
            result = call_tool(callable_tool, state)
            mocked = False

        state[tool_name] = result
        state["last_tool_result"] = result
        if isinstance(result, dict):
            state.update(result)
        trace.tools.append(
            ToolCall(name=tool_name, permission=permission, mocked=mocked, result=result)
        )

    if node.output and node.output not in state:
        state[node.output] = _default_agent_output(node, state)


def _normalize_mock_result(value: Any) -> Any:
    if isinstance(value, dict) and set(value.keys()) == {"result"}:
        return value["result"]
    return value


def _select_next(next_value: str | dict[str, str] | None, state: dict[str, Any]) -> str | None:
    if next_value is None:
        return None
    if isinstance(next_value, str):
        return next_value

    for key in _routing_candidates(state):
        if key in next_value:
            return next_value[key]

    for fallback in ("approved", "success", "default", "done"):
        if fallback in next_value:
            return next_value[fallback]

    return next(iter(next_value.values()))


def _routing_candidates(state: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for key in ("route", "decision", "status"):
        value = state.get(key)
        if isinstance(value, str):
            candidates.append(value)
    last = state.get("last_tool_result")
    if isinstance(last, dict):
        for key in ("route", "decision", "status"):
            value = last.get(key)
            if isinstance(value, str):
                candidates.append(value)
    return candidates


def _default_agent_output(node: GraphNode, state: dict[str, Any]) -> str:
    message = state.get("message") or state.get("input") or "request"
    return f"{node.agent or node.id} processed {message}"
