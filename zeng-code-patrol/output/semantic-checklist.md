# Output Semantic Checklist: zeng-code-patrol

## Report Semantics
- [ ] Report title or `patrol_id` clearly identifies the scan instance
- [ ] `summary` accurately reflects the scanned codebase state at the time of execution
- [ ] `quality_score` trend direction is interpretable (not misleading due to ruleset changes)

## Issue Semantics
- [ ] P0 issues represent genuine blockers, not false positives from overly broad regex
- [ ] P1 issues represent actionable high-risk items, not style nits
- [ ] Each issue `evidence` field contains enough context for a human to verify
- [ ] `impact` field explains business or maintenance risk, not just technical description
- [ ] `fix_suggestion` is safe to apply and does not break architecture boundaries

## Hotspot Semantics
- [ ] High-density hotspots correlate with recent high-churn directories
- [ ] Hotspot directories are actionable (not top-level project root unless truly warranted)

## Baseline Semantics
- [ ] `new_issues` are genuinely new, not caused by code movement or fingerprint algorithm changes
- [ ] `resolved_issues` were intentionally fixed, not hidden by exclusion changes
- [ ] `persistent_issues` are acknowledged technical debt, not ignored problems

## Evidence Semantics
- [ ] Raw evidence files are sufficient to reconstruct the report independently
- [ ] `patrol-state.json` accurately reflects the execution boundary
