from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

from capsule.graph.models import CapsuleGraph, GraphNode
from capsule.spec.loader import ProjectContext
from capsule.spec.paths import Entrypoint, parse_python_entrypoint, resolve_project_path


def compile_crewai(
    context: ProjectContext,
    graph: CapsuleGraph,
    output_dir: Path | None = None,
) -> Path:
    out_dir = output_dir or context.root / "dist" / "crewai"
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

    # Generate tool import helper block
    tool_declarations = []
    for tool_name, entry in tool_functions.items():
        tool_declarations.append(
            f"{tool_name} = _load_tool({{\n"
            f"    'name': '{tool_name}',\n"
            f"    'type': 'python',\n"
            f"    'function': '{entry.function}'\n"
            f"}})"
        )
    tools_block = "\n".join(tool_declarations)

    # Render Flow methods for each GraphNode
    flow_methods = []
    for node_id, node in graph.nodes.items():
        method_str = _render_node_method(graph, node)
        flow_methods.append(method_str)

        # If it has a router, generate the router method
        if node.next and not isinstance(node.next, str):
            router_str = _render_router_method(node)
            flow_methods.append(router_str)

    flow_methods_str = "\n\n".join(flow_methods)

    lines = [
        "from __future__ import annotations",
        "",
        "import importlib.util",
        "import json",
        "import sys",
        "from pathlib import Path",
        "from typing import Any",
        "",
        "from crewai import Agent, Crew, Task",
        "from crewai.flow.flow import Flow, listen, router, start",
        "from pydantic import BaseModel",
        "",
        "",
        "BASE_DIR = Path(__file__).resolve().parent",
        "",
        "class State(BaseModel):",
        "    message: str = ''",
        "    route: str = ''",
        "    final_reply: str = ''",
        "    last_node: str = ''",
        "    policy: str = ''",
        "    human_gate: str = ''",
        "",
        "def _load_input() -> dict[str, Any]:",
        "    if len(sys.argv) > 1:",
        "        with open(sys.argv[1], 'r', encoding='utf-8') as file:",
        "            return json.load(file)",
        "    return {'message': 'I want a refund for my last order.'}",
        "",
        "def _load_tool(tool: dict[str, str]):",
        "    if tool.get('type') == 'mcp':",
        "        server = tool.get('server')",
        "        name = tool.get('mcp_tool')",
        "        raise RuntimeError(",
        "            f\"MCP tool '{tool['name']}' targets '{server}:{name}' but MCP execution \"",
        "            'is declaration-only in this generated project.'",
        "        )",
        "    path = BASE_DIR / 'tools' / f\"{tool['name']}.py\"",
        "    module_name = f\"_capsule_tool_{tool['name']}\"",
        "    spec = importlib.util.spec_from_file_location(module_name, path)",
        "    if spec is None or spec.loader is None:",
        "        raise RuntimeError(f'Cannot load tool module: {path}')",
        "    module = importlib.util.module_from_spec(spec)",
        "    spec.loader.exec_module(module)",
        "    loaded = getattr(module, tool['function'])",
        "    if not callable(loaded):",
        "        raise RuntimeError(f\"Tool is not callable: {tool['name']}\")",
        "    return loaded",
        "",
        "# --- Tools Configuration ---",
        tools_block,
        "",
        "# --- CrewAI Flow Definition ---",
        "class CapsuleFlow(Flow[State]):",
        "",
        textwrap.indent(flow_methods_str, "    "),
        "",
        "if __name__ == '__main__':",
        "    input_data = _load_input()",
        "    flow = CapsuleFlow()",
        "    flow.state.message = input_data.get('message', '')",
        "    flow.kickoff()",
        "    print(json.dumps(flow.state.model_dump(), indent=2))",
    ]
    return "\n".join(lines) + "\n"


def _tool_functions(graph: CapsuleGraph) -> dict[str, Entrypoint]:
    return {
        name: parse_python_entrypoint(Path("."), tool.entrypoint or "")
        for name, tool in graph.tools.items()
        if tool.type == "python"
    }


def _render_node_method(graph: CapsuleGraph, node: GraphNode) -> str:
    # 1. Determine the decorator
    if node.id == graph.start:
        decorator = "@start()"
    else:
        # Find the parent node of this node in the graph to listen to
        parent = _find_parent_node(graph, node.id)
        if parent:
            if parent.next and not isinstance(parent.next, str):
                # Branching next. We listen to the label of this route in the router of the parent
                decorator = f'@listen("{node.id}")'
            else:
                # Direct string transition. We listen to the parent method completion
                decorator = f"@listen({parent.id})"
        else:
            decorator = "@listen()"

    # 2. Build method body based on node type
    if node.type == "human_gate":
        body = (
            "self.state.human_gate = 'approved'\n"
            "self.state.route = 'approved'\n"
            f"self.state.last_node = '{node.id}'"
        )
    else:
        if not node.agent:
            body = f"self.state.last_node = '{node.id}'"
        else:
            agent = graph.agents[node.agent]
            tools_list = ", ".join(agent.tools)

            # CrewAI execution block
            body = (
                f"# Load agent prompt\n"
                f"instructions = Path(BASE_DIR / 'prompts/{node.agent}.md').read_text(encoding='utf-8')\n\n"
                f"agent = Agent(\n"
                f"    role='{node.agent}',\n"
                f"    goal='Execute task instructions',\n"
                f"    backstory=instructions,\n"
                f"    tools=[{tools_list}],\n"
                f"    verbose=True\n"
                f")\n\n"
                f"task = Task(\n"
                f"    description=f'Process request: {{self.state.message}}',\n"
                f"    expected_output='Processed result',\n"
                f"    agent=agent\n"
                f")\n\n"
                f"crew = Crew(agents=[agent], tasks=[task], verbose=True)\n"
                f"result = crew.kickoff(inputs=self.state.model_dump())\n\n"
                f"# Try to update state fields from tool outputs\n"
                f"try:\n"
                f"    data = json.loads(result.raw)\n"
                f"    if isinstance(data, dict):\n"
                f"        for k, v in data.items():\n"
                f"            if hasattr(self.state, k):\n"
                f"                setattr(self.state, k, v)\n"
                f"except Exception:\n"
                f"    pass\n\n"
                f"self.state.last_node = '{node.id}'\n"
            )
            # If the node has branching next steps, we must return the routing label
            if node.next and not isinstance(node.next, str):
                body += "return self.state.route or 'approved'"

    return f"{decorator}\ndef {node.id}(self) -> Any:\n{textwrap.indent(body, '    ')}"


def _render_router_method(node: GraphNode) -> str:
    body = "return previous_result"
    return (
        f"@router({node.id})\ndef route_{node.id}(self, previous_result) -> str:\n"
        f"{textwrap.indent(body, '    ')}"
    )


def _find_parent_node(graph: CapsuleGraph, target_id: str) -> GraphNode | None:
    for node in graph.nodes.values():
        if node.next:
            if isinstance(node.next, str) and node.next == target_id:
                return node
            elif not isinstance(node.next, str) and target_id in node.next.values():
                return node
    return None


def _render_pyproject(name: str) -> str:
    safe_name = name.replace("_", "-")
    return (
        textwrap.dedent(
            f"""
        [project]
        name = "{safe_name}-crewai"
        version = "0.1.0"
        requires-python = ">=3.10"
        dependencies = ["crewai>=0.30.0"]
        """
        ).strip()
        + "\n"
    )


def _render_readme(name: str) -> str:
    return (
        textwrap.dedent(
            f"""
        # {name} CrewAI Flow Output

        This project was generated by Capsule.

        Run it with:

        ```bash
        uv run --with crewai python main.py path/to/input.json
        ```

        The generated code is intentionally readable so users can inspect and modify it.
        """
        ).strip()
        + "\n"
    )
