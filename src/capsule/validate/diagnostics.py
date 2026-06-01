from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    path: str | None = None

    def format(self) -> str:
        location = f" [{self.path}]" if self.path else ""
        return f"{self.code}{location}: {self.message}"


@dataclass
class ValidationReport:
    errors: list[Diagnostic] = field(default_factory=list)
    warnings: list[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, code: str, message: str, path: str | None = None) -> None:
        self.errors.append(Diagnostic(code=code, message=message, path=path))

    def add_warning(self, code: str, message: str, path: str | None = None) -> None:
        self.warnings.append(Diagnostic(code=code, message=message, path=path))
