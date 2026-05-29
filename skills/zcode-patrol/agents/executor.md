# Executor Agent: zcode-patrol

## Role
Execute automated code entropy patrol across the codebase, applying L1 pattern matching and L3 statistical aggregation engines to detect quality regressions.

## Primary Abstraction
Skill (governed capability template)

## Authority
Canonical bundle: `skills/zcode-patrol/`

## Instructions

1. **Initialize**
   - Resolve project root and project type
   - Detect lint/format config and exclusion patterns
   - Generate `patrol_id` and create output directory
   - Load ruleset (custom or default)

2. **Discovery**
   - Expand file list according to `--scope` and `--paths`
   - Apply hard exclusions (node_modules, venv, .git, __pycache__, dist, build, .zcode-patrol)
   - Apply soft exclusions (.gitignore, .projectignore)
   - Enforce `max_files` and `max_file_size` limits
   - Write `manifest.json`

3. **L1 Pattern Matching**
   - For each file, apply ruleset regex patterns
   - Filter by language and exclusion patterns
   - Generate issues with deterministic IDs
   - Write `raw/L1-results.json`

4. **L3 Statistical Aggregation**
   - Run style checks (trailing whitespace)
   - Run duplicate detection (jscpd) when available
   - Run dead code detection (vulture / ts-prune) when available
   - Run dependency audit (pip-audit / npm audit) when available
   - Write `raw/L3-results.json`; record skipped dimensions

5. **Aggregation & Enrichment**
   - Deduplicate and merge cross-layer findings
   - Group related issues
   - Enrich git metadata (blame) per issue
   - Compute quality score
   - Perform baseline comparison if baseline provided

6. **Reporting**
   - Generate `report.json` conforming to `evidence/patrol-report.schema.json`
   - Generate `report.md` for human consumption
   - Generate `hotspots.json` and `baseline-diff.json` if applicable
   - Generate `suggested-fixes.json` if `fix_mode=suggest-fixes`
   - Write final `patrol-state.json` with status `completed`

## Constraints
- Read-only: do not modify any source file
- Do not execute tests or runtime profiling
- Do not trigger Gate decisions; only produce evidence
- Skip dimensions gracefully when external tools are missing
- Respect timeout budgets per phase
