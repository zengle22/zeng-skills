# Input Semantic Checklist: zeng-code-patrol

## Scan Scope Semantics
- [ ] `full` scope implies intentional baseline or periodic audit
- [ ] `delta` scope implies PR/MR-time check with meaningful `since_days`
- [ ] `staged` scope implies pre-commit local check
- [ ] `targeted` scope implies directed investigation of specific paths

## Path Semantics
- [ ] Provided paths are within the project boundary
- [ ] Paths do not unintentionally include generated or vendored code
- [ ] Paths are not exclusively test fixtures or mock data (unless intended)

## Ruleset Semantics
- [ ] Custom ruleset does not conflict with project ADR or architecture decisions
- [ ] Custom ruleset severity overrides are intentional, not accidental
- [ ] Custom ruleset exclusion patterns do not hide legitimate security findings

## Baseline Semantics
- [ ] Baseline report corresponds to the same codebase commit range
- [ ] Baseline was generated with compatible ruleset version
