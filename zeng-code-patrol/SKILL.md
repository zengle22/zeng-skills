---
name: zeng-code-patrol
description: "定期对代码库进行自动化巡检，发现常见代码问题（风格漂移、架构腐化、安全漏洞、性能陷阱、重复代码等），生成结构化报告并推动修复，阻止代码熵增。"
argument-hint: "[--paths <dir>...] [--scope full|delta|staged|targeted] [--format markdown|json] [--max-files 500] [--max-file-size 1048576] [--since-days 7] [--output-dir .zeng-code-patrol] [--non-interactive] [--min-severity P0|P1|P2|P3] [--fix-mode report-only|suggest-fixes] [--baseline <path>] [--ruleset <path>] [--resume <patrol_id>] [--fail-on-p0p1]"
allowed-tools:
  - ReadFile
  - WriteFile
  - Shell
  - Grep
  - Glob
  - Task
---

# zeng-code-patrol

Governed code entropy patrol skill. Performs read-only static analysis across configurable dimensions, produces structured evidence, and supports baseline comparison — without modifying source code or making gate decisions.

## Primary Abstraction

Skill (governed capability template)

## Secondary Abstraction

Workflow — multi-phase scan with checkpoint/resume support

## Authority

Canonical bundle: `skills/zeng-code-patrol/`

## Not Equal To

- Not a replacement for ESLint, Pylint, SonarQube (supplements/aggregates)
- Not a runtime profiler or test executor
- Not a source code modifier (v1.0 is read-only)
- Not a gate decision maker (evidence-only)

## Canonical Authority

- ADR: ADR-020 (standard skill baseline), ADR-038 (runtime abstraction)
- Upstream: project governance maps under `ssot/governance/maps/`
- Evidence schemas: `evidence/patrol-report.schema.json`, `evidence/issue.schema.json`, `evidence/patrol-state.schema.json`

## Runtime Boundary Baseline

This capability is a governed `Skill` for `Codebase → Quality Evidence` transformation.

- **Read-only aggregation** — does NOT modify source files.
- **Evidence-only output** — does NOT execute gate decisions or block pipelines.
- **Deterministic ID** — `patrol_id` and issue IDs are deterministic and reproducible.

## Required Read Order

1. `zeng.contract.yaml`
2. `zeng.lifecycle.yaml`
3. `input/contract.yaml`
4. `output/contract.yaml`
5. `agents/executor.md`
6. `agents/supervisor.md`
7. `input/semantic-checklist.md`
8. `output/semantic-checklist.md`
9. `evidence/*.schema.json`

## Execution Protocol

1. **Initialize**
   - Resolve project root and type
   - Load ruleset (default or custom)
   - Generate `patrol_id` and create `{output_dir}/{patrol_id}/` structure
   - If `--resume` provided, load `patrol-state.json` and skip completed phases

2. **Discovery**
   - Expand file list per `--scope` (`full`, `delta`, `staged`, `targeted`)
   - Apply exclusions (hard + `.gitignore` + `.projectignore`)
   - Enforce `max_files` and `max_file_size`
   - Write `manifest.json`

3. **Scan (L1 + L3)**
   - **L1 Pattern Matching**: apply ruleset regex/AST rules per file
   - **L3 Statistical Aggregation**: run external tools (jscpd, vulture, pip-audit, npm audit) when available
   - Record skipped dimensions with reasons
   - Write `raw/L1-results.json`, `raw/L3-results.json`

4. **Aggregation & Enrichment**
   - Deduplicate and merge cross-layer findings
   - Group related issues
   - Enrich git metadata (`git blame`) per issue
   - Compute quality score
   - Perform baseline comparison if `--baseline` provided

5. **Reporting**
   - Generate `report.json` (conforms to `evidence/patrol-report.schema.json`)
   - Generate `report.md` for human consumption
   - Generate `hotspots.json`, `baseline-diff.json`, `suggested-fixes.json` as applicable
   - Write final `patrol-state.json` with status `completed`

6. **Validation**
   - Run `scripts/validate_output.sh` against `report.json`
   - Supervisor reviews evidence completeness and consistency

## Workflow Boundary

- **Input**: directory paths + scan configuration + optional ruleset/baseline/resume
- **Output**: patrol artifact bundle under `{output_dir}/{patrol_id}/`
  - `report.json` / `report.md`
  - `manifest.json`
  - `patrol-state.json`
  - `hotspots.json`
  - `baseline-diff.json` (if baseline)
  - `suggested-fixes.json` (if `fix_mode=suggest-fixes`)
  - `raw/L1-results.json`, `raw/L3-results.json`
- **Out of scope**:
  - Source code modification
  - Test execution or runtime profiling
  - Gate approval/rejection/block
  - SARIF output (v1.1+ candidate)
  - Auto-fix application (v1.2+ candidate)

## Patrol Dimensions

| ID | Name | Engine | Severity |
|----|------|--------|----------|
| D01 | Style Consistency | L1 + L3 | P2-P3 |
| D02 | Architecture Compliance | L1 | P0-P1 |
| D03 | Security Patterns | L1 | P0-P1 |
| D04 | Performance Anti-patterns | L1 | P1-P2 |
| D05 | Duplication & Dead Code | L3 | P2-P3 |
| D06 | Documentation Sync | L1 | P2-P3 |
| D07 | Dependency Health | L3 | P1-P2 |
| D08 | Test Coverage Drift | L1 | P1-P2 |

## Non-Negotiable Rules

- Do not modify source files — this is a read-only skill.
- Do not execute tests or runtime profiling.
- Do not make gate decisions — only produce evidence.
- Do not fabricate statistics — counts must match raw evidence.
- Skip dimensions gracefully when tools are unavailable; never crash.
- Respect timeout budgets per phase (see `input/contract.yaml`).
- `patrol_id` must be deterministic from timestamp + random suffix.
- Issue IDs must follow `{patrol_id}-{rule_id}-{seq:04d}` format.
- Quality score must be between 0 and 100.
- Default exit code is 0; exit code 1 only when `--fail-on-p0p1` is explicitly set.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (default, even if P0/P1 found) |
| 1 | Success with P0/P1 found (only if `--fail-on-p0p1`) |
| 2 | System error (invalid args, bad ruleset, missing git for delta/staged) |
| 3 | Partial success (some dimensions skipped due to timeout/missing tools) |

## Usage Examples

```bash
# Full scan, Markdown output
./scripts/run.sh --paths src/ tests/ --scope full --format markdown

# Delta scan with baseline comparison
./scripts/run.sh --paths src/ --scope delta --since-days 7 --baseline .zeng-code-patrol/20260506-120000-xxx/report.json

# CI-friendly JSON, fail on P0/P1
./scripts/run.sh --paths src/ --min-severity P1 --format json --non-interactive --fail-on-p0p1

# Resume interrupted patrol
./scripts/run.sh --resume 20260513-120000-a1b2c3d4e5f6
```

## Compatibility Note

This skill resides at `skills/zeng-code-patrol/` (flat path). Per ADR-020 §3.2, the canonical path pattern is `skills/l{n}/<skill-name>/`. This flat path is retained as a transitional compatibility layout pending bulk migration of existing QA skill family.
