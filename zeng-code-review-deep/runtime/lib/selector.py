"""Agent selector based on hard-coded rules (MVP)."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import yaml


class AgentSelector:
    """Select agents to activate based on diff content and file types."""

    def __init__(self, rules_path: Path) -> None:
        self.rules_path = rules_path
        self.rules: dict[str, Any] = {}
        if rules_path.exists():
            self.rules = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}

    def select(
        self,
        changed_files: list[str],
        diff_content: str,
        pr_metadata: dict[str, Any] | None = None,
        frz_exists: bool = False,
    ) -> dict[str, Any]:
        """Return selected agents based on input signals."""
        core = list(self.rules.get("core_agents", []))
        language = []
        specialist = []

        # Language experts
        for expert in self.rules.get("language_experts", []):
            suffixes = expert.get("trigger", {}).get("file_suffix", [])
            if any(f.endswith(tuple(suffixes)) for f in changed_files):
                language.append(expert["agent_id"])

        # Specialist agents
        for spec in self.rules.get("specialist_agents", []):
            if self._match_specialist(spec, changed_files, diff_content, pr_metadata, frz_exists):
                specialist.append(spec["agent_id"])

        max_agents = self.rules.get("max_agents", 10)
        total = core + language + specialist
        if len(total) > max_agents:
            # Priority: core > language > specialist
            total = core + language
            remaining = max_agents - len(total)
            if remaining > 0:
                total += specialist[:remaining]

        return {
            "core_agents": core,
            "language_experts": language,
            "specialist_agents": specialist,
            "selected": total,
            "moderator": self.rules.get("moderator", "moderator"),
        }

    def _match_specialist(
        self,
        spec: dict[str, Any],
        changed_files: list[str],
        diff_content: str,
        pr_metadata: dict[str, Any] | None,
        frz_exists: bool,
    ) -> bool:
        trigger = spec.get("trigger", {})

        # FRZ-based trigger
        if trigger.get("frz_exists") and not frz_exists:
            return False

        # File pattern trigger
        patterns = trigger.get("file_patterns", [])
        if patterns and not any(
            fnmatch.fnmatch(f, p) or fnmatch.fnmatch(f, "*/" + p)
            for f in changed_files for p in patterns
        ):
            return False

        # File suffix trigger
        suffixes = trigger.get("file_suffix", [])
        if suffixes and not any(f.endswith(tuple(suffixes)) for f in changed_files):
            return False

        # Diff keyword trigger
        keywords = trigger.get("diff_keywords", [])
        if keywords and not any(kw.lower() in diff_content.lower() for kw in keywords):
            return False

        # PR metadata trigger
        meta_keywords = trigger.get("pr_metadata_keywords", [])
        if meta_keywords and pr_metadata:
            pr_text = " ".join(str(v) for v in pr_metadata.values()).lower()
            if not any(kw.lower() in pr_text for kw in meta_keywords):
                return False

        return True
