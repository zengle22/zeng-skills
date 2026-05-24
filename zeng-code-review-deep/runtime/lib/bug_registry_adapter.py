"""Adapter to export P0 issues to ADR-055 bug-registry.yaml format.

ADR-055 may not be finalized; this module provides:
1. Internal format (always stable)
2. Optional ADR-055-compatible export when schema is available
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.lib.fs import write_json


ADR055_SCHEMA_VERSION = "0.1-preview"


def export_to_bug_registry(
    fix_tasks: dict[str, Any],
    output_path: Path,
    *,
    adr055_mode: bool = False,
) -> dict[str, Any]:
    """Export P0 fix-tasks as bug registry entries.

    Args:
        fix_tasks: fix-tasks.json content
        output_path: where to write the registry
        adr055_mode: if True, attempt ADR-055 compatible format;
                     otherwise use internal stable format
    """
    p0_tasks = [t for t in fix_tasks.get("tasks", []) if t.get("severity") == "P0"]

    if adr055_mode:
        payload = _to_adr055(p0_tasks, fix_tasks.get("batch_id", ""))
    else:
        payload = _to_internal(p0_tasks, fix_tasks.get("batch_id", ""))

    write_json(output_path, payload)
    return payload


def _to_internal(tasks: list[dict[str, Any]], batch_id: str) -> dict[str, Any]:
    return {
        "format": "ll-code-review-deep-internal",
        "version": "1.0",
        "batch_id": batch_id,
        "entries": [
            {
                "bug_id": f"{batch_id}-bug-{idx+1:03d}",
                "source_task_id": task.get("task_id"),
                "source_issue_id": task.get("issue_id"),
                "file": task.get("file"),
                "line_range": task.get("line_range"),
                "severity": task.get("severity"),
                "description": task.get("problem"),
                "status": "OPEN",
                "strategy": task.get("fix_strategy"),
            }
            for idx, task in enumerate(tasks)
        ],
    }


def _to_adr055(tasks: list[dict[str, Any]], batch_id: str) -> dict[str, Any]:
    # TODO: update this when ADR-055 schema is finalized
    return {
        "schema_version": ADR055_SCHEMA_VERSION,
        "registry_id": f"bug-reg-{batch_id}",
        "entries": [
            {
                "id": f"{batch_id}-bug-{idx+1:03d}",
                "severity": task.get("severity"),
                "component": task.get("file", "").split("/")[0] if task.get("file") else "unknown",
                "description": task.get("problem"),
                "status": "open",
                "source_ref": task.get("issue_id"),
            }
            for idx, task in enumerate(tasks)
        ],
    }
