from __future__ import annotations

import sys
from pathlib import Path
import pytest

from capsule.graph.builder import build_graph
from capsule.runtime.executor import run_graph
from capsule.security.permissions import CapsulePermissionError
from capsule.spec.loader import load_project


EXAMPLE = Path("examples/refund-support-agent")


def test_unauthorized_non_read_permission_raises_error():
    context = load_project(EXAMPLE)
    graph = build_graph(context)

    # Tool 'draft_reply' requires 'write_draft' permission which is not 'read'
    input_data = {"message": "I want a refund for my last order."}

    # Verify execution fails when 'write_draft' is not authorized
    with pytest.raises(CapsulePermissionError) as exc_info:
        run_graph(graph, context.root, input_data)

    assert "blocked: permission 'write_draft' is not authorized" in str(exc_info.value)


def test_authorized_permission_succeeds():
    context = load_project(EXAMPLE)
    graph = build_graph(context)
    input_data = {"message": "I want a refund for my last order."}

    # Succeeds with allowed_permissions set
    res = run_graph(graph, context.root, input_data, allowed_permissions=["write_draft"])
    assert res.output["route"] == "approved"

    # Succeeds with allow_all set
    res_all = run_graph(graph, context.root, input_data, allow_all=True)
    assert res_all.output["route"] == "approved"


def test_interactive_prompt_approval(monkeypatch):
    context = load_project(EXAMPLE)
    graph = build_graph(context)
    input_data = {"message": "I want a refund for my last order."}

    # Mock isatty to return True
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)

    # Mock Confirm.ask to return True (approve)
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: True)

    # Execution should succeed because Confirm.ask returns True
    res = run_graph(graph, context.root, input_data, allowed_permissions=[])
    assert res.output["route"] == "approved"


def test_interactive_prompt_denial(monkeypatch):
    context = load_project(EXAMPLE)
    graph = build_graph(context)
    input_data = {"message": "I want a refund for my last order."}

    # Mock isatty to return True
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)

    # Mock Confirm.ask to return False (deny)
    from rich.prompt import Confirm

    monkeypatch.setattr(Confirm, "ask", lambda *args, **kwargs: False)

    # Execution should fail because Confirm.ask returns False
    with pytest.raises(CapsulePermissionError):
        run_graph(graph, context.root, input_data, allowed_permissions=[])
