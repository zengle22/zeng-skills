"""Generate fix-tasks.json from review-consensus."""

from __future__ import annotations

import copy
import datetime
from typing import Any

from runtime.lib.fix_strategies import classify_strategy


def generate_fix_tasks(batch_id: str, consensus: dict[str, Any]) -> dict[str, Any]:
    """Create fix-tasks.json from consensus issues.

    Only P0/P1 issues generate fix-tasks. P2/P3 are recorded but
    marked DEFERRED unless explicitly flagged for cleanup.
    """
    issues = copy.deepcopy(consensus.get("issues", []))
    tasks: list[dict[str, Any]] = []
    seq = 1

    for issue in issues:
        sev = issue.get("severity", "P3")
        if sev not in {"P0", "P1", "P2"}:
            continue

        strategy = classify_strategy(sev, issue.get("dimension", ""), issue.get("description", ""))
        task = {
            "task_id": f"{batch_id}-fix-{seq:03d}",
            "issue_id": issue.get("issue_id", ""),
            "severity": sev,
            "status": "PENDING",
            "file": issue.get("file", ""),
            "line_range": issue.get("line_range", []),
            "dimension": issue.get("dimension", ""),
            "problem": issue.get("description", ""),
            "fix_strategy": strategy.value,
            "auto_patch": {
                "available": False,
                "patch_ref": "",
                "confidence": "low",
                "affected_tests": [],
                "risk_assessment": "无副作用",
            },
            "manual_guidance": "",
            "verification_command": "",
            "estimated_effort": "M" if sev == "P0" else "S",
        }
        tasks.append(task)
        seq += 1

    summary = {"total": len(tasks), "P0": 0, "P1": 0, "P2": 0}
    for task in tasks:
        s = task.get("severity", "P2")
        if s in summary:
            summary[s] = summary.get(s, 0) + 1

    return {
        "batch_id": batch_id,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "tasks": tasks,
        "summary": summary,
    }
