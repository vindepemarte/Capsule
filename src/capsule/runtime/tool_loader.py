from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from capsule.spec.paths import parse_python_entrypoint


class ToolLoadError(RuntimeError):
    """Raised when a Python tool cannot be loaded or called."""


def load_python_tool(root: Path, entrypoint: str) -> Callable[..., Any]:
    parsed = parse_python_entrypoint(root, entrypoint)
    module = _load_module(parsed.file)
    try:
        tool = getattr(module, parsed.function)
    except AttributeError as exc:
        raise ToolLoadError(
            f"Tool function '{parsed.function}' not found in {parsed.file}"
        ) from exc
    if not callable(tool):
        raise ToolLoadError(f"Tool entrypoint '{entrypoint}' is not callable")
    return tool


def call_tool(tool: Callable[..., Any], state: dict[str, Any]) -> Any:
    signature = inspect.signature(tool)
    parameters = list(signature.parameters.values())
    if not parameters:
        return tool()
    if len(parameters) == 1:
        return tool(state)

    kwargs = {
        parameter.name: state[parameter.name] for parameter in parameters if parameter.name in state
    }
    return tool(**kwargs)


def _load_module(path: Path) -> ModuleType:
    module_name = f"_capsule_tool_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ToolLoadError(f"Cannot load Python module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
