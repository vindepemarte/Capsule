from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

from capsule.graph.models import CapsuleGraph
from capsule.spec.loader import ProjectContext
from capsule.spec.paths import Entrypoint, parse_python_entrypoint, resolve_project_path


def compile_openai_agents(
    context: ProjectContext,
    graph: CapsuleGraph,
    output_dir: Path | None = None,
) -> Path:
    out_dir = output_dir or context.root / "dist" / "openai-agents"
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

    # 1. Generate tool import helper block
    # For each python tool, generate loading logic
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

    # 2. Define the Agent declarations
    agent_declarations = []
    for node_id, node in graph.nodes.items():
        if node.type == "human_gate":
            agent_declarations.append(
                f"{node_id}_agent = Agent(\n"
                f"    name='{node_id}',\n"
                f"    instructions='You are a human approval gate stub. Proceed to the next step.',\n"
                f")"
            )
        elif node.agent:
            agent = graph.agents[node.agent]
            prompt_name = node.agent
            tools_list = ", ".join(agent.tools)
            agent_declarations.append(
                f"{node_id}_agent = Agent(\n"
                f"    name='{node_id}',\n"
                f"    instructions=Path(BASE_DIR / 'prompts/{prompt_name}.md').read_text(encoding='utf-8'),\n"
                f"    tools=[{tools_list}],\n"
                f")"
            )
    agents_block = "\n".join(agent_declarations)

    # 3. Define the handoffs / transitions
    handoff_declarations = []
    for node_id, node in graph.nodes.items():
        if node.next:
            if isinstance(node.next, str):
                targets = [node.next]
            else:
                targets = list(node.next.values())

            handoffs = [f"handoff(agent={target}_agent)" for target in targets]
            handoff_declarations.append(
                f"{node_id}_agent.handoffs = [\n    " + ",\n    ".join(handoffs) + "\n]"
            )
    handoffs_block = "\n".join(handoff_declarations)

    lines = [
        "from __future__ import annotations",
        "",
        "import asyncio",
        "import importlib.util",
        "import json",
        "import sys",
        "from pathlib import Path",
        "from typing import Any",
        "",
        "from agents import Agent, Runner, handoff",
        "",
        "",
        "BASE_DIR = Path(__file__).resolve().parent",
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
        "# --- Agent Declarations ---",
        agents_block,
        "",
        "# --- Handoff Configuration ---",
        handoffs_block,
        "",
        "async def run_workflow():",
        "    input_data = _load_input()",
        "    message = input_data.get('message', '')",
        f"    result = await Runner.run({graph.start}_agent, message)",
        "    print(json.dumps({",
        "        'final_output': result.final_output,",
        "        'status': 'success'",
        "    }, indent=2))",
        "",
        "if __name__ == '__main__':",
        "    asyncio.run(run_workflow())",
    ]
    return "\n".join(lines) + "\n"


def _tool_functions(graph: CapsuleGraph) -> dict[str, Entrypoint]:
    return {
        name: parse_python_entrypoint(Path("."), tool.entrypoint or "")
        for name, tool in graph.tools.items()
        if tool.type == "python"
    }


def _render_pyproject(name: str) -> str:
    safe_name = name.replace("_", "-")
    return (
        textwrap.dedent(
            f"""
        [project]
        name = "{safe_name}-openai-agents"
        version = "0.1.0"
        requires-python = ">=3.10"
        dependencies = ["openai-agents>=0.1.0"]
        """
        ).strip()
        + "\n"
    )


def _render_readme(name: str) -> str:
    return (
        textwrap.dedent(
            f"""
        # {name} OpenAI Agents SDK Output

        This project was generated by Capsule.

        Run it with:

        ```bash
        uv run --with openai-agents python main.py path/to/input.json
        ```

        The generated code is intentionally readable so users can inspect and modify it.
        """
        ).strip()
        + "\n"
    )
