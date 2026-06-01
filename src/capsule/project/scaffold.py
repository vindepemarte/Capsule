from __future__ import annotations

import textwrap
from pathlib import Path


class ScaffoldError(RuntimeError):
    """Raised when a Capsule project cannot be scaffolded safely."""


def create_project(name: str, destination: Path | None = None) -> Path:
    root = (destination or Path.cwd() / name).resolve()
    if root.exists() and any(root.iterdir()):
        raise ScaffoldError(f"Destination is not empty: {root}")

    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "tools").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "examples").mkdir(parents=True, exist_ok=True)

    _write(root / ".gitignore", GITIGNORE)
    _write(root / "capsule.yaml", _manifest(name))
    _write(root / "agents" / "triage.md", TRIAGE_PROMPT)
    _write(root / "agents" / "responder.md", RESPONDER_PROMPT)
    _write(root / "tools" / "policy_search.py", POLICY_TOOL)
    _write(root / "tools" / "draft_reply.py", DRAFT_TOOL)
    _write(root / "tests" / "refund_request.yaml", TEST_CASE)
    _write(root / "examples" / "refund-request.json", EXAMPLE_INPUT)
    return root


def _write(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def _manifest(name: str) -> str:
    return f"""
    name: {name}
    version: 0.1.0
    description: Handles refund request triage and reply drafting.

    input_schema:
      type: object
      required:
        - message
      properties:
        message:
          type: string
          minLength: 1
      additionalProperties: true

    output_schema:
      type: object
      required:
        - final_reply
      properties:
        final_reply:
          type: string
          minLength: 1
        route:
          type: string
      additionalProperties: true

    models:
      default:
        provider: local
        model: deterministic-dev

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
    """


TRIAGE_PROMPT = """
You triage customer support refund requests.

Decide whether the request can be handled automatically or needs human review.
Use policy_search before routing.
"""

RESPONDER_PROMPT = """
You draft clear, polite customer support replies.

Use draft_reply to create the final response.
"""

POLICY_TOOL = """
def search_policy(state):
    message = state.get("message", "").lower()
    if "refund" in message:
        return {
            "route": "approved",
            "policy": "Refunds are available within 30 days when the order is eligible."
        }
    return {
        "route": "needs_human",
        "policy": "No matching refund policy was found."
    }
"""

DRAFT_TOOL = """
def create_draft(state):
    policy = state.get("policy", "We need to review your request.")
    message = state.get("message", "your request")
    return {
        "final_reply": (
            "Thanks for reaching out. Based on our policy, "
            f"{policy} We reviewed this request: {message}"
        )
    }
"""

TEST_CASE = """
name: refund request routes to responder
input:
  message: "I want a refund for my last order."
mock_tools:
  policy_search:
    route: approved
    policy: "Refunds are available within 30 days."
  draft_reply:
    final_reply: "Thanks for reaching out. Refunds are available within 30 days."
expect:
  path:
    - triage
    - responder
  output_contains:
    final_reply: "refund"
  tool_calls:
    - policy_search
    - draft_reply
"""

EXAMPLE_INPUT = """
{
  "message": "I want a refund for my last order."
}
"""

GITIGNORE = """
.capsule/
dist/
capsule.lock
__pycache__/
*.pyc
"""
