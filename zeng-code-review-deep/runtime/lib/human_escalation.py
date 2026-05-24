"""Human escalation for unresolved conflicts (AskUserQuestion pattern)."""

from __future__ import annotations

from typing import Any


class HumanEscalation:
    """Generate structured human escalation options when conflict arbitration
    fails after 2 rounds.
    """

    OPTIONS = {
        "A": {"label": "采纳 P0", "severity": "P0"},
        "B": {"label": "采纳 P1", "severity": "P1"},
        "C": {"label": "采纳 P2", "severity": "P2"},
        "D": {"label": "采纳 P3", "severity": "P3"},
        "E": {"label": "标记为\"非问题\"", "severity": "none"},
        "F": {"label": "标记为\"需更多信息\"", "severity": "pending"},
    }

    def build_question(self, conflict: dict[str, Any]) -> dict[str, Any]:
        """Build a structured AskUserQuestion payload."""
        dispute = conflict.get("severity_dispute", {})
        agents = ", ".join(f"{agent}={sev}" for agent, sev in dispute.items())

        return {
            "type": "human_escalation",
            "conflict_id": conflict.get("conflict_id", ""),
            "file": conflict.get("file", ""),
            "line_range": conflict.get("line_range", []),
            "dimension": conflict.get("dimension", ""),
            "question": f"Agent 间对以下问题的 severity 存在分歧（{agents}），2 轮讨论未达成一致。请选择裁决：",
            "options": {
                k: v["label"]
                for k, v in self.OPTIONS.items()
            },
            "default": "F",
            "timeout_seconds": 300,
        }

    def resolve(self, conflict: dict[str, Any], choice: str) -> dict[str, Any]:
        """Apply human decision to conflict."""
        option = self.OPTIONS.get(choice.upper())
        if not option:
            option = self.OPTIONS["F"]

        return {
            "conflict_id": conflict.get("conflict_id", ""),
            "status": "human_decided",
            "resolution": {
                "severity": option["severity"],
                "reason": f"人工选择: {option['label']}",
            },
        }
