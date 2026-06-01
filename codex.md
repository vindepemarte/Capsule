# Capsule Codex Guide

## Purpose

This file defines how we build Capsule.

Capsule is meant to become a Docker-like packaging, compiler, and runtime layer for AI agent workflows. Because this project can easily become messy if we add frameworks, runtimes, adapters, specs, tests, registries, and security features without discipline, every change must protect modularity, clarity, security, and source-of-truth alignment.

## Non-Negotiable Rule

NO MATTER WHAT, before creating or changing code, structure, docs, specs, commands, tests, adapters, or configuration, we must ask the critical questions in this file.

If the answer exposes risk, we stop and fix the structure first.

## Critical Questions Before Every Change

### 1. Is this structure modularized properly?

Every feature must live in the correct module.

Do not create giant files that mix parsing, validation, runtime execution, framework compilation, CLI commands, tests, and documentation logic together.

Expected separation:

- CLI command code should stay separate from core business logic.
- Manifest parsing should stay separate from validation.
- Validation should stay separate from runtime execution.
- Runtime execution should stay separate from compiler adapters.
- Compiler adapters should stay separate from the Capsule Graph.
- Tests should stay close to the behavior they protect.

If a module starts doing too many jobs, split it before adding more functionality.

### 2. Are the files I am trying to create exceeding 500 lines of code?

No source file should casually exceed 500 lines.

Before adding code to any file, ask:

- Is this file already close to 500 lines?
- Will this file exceed 500 lines if we keep adding features?
- Is this file becoming a dumping ground?
- Would a beginner developer understand what this file owns?

If the answer is yes, find a better modular structure before continuing.

A file can exceed 500 lines only when there is a strong reason, such as generated output or a clearly documented exception. Normal application code should be split earlier.

### 3. Does this functionality already exist somewhere?

Before implementing anything new, search the project.

Ask:

- Is there already a module, helper, schema, adapter, command, type, validator, or test that does this?
- Is there an existing pattern that this change should follow?
- Am I duplicating behavior instead of extending the existing system?
- Is there a file I need to understand before touching this feature?

Do not create parallel systems for the same concept.

If a feature already exists, improve or reuse it instead of rewriting it somewhere else.

### 4. Do I need to change any other file for this to work seamlessly?

Every change must be integrated, not isolated.

Ask:

- Does the CLI need to expose this?
- Does the manifest schema need to change?
- Does validation need to know about this?
- Does the Capsule Graph need a new field or node type?
- Does the local runtime need support?
- Do compiler adapters need support?
- Do tests need updates?
- Does documentation need updates?
- Does `manifest.json` need updates?

If a feature requires multiple layers, update all required layers in the same implementation pass unless there is a clear staged plan.

### 5. Is security in place?

Capsule will handle agents, tools, model providers, local files, environment variables, MCP servers, secrets, network calls, and executable workflows. Security cannot be added later as an afterthought.

Before adding functionality, ask:

- Does this expose secrets?
- Does this execute untrusted code?
- Does this allow arbitrary file access?
- Does this allow arbitrary network access?
- Does this call external tools or MCP servers?
- Does this need permissions or user approval?
- Does this need sandboxing?
- Does this need audit logs?
- Does this need input validation?
- Does this need safe defaults?

Default behavior should be explicit, inspectable, and least-privilege.

Never hide risky behavior behind convenience.

### 6. Are we in line with the source of truth?

Before implementing product behavior, check the source of truth.

Current source-of-truth files:

- `plan.md`: product direction, architecture, MVP scope, phases, and design principles.
- `codex.md`: development rules and implementation discipline.
- `manifest.json`: project navigation map and file inventory.

If a decision conflicts with the source of truth, do not silently implement it.

Update the source of truth first, or document the decision clearly in the relevant file.

### 7. Is the structure clear enough that a beginner developer can understand it?

Capsule should be understandable to a beginner developer.

Ask:

- Can someone open the project and understand where to start?
- Are folder names obvious?
- Are file names specific?
- Are modules small enough to understand?
- Are abstractions named clearly?
- Are there simple examples?
- Are error messages useful?
- Are docs written in plain language?

Do not make the codebase clever at the cost of readability.

The project should feel serious, but not intimidating.

### 8. Have we updated `manifest.json`?

Every file and folder must be represented in `manifest.json`.

Any time we add, remove, rename, or significantly repurpose a file or folder, update `manifest.json` in the same change.

The manifest must help a human or AI quickly understand:

- What each file does.
- What each folder owns.
- Which files are source of truth.
- Which files are generated.
- Which files should be edited manually.
- Which areas are planned but not implemented yet.

If `manifest.json` is stale, the change is incomplete.

## Required Change Workflow

Before coding:

1. Read the relevant source-of-truth files.
2. Search for existing functionality.
3. Decide which module owns the change.
4. Check whether any target file risks exceeding 500 lines.
5. Identify all files that must change together.
6. Check security implications.
7. Plan tests or verification.
8. Update `manifest.json` if structure changes.

During coding:

1. Keep files small and focused.
2. Prefer clear names over clever names.
3. Add only necessary comments.
4. Keep public interfaces stable where possible.
5. Make errors actionable.
6. Avoid hidden global behavior.
7. Avoid framework lock-in inside the core graph.

Before finishing:

1. Verify the change works.
2. Confirm no file grew into a bad module boundary.
3. Confirm source-of-truth files still match the implementation.
4. Confirm `manifest.json` is current.
5. Confirm security-sensitive behavior is explicit.
6. Confirm a beginner developer can understand where the change lives.

## Architecture Bias

Capsule must be built around a stable core and replaceable adapters.

Preferred architecture:

- `spec`: manifest schema and parsing.
- `graph`: framework-neutral Capsule Graph.
- `validate`: validation rules and diagnostics.
- `runtime`: local execution engine.
- `adapters`: compilers for LangGraph, CrewAI, OpenAI Agents SDK, and others.
- `cli`: user-facing commands.
- `tests`: behavior and integration checks.
- `docs`: human-readable usage and design documentation.
- `examples`: small real workflows.

Do not let framework-specific code leak into the core graph.

The graph should not know that LangGraph, CrewAI, Dify, or any other framework exists. Adapters should handle those details.

## Current Implementation Map

The current MVP implementation follows the source layout below.

- `src/capsule/cli`: Typer commands and terminal rendering, including project inspection, bundle inspection, run history, and run detail output.
- `src/capsule/spec`: `capsule.yaml` schema models, Python and MCP tool declaration shapes, payload JSON Schema validation, manifest JSON Schema generation, YAML loading, and safe project path resolution.
- `src/capsule/validate`: validation diagnostics, payload schema checks, and project validation rules.
- `src/capsule/graph`: framework-neutral Capsule Graph models, builder, JSON serialization, and summary output.
- `src/capsule/runtime`: local graph execution, input/output schema enforcement, Python tool loading, mocked MCP declaration handling, and run traces.
- `src/capsule/history`: SQLite-backed local run history storage and lookup.
- `src/capsule/testing`: YAML workflow test models and test runner.
- `src/capsule/security`: permission checks for privileged tool execution and static security scans for risky permissions/tool behavior.
- `src/capsule/bundle`: `capsule.lock`, schema and tool metadata pinning, `.capsule` archive generation, bundle inspection, and lockfile hash verification.
- `src/capsule/adapters/langgraph`: LangGraph compiler adapter with generated tool execution and branch routing.
- `src/capsule/project`: starter project scaffolding.
- `examples/refund-support-agent`: checked-in MVP Python-tool workflow.
- `examples/mcp-research-agent`: checked-in P1 declaration-only MCP workflow with mocked tests.
- `tests`: automated coverage for the MVP vertical slice.

If a new feature crosses more than one of these areas, update all affected layers in the same implementation pass or record the staged limitation clearly.

## Security Bias

Capsule should assume agent workflows can be dangerous.

Default principles:

- No silent secret access.
- No silent local file access outside allowed paths.
- No silent network access where permissions are required.
- No silent tool execution.
- No hidden MCP server trust.
- No unsafe generated code without inspection.
- No registry install without clear metadata.

The long-term product should support signed bundles, permission manifests, lockfiles, audit logs, and safe execution modes.

## Simplicity Bias

If there are two possible designs, choose the one that a beginner developer can explain.

Avoid premature abstractions.

A small, clear implementation is better than a powerful but confusing one.

The goal is not to impress framework authors. The goal is to make agent workflows portable, understandable, testable, and safe.

## Capsule-Specific North Star

Every major implementation decision should support this product promise:

Build an agent workflow once, package it as a Capsule, test it, and run or compile it across different agent runtimes without rewriting the workflow.

If a change does not help that promise, question whether it belongs in the project.
