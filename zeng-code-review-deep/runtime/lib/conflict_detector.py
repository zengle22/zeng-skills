"""Enhanced conflict detection with severity dispute analysis."""

from __future__ import annotations

from typing import Any


class ConflictDetector:
    """Detect severity conflicts between agents on the same issue."""

    SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "none": 4}

    def detect(self, reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Scan all reviews and return conflict records where severity
        divergence meets the threshold (>= 2 levels or P0/P1 vs none).
        """
        # Group issues by dedup key
        groups: dict[str, list[dict[str, Any]]] = {}
        for review in reviews:
            agent_id = review.get("agent_id", "unknown")
            for issue in review.get("issues", []):
                key = self._dedup_key(issue)
                groups.setdefault(key, []).append({**issue, "_source_agent": agent_id})

        conflicts: list[dict[str, Any]] = []
        for key, group in groups.items():
            if len(group) < 2:
                continue
            conflict = self._analyze_group(key, group)
            if conflict:
                conflicts.append(conflict)
        return conflicts

    def _dedup_key(self, issue: dict[str, Any]) -> str:
        file_path = issue.get("file", "")
        line_range = issue.get("line_range", [0])
        start = line_range[0] if line_range else 0
        dimension = issue.get("dimension", "")
        return f"{file_path}::{start}::{dimension}"

    def _analyze_group(self, key: str, group: list[dict[str, Any]]) -> dict[str, Any] | None:
        severities = set()
        severity_dispute: dict[str, str] = {}
        issue_ids = []
        for issue in group:
            sev = issue.get("severity", "P3")
            agent = issue.get("_source_agent", "unknown")
            severities.add(sev)
            severity_dispute[agent] = sev
            if issue.get("issue_id"):
                issue_ids.append(issue["issue_id"])

        if len(severities) <= 1:
            return None

        nums = sorted(self.SEVERITY_ORDER.get(s, 99) for s in severities)
        span = nums[-1] - nums[0]

        # Must-discuss conditions
        must_discuss = span >= 2
        has_p0_or_p1_vs_none = any(
            s in {"P0", "P1"} for s in severities
        ) and "none" in severities

        if not must_discuss and not has_p0_or_p1_vs_none:
            # Adjacent levels: auto-resolve, no conflict record needed
            return None

        file_path = group[0].get("file", "")
        line_range = group[0].get("line_range", [0])
        dimension = group[0].get("dimension", "")

        return {
            "key": key,
            "file": file_path,
            "line_range": line_range,
            "dimension": dimension,
            "severity_dispute": severity_dispute,
            "span": span,
            "must_discuss": must_discuss or has_p0_or_p1_vs_none,
            "issue_ids": issue_ids,
        }
