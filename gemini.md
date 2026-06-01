# Gemini Development Rules for Capsule

This file defines the specific guidelines, validation checklists, and quality standards followed by the Gemini AI agent when contributing to the Capsule project. It extends the core rules defined in [codex.md](file:///Users/vdpm/Documents/codex-projects/Capsule/codex.md) and ensures that all AI-generated code is robust, production-ready, and perfectly integrated.

---

## 1. Code Quality & Style Standard
- **Automated Formatting**: Always format files using `ruff format`. No PR or commit should fail `ruff format --check .`.
- **Linting Compliance**: All Python code must pass `ruff check .` without warnings or errors.
- **Python Modernity**: Enforce Python 3.12+ features (such as PEP 695 type parameter syntax, modern type hints, pattern matching) where appropriate.

## 2. Rule Checklist Before Completing Any Task
Before declaring a task done or asking for user review, Gemini must execute and verify the following list:

- [ ] **Tests Pass**: Run `uv run pytest` and ensure that all 40+ tests pass with zero failures.
- [ ] **File Size Boundary**: Verify that no modified or new Python file exceeds **500 lines of code** (as per [codex.md](file:///Users/vdpm/Documents/codex-projects/Capsule/codex.md) rules).
- [ ] **Manifest Alignment**: Ensure that any new, renamed, or deleted file/folder is updated in [manifest.json](file:///Users/vdpm/Documents/codex-projects/Capsule/manifest.json).
- [ ] **No Placeholders**: Ensure that code is complete, self-contained, and contains no placeholder comments (`# TODO`, `pass` without implementation, etc.) unless representing explicitly deferred stubs.
- [ ] **Security Checks**: Run `uv run capsule scan` on all modified examples or codebases to guarantee that static scans do not trigger unexpected security flags.

## 3. Manifest Integrity
- Whenever a file is added, modified in purpose, or deleted, update [manifest.json](file:///Users/vdpm/Documents/codex-projects/Capsule/manifest.json).
- Ensure that the description and purpose match the implementation.

## 4. Test Parity & Coverage
- Ensure regression tests cover new flags, schemas, or routing paths.
- Run tests in the default dev environment using `uv run pytest` or `.venv/bin/pytest`.
