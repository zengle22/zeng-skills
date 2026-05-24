"""Filesystem helpers for the CLI runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# enum_guard not needed for review runtime
from runtime.lib.errors import CommandError


def resolve_workspace_root(request_root: str | None, arg_root: str | None, request_path: Path) -> Path:
    root_value = arg_root or request_root or str(request_path.parent)
    return Path(root_value).resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CommandError("INVALID_REQUEST", f"request file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CommandError("INVALID_REQUEST", f"invalid json file: {path}", [str(exc)]) from exc


def _is_ssot_path(path: Path) -> bool:
    """Return True if path is an SSOT path (not FRZ)."""
    parts = path.resolve().parts
    return "ssot" in parts and "frz" not in parts


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CommandError("PRECONDITION_FAILED", f"content file not found: {path}") from exc


def write_text(path: Path, text: str, mode: str = "w") -> None:
    ensure_parent(path)
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(text)


def to_canonical_path(path: Path, workspace_root: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def canonical_to_path(canonical_path: str, workspace_root: Path) -> Path:
    path = Path(canonical_path)
    return path if path.is_absolute() else (workspace_root / path)

