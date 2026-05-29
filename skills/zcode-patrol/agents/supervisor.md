# Supervisor Agent: zcode-patrol

## Validation Checklist

1. **Input Consistency**
   - [ ] All provided `paths` exist and are readable
   - [ ] `scope` is valid for the current environment (git available for delta/staged)
   - [ ] `ruleset` YAML parses successfully when provided
   - [ ] `baseline` report conforms to schema when provided
   - [ ] `resume` state file exists and is readable when provided

2. **Discovery Quality**
   - [ ] `manifest.json` contains at least one file when paths are non-empty
   - [ ] Hard exclusions correctly exclude build artifacts and dependencies
   - [ ] `max_files` limit is enforced without silent truncation of critical files

3. **Scan Coverage**
   - [ ] L1 rules were applied to all files in manifest matching their language scope
   - [ ] L3 engines were attempted; skipped dimensions are documented with reasons
   - [ ] No uncaught exceptions caused silent loss of findings

4. **Issue Quality**
   - [ ] Every issue has required fields: `id`, `rule_id`, `dimension`, `severity`, `file`, `line_start`, `message`, `found_by`, `confidence`
   - [ ] Issue IDs follow `{patrol_id}-{rule_id}-{seq:04d}` format
   - [ ] Severity values are one of P0/P1/P2/P3
   - [ ] Duplicate issues across L1/L3 are merged, not double-counted

5. **Report Integrity**
   - [ ] `report.json` validates against `evidence/patrol-report.schema.json`
   - [ ] `summary.total_issues` equals sum of severity breakdown
   - [ ] `quality_score` is between 0 and 100
   - [ ] `hotspots` directories correspond to actual scanned paths
   - [ ] Baseline comparison numbers are consistent (new + resolved + persistent = baseline total + new)

6. **State & Evidence**
   - [ ] `patrol-state.json` status is `completed` on success, `failed` on error
   - [ ] Raw evidence files (`raw/L1-results.json`, `raw/L3-results.json`) are present
   - [ ] No source files were modified during execution

7. **Non-Negotiable Rules**
   - [ ] Skill did not modify any source code
   - [ ] Skill did not block or fail the pipeline solely based on P0/P1 findings (unless `--fail-on-p0p1` explicitly enabled)
   - [ ] Skill did not fabricate evidence or statistics
