---
name: ll-code-review-deep
description: "多智能体深度代码审查技能。对单次 Commit/PR/模块执行 4+ 维度并行专项审查，合并去重后生成结构化修复任务与最终报告。"
argument-hint: "[--mode commit|pr|module|frz] [--ref REF] [--base BASE] [--head HEAD] [--path PATH] [--frz-ref FRZ_REF] [--output-dir .cr-deep] [--preview] [--apply-patches BATCH_ID]"
allowed-tools:
  - ReadFile
  - WriteFile
  - Shell
  - Grep
  - Glob
  - Task
---

# ll-code-review-deep

Governed multi-agent deep code review skill. Spawns specialized reviewer agents in parallel across configurable quality dimensions, merges findings through a moderator, and produces structured fix-tasks plus a human-readable final report.

## Primary Abstraction

Skill (governed capability template)

## Secondary Abstraction

Pipeline — multi-phase review with checkpoint/resume support

## Authority

Canonical bundle: `skills/ll-code-review-deep/`

## Not Equal To

- Not a replacement for `bmad-code-review` (complements it; bmad for quick scan, deep for critical PRs)
- Not a source code auto-fixer (produces fix-tasks + optional patches, human decides)
- Not a runtime test executor
- Not a gate decision maker (evidence-only)

## Canonical Authority

- ADR: ADR-058
- Upstream: project governance maps under `ssot/governance/maps/`
- Evidence schemas: `schemas/*.schema.json`

## Runtime Boundary Baseline

This capability is a governed `Skill` for `Code Change → Quality Evidence + Fix Tasks` transformation.

- **Read-only review** — does NOT modify source files unless `--apply-patches` is explicitly invoked.
- **Evidence-only output** — does NOT execute gate decisions or block pipelines.
- **Deterministic batch_id** — `CR-{YYYYMMDD}-{seq:03d}`.
- **Issue IDs** follow `{batch_id}-{agent_id}-{severity}-{seq:03d}` format.

## Required Read Order

1. `ll.contract.yaml`
2. `ll.lifecycle.yaml`
3. `schemas/problem.schema.json`
4. `schemas/batch-state.schema.json`
5. `schemas/role-panel.schema.json`
6. `schemas/fix-task.schema.json`
7. `schemas/conflict.schema.json`
8. `agents/standards-guardian.md`
9. `agents/logic-verifier.md`
10. `agents/moderator.md`

## Execution Protocol

1. **Initialize**
   - Parse mode and refs
   - Generate `batch_id` and create `{output_dir}/{batch_id}/` structure
   - Capture input snapshot (git diff, PR description, file context)
   - Write `batch-state.json` with status `initializing`

2. **Role Selection**
   - MVP: hard-code 4 core agents + moderator
   - Write `role-panel.json`
   - Update `batch-state.json` → `reviewing`

3. **Parallel Review (Phase 1A)**
   - Spawn each selected agent with standard prompt + rubric + diff
   - Each agent writes `{agent_id}-review.json` immediately upon completion
   - Update `batch-state.json` agent statuses

4. **Merge & Conflict Detection (Phase 1B)**
   - Moderator reads all review.json files
   - Deduplicate by (file + line_range + dimension)
   - Detect severity conflicts (diff ≥ 2 levels or P0 vs "none")
   - Write `consolidated-review.json` + `review-conflicts.json`

5. **Consensus Build (Phase 1D — MVP skip 1C)**
   - MVP: adjacent severity conflicts auto-resolved to higher level
   - Write `review-consensus.json`
   - Update severity summary in `batch-state.json`

6. **Fix Task Generation (Phase 2 — MVP simplified)**
   - For each P0/P1 in consensus, generate fix-task entry
   - Write `fix-tasks.json`

7. **Report Synthesis (Phase 4 — MVP)**
   - Generate `final-report.md` with severity tables and per-file summaries
   - Update `batch-state.json` → `completed`

## Workflow Boundary

- **Input**: git diff / PR diff / module path + optional FRZ package
- **Output**: review artifact bundle under `{output_dir}/{batch_id}/`
  - `batch-state.json`
  - `role-panel.json`
  - `reviews/{agent}-review.json`
  - `consolidated-review.json`
  - `review-consensus.json`
  - `fix-tasks.json` (MVP: simplified)
  - `final-report.md`
- **Out of scope (MVP)**:
  - Conflict discussion rounds (Phase 1C)
  - Auto-patch generation and application
  - Independent audit agent (Phase 3)
  - Smart selector (Phase 0 uses hard-coded rules)

## Non-Negotiable Rules

- Do not modify source files during review phases.
- Do not fabricate issues — every finding must have exact code evidence.
- Style-only issues must not be P0/P1.
- Agent output must conform to `problem.schema.json`.
- `batch-state.json` must be updated after every phase.
- All artifacts written to disk immediately; no in-memory-only state.
- Default exit code is 0; exit code 1 on structural failure.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (review completed, report generated) |
| 1 | Structural failure (invalid args, schema validation error, git error) |
| 2 | Partial success (some agents timed out or failed, but consensus produced) |

## Usage Examples

```bash
# Commit-level quick review
ll code-review-deep --mode commit --ref HEAD~1

# PR-level full review
ll code-review-deep --mode pr --base main --head feature/x

# Module health check
ll code-review-deep --mode module --path src/services/order/
```

## Compatibility Note

This skill is part of the LEE Lite governed skill family under `skills/ll-code-review-deep/`. It follows ADR-058 for multi-agent deep review and ADR-057 for artifact directory layout.
