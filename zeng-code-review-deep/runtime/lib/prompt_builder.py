"""Assemble standard prompts for review agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PromptBuilder:
    """Build agent prompts from templates, rubric, and input content."""

    def __init__(self, skill_dir: Path) -> None:
        self.skill_dir = skill_dir
        self.agents_dir = skill_dir / "agents"

    def build_prompt(
        self,
        agent_id: str,
        batch_id: str,
        diff_content: str,
        context_files: dict[str, str] | None = None,
        frz_content: str | None = None,
    ) -> str:
        """Assemble a complete prompt for the specified agent."""
        agent_md = self.agents_dir / f"{agent_id}.md"
        agent_text = agent_md.read_text(encoding="utf-8") if agent_md.exists() else ""

        rubric_md = self.skill_dir / "code-review-rubric.md"
        rubric_text = rubric_md.read_text(encoding="utf-8") if rubric_md.exists() else ""

        parts = [
            agent_text,
            "",
            "【待审查代码变更】",
            "---",
            diff_content,
            "---",
        ]

        if context_files:
            parts.append("")
            parts.append("【完整文件上下文】")
            for path, content in context_files.items():
                parts.append(f"### {path}")
                parts.append("```")
                parts.append(content)
                parts.append("```")

        if frz_content:
            parts.append("")
            parts.append("【FRZ 对照文档】")
            parts.append(frz_content)

        if rubric_text:
            parts.append("")
            parts.append("【固定 Rubric】")
            parts.append(rubric_text)

        parts.append("")
        parts.append("【批次信息】")
        parts.append(f"batch_id: {batch_id}")
        parts.append("")
        parts.append("请严格按上述格式输出 JSON 数组。")

        return "\n".join(parts)

    def build_moderator_prompt(
        self,
        batch_id: str,
        reviews: list[dict[str, Any]],
    ) -> str:
        """Assemble moderator merge prompt from collected reviews."""
        moderator_md = self.agents_dir / "moderator.md"
        moderator_text = moderator_md.read_text(encoding="utf-8") if moderator_md.exists() else ""

        parts = [
            moderator_text,
            "",
            f"【批次信息】\nbatch_id: {batch_id}",
            "",
            "【各 Agent 审查结果】",
        ]

        for review in reviews:
            agent_id = review.get("agent_id", "unknown")
            issues = review.get("issues", [])
            parts.append(f"\n### Agent: {agent_id} ({len(issues)} issues)")
            parts.append("```json")
            parts.append(json.dumps(issues, ensure_ascii=False, indent=2))
            parts.append("```")

        parts.append("")
        parts.append("请输出 consolidated-review.json 和 review-conflicts.json 的完整 JSON 对象。")

        return "\n".join(parts)
