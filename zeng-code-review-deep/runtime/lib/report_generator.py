"""Generate human-readable final-report.md from consensus and fix-tasks."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from runtime.lib.fs import write_text


def generate_report(
    batch_id: str,
    mode: str,
    ref: str,
    base_ref: str | None,
    consensus: dict[str, Any],
    fix_tasks: dict[str, Any],
    role_panel: dict[str, Any],
    output_path: Path,
) -> None:
    """Render final-report.md from structured data."""
    summary = consensus.get("summary", {})
    issues = consensus.get("issues", [])
    tasks = fix_tasks.get("tasks", [])
    agents = role_panel.get("selected_agents", [])

    lines = [
        f"# Deep Code Review Report — {batch_id}",
        "",
        "## 执行摘要",
        "",
        f"- **审查模式**: {mode}",
        f"- **审查范围**: {ref}",
        f"- **Base Ref**: {base_ref or 'N/A'}",
        f"- **生成时间**: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"- **参与 Agent**: {', '.join(a['agent_id'] for a in agents)}",
        f"- **发现问题总数**: {summary.get('total', 0)}",
        f"- **P0 (阻塞)**: {summary.get('P0', 0)} | **P1 (高风险)**: {summary.get('P1', 0)} | **P2 (中风险)**: {summary.get('P2', 0)} | **P3 (低风险)**: {summary.get('P3', 0)}",
        "",
        "## 按 Severity 汇总",
        "",
    ]

    for sev in ("P0", "P1", "P2", "P3"):
        sev_issues = [i for i in issues if i.get("severity") == sev]
        if not sev_issues:
            continue
        lines.append(f"### {sev}")
        lines.append("")
        lines.append("| 文件 | 行号 | 维度 | 问题描述 | 发现者 |")
        lines.append("|------|------|------|---------|--------|")
        for issue in sev_issues:
            line_range = issue.get("line_range", [])
            line_str = f"{line_range[0]}" if len(line_range) == 1 else f"{line_range[0]}-{line_range[-1]}"
            found_by = ", ".join(issue.get("found_by", []))
            desc = issue.get("description", "").replace("|", "\\|")
            lines.append(
                f"| `{issue.get('file', '')}` | {line_str} | {issue.get('dimension', '')} | {desc} | {found_by} |"
            )
        lines.append("")

    lines.append("## 按文件汇总")
    lines.append("")
    file_map: dict[str, list[dict[str, Any]]] = {}
    for issue in issues:
        file_map.setdefault(issue.get("file", ""), []).append(issue)
    for file_path in sorted(file_map):
        if not file_path:
            continue
        lines.append(f"### `{file_path}`")
        for issue in file_map[file_path]:
            line_range = issue.get("line_range", [])
            line_str = f"{line_range[0]}" if len(line_range) == 1 else f"{line_range[0]}-{line_range[-1]}"
            lines.append(f"- **[{issue.get('severity')}]** {issue.get('description')} (`{line_str}`)")
        lines.append("")

    if tasks:
        lines.append("## 修复任务清单")
        lines.append("")
        lines.append("| 任务 ID | 对应 Issue | 策略 | 预估工时 | 状态 |")
        lines.append("|---------|-----------|------|---------|------|")
        for task in tasks:
            lines.append(
                f"| {task.get('task_id', '')} | {task.get('issue_id', '')} | "
                f"{task.get('fix_strategy', '')} | {task.get('estimated_effort', '')} | {task.get('status', '')} |"
            )
        lines.append("")

    lines.append("## 产物清单")
    lines.append("")
    lines.append(f"- **batch-state**: `{batch_id}/batch-state.json`")
    lines.append(f"- **role-panel**: `{batch_id}/role-panel.json`")
    lines.append(f"- **review-consensus**: `{batch_id}/review-consensus.json`")
    lines.append(f"- **fix-tasks**: `{batch_id}/fix-tasks.json`")
    lines.append(f"- **final-report**: `{batch_id}/final-report.md`")
    lines.append("")

    write_text(output_path, "\n".join(lines))
