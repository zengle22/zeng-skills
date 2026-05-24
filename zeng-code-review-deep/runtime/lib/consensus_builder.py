"""Build consensus list from consolidated review (MVP: pass-through with renumbering)."""

from __future__ import annotations

import copy
import datetime
from typing import Any


class ConsensusBuilder:
    """Transform consolidated review into the authoritative consensus document."""

    def build(self, batch_id: str, consolidated: dict[str, Any]) -> dict[str, Any]:
        """Build review-consensus.json from consolidated-review.json.

        In MVP, this is mostly a pass-through with sequential renumbering.
        Future iterations will apply conflict arbitration results and human decisions.
        """
        # Deep-copy to avoid mutating the consolidated dict passed by caller
        issues = copy.deepcopy(consolidated.get("issues", []))

        # Renumber consensus IDs sequentially
        for idx, issue in enumerate(issues, start=1):
            issue["issue_id"] = f"{batch_id}-consensus-{issue.get('severity', 'P3')}-{idx:03d}"

        summary = {"total": len(issues), "P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for issue in issues:
            sev = issue.get("severity", "P3")
            if sev in summary:
                summary[sev] = summary.get(sev, 0) + 1

        return {
            "batch_id": batch_id,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "issues": issues,
            "summary": summary,
        }
