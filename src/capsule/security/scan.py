from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from capsule.spec.loader import ProjectContext
from capsule.spec.paths import CapsulePathError, parse_python_entrypoint


RISKY_PERMISSION_KEYWORDS = {
    "write": "can modify external or workflow state",
    "delete": "can remove data",
    "admin": "may imply privileged access",
    "secret": "may access secrets",
    "network": "may call external services",
    "shell": "may execute shell commands",
    "exec": "may execute code or commands",
    "file": "may access local files",
}

RISKY_IMPORTS = {
    "subprocess": ("high", "can execute external commands"),
    "socket": ("medium", "can open network connections"),
    "requests": ("medium", "can call external HTTP services"),
    "httpx": ("medium", "can call external HTTP services"),
    "urllib": ("medium", "can call external HTTP services"),
    "shutil": ("medium", "can mutate files and directories"),
}

RISKY_CALLS = {
    "eval": ("high", "can execute dynamic Python expressions"),
    "exec": ("high", "can execute dynamic Python code"),
    "open": ("medium", "can read or write local files"),
}


@dataclass(frozen=True)
class SecurityFinding:
    code: str
    severity: str
    message: str
    path: str | None = None

    def format(self) -> str:
        location = f" [{self.path}]" if self.path else ""
        return f"{self.severity.upper()} {self.code}{location}: {self.message}"


def scan_project(context: ProjectContext) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    for tool_name, tool in context.manifest.tools.items():
        findings.extend(_scan_permission(tool_name, tool.permission))
        if tool.type == "mcp":
            findings.append(
                SecurityFinding(
                    code="mcp_tool_declared",
                    severity="medium",
                    message=(
                        f"Tool '{tool_name}' declares MCP server '{tool.server}' and "
                        "requires explicit trust before real execution."
                    ),
                    path=f"tools.{tool_name}",
                )
            )
            continue
        try:
            entrypoint = parse_python_entrypoint(context.root, tool.entrypoint or "")
        except CapsulePathError:
            continue
        if entrypoint.file.exists():
            findings.extend(_scan_tool_source(tool_name, entrypoint.file, tool.entrypoint))
    return findings


def _scan_permission(tool_name: str, permission: str) -> list[SecurityFinding]:
    permission_lower = permission.lower()
    findings = []
    for keyword, reason in RISKY_PERMISSION_KEYWORDS.items():
        if keyword in permission_lower:
            findings.append(
                SecurityFinding(
                    code="risky_permission",
                    severity="medium",
                    message=f"Tool '{tool_name}' declares permission '{permission}', which {reason}.",
                    path=f"tools.{tool_name}.permission",
                )
            )
            break
    return findings


def _scan_tool_source(tool_name: str, path: Path, entrypoint: str) -> list[SecurityFinding]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [
            SecurityFinding(
                code="tool_syntax_unscanned",
                severity="medium",
                message=f"Tool '{tool_name}' could not be security scanned because Python parsing failed: {exc}",
                path=entrypoint,
            )
        ]

    findings: list[SecurityFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            findings.extend(
                _scan_imports(tool_name, entrypoint, [alias.name for alias in node.names])
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            findings.extend(_scan_imports(tool_name, entrypoint, [node.module]))
        elif isinstance(node, ast.Call):
            finding = _scan_call(tool_name, entrypoint, node)
            if finding:
                findings.append(finding)
        elif _is_environment_access(node):
            findings.append(
                SecurityFinding(
                    code="environment_access",
                    severity="medium",
                    message=f"Tool '{tool_name}' reads environment variables; secrets should be explicit.",
                    path=entrypoint,
                )
            )
    return _dedupe(findings)


def _scan_imports(tool_name: str, entrypoint: str, imports) -> list[SecurityFinding]:
    findings = []
    for imported in imports:
        root = imported.split(".", 1)[0]
        if root in RISKY_IMPORTS:
            severity, reason = RISKY_IMPORTS[root]
            findings.append(
                SecurityFinding(
                    code="risky_import",
                    severity=severity,
                    message=f"Tool '{tool_name}' imports '{root}', which {reason}.",
                    path=entrypoint,
                )
            )
    return findings


def _scan_call(tool_name: str, entrypoint: str, node: ast.Call) -> SecurityFinding | None:
    name = _call_name(node)
    if name in RISKY_CALLS:
        severity, reason = RISKY_CALLS[name]
        return SecurityFinding(
            code="risky_call",
            severity=severity,
            message=f"Tool '{tool_name}' calls '{name}', which {reason}.",
            path=entrypoint,
        )
    if name in {"getenv", "os.getenv"}:
        return SecurityFinding(
            code="environment_access",
            severity="medium",
            message=f"Tool '{tool_name}' reads environment variables; secrets should be explicit.",
            path=entrypoint,
        )
    return None


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parent = node.func.value
        if isinstance(parent, ast.Name):
            return f"{parent.id}.{node.func.attr}"
        return node.func.attr
    return None


def _is_environment_access(node: ast.AST) -> bool:
    if not isinstance(node, ast.Attribute) or node.attr != "environ":
        return False
    return isinstance(node.value, ast.Name) and node.value.id == "os"


def _dedupe(findings: list[SecurityFinding]) -> list[SecurityFinding]:
    seen = set()
    unique = []
    for finding in findings:
        key = (finding.code, finding.severity, finding.message, finding.path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique
