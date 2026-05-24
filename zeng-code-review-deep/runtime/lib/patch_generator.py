"""Generate auto-patches for MINIMAL_CHANGE and REMOVE_CODE strategies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.lib.fs import write_text


class PatchGenerator:
    """Generate unified diff patches for high-confidence fix tasks."""

    def generate(self, task: dict[str, Any], file_content: str) -> str | None:
        """Generate a patch diff for the given fix task.

        Returns None if the strategy is not supported or confidence is too low.
        """
        strategy = task.get("fix_strategy", "")
        if strategy not in {"MINIMAL_CHANGE", "REMOVE_CODE"}:
            return None

        # MVP: generate a minimal diff header + guidance comment.
        # Future: integrate with AST manipulation or LLM patch generation.
        file_path = task.get("file", "")
        line_range = task.get("line_range", [])
        if not line_range:
            return None

        start = line_range[0]
        end = line_range[-1] if len(line_range) > 1 else start

        patch_lines = [
            f"--- a/{file_path}",
            f"+++ b/{file_path}",
            f"@@ -{start},{end - start + 1} +{start},{end - start + 1} @@",
            f"# Fix task: {task.get('task_id', '')}",
            f"# Strategy: {strategy}",
            f"# Problem: {task.get('problem', '')}",
            f"# Guidance: {task.get('manual_guidance', 'See fix-tasks.json')}",
        ]

        return "\n".join(patch_lines)

    def write_patch(self, task: dict[str, Any], patch: str, batch_dir: Path) -> Path:
        """Write patch to auto-patches directory."""
        patches_dir = batch_dir / "auto-patches"
        patches_dir.mkdir(parents=True, exist_ok=True)
        patch_file = patches_dir / f"{task['task_id']}.diff"
        write_text(patch_file, patch)
        return patch_file
