"""Agent invocation framework — supports sequential (default) and parallel modes.

In the AI agent runtime (Claude Code / Kimi CLI / Codex), actual LLM execution
is performed by the outer agent loop. This module provides:

- Sequential execution (default): safe fallback for all runtimes
- Parallel execution (experimental): when the outer runtime supports concurrent
  subagents (e.g. Kimi CLI ``Task`` tool)
- Mock execution: for pipeline testing without LLM calls

The executor callable abstracts the actual invocation mechanism:
- ``MockAgentExecutor``: returns empty valid JSON for testing
- ``PromptFileExecutor``: writes prompt to disk for outer-agent execution
- Future: subprocess or API-based executors
"""

from __future__ import annotations

import concurrent.futures
import os
from pathlib import Path
from typing import Any, Callable

from runtime.lib.errors import CommandError
from runtime.lib.fs import write_text


class AgentRunner:
    """Orchestrate agent review jobs with sequential or parallel dispatch."""

    def __init__(
        self,
        max_workers: int = 4,
        timeout_seconds: int = 120,
        sequential: bool | None = None,
    ) -> None:
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        # Auto-detect: default to sequential unless CR_DEEP_PARALLEL is set
        if sequential is None:
            self.sequential = os.environ.get("CR_DEEP_PARALLEL", "").lower() not in {"1", "true", "yes"}
        else:
            self.sequential = sequential

    def run(
        self,
        jobs: list[dict[str, Any]],
        executor: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Dispatch jobs according to the configured mode."""
        if self.sequential:
            return self.run_sequential(jobs, executor)
        return self.run_parallel(jobs, executor)

    def run_sequential(
        self,
        jobs: list[dict[str, Any]],
        executor: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Execute jobs one by one in order.

        This is the default and safest mode:
        - Works in all outer-agent runtimes (Claude Code, Kimi CLI, Codex)
        - No risk of concurrent subagent limits
        - Easier to debug and recover
        """
        results: list[dict[str, Any]] = []
        for job in jobs:
            agent_id = job.get("agent_id", "unknown")
            try:
                result = executor(job)
                results.append({"agent_id": agent_id, "status": "completed", "result": result})
            except Exception as exc:
                results.append({"agent_id": agent_id, "status": "failed", "error": str(exc)})
        return results

    def run_parallel(
        self,
        jobs: list[dict[str, Any]],
        executor: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Execute jobs concurrently using a thread pool.

        **Experimental**: only viable when the outer runtime supports
        concurrent subagents (e.g. Kimi CLI ``Task`` tool with sufficient
        concurrency quota). Falls back to sequential if any job fails
        due to resource exhaustion.
        """
        results: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            future_to_job = {
                pool.submit(self._run_single, executor, job): job
                for job in jobs
            }
            for future in concurrent.futures.as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    results.append({"agent_id": job["agent_id"], "status": "completed", "result": result})
                except Exception as exc:
                    results.append({
                        "agent_id": job["agent_id"],
                        "status": "failed",
                        "error": str(exc),
                    })
        return results

    def _run_single(
        self,
        executor: Callable[[dict[str, Any]], dict[str, Any]],
        job: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a single job with optional retry logic."""
        # Sprint 2 MVP: single attempt. Retry logic can be added here later.
        return executor(job)


class MockAgentExecutor:
    """Placeholder executor for pipeline testing without LLM calls.

    Returns empty but schema-valid review JSON so that Moderator,
    ConsensusBuilder, and report generation can be tested end-to-end.
    """

    def __init__(self, skill_dir: Path) -> None:
        self.skill_dir = skill_dir

    def __call__(self, job: dict[str, Any]) -> dict[str, Any]:
        agent_id = job["agent_id"]
        batch_id = job.get("batch_id", "unknown")
        return {
            "agent_id": agent_id,
            "batch_id": batch_id,
            "issues": [],
            "summary": {"total": 0, "P0": 0, "P1": 0, "P2": 0, "P3": 0},
        }


class PromptFileExecutor:
    """Write agent prompt to disk for outer-agent execution.

    This executor does NOT invoke an LLM directly. Instead it:
    1. Writes the assembled prompt to ``{batch_dir}/.prompts/{agent_id}.md``
    2. Returns a placeholder result indicating the prompt is ready

    The outer AI agent (Claude Code / Kimi CLI) is then expected to:
    - Read the prompt file
    - Execute the review according to the agent's rubric
    - Write the result to ``reviews/{agent_id}-review.json``

    This is the production pattern used by ``qa_skill_runtime.py``.
    """

    def __init__(self, batch_dir: Path) -> None:
        self.batch_dir = batch_dir
        self.prompts_dir = batch_dir / ".prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def __call__(self, job: dict[str, Any]) -> dict[str, Any]:
        agent_id = job["agent_id"]
        prompt = job.get("prompt", "")
        batch_id = job.get("batch_id", "unknown")

        prompt_file = self.prompts_dir / f"{agent_id}.md"
        write_text(prompt_file, prompt)

        return {
            "agent_id": agent_id,
            "batch_id": batch_id,
            "status": "PROMPT_WRITTEN",
            "prompt_file": str(prompt_file),
            "issues": [],
            "summary": {"total": 0, "P0": 0, "P1": 0, "P2": 0, "P3": 0},
        }
