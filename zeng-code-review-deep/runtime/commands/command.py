"""CLI handler for ll-code-review-deep (ADR-058 full delivery)."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

from runtime.lib.agent_runner import AgentRunner, MockAgentExecutor, PromptFileExecutor
from runtime.lib.artifact_manager import ArtifactManager, generate_batch_id
from runtime.lib.cleanup import cleanup_old_batches
from runtime.lib.consensus_builder import ConsensusBuilder
from runtime.lib.fix_task_generator import generate_fix_tasks
from runtime.lib.input_parser import InputParser, validate_mode_args
from runtime.lib.moderator import Moderator
from runtime.lib.prompt_builder import PromptBuilder
from runtime.lib.report_generator import generate_report
from runtime.lib.selector import AgentSelector
from runtime.lib.errors import CommandError, ensure
from runtime.lib.fs import canonical_to_path, to_canonical_path
from runtime.lib.protocol import CommandContext, run_with_protocol


def _run_review(ctx: CommandContext) -> tuple[str, str, dict[str, Any], list[str], list[str]]:
    payload = ctx.payload
    mode = str(payload.get("mode") or "commit").strip().lower()
    output_dir_raw = str(payload.get("output_dir") or ".cr-deep").strip()
    output_dir = canonical_to_path(output_dir_raw, ctx.workspace_root)

    ref, base_ref = validate_mode_args(mode, payload)

    # 1. Initialize artifacts
    batch_id = generate_batch_id()
    am = ArtifactManager(output_dir, batch_id, ctx.workspace_root)
    am.init_batch_dir(mode, ref, base_ref)

    # 2. Capture input
    parser = InputParser(ctx.workspace_root)
    diff = parser.capture_diff(ref, base_ref)
    changed_files = parser.capture_changed_files(ref, base_ref)
    context_map = parser.build_context_map(changed_files, max_files=10)
    pr_desc = payload.get("pr_description")
    if pr_desc:
        pr_desc = str(pr_desc)
    parser.write_snapshot(am, diff, pr_desc)

    am.update_state({"status": "reviewing"})

    # 3. Role selection (hard-coded rules, MVP)
    skill_dir = Path(__file__).parent.parent.parent
    selector = AgentSelector(skill_dir / "selector_rules.yaml")
    selection = selector.select(
        changed_files=changed_files,
        diff_content=diff,
        pr_metadata={"description": pr_desc} if pr_desc else None,
        frz_exists=bool(payload.get("frz_ref")),
    )
    selected_agents = selection["selected"]
    role_panel = {
        "batch_id": batch_id,
        "mode": mode,
        "selected_agents": [
            {"agent_id": a, "dimensions": [], "reason": "selector_rules.yaml"}
            for a in selected_agents
        ],
        "language_experts": selection.get("language_experts", []),
        "moderator": selection.get("moderator", "moderator"),
    }
    am.write_artifact("role-panel.json", role_panel)

    # 4. Agent review execution
    prompt_builder = PromptBuilder(skill_dir)

    jobs = [
        {
            "agent_id": agent_id,
            "batch_id": batch_id,
            "prompt": prompt_builder.build_prompt(
                agent_id=agent_id,
                batch_id=batch_id,
                diff_content=diff,
                context_files=context_map,
            ),
        }
        for agent_id in selected_agents
    ]

    # Write prompt files for outer-agent execution
    prompt_executor = PromptFileExecutor(am.batch_dir)
    for job in jobs:
        prompt_executor(job)

    use_mock = str(payload.get("mock") or "").lower() in {"1", "true", "yes"}

    am.set_agent_status("moderator", "pending")
    for agent_id in selected_agents:
        am.set_agent_status(agent_id, "running")

    reviews_for_moderator: list[dict[str, Any]] = []
    if use_mock:
        runner = AgentRunner(max_workers=4, timeout_seconds=120)
        run_results = runner.run(jobs, MockAgentExecutor(skill_dir))
        for result in run_results:
            agent_id = result["agent_id"]
            if result.get("status") == "completed":
                review_data = result.get("result", {})
                review_data["agent_id"] = agent_id
                am.write_artifact(f"reviews/{agent_id}-review.json", review_data)
                am.set_agent_status(agent_id, "completed", issues_count=review_data.get("summary", {}).get("total", 0))
                reviews_for_moderator.append(review_data)
            else:
                am.set_agent_status(agent_id, "failed", error=result.get("error", ""))
    else:
        for agent_id in selected_agents:
            review = am.read_review_json(agent_id)
            if review:
                review["agent_id"] = agent_id
                am.set_agent_status(agent_id, "completed", issues_count=review.get("summary", {}).get("total", 0))
                reviews_for_moderator.append(review)
            else:
                am.set_agent_status(agent_id, "pending")

    if not reviews_for_moderator and not use_mock:
        prompt_refs = [f"{batch_id}/.prompts/{a}.md" for a in selected_agents]
        return (
            "PRECONDITION_FAILED",
            "agent prompts prepared; waiting for outer AI agent to execute reviews",
            {
                "canonical_path": to_canonical_path(am.batch_dir, ctx.workspace_root),
                "batch_id": batch_id,
                "prompt_refs": prompt_refs,
                "next_step": "outer_agent_executes_prompts",
            },
            [],
            prompt_refs,
        )

    # 5. Merge & Moderator
    am.update_state({"status": "merging"})
    moderator = Moderator()
    merge_result = moderator.merge(batch_id, reviews_for_moderator)

    am.write_artifact("consolidated-review.json", merge_result["consolidated"])
    am.write_artifact("review-conflicts.json", merge_result["conflicts"])
    am.set_agent_status("moderator", "completed")

    # 6. Consensus build
    consensus_builder = ConsensusBuilder()
    consensus = consensus_builder.build(batch_id, merge_result["consolidated"])
    am.write_artifact("review-consensus.json", consensus)

    # 7. Fix tasks
    fix_tasks = generate_fix_tasks(batch_id, consensus)
    am.write_artifact("fix-tasks.json", fix_tasks)

    # 8. Final report
    report_path = am.batch_dir / "final-report.md"
    generate_report(
        batch_id=batch_id,
        mode=mode,
        ref=ref,
        base_ref=base_ref,
        consensus=consensus,
        fix_tasks=fix_tasks,
        role_panel=role_panel,
        output_path=report_path,
    )
    am.register_artifact("final-report.md")

    am.update_state({
        "status": "completed",
        "severity_summary": consensus["summary"],
    })

    canonical = to_canonical_path(am.batch_dir, ctx.workspace_root)
    return (
        "OK",
        "deep code review completed",
        {
            "canonical_path": canonical,
            "batch_id": batch_id,
            "mode": mode,
            "summary": consensus["summary"],
        },
        [],
        [f"{canonical}/final-report.md"],
    )


def _run_cleanup(ctx: CommandContext) -> tuple[str, str, dict[str, Any], list[str], list[str]]:
    payload = ctx.payload
    output_dir_raw = str(payload.get("output_dir") or ".cr-deep").strip()
    output_dir = canonical_to_path(output_dir_raw, ctx.workspace_root)
    retention_days = int(payload.get("retention_days", 30))

    removed = cleanup_old_batches(output_dir, retention_days)
    return (
        "OK",
        f"cleanup completed: removed {len(removed)} old batch directories",
        {"removed": removed, "retention_days": retention_days},
        [],
        [],
    )


def _handler(ctx: CommandContext) -> tuple[str, str, dict[str, Any], list[str], list[str]]:
    if ctx.action == "cleanup":
        return _run_cleanup(ctx)
    return _run_review(ctx)


def handle(args: Namespace) -> int:
    return run_with_protocol(args, _handler)
