from __future__ import annotations

from capsule.graph.models import CapsuleGraph


def graph_summary(graph: CapsuleGraph) -> str:
    lines = [
        f"Capsule: {graph.name} ({graph.version})",
        f"Description: {graph.description or 'n/a'}",
        f"Start: {graph.start}",
        "",
        "Schemas:",
        f"- input_schema: {'declared' if graph.input_schema else 'none'}",
        f"- output_schema: {'declared' if graph.output_schema else 'none'}",
        "",
        "Agents:",
    ]

    for agent in graph.agents.values():
        tools = ", ".join(agent.tools) if agent.tools else "none"
        lines.append(f"- {agent.name}: model={agent.model}, tools={tools}")

    lines.append("")
    lines.append("Tools:")
    for name, tool in graph.tools.items():
        lines.append(f"- {name}: type={tool.type}, permission={tool.permission}")

    lines.append("")
    lines.append("Workflow:")
    for node in graph.nodes.values():
        lines.append(
            f"- {node.id}: type={node.type}, agent={node.agent or 'n/a'}, next={node.next}"
        )

    lines.append("")
    lines.append("Tests:")
    for test in graph.tests:
        lines.append(f"- {test}")
    if not graph.tests:
        lines.append("- none")

    return "\n".join(lines)
