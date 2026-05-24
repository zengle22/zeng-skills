"""Parse git diff, PR descriptions, file contexts, and FRZ packages."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from runtime.lib.errors import CommandError, ensure


class InputParser:
    """Collect input snapshots for deep code review."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def capture_diff(self, ref: str, base_ref: str | None = None) -> str:
        """Capture git diff for the given ref or base..head range."""
        if base_ref:
            range_spec = f"{base_ref}...{ref}"
        else:
            range_spec = ref

        try:
            result = subprocess.run(
                ["git", "diff", range_spec],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as exc:
            raise CommandError(
                "INVALID_REQUEST",
                f"git diff failed for {range_spec}",
                diagnostics=[exc.stderr or ""],
            ) from exc
        except FileNotFoundError as exc:
            raise CommandError("INVALID_REQUEST", "git not found in PATH") from exc

    def capture_changed_files(self, ref: str, base_ref: str | None = None) -> list[str]:
        """Return list of changed file paths (relative to repo root)."""
        if base_ref:
            range_spec = f"{base_ref}...{ref}"
        else:
            range_spec = ref

        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", range_spec],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except subprocess.CalledProcessError:
            return []

    def read_file_context(self, relative_path: str) -> str:
        """Read a file from workspace for context."""
        path = self.workspace_root / relative_path
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def build_context_map(self, changed_files: list[str], max_files: int = 10) -> dict[str, str]:
        """Build a map of file path -> content for relevant files."""
        context: dict[str, str] = {}
        for f in changed_files[:max_files]:
            content = self.read_file_context(f)
            if content:
                context[f] = content
        return context

    def write_snapshot(self, artifact_manager: Any, diff: str, pr_desc: str | None = None) -> None:
        """Persist input snapshot to the batch directory."""
        artifact_manager.write_text_artifact("input-snapshot/diff.patch", diff)
        if pr_desc:
            artifact_manager.write_text_artifact("input-snapshot/pr-description.md", pr_desc)


def validate_mode_args(mode: str, payload: dict[str, Any]) -> tuple[str, str | None]:
    """Validate arguments for the given mode and return (ref, base_ref)."""
    if mode == "commit":
        ref = str(payload.get("ref") or "HEAD~1").strip()
        return ref, None
    if mode == "pr":
        base = str(payload.get("base") or "main").strip()
        head = str(payload.get("head") or "").strip()
        ensure(head, "INVALID_REQUEST", "pr mode requires --head")
        return head, base
    if mode == "module":
        path = str(payload.get("path") or "").strip()
        ensure(path, "INVALID_REQUEST", "module mode requires --path")
        return path, None
    if mode == "frz":
        frz_ref = str(payload.get("frz_ref") or "").strip()
        path = str(payload.get("path") or "").strip()
        ensure(frz_ref, "INVALID_REQUEST", "frz mode requires --frz-ref")
        ensure(path, "INVALID_REQUEST", "frz mode requires --path")
        return path, frz_ref
    raise CommandError("INVALID_REQUEST", f"unsupported mode: {mode}")
