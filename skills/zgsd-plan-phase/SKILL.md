---
name: zgsd-plan-phase
description: Bridge impl task packs to GSD PLAN format for deterministic phase planning. Trigger when user says "plan phase", "bridge task pack", or invokes /zgsd-plan-phase.
---

# zgsd-plan-phase

## Trigger

Invoke when user:
- Says "plan phase N from impl task pack"
- Says "bridge task pack to GSD plan"
- Invokes `/zgsd-plan-phase`

## What This Skill Does

Converts impl task packs (containing `task-list.json`, `task-*.md`, `dag-validation.json`) into GSD-executable `*-PLAN.md` files. Preserves the impl task pack as single source of truth, generates standard GSD PLAN contract that `$gsd-execute-phase` can consume.

## Self-Contained Structure

This skill directory is self-contained. Copy it to any project and it works.

```
zgsd-plan-phase/
├── SKILL.md                    # This file
├── import-task-pack.mjs        # Main bridge script
├── validate-bridge.mjs         # Bridge validation script
└── schemas/
    ├── task-pack.schema.json
    └── task-bridge.schema.json
```

## How to Run

### Step 1: Parse User Command

Extract from user message:
- `<phase>` — phase number (e.g., `0`)
- `<impl-dir>` — path to impl task pack directory
- Optional flags: `--dry-run`, `--force`, `--append`, `--skip-review`, `--app-dir <path>`, `--project-root <path>`

### Step 1.5: Determine App Directory

The `--app-dir` parameter (or auto-detected app directory) is critical for **path normalization**.

**Problem**: impl task markdown and acceptance criteria may reference bare paths like:
- `src/lib/ai/provider.factory.ts` instead of `apps/ai-coach-skill/src/lib/ai/provider.factory.ts`
- `tests/unit/env.test.ts` instead of `apps/ai-coach-skill/tests/unit/env.test.ts`
- `.eslintrc.js` instead of `apps/ai-coach-skill/.eslintrc.js`

If these paths are written to the PLAN as-is, the agent executing the PLAN will create files at the project root instead of under the actual app directory.

**Solution**: The bridge script automatically normalizes bare paths by detecting common prefixes (`src/`, `tests/`, `test/`, `lib/`, `app/`, `pages/`, config files) and prepending the app directory. If `--app-dir` is not specified, it auto-detects from candidates: `apps/ai-coach-skill`, `apps/web`, `src`, `.`.

**Always verify** the app directory is correct before running the bridge.

### Step 2: Run Bridge Script

Determine the script path relative to project root. The skill may be installed in `.claude/skills/zgsd-plan-phase/` or `.agents/skills/zgsd-plan-phase/` or any other location.

Execute via Bash tool from project root:

```bash
# Find the skill directory and run the script
SKILL_DIR=$(find . -path "*/zgsd-plan-phase/import-task-pack.mjs" -not -path "*/node_modules/*" | head -1 | xargs dirname)
node "$SKILL_DIR/import-task-pack.mjs" --phase <phase> --impl <impl-dir>
```

Add flags if user requested them (e.g., `--dry-run`, `--app-dir apps/my-app`).

### Step 2.5: Context Assembly Integration

If the project contains `doc/dev/DEV-002-Context-Assembly.md` and `scripts/docs/assemble-context.mjs`, the bridge automatically enables Context Assembly integration:

1. Generate or refresh `.planning/phases/<phase-id>/AI-CONTEXT-PACK.md` and `.json`.
2. Insert `## 0. Context Assembly Gate` into every generated `*-PLAN.md`.
3. Record `context_assembly` metadata in `{padded}-TASK-BRIDGE.json`.
4. Make bridge validation fail if the phase Context Pack reports blocking `missing` or `conflicts`.

The generated gate infers `--task` from target files (`api_change`, `data_change`, `business_rule_change`, `backend_implementation`, `skill_change`) and falls back to `phase_execution` when no narrower task type is detected.

This is a semi-integrated DEV-002 path: it does not modify GSD executor/core, but it gives every PLAN an explicit context gate before execution.

### Step 3: Display Results

Show the user:
- Pre-flight gate status
- Task mapping summary (X tasks mapped, Y requirements covered)
- Wave and dependency summary
- Generated files list
- Validation gate results
- Review gate result (PASS / REJECT)

### Step 4: Report Next Steps

- If review **PASS**: Tell user `Next: $gsd-execute-phase <phase>`
- If review **REJECT**: Show failures, do NOT suggest execution

## Validation Command

To validate existing bridge output:

```bash
SKILL_DIR=$(find . -path "*/zgsd-plan-phase/validate-bridge.mjs" -not -path "*/node_modules/*" | head -1 | xargs dirname)
node "$SKILL_DIR/validate-bridge.mjs" --phase <n> [--project-root <path>]
```

## Prerequisites

Verify before running:
- `.planning/ROADMAP.md` exists
- `AGENTS.md`, `AI_CONSTITUTION.md`, `rules/agent-coding-guardrails.md` exist
- Impl directory contains `task-list.json`, `dag-validation.json`
- `dag-validation.json` status is `PASS`

## Generated Output

Files in `.planning/phases/{padded-phase}-{phase-slug}/`:

| File | Purpose |
|------|---------|
| `{padded}-CONTEXT.md` | Locked implementation decisions |
| `AI-CONTEXT-PACK.md` / `.json` | DEV-002 phase Context Pack generated when assembler is available |
| `{padded}-TASK-BRIDGE.json` | Machine-readable bridge manifest, including `context_assembly` metadata |
| `{padded}-01-PLAN.md` ... `{padded}-NN-PLAN.md` | GSD-executable plans with `## 0. Context Assembly Gate` |
| `{padded}-QUALITY-MAP.json` | Requirement-to-test mapping |
| `{padded}-VALIDATION.md` | Validation strategy skeleton |
