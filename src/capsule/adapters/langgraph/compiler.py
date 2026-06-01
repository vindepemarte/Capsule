from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

from capsule.graph.models import CapsuleGraph, GraphNode
from capsule.spec.loader import ProjectContext
from capsule.spec.paths import Entrypoint, parse_python_entrypoint, resolve_project_path


def compile_langgraph(
    context: ProjectContext,
    graph: CapsuleGraph,
    output_dir: Path | None = None,
) -> Path:
    out_dir = output_dir or context.root / "dist" / "langgraph"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "prompts").mkdir(parents=True)
    (out_dir / "tools").mkdir(parents=True)

    _write_generated_manifest(out_dir, graph)
    _copy_assets(context, out_dir)
    (out_dir / "main.py").write_text(_render_main(graph), encoding="utf-8")
    (out_dir / "pyproject.toml").write_text(
        _render_pyproject(context.manifest.name), encoding="utf-8"
    )
    (out_dir / "README.md").write_text(_render_readme(context.manifest.name), encoding="utf-8")
    return out_dir


def _copy_assets(context: ProjectContext, out_dir: Path) -> None:
    for name, agent in context.manifest.agents.items():
        source = resolve_project_path(context.root, agent.prompt, f"agents.{name}.prompt")
        shutil.copy2(source, out_dir / "prompts" / f"{name}.md")

    for name, tool in context.manifest.tools.items():
        if tool.type == "python":
            source = parse_python_entrypoint(context.root, tool.entrypoint or "").file
            shutil.copy2(source, out_dir / "tools" / f"{name}.py")


def _write_generated_manifest(out_dir: Path, graph: CapsuleGraph) -> None:
    data = graph.model_dump(mode="json")
    (out_dir / "capsule-graph.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def _render_main(graph: CapsuleGraph) -> str:
    tool_functions = _tool_functions(graph)
    agent_tools = _agent_tools(graph, tool_functions)
    node_functions = "\n\n".join(
        _render_node_function(graph, node) for node in graph.nodes.values()
    )
    add_nodes = [f'    builder.add_node("{node.id}", {node.id})' for node in graph.nodes.values()]
    add_edges = [_render_edges(node) for node in graph.nodes.values()]
    agent_tools_json = _to_python_literal(agent_tools)

    lines = [
        "from __future__ import annotations",
        "",
        "import importlib.util",
        "import inspect",
        "import json",
        "import sys",
        "from pathlib import Path",
        "from typing import Any, TypedDict",
        "",
        "from langgraph.graph import END, START, StateGraph",
        "",
        "",
        "BASE_DIR = Path(__file__).resolve().parent",
        f"AGENT_TOOLS = {agent_tools_json}",
        "",
        "class State(TypedDict, total=False):",
        "    message: str",
        "    route: str",
        "    decision: str",
        "    status: str",
        "    policy: str",
        "    final_reply: str",
        "    human_gate: str",
        "    last_node: str",
        "    last_tool_result: Any",
        "",
        "",
        "def _load_input() -> dict[str, Any]:",
        "    if len(sys.argv) > 1:",
        '        with open(sys.argv[1], "r", encoding="utf-8") as file:',
        "            return json.load(file)",
        '    return {"message": "I want a refund for my last order."}',
        "",
        "",
        "def _select_route(state: State) -> str:",
        '    for key in ("route", "decision", "status"):',
        "        value = state.get(key)",
        "        if isinstance(value, str):",
        "            return value",
        '    last = state.get("last_tool_result")',
        "    if isinstance(last, dict):",
        '        for key in ("route", "decision", "status"):',
        "            value = last.get(key)",
        "            if isinstance(value, str):",
        "                return value",
        '    return "approved"',
        "",
        "",
        "def _load_tool(tool: dict[str, str]):",
        '    if tool.get("type") == "mcp":',
        '        server = tool.get("server")',
        '        name = tool.get("mcp_tool")',
        "        raise RuntimeError(",
        "            f\"MCP tool '{tool['name']}' targets '{server}:{name}' but MCP execution \"",
        '            "is declaration-only in this generated project."',
        "        )",
        '    path = BASE_DIR / "tools" / f"{tool[\'name\']}.py"',
        "    module_name = f\"_capsule_tool_{tool['name']}\"",
        "    spec = importlib.util.spec_from_file_location(module_name, path)",
        "    if spec is None or spec.loader is None:",
        '        raise RuntimeError(f"Cannot load tool module: {path}")',
        "    module = importlib.util.module_from_spec(spec)",
        "    spec.loader.exec_module(module)",
        "    loaded = getattr(module, tool['function'])",
        "    if not callable(loaded):",
        "        raise RuntimeError(f\"Tool is not callable: {tool['name']}\")",
        "    return loaded",
        "",
        "",
        "def _call_tool(tool_fn, state: dict[str, Any]) -> Any:",
        "    parameters = list(inspect.signature(tool_fn).parameters.values())",
        "    if not parameters:",
        "        return tool_fn()",
        "    if len(parameters) == 1:",
        "        return tool_fn(state)",
        "    kwargs = {param.name: state[param.name] for param in parameters if param.name in state}",
        "    return tool_fn(**kwargs)",
        "",
        "",
        "def _run_agent(agent_name: str, state: State) -> dict[str, Any]:",
        "    current = dict(state)",
        '    updates: dict[str, Any] = {"current_agent": agent_name}',
        "    current.update(updates)",
        "    for tool in AGENT_TOOLS.get(agent_name, []):",
        "        result = _call_tool(_load_tool(tool), current)",
        "        tool_updates = {tool['name']: result, \"last_tool_result\": result}",
        "        if isinstance(result, dict):",
        "            tool_updates.update(result)",
        "        current.update(tool_updates)",
        "        updates.update(tool_updates)",
        "    return updates",
        "",
        "",
        node_functions,
        "",
        "",
        "def build_graph():",
        "    builder = StateGraph(State)",
        *add_nodes,
        f'    builder.add_edge(START, "{graph.start}")',
        *add_edges,
        "    return builder.compile()",
        "",
        "",
        'if __name__ == "__main__":',
        "    app = build_graph()",
        "    result = app.invoke(_load_input())",
        "    print(json.dumps(result, indent=2))",
    ]
    return "\n".join(lines) + "\n"


def _tool_functions(graph: CapsuleGraph) -> dict[str, Entrypoint]:
    return {
        name: parse_python_entrypoint(Path("."), tool.entrypoint or "")
        for name, tool in graph.tools.items()
        if tool.type == "python"
    }


def _agent_tools(
    graph: CapsuleGraph, tool_functions: dict[str, Entrypoint]
) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for agent_name, agent in graph.agents.items():
        result[agent_name] = [
            _tool_descriptor(graph, tool_name, tool_functions) for tool_name in agent.tools
        ]
    return result


def _tool_descriptor(
    graph: CapsuleGraph,
    tool_name: str,
    tool_functions: dict[str, Entrypoint],
) -> dict:
    tool = graph.tools[tool_name]
    descriptor = {
        "name": tool_name,
        "type": tool.type,
        "permission": graph.permissions[tool_name],
    }
    if tool.type == "python":
        descriptor["function"] = tool_functions[tool_name].function
    else:
        descriptor["server"] = tool.server
        descriptor["mcp_tool"] = tool.tool
    return descriptor


def _render_node_function(graph: CapsuleGraph, node: GraphNode) -> str:
    if node.type == "human_gate":
        body = (
            'return {"human_gate": "approved", "route": "approved", "last_node": "' + node.id + '"}'
        )
    else:
        body = _render_agent_body(graph, node)

    return f"def {node.id}(state: State) -> dict[str, Any]:\n{textwrap.indent(body, '    ')}"


def _render_agent_body(graph: CapsuleGraph, node: GraphNode) -> str:
    if not node.agent:
        return f'return {{"last_node": "{node.id}"}}'

    lines = [
        f'updates = _run_agent("{node.agent}", state)',
        "merged = dict(state)",
        "merged.update(updates)",
    ]
    if node.output:
        default_output = f"{node.agent or node.id} processed "
        lines.extend(
            [
                f'if "{node.output}" not in merged:',
                (
                    f'    updates["{node.output}"] = '
                    f'merged.get("{node.output}", "{default_output}" + merged.get("message", "request"))'
                ),
            ]
        )
    lines.extend([f'updates["last_node"] = "{node.id}"', "return updates"])
    _ = graph
    return "\n".join(lines)


def _render_edges(node: GraphNode) -> str:
    if node.next is None:
        return f'    builder.add_edge("{node.id}", END)'
    if isinstance(node.next, str):
        return f'    builder.add_edge("{node.id}", "{node.next}")'
    return f'    builder.add_conditional_edges("{node.id}", _select_route, {dict(node.next)})'


def _to_python_literal(value: object) -> str:
    return json.dumps(value, indent=4).replace("true", "True").replace("false", "False")


def _render_pyproject(name: str) -> str:
    safe_name = name.replace("_", "-")
    return (
        textwrap.dedent(
            f"""
        [project]
        name = "{safe_name}-langgraph"
        version = "0.1.0"
        requires-python = ">=3.10"
        dependencies = ["langgraph>=1.0"]
        """
        ).strip()
        + "\n"
    )


def _render_readme(name: str) -> str:
    return (
        textwrap.dedent(
            f"""
        # {name} LangGraph Output

        This project was generated by Capsule.

        Run it with:

        ```bash
        uv run --with langgraph python main.py path/to/input.json
        ```

        The generated code is intentionally readable so users can inspect and modify it.
        """
        ).strip()
        + "\n"
    )
