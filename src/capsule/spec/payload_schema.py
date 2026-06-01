from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator, SchemaError, ValidationError


class PayloadSchemaError(ValueError):
    """Raised when a payload does not satisfy a Capsule-declared JSON Schema."""


def schema_definition_errors(schema: dict[str, Any] | None, label: str) -> list[str]:
    if schema is None:
        return []

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"{label} is not a valid JSON Schema: {exc.message}"]

    return []


def validate_payload(schema: dict[str, Any] | None, payload: Any, label: str) -> None:
    if schema is None:
        return

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=_error_sort_key)
    if errors:
        detail = "; ".join(_format_error(error) for error in errors[:3])
        raise PayloadSchemaError(f"{label} does not match declared schema: {detail}")


def _error_sort_key(error: ValidationError) -> tuple[list[str], str]:
    return ([str(part) for part in error.path], error.message)


def _format_error(error: ValidationError) -> str:
    path = ".".join(str(part) for part in error.path) or "$"
    return f"{path}: {error.message}"
