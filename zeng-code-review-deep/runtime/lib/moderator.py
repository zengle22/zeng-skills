"""Moderator merge & deduplication logic (MVP simplified)."""

from __future__ import annotations

import datetime
from typing import Any


class Moderator:
    """Merge multiple agent reviews, deduplicate, and detect conflicts."""

    # Severity ordering for comparison
    SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "none": 4}

    def merge(self, batch_id: str, reviews: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge reviews into consolidated output + conflicts.

        Returns a dict with keys:
            - consolidated: dict matching consolidated-review structure
            - conflicts: dict matching review-conflicts structure
        """
        all_issues: list[dict[str, Any]] = []
        for review in reviews:
            issues = review.get("issues", [])
            agent_id = review.get("agent_id", "unknown")
            for issue in issues:
                issue = dict(issue)
                if agent_id not in issue.get("found_by", []):
                    issue.setdefault("found_by", []).append(agent_id)
                all_issues.append(issue)

        # Group by dedup key
        groups: dict[str, list[dict[str, Any]]] = {}
        for issue in all_issues:
            key = self._dedup_key(issue)
            groups.setdefault(key, []).append(issue)

        merged_issues: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        seq = 1
        conflict_seq = 1

        for key, group in groups.items():
            merged, conflict = self._merge_group(batch_id, group, seq, conflict_seq)
            merged_issues.append(merged)
            seq += 1
            if conflict:
                conflicts.append(conflict)
                conflict_seq += 1

        # Sort by severity then file
        merged_issues.sort(key=lambda i: (self.SEVERITY_ORDER.get(i.get("severity", "P3"), 99), i.get("file", "")))

        summary = {"total": len(merged_issues), "P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for issue in merged_issues:
            sev = issue.get("severity", "P3")
            if sev in summary:
                summary[sev] = summary.get(sev, 0) + 1

        consolidated = {
            "batch_id": batch_id,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "issues": merged_issues,
            "summary": summary,
        }

        conflicts_doc = {
            "batch_id": batch_id,
            "conflicts": conflicts,
        }

        return {"consolidated": consolidated, "conflicts": conflicts_doc}

    def _dedup_key(self, issue: dict[str, Any]) -> str:
        file_path = issue.get("file", "")
        line_range = issue.get("line_range", [0])
        start = line_range[0] if line_range else 0
        dimension = issue.get("dimension", "")
        return f"{file_path}::{start}::{dimension}"

    def _merge_group(
        self,
        batch_id: str,
        group: list[dict[str, Any]],
        seq: int,
        conflict_seq: int,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Merge a group of issues pointing to the same location/dimension."""
        # Severity: take highest
        severities = [i.get("severity", "P3") for i in group]
        best_sev = min(severities, key=lambda s: self.SEVERITY_ORDER.get(s, 99))

        # Evidence: longest
        best_evidence = max(group, key=lambda i: len(i.get("evidence", ""))).get("evidence", "")

        # Description: longest
        best_desc = max(group, key=lambda i: len(i.get("description", ""))).get("description", "")

        # found_by: union
        found_by: list[str] = []
        for issue in group:
            for agent in issue.get("found_by", []):
                if agent not in found_by:
                    found_by.append(agent)

        # confidence: highest
        confidence = "low"
        for issue in group:
            c = issue.get("confidence", "low")
            if c == "high" or (confidence == "low" and c == "medium"):
                confidence = c

        merged_from = [i.get("issue_id", "") for i in group if i.get("issue_id")]

        merged = {
            "issue_id": f"{batch_id}-consensus-{best_sev}-{seq:03d}",
            "severity": best_sev,
            "dimension": group[0].get("dimension", ""),
            "file": group[0].get("file", ""),
            "line_range": group[0].get("line_range", [0]),
            "evidence": best_evidence,
            "description": best_desc,
            "found_by": found_by,
            "confidence": confidence,
            "rubric_ref": group[0].get("rubric_ref", ""),
            "merged_from": merged_from,
        }

        # Conflict detection
        conflict = self._detect_conflict(batch_id, group, merged, conflict_seq)
        return merged, conflict

    def _detect_conflict(
        self,
        batch_id: str,
        group: list[dict[str, Any]],
        merged: dict[str, Any],
        conflict_seq: int,
    ) -> dict[str, Any] | None:
        """Detect if this group has severity disagreements requiring conflict record."""
        severities = set(i.get("severity", "P3") for i in group)
        if len(severities) <= 1:
            return None

        # Check severity span
        nums = sorted(self.SEVERITY_ORDER.get(s, 99) for s in severities)
        span = nums[-1] - nums[0]

        # In MVP: adjacent levels auto-resolve; record conflict only if span >= 2
        # Still record all conflicts for transparency, but mark auto_resolved for adjacent
        status = "auto_resolved" if span <= 1 else "auto_resolved"

        severity_dispute: dict[str, str] = {}
        for issue in group:
            for agent in issue.get("found_by", []):
                if agent not in severity_dispute:
                    severity_dispute[agent] = issue.get("severity", "P3")

        return {
            "conflict_id": f"{batch_id}-conflict-{conflict_seq:03d}",
            "issue_ids": [i.get("issue_id", "") for i in group],
            "file": merged["file"],
            "line_range": merged["line_range"],
            "dimension": merged["dimension"],
            "severity_dispute": severity_dispute,
            "status": status,
            "resolution": {
                "severity": merged["severity"],
                "reason": "MVP: Moderator auto-resolved to highest severity",
            },
            "rounds": 0,
        }
