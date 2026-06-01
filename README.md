<p align="center">
  <img src="docs/logo.png" alt="Capsule Logo" width="400"/>
</p>

# Capsule 🚀

**Docker-like packaging, compilation, and testing layer for AI agent workflows.**

[![Install from GitHub](https://img.shields.io/badge/install-pip%20git%2Bgithub-2ea44f.svg)](https://github.com/vindepemarte/Capsule)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Capsule is an open-source tool built to reduce **framework lock-in** and improve **reproducibility** in AI agent development. Instead of building agent workflows tightly coupled to a single orchestration library, Capsule lets you **define your workflow once in a framework-neutral spec, test it locally, and compile it to supported target runtimes.**

---

## 💡 Why Capsule?

As AI agent applications grow, developers build complex networks of specialized agents, prompt templates, local tools, and model configs. Today, these are typically built inside frameworks like LangGraph, CrewAI, or OpenAI Agents SDK. 

This leads to several critical issues:
* **Framework Lock-in:** Moving a workflow from LangGraph to CrewAI or OpenAI Agents SDK means throwing away your codebase and rewriting state management, tool bindings, and routing from scratch.
* **Lack of Standalone Testing:** Testing how prompts and agent routes behave across versions without writing custom, complex Python scripts is incredibly difficult.
* **Security & Audits:** If you run an untrusted agent workflow, there is no standardized way to verify what system files, environment variables, or APIs the agent is allowed to access.

**Capsule solves this by serving as a declarative packaging, validation, testing, and compilation layer that sits *above* the execution frameworks.**

---

## 🛠️ Key Features

* **Define Once, Compile to Supported Targets:** Author your agents, prompts, local Python/MCP tools, and routing steps in a standard `capsule.yaml` file. Compile directly to **LangGraph**, **CrewAI Flows**, or **OpenAI Agents SDK** targets.
* **Runtime Permission Sandboxing:** Intercept tool calls dynamically at runtime. Enforce read, write, or custom scopes. Interactively request approval in terminals, or use pre-approval flags (`--allow-permission` / `--allow-all`) in script pipelines.
* **Declarative Workflow Tests:** Run deterministic, YAML-defined test cases against your workflow with mocked tool responses, checking output values and execution paths.
* **Static Security Scanning:** Instantly audit files, permissions, and tools using `capsule scan` to identify risky imports, shell executions, and permission violations.
* **Lockfiles & Portable Bundles:** Build hermetic `.capsule` zip archives paired with a `capsule.lock` that pins asset hashes to guarantee reproducibility when sharing workflows.
* **Interactive Documentation & Spec Explorer:** Explore all manifest configurations and guides via a beautiful, local documentation page (`docs/site/index.html`) featuring a reactive Spec Explorer.

---

## ✅ Current Compatibility Status

Capsule is not a universal exporter for every AI framework yet. This is the current tested contract:

| Target | Status | What to expect |
| --- | --- | --- |
| **Capsule local runtime** | ✅ Runnable | `capsule validate`, `capsule scan`, `capsule test`, `capsule run`, `capsule build`, and `capsule verify-bundle` work on the included starter project. |
| **LangGraph** | ✅ Runnable generated output | `capsule compile --target langgraph` produces a native LangGraph project that runs end-to-end with local Python tools and no LLM API key for the starter workflow. |
| **CrewAI Flows** | ✅ Generated and import-tested | `capsule compile --target crewai` produces a CrewAI Flow project with CrewAI `BaseTool` wrappers. Import smoke tests pass against real CrewAI on Python 3.12. Full native execution requires model/provider credentials such as `OPENAI_API_KEY`. |
| **OpenAI Agents SDK** | ✅ Generated and import-tested | `capsule compile --target openai-agents` produces an OpenAI Agents SDK project that imports against the real package. Full native execution requires `OPENAI_API_KEY` or another configured provider. |
| **Haystack / AutoGen / Semantic Kernel** | 🚧 Not supported yet | These are planned adapter targets. Today, `capsule compile --target haystack` is expected to return `Unsupported target: haystack`. |

The strongest no-credential framework proof today is **LangGraph**. CrewAI and OpenAI Agents are valid generated adapter outputs, but their native runtimes call an LLM provider by design.

---

## 📖 Quickstart Tutorial

### 1. Installation
Install the CLI directly from GitHub:
```bash
pip install git+https://github.com/vindepemarte/Capsule.git
capsule --help
```

### 2. Scaffold a New Project
Initialize a starter Capsule template:
```bash
capsule init customer-support-agent
cd customer-support-agent
```

### 3. Validate & Scan
Verify the project structure and audit security boundaries:
```bash
# Validate manifest paths, schema links, and routing connections
capsule validate

# Scan for security risks, undeclared tool parameters, and dangerous imports
capsule scan
```

### 4. Run the Workflow Locally
Execute the agent workflow using Capsule's local development runtime:
```bash
capsule run --input examples/refund-request.json --allow-all
```

### 5. Run Workflow Tests
Test routing logic and outputs with mocked tool results:
```bash
capsule test
```

### 6. Compile to a Supported Framework
Compile the neutral workflow definition into native target code for one of the supported adapters:

**Target 1: LangGraph**
```bash
capsule compile --target langgraph
# Run the compiled project natively.
# The starter workflow runs without an LLM key because its tools are deterministic.
uv run --with langgraph python dist/langgraph/main.py examples/refund-request.json
```

**Target 2: OpenAI Agents SDK**
```bash
capsule compile --target openai-agents
# Full native execution requires OPENAI_API_KEY or another configured provider.
uv run --with openai-agents python dist/openai-agents/main.py examples/refund-request.json
```

**Target 3: CrewAI Flows**
```bash
capsule compile --target crewai
# Use Python 3.12 for the current CrewAI dependency stack.
# Full native execution requires model/provider credentials.
uv run --python 3.12 --with crewai python dist/crewai/main.py examples/refund-request.json
```

### 7. Package and Verify
Create a portable, locked bundle of your workflow for production or sharing:
```bash
# Build the .capsule bundle and generate capsule.lock
capsule build

# Verify a bundle's files against lockfile hashes before execution
capsule verify-bundle dist/customer-support-agent-0.1.0.capsule
```

---

## 📄 Manifest Spec (`capsule.yaml`)

Workflows are declared cleanly in a structured format:

```yaml
name: refund-support-agent
version: 0.1.0
description: Triage customer refund requests and draft responses.

models:
  default:
    provider: openai
    model: gpt-4o-mini

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

---

## 🗺️ Project Navigation

* `docs/site/`: The Interactive Web Documentation & YAML Spec Explorer.
* `src/capsule/spec/`: Manifest models, YAML loading, and schemas.
* `src/capsule/graph/`: Framework-neutral dependency and workflow graph.
* `src/capsule/validate/`: Integrity rules and path diagnostics.
* `src/capsule/security/`: Permissions checks and static source scans.
* `src/capsule/runtime/`: Local dev runner, runtime permissions checking, schema enforcement.
* `src/capsule/testing/`: Declarative YAML workflow test runner.
* `src/capsule/adapters/`: Compiler targets (**LangGraph**, **OpenAI Agents SDK**, **CrewAI**).
* `src/capsule/bundle/`: Bundler engine, hash-verifier, and lockfile generator.

---

## 🤝 Contributing

We welcome contributions of all kinds! If you'd like to implement new compiler targets (e.g., AutoGen, Haystack, or TypeScript adapters), enrich security rules, or build UI dashboards:
1. Fork the repo and create your branch.
2. Ensure all tests pass: `uv run pytest`.
3. Format with ruff: `uv run ruff format .` and `uv run ruff check .`.
4. Open a Pull Request.

---

## 🔮 Roadmap & Vision

Capsule's ultimate goal is to become the **universal packaging, distribution, and runtime verification standard for AI agent workflows**. 

Current progress:

- [x] Core `capsule.yaml` package format.
- [x] CLI scaffold, validate, inspect, graph, run, test, compile, build, scan, history, and bundle verification commands.
- [x] Framework-neutral Capsule Graph.
- [x] Local development runtime with structured traces.
- [x] Declarative YAML workflow tests with mocked tool responses.
- [x] Runtime permission checks with `--allow-permission`, `--allow-all`, and interactive approval.
- [x] Static security scanning for risky permissions, imports, environment access, and MCP declarations.
- [x] `capsule.lock` generation and `.capsule` zip bundle creation.
- [x] Bundle inspection and hash verification.
- [x] LangGraph compiler adapter with runnable generated output.
- [x] CrewAI Flow compiler adapter with real-package import smoke test.
- [x] OpenAI Agents SDK compiler adapter with real-package import smoke test.
- [x] Declaration-only MCP tool support with mocked local tests.
- [x] Refund support, MCP research, and translation editor example projects.
- [x] Interactive documentation site and `capsule.yaml` Spec Explorer.

Next milestones:

- [ ] Signed bundles.
- [ ] Public or Git-backed Capsule registry prototype.
- [ ] Real MCP runtime orchestration with server startup, authorization prompts, and session pooling.
- [ ] Hermetic Python tool sandboxing through gRPC, containers, or WASM.
- [ ] Visual graph inspector and debugger.
- [ ] No-credential native smoke test mode for every compiler target.
- [ ] TypeScript runtime target.
- [ ] Additional adapters for AutoGen, Haystack, and Semantic Kernel.
- [ ] Docker or OCI image generation for compiled runtimes.

---

## 📈 Star History

If you believe in a framework-neutral, open standard for AI agents, consider starring the repository to support our open-source journey:

[![Star History Chart](https://api.star-history.com/svg?repos=vindepemarte/Capsule&type=Date)](https://star-history.com/#vindepemarte/Capsule&Date)

---

## 🛡️ License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
