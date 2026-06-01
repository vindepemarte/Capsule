# Capsule MVP

The first Capsule MVP proves that one `capsule.yaml` can be validated, converted into a Capsule Graph, run locally, tested, compiled to LangGraph, and bundled as `.capsule`.

Run the checked-in example:

```bash
uv run capsule validate examples/refund-support-agent
uv run capsule scan examples/refund-support-agent
uv run capsule schema
uv run capsule graph examples/refund-support-agent
uv run capsule inspect examples/refund-support-agent
uv run capsule run examples/refund-support-agent --input examples/refund-support-agent/examples/refund-request.json
uv run capsule history examples/refund-support-agent
uv run capsule show-run <run-id> --path examples/refund-support-agent
uv run capsule test examples/refund-support-agent
uv run capsule compile examples/refund-support-agent --target langgraph
uv run capsule build examples/refund-support-agent
uv run capsule inspect-bundle examples/refund-support-agent/dist/refund-support-agent-0.1.0.capsule
uv run capsule verify-bundle examples/refund-support-agent/dist/refund-support-agent-0.1.0.capsule
```

The current implementation is intentionally small. It is the first vertical slice, not the finished ecosystem.

Local run history is stored in `.capsule/runs.sqlite` inside the Capsule project and should not be committed.

`capsule scan` performs a static security scan of declared Python tools and permissions. It currently warns about risky permission labels, command execution imports, network imports, environment variable access, and dynamic code execution patterns.

`capsule verify-bundle` checks a `.capsule` archive against `capsule.lock` hashes so users can detect missing or tampered prompt, tool, and test files.

`capsule schema` prints the JSON Schema for `capsule.yaml`. The checked-in schema lives at `docs/capsule.schema.json` and can be regenerated with `uv run capsule schema --output docs/capsule.schema.json`.

`capsule graph` prints the framework-neutral Capsule Graph as JSON. Use `--output` to write it to disk for debugging, adapter development, or external tooling.

The checked-in example declares `input_schema` and `output_schema` in `capsule.yaml`. Capsule validates those JSON Schema definitions during `validate`, carries them into the neutral Capsule Graph, enforces them during local `run` and `test`, and records them in `capsule.lock`.

## P1 MCP Declarations

`examples/mcp-research-agent` demonstrates declaration-only MCP tool support. Capsule can validate MCP tool metadata, carry it through the Capsule Graph, include it in `capsule.lock`, bundle it, and run mocked tests against it. Real MCP execution is still intentionally deferred; the local runtime raises a clear error when an MCP tool is used without a mock.
