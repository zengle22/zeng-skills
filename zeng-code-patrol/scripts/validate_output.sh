#!/usr/bin/env bash
# validate_output.sh — Output validation for zeng-code-patrol
set -euo pipefail

REPORT_PATH="${1:-}"
if [[ -z "${REPORT_PATH}" ]]; then
  echo "[ERROR] Usage: validate_output.sh <report.json>"
  exit 2
fi

if [[ ! -f "${REPORT_PATH}" ]]; then
  echo "[ERROR] Report not found: ${REPORT_PATH}"
  exit 2
fi

ERRORS=0

# Check valid JSON
if ! python3 -c "import json; json.load(open('${REPORT_PATH}'))" 2>/dev/null; then
  echo "[ERROR] report.json is not valid JSON"
  ERRORS=$((ERRORS + 1))
fi

# Check required top-level fields
for field in patrol_id started_at completed_at config summary issues; do
  if ! python3 -c "import json; d=json.load(open('${REPORT_PATH}')); exit(0 if '${field}' in d else 1)" 2>/dev/null; then
    echo "[ERROR] Missing required field: ${field}"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check summary fields
for field in total_files_scanned total_issues severity_breakdown dimension_breakdown skipped_dimensions quality_score; do
  if ! python3 -c "import json; d=json.load(open('${REPORT_PATH}')); exit(0 if '${field}' in d.get('summary',{}) else 1)" 2>/dev/null; then
    echo "[ERROR] Missing required summary field: ${field}"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check quality_score range
if ! python3 -c "
import json
d=json.load(open('${REPORT_PATH}'))
qs=d.get('summary',{}).get('quality_score', -1)
exit(0 if 0 <= qs <= 100 else 1)
" 2>/dev/null; then
  echo "[ERROR] quality_score out of range [0, 100]"
  ERRORS=$((ERRORS + 1))
fi

if [[ ${ERRORS} -gt 0 ]]; then
  echo "[FAIL] ${ERRORS} output validation error(s)"
  exit 2
fi

echo "[OK] Output validation passed"
