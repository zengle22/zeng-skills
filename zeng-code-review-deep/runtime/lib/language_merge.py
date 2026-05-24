"""Language expert merge rules: bump severity when both language and business dims agree."""

from __future__ import annotations

from typing import Any


class LanguageMerge:
    """Adjust consensus severity when language experts and business reviewers
    both identify the same issue.
    """

    SEVERITY_ORDER = ["P0", "P1", "P2", "P3"]

    def apply(
        self,
        consensus: dict[str, Any],
        language_reviews: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Bump severity by one level (capped at P0) for issues found by
        both a language expert and a business dimension agent.
        """
        issues = list(consensus.get("issues", []))

        # Build a lookup of language issues by (file, line_start, dimension_keyword)
        lang_issues: list[dict[str, Any]] = []
        for review in language_reviews:
            lang_issues.extend(review.get("issues", []))

        for issue in issues:
            found_by = issue.get("found_by", [])
            has_lang_expert = any(
                agent in found_by for agent in ("ts-expert", "python-expert", "go-expert")
            )
            has_business = any(
                agent in found_by
                for agent in (
                    "consistency-hunter", "standards-guardian", "logic-verifier",
                    "data-architect", "contract-guardian", "ai-code-inspector",
                    "requirement-aligner", "test-auditor",
                )
            )
            if has_lang_expert and has_business:
                current = issue.get("severity", "P3")
                new_sev = self._bump(current)
                if new_sev != current:
                    issue["severity"] = new_sev
                    issue["_bumped_by_language_expert"] = True

        # Recompute summary
        summary = {"total": len(issues), "P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for issue in issues:
            sev = issue.get("severity", "P3")
            if sev in summary:
                summary[sev] = summary.get(sev, 0) + 1

        consensus["issues"] = issues
        consensus["summary"] = summary
        return consensus

    def _bump(self, severity: str) -> str:
        idx = self.SEVERITY_ORDER.index(severity)
        if idx == 0:
            return severity  # Already P0, can't go higher
        return self.SEVERITY_ORDER[idx - 1]
