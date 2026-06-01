# Capsule PRD

## Document Status

Status: production planning source of truth  
Project: Capsule  
Last updated: 2026-06-01  
Primary audience: founders, maintainers, contributors, and AI coding agents  

Capsule is an open-source developer tool for packaging AI agent workflows once and running or compiling them across different agent runtimes.

The short version:

```text
Capsule is Docker-like packaging for AI agent workflows.
```

The precise version:

```text
Capsule is a framework-neutral packaging, validation, testing, bundling, and compiler layer for AI agent workflows.
```

Capsule should not become another agent framework. Its job is to sit above frameworks and make agent workflows portable, inspectable, testable, reproducible, and safer to run.

## Product Promise

Build an agent workflow once, package it as a Capsule, test it, and run or compile it across agent runtimes without rewriting the workflow.

The first production-quality demo must prove this flow:

```bash
capsule init refund-support-agent
cd refund-support-agent
capsule validate
capsule run --input examples/refund-request.json
capsule test
capsule compile --target langgraph
capsule build
```

The result should be:

- A valid `capsule.yaml` project.
- A local run using Capsule's own development runtime.
- Passing workflow tests.
- A generated LangGraph project.
- A portable `.capsule` bundle.

## Why Capsule Exists

AI agent development is fragmented.

Today, a workflow built in LangGraph, CrewAI, OpenAI Agents SDK, Haystack, Dify, or another framework is usually locked into that framework. Moving it somewhere else often means rewriting agent definitions, prompts, tool bindings, state handling, memory behavior, branching logic, tests, and deployment wiring.

This creates real problems:

- Agent workflows are difficult to share.
- Agent workflows are difficult to inspect.
- Agent workflows are difficult to reproduce.
- Agent workflows are difficult to test consistently.
- Agent workflows are difficult to move across frameworks.
- Teams get locked into a framework before they understand their long-term needs.
- Open-source agent projects cannot be composed together cleanly.

Capsule solves the missing layer: a portable package format and compiler workflow for agents.

## How Capsule Relates To Docker

Docker packages runtime infrastructure.

Docker handles:

- Operating system dependencies.
- Language runtimes.
- Installed packages.
- Environment variables.
- Startup commands.
- Services and ports.

Capsule packages agent workflow structure.

Capsule handles:

- Agents.
- Prompts.
- Models.
- Tools.
- Permissions.
- Workflow branches.
- Human approval gates.
- Memory and retrieval declarations.
- Tests and mocked tool responses.
- Capsule Graph generation.
- Runtime adapters.
- Framework compilation.
- Bundle metadata and lockfiles.

Docker can run a LangGraph app reliably, but it cannot turn that app into CrewAI, OpenAI Agents SDK, Haystack, or a local Capsule runtime. Docker also does not understand whether an agent workflow is portable, safe, testable, or correctly wired.

The long-term relationship should be:

```text
Capsule defines and compiles the agent workflow.
Docker ships the generated runtime when container deployment is needed.
```

## Target Users

### 1. Agent Developers

Developers building agent workflows who want a clean project format, validation, tests, and a way to avoid framework lock-in.

Primary need: define once, run locally, compile elsewhere.

### 2. Open-Source Maintainers

Maintainers who want to publish reusable agent workflows that others can inspect, test, install, and adapt.

Primary need: package and share workflows in a predictable format.

### 3. Product Teams

Teams experimenting with agent frameworks who do not want to rewrite their product if they change runtimes later.

Primary need: portability and reproducibility.

### 4. Security-Conscious Teams

Teams that need visibility into tools, permissions, secrets, local file access, network access, and generated code.

Primary need: explicit permission boundaries and audit-friendly workflow definitions.

## Positioning

Capsule is not:

- A chatbot UI.
- A hosted agent platform.
- A visual workflow builder.
- A replacement for LangGraph, CrewAI, OpenAI Agents SDK, Haystack, or Dify.
- A model provider.
- A vector database.
- A Docker replacement.

Capsule is:

- A workflow package format.
- A CLI for agent projects.
- A validator for portable agent definitions.
- A local development runtime.
- A test harness for agent workflows.
- A compiler from a neutral workflow graph to target frameworks.
- A bundle format for sharing agent workflows.

The market position:

```text
Agent frameworks execute workflows.
Capsule packages and compiles workflows.
```

## Product Principles

### Framework Neutrality

The core must not depend on LangGraph, CrewAI, OpenAI Agents SDK, Dify, or any other target framework.

Framework-specific behavior belongs only in adapters.

### Modularity

Every module must have one clear responsibility.

CLI code must not contain parser logic. Parser logic must not contain runtime logic. Runtime logic must not contain compiler adapter logic.

No normal source file should casually exceed 500 lines. If a file is heading toward 500 lines, split the module before adding more behavior.

### Beginner Readability

The codebase should be understandable to a beginner developer.

Names should be explicit. Errors should be actionable. Examples should be small. The project should feel serious, but not intimidating.

### Security By Default

Agent workflows can execute tools, read files, access secrets, call networks, and invoke MCP servers. Capsule must treat those actions as risky by default.

No silent secret access. No silent local file access outside declared paths. No silent network access where permissions are required. No silent tool execution.

### Source-Of-Truth Alignment

The current source-of-truth files are:

- `plan.md`: product PRD and production plan.
- `codex.md`: development discipline and project rules.
- `manifest.json`: project navigation map.

Any structural change must update `manifest.json`.

## MVP Strategy

The MVP is a compiler MVP.

Capsule must prove that a single `capsule.yaml` can:

1. Validate successfully.
2. Convert into a framework-neutral Capsule Graph.
3. Run locally through Capsule's development runtime.
4. Run tests with deterministic mocked inputs and tool responses.
5. Compile into a runnable LangGraph project.
6. Build into a `.capsule` bundle.

The MVP should not try to support every framework. The first adapter is LangGraph because graph-shaped workflows, state, branching, and human-in-the-loop behavior map well to Capsule's product direction.

## MVP In Scope

### CLI

Required commands:

```bash
capsule init <name>
capsule validate
capsule inspect
capsule run --input <file>
capsule test
capsule compile --target langgraph
capsule build
```

Expected behavior:

- `init` creates a small example project.
- `validate` checks the manifest, referenced files, workflow graph, permissions, and test declarations.
- `inspect` prints a human-readable summary of agents, tools, models, workflow steps, permissions, and tests.
- `run` executes the workflow locally with a JSON input file.
- `test` runs declared tests using mocked tool responses where provided.
- `compile` generates target framework output.
- `build` creates a `.capsule` bundle and `capsule.lock`.

### Manifest

The MVP manifest is `capsule.yaml`.

It must define:

- Project name.
- Version.
- Description.
- Models.
- Agents.
- Tools.
- Workflow start step.
- Workflow steps.
- Permissions.
- Tests.

Example:

```yaml
name: refund-support-agent
version: 0.1.0
description: Handles refund request triage and reply drafting.

models:
  default:
    provider: openai
    model: gpt-4.1-mini

agents:
  triage:
    prompt: agents/triage.md
    model: default
    tools:
      - policy_search

  responder:
    prompt: agents/responder.md
    model: default
    tools:
      - draft_reply

tools:
  policy_search:
    type: python
    entrypoint: tools/policy_search.py:search_policy
    permission: read

  draft_reply:
    type: python
    entrypoint: tools/draft_reply.py:create_draft
    permission: write_draft

workflow:
  start: triage
  steps:
    - id: triage
      type: agent
      agent: triage
      next:
        approved: responder
        needs_human: human_review

    - id: human_review
      type: human_gate
      next: responder

    - id: responder
      type: agent
      agent: responder
      output: final_reply

permissions:
  tools:
    policy_search: read
    draft_reply: write_draft

tests:
  - tests/refund_request.yaml
```

### Capsule Graph

The Capsule Graph is the core internal representation.

It must represent:

- Agents.
- Prompts.
- Model references.
- Tool references.
- Workflow nodes.
- Workflow edges.
- Branching rules.
- Human gates.
- Input schemas.
- Output schemas.
- Permission declarations.
- Test references.

The graph must not know about LangGraph or any other external framework. It is the neutral layer that all adapters consume.

### Local Runtime

The local runtime exists for development, validation, and parity testing.

MVP local runtime requirements:

- Load a Capsule Graph.
- Accept JSON input.
- Execute agent steps in graph order.
- Execute declared Python tools only when permitted.
- Support simple branching.
- Support a human gate stub for local development.
- Produce a structured run trace.

The local runtime does not need to be a full production agent orchestrator in the MVP.

### LangGraph Adapter

The first compiler adapter must generate a readable LangGraph project from the Capsule Graph.

Generated output should include:

- Python source files.
- Dependency declaration.
- Prompt assets.
- Tool wrappers.
- A runnable entrypoint.
- A README explaining how to run the generated project.

The generated code should be understandable and inspectable. Do not generate opaque code that users cannot debug.

### Testing

Capsule tests should be YAML files that define:

- Input payload.
- Optional mocked tool responses.
- Expected final output fields.
- Expected workflow path when relevant.
- Expected tool calls when relevant.

Example:

```yaml
name: refund request routes to responder
input:
  message: "I want a refund for my last order."
mock_tools:
  policy_search:
    result: "Refunds are available within 30 days."
expect:
  path:
    - triage
    - responder
  output_contains:
    final_reply: "refund"
```

### Bundle

The MVP bundle artifact is:

```text
<name>-<version>.capsule
```

The bundle should include:

- `capsule.yaml`.
- `capsule.lock`.
- Agent prompt files.
- Tool source files or schemas.
- Test files.
- Permission metadata.
- Build metadata.

The exact physical format can start as a zip archive with a `.capsule` extension. OCI-style packaging can be explored later.

### Lockfile

`capsule.lock` exists to improve reproducibility.

It should pin:

- Capsule spec version.
- Prompt file hashes.
- Tool file hashes.
- Adapter version.
- Python dependency metadata where available.
- Model provider and model names.
- Bundle build timestamp.

The MVP does not guarantee deterministic LLM output. It guarantees that the workflow structure and referenced assets are pinned.

## MVP Out Of Scope

The following are not required for the first production-quality demo:

- Hosted cloud platform.
- Visual workflow builder.
- Public registry.
- Private registry.
- Signed bundles.
- Docker image generation.
- Full MCP execution.
- TypeScript runtime.
- Dify export.
- CrewAI adapter.
- OpenAI Agents SDK adapter.
- Haystack adapter.
- Distributed execution.
- Advanced RAG pipeline management.
- Long-term memory engine.
- Production monitoring dashboard.

These are roadmap items only after the core abstraction proves useful.

## Recommended Technical Stack

Capsule should be Python-first.

Core stack:

- Python 3.12+.
- uv for dependency and environment management.
- Typer for CLI commands.
- Rich for terminal output.
- Pydantic for manifest and graph models.
- PyYAML or ruamel.yaml for YAML loading.
- pytest for tests.
- Ruff for linting and formatting.
- SQLite for local run history, traces, and test reports when persistence is needed.

First adapter:

- LangGraph.

Later adapters:

- CrewAI.
- OpenAI Agents SDK.
- Haystack.
- Dify export.
- TypeScript runtime.

## Proposed Codebase Shape

The implementation should use a `src` layout.

```text
Capsule/
  plan.md
  codex.md
  manifest.json
  pyproject.toml
  README.md
  src/
    capsule/
      cli/
      spec/
      graph/
      validate/
      runtime/
      adapters/
        langgraph/
      testing/
      security/
      bundle/
  examples/
    refund-support-agent/
  tests/
  docs/
```

Module ownership:

- `cli`: Typer commands and terminal UX only.
- `spec`: `capsule.yaml` loading, path resolution, and schema models.
- `graph`: framework-neutral Capsule Graph data structures.
- `validate`: validation rules and diagnostics.
- `runtime`: local graph executor.
- `adapters`: compiler adapters for target frameworks.
- `testing`: Capsule test file loading, mocks, assertions, and reports.
- `security`: permission checks, secret handling rules, and safety diagnostics.
- `bundle`: `.capsule` and `capsule.lock` generation.

The implementation must follow `codex.md`: keep files modular, avoid 500+ line source files, reuse existing functionality before creating new modules, and update `manifest.json` whenever structure changes.

## Core Data Flow

The normal Capsule flow:

```text
capsule.yaml
  -> spec loader
  -> manifest model
  -> validator
  -> Capsule Graph
  -> local runtime OR compiler adapter
  -> run trace, generated project, or .capsule bundle
```

The key invariant:

```text
All runtimes and adapters consume the Capsule Graph, not raw capsule.yaml.
```

This keeps framework-specific logic out of the core.

## Security Requirements

Capsule must treat tool execution and external access as privileged behavior.

MVP security requirements:

- Validate all paths referenced by `capsule.yaml`.
- Prevent path traversal outside the project unless explicitly allowed.
- Require tools to be declared before use.
- Require permissions to be declared before tool execution.
- Do not read secrets silently.
- Do not execute undeclared tools.
- Print clear warnings for risky permissions.
- Keep generated framework output inspectable.
- Include permission metadata in `.capsule` bundles.

Post-MVP security roadmap:

- MCP permission scopes.
- Signed bundles.
- Registry trust metadata.
- Policy files.
- Sandboxed tool execution.
- Audit logs.
- Secret broker integrations.

## Product Requirements

### P0 Requirements (Completed)

P0 is required for the MVP to be considered complete.

- [x] A developer can create a new Capsule project with `capsule init`.
- [x] A developer can validate `capsule.yaml` with useful errors.
- [x] Capsule can build a neutral Capsule Graph from the manifest.
- [x] Capsule can run a simple workflow locally from JSON input.
- [x] Capsule can run YAML-defined tests.
- [x] Capsule can compile the same workflow to LangGraph.
- [x] Capsule can create a `.capsule` bundle.
- [x] Capsule can create `capsule.lock`.
- [x] The codebase is modular and beginner-readable.
- [x] `manifest.json` stays current as structure changes.

### P1 Requirements

P1 is next after MVP. All P1 requirements have been successfully implemented.

- [x] CrewAI adapter. (Completed)
- [x] OpenAI Agents SDK adapter. (Completed)
- [x] Better run traces. (Completed)
- [x] SQLite-backed run history. (Completed)
- [x] MCP tool declaration support. (Completed)
- [x] More complete permission model. (Completed)
- [x] Better examples. (Completed)
- [x] Documentation site. (Completed)

### P2 Requirements

P2 is longer-term.

- Capsule registry.
- Signed bundles.
- Docker image generation.
- TypeScript runtime.
- Dify import/export.
- Visual graph inspection.
- Hosted validation service.
- Organization policies.

## Acceptance Criteria For MVP

The MVP is done when all of these are true:

- `capsule init refund-support-agent` creates a working example project.
- `capsule validate` succeeds on the example project.
- `capsule validate` returns actionable errors for missing prompts, unknown tools, invalid workflow edges, and undeclared permissions.
- `capsule inspect` shows the workflow structure clearly.
- `capsule run --input examples/refund-request.json` runs the example locally.
- `capsule test` runs at least one YAML test with mocked tool output.
- `capsule compile --target langgraph` generates a runnable LangGraph project.
- The generated LangGraph project can run the same example input.
- `capsule build` creates a `.capsule` bundle and `capsule.lock`.
- No normal source file exceeds 500 lines without a documented exception.
- The implementation has tests for parser, validator, graph, local runtime, test harness, bundle creation, and LangGraph adapter.
- `manifest.json` lists all important files and folders.

## Roadmap

### Phase 1: PRD And Project Foundation (Completed)

Deliverables:
- Production PRD.
- Development rules.
- Project manifest.
- Initial README.
- Python project scaffold.
- Basic test and lint setup.

### Phase 2: Spec And Validation (Completed)

Deliverables:
- `capsule.yaml` Pydantic models.
- YAML loader.
- Path resolver.
- Validation diagnostics.
- Example project.

### Phase 3: Capsule Graph (Completed)

Deliverables:
- Capsule Graph models.
- Manifest-to-graph conversion.
- Graph inspection.
- Serialization for debugging.

### Phase 4: Local Runtime (Completed)

Deliverables:
- Simple graph executor.
- Tool execution interface.
- Permission checks.
- Human gate stub.
- Structured trace output.

### Phase 5: Testing And Lockfile (Completed)

Deliverables:
- YAML test format.
- Mock tool responses.
- Output assertions.
- Workflow path assertions.
- `capsule.lock` generation.

### Phase 6: LangGraph Compiler (Completed)

Deliverables:
- LangGraph adapter.
- Generated Python project.
- Generated README.
- Runnable compiled example.
- Parity smoke test.

### Phase 7: Bundle (Completed)

Deliverables:
- `.capsule` archive creation.
- Bundle metadata.
- Included prompts, tools, tests, permissions, and lockfile.
- Bundle inspection command.

### Phase 8: Post-MVP Expansion (In Progress)

Deliverables:
- [x] CrewAI adapter. (Completed)
- [x] OpenAI Agents SDK adapter. (Completed)
- [x] MCP declarations stubs & stubs validations. (Completed)
- [x] Interactive permissions engine at runtime. (Completed)
- [x] Multi-agent translation examples. (Completed)
- [x] Interactive documentation website with spec explorer. (Completed)
- [ ] Signed bundles.
- [ ] Registry prototype.

## Risks

### Risk: Capsule Becomes Another Agent Framework

Mitigation: keep the core focused on spec, graph, validation, testing, bundling, and compilation. Keep execution runtime minimal in the MVP.

### Risk: Capsule Graph Becomes Too Generic

Mitigation: support only the workflow primitives needed for the MVP first: agents, tools, branching, human gates, inputs, outputs, permissions, and tests.

### Risk: Runtime Parity Is Hard

Mitigation: define parity narrowly at first. MVP parity means the same example workflow can run locally and as generated LangGraph code with equivalent path and output behavior.

### Risk: Security Is Deferred

Mitigation: include permissions, path validation, explicit tool declarations, and inspectable generated output from the first implementation.

### Risk: The Spec Gets Too Complex

Mitigation: keep `capsule.yaml` small, readable, and example-driven. Add schema features only when required by real examples.

## Open Questions

These are intentionally deferred until after MVP implementation begins:

- Should `Capsulefile` exist as an alias for `capsule.yaml`?
- Should `.capsule` eventually use OCI image concepts?
- Should MCP become the default tool protocol?
- How strict should output parity be across all adapters?
- Should a hosted registry be centralized, Git-based, or decentralized?

The MVP should not block on these questions.

## Final Direction

Capsule should become the open packaging standard for AI agent workflows.

The first milestone is not a large platform. It is a small, excellent CLI that proves one thing clearly:

```text
One portable agent workflow can be validated, tested, bundled, run locally, and compiled into LangGraph.
```

That is the Docker-for-agents moment.
