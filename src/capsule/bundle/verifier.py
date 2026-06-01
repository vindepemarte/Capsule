from __future__ import annotations

import hashlib
import zipfile
from pathlib import PurePosixPath
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from capsule.spec.models import CapsuleManifest


class BundleVerificationReport(BaseModel):
    ok: bool
    bundle: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checked_files: list[str] = Field(default_factory=list)


def verify_bundle(path) -> BundleVerificationReport:
    errors: list[str] = []
    warnings: list[str] = []
    checked_files: list[str] = []

    if not zipfile.is_zipfile(path):
        return BundleVerificationReport(
            ok=False,
            bundle=str(path),
            errors=[f"Bundle is not a valid zip archive: {path}"],
        )

    with zipfile.ZipFile(path) as archive:
        names = sorted(archive.namelist())
        errors.extend(_unsafe_archive_names(names))

        manifest_data = _read_yaml(archive, "capsule.yaml", errors)
        lock_data = _read_yaml(archive, "capsule.lock", errors)

        manifest = _parse_manifest(manifest_data, errors)
        if manifest and lock_data:
            _verify_identity(manifest, lock_data, errors)
            _verify_schemas(manifest, lock_data, errors)
            _verify_tool_metadata(manifest, lock_data, errors)
            _verify_assets(archive, manifest, lock_data, errors, warnings, checked_files)

        for required in ("capsule.bundle.json", "capsule.yaml", "capsule.lock"):
            if required not in names:
                errors.append(f"Missing required bundle file: {required}")

    return BundleVerificationReport(
        ok=not errors,
        bundle=str(path),
        errors=errors,
        warnings=warnings,
        checked_files=sorted(checked_files),
    )


def _unsafe_archive_names(names: list[str]) -> list[str]:
    errors = []
    for name in names:
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts:
            errors.append(f"Unsafe archive path: {name}")
    return errors


def _read_yaml(archive: zipfile.ZipFile, name: str, errors: list[str]) -> dict[str, Any]:
    if name not in archive.namelist():
        return {}
    try:
        data = yaml.safe_load(archive.read(name).decode("utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"Invalid YAML in {name}: {exc}")
        return {}
    return data if isinstance(data, dict) else {}


def _parse_manifest(data: dict[str, Any], errors: list[str]) -> CapsuleManifest | None:
    if not data:
        return None
    try:
        return CapsuleManifest.model_validate(data)
    except ValidationError as exc:
        errors.append(f"Invalid capsule.yaml in bundle: {exc}")
        return None


def _verify_identity(
    manifest: CapsuleManifest,
    lock_data: dict[str, Any],
    errors: list[str],
) -> None:
    if lock_data.get("name") != manifest.name:
        errors.append("capsule.lock name does not match capsule.yaml")
    if lock_data.get("version") != manifest.version:
        errors.append("capsule.lock version does not match capsule.yaml")
    if not lock_data.get("specVersion"):
        errors.append("capsule.lock is missing specVersion")


def _verify_schemas(
    manifest: CapsuleManifest,
    lock_data: dict[str, Any],
    errors: list[str],
) -> None:
    schemas = lock_data.get("schemas")
    if not isinstance(schemas, dict):
        errors.append("capsule.lock is missing schemas metadata")
        return
    if schemas.get("input") != manifest.input_schema:
        errors.append("capsule.lock input schema does not match capsule.yaml")
    if schemas.get("output") != manifest.output_schema:
        errors.append("capsule.lock output schema does not match capsule.yaml")


def _verify_assets(
    archive: zipfile.ZipFile,
    manifest: CapsuleManifest,
    lock_data: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    checked_files: list[str],
) -> None:
    _verify_prompt_hashes(archive, manifest, lock_data, errors, warnings, checked_files)
    _verify_tool_hashes(archive, manifest, lock_data, errors, warnings, checked_files)
    _verify_test_hashes(archive, manifest, lock_data, errors, warnings, checked_files)


def _verify_tool_metadata(
    manifest: CapsuleManifest,
    lock_data: dict[str, Any],
    errors: list[str],
) -> None:
    metadata = lock_data.get("toolMetadata")
    if not isinstance(metadata, dict):
        errors.append("capsule.lock is missing toolMetadata")
        return
    for tool_name, tool in manifest.tools.items():
        if metadata.get(tool_name) != tool.model_dump(mode="json"):
            errors.append(f"capsule.lock metadata does not match tool '{tool_name}'")


def _verify_prompt_hashes(
    archive: zipfile.ZipFile,
    manifest: CapsuleManifest,
    lock_data: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    checked_files: list[str],
) -> None:
    prompt_hashes = lock_data.get("prompts", {})
    for agent_name, agent in manifest.agents.items():
        expected_hash = prompt_hashes.get(agent_name)
        _verify_hash(
            archive,
            agent.prompt,
            expected_hash,
            f"prompt for agent '{agent_name}'",
            errors,
            warnings,
            checked_files,
        )


def _verify_tool_hashes(
    archive: zipfile.ZipFile,
    manifest: CapsuleManifest,
    lock_data: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    checked_files: list[str],
) -> None:
    tool_hashes = lock_data.get("tools", {})
    for tool_name, tool in manifest.tools.items():
        if tool.type != "python":
            continue
        tool_path = (tool.entrypoint or "").split(":", 1)[0]
        expected_hash = tool_hashes.get(tool_name)
        _verify_hash(
            archive,
            tool_path,
            expected_hash,
            f"tool '{tool_name}'",
            errors,
            warnings,
            checked_files,
        )


def _verify_test_hashes(
    archive: zipfile.ZipFile,
    manifest: CapsuleManifest,
    lock_data: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    checked_files: list[str],
) -> None:
    test_hashes = lock_data.get("tests", {})
    for test_path in manifest.tests:
        expected_hash = test_hashes.get(test_path)
        _verify_hash(
            archive,
            test_path,
            expected_hash,
            f"test '{test_path}'",
            errors,
            warnings,
            checked_files,
        )


def _verify_hash(
    archive: zipfile.ZipFile,
    archive_path: str,
    expected_hash: str | None,
    label: str,
    errors: list[str],
    warnings: list[str],
    checked_files: list[str],
) -> None:
    if archive_path not in archive.namelist():
        errors.append(f"Missing {label}: {archive_path}")
        return
    if not expected_hash:
        warnings.append(f"No lockfile hash found for {label}")
        return

    actual_hash = hashlib.sha256(archive.read(archive_path)).hexdigest()
    checked_files.append(archive_path)
    if actual_hash != expected_hash:
        errors.append(f"Hash mismatch for {label}: {archive_path}")
