from __future__ import annotations

from capsule.graph.models import CapsuleGraph, GraphAgent, GraphNode
from capsule.spec.loader import ProjectContext
from capsule.spec.paths import resolve_project_path


def build_graph(context: ProjectContext) -> CapsuleGraph:
    manifest = context.manifest
    agents: dict[str, GraphAgent] = {}
    nodes: dict[str, GraphNode] = {}

    for name, agent in manifest.agents.items():
        prompt_path = resolve_project_path(context.root, agent.prompt, f"agents.{name}.prompt")
        agents[name] = GraphAgent(
            name=name,
            prompt_path=agent.prompt,
            prompt=prompt_path.read_text(encoding="utf-8"),
            model=agent.model,
            tools=agent.tools,
        )

    for step in manifest.workflow.steps:
        nodes[step.id] = GraphNode(
            id=step.id,
            type=step.type,
            agent=step.agent,
            next=step.next,
            output=step.output,
        )

    return CapsuleGraph(
        name=manifest.name,
        version=manifest.version,
        description=manifest.description,
        input_schema=manifest.input_schema,
        output_schema=manifest.output_schema,
        models=manifest.models,
        agents=agents,
        tools=manifest.tools,
        start=manifest.workflow.start,
        nodes=nodes,
        permissions=manifest.permissions.tools,
        tests=manifest.tests,
    )
