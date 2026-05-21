#!/usr/bin/env bash
# run.sh — Entry point for zeng-code-patrol skill
# Usage: ./run.sh --paths <dir> [<dir>...] [--scope full|delta|staged|targeted]
#                [--format markdown|json] [--max-files N] [--max-file-size B]
#                [--since-days N] [--output-dir <path>] [--baseline <path>]
#                [--ruleset <path>] [--min-severity P0|P1|P2|P3]
#                [--fix-mode report-only|suggest-fixes] [--non-interactive]
#                [--resume <id>] [--fail-on-p0p1]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Defaults
PATHS=()
SCOPE="full"
FORMAT="markdown"
MAX_FILES=500
MAX_FILE_SIZE=1048576
SINCE_DAYS=""
OUTPUT_DIR=".zeng-code-patrol"
BASELINE=""
RULESET=""
MIN_SEVERITY="P3"
FIX_MODE="report-only"
NON_INTERACTIVE=false
RESUME=""
FAIL_ON_P0P1=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --paths) shift; while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do PATHS+=("$1"); shift; done;;
    --scope) SCOPE="$2"; shift 2;;
    --format) FORMAT="$2"; shift 2;;
    --max-files) MAX_FILES="$2"; shift 2;;
    --max-file-size) MAX_FILE_SIZE="$2"; shift 2;;
    --since-days) SINCE_DAYS="$2"; shift 2;;
    --output-dir) OUTPUT_DIR="$2"; shift 2;;
    --baseline) BASELINE="$2"; shift 2;;
    --ruleset) RULESET="$2"; shift 2;;
    --min-severity) MIN_SEVERITY="$2"; shift 2;;
    --fix-mode) FIX_MODE="$2"; shift 2;;
    --non-interactive) NON_INTERACTIVE=true; shift;;
    --resume) RESUME="$2"; shift 2;;
    --fail-on-p0p1) FAIL_ON_P0P1=true; shift;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

# Default paths to current directory if none provided
if [[ ${#PATHS[@]} -eq 0 ]]; then
  PATHS=(".")
fi

# Validate input
bash "${SCRIPT_DIR}/validate_input.sh" \
  --paths "${PATHS[@]}" \
  --scope "${SCOPE}" \
  --format "${FORMAT}" \
  --max-files "${MAX_FILES}" \
  --max-file-size "${MAX_FILE_SIZE}" \
  --min-severity "${MIN_SEVERITY}" \
  --fix-mode "${FIX_MODE}"

# Resolve project root
if git rev-parse --show-toplevel &>/dev/null; then
  PROJECT_ROOT="$(git rev-parse --show-toplevel)"
else
  PROJECT_ROOT="${PWD}"
fi

# Generate patrol_id or reuse resume
if [[ -n "${RESUME}" ]]; then
  PATROL_ID="${RESUME}"
  if [[ ! -f "${OUTPUT_DIR}/${PATROL_ID}/patrol-state.json" ]]; then
    echo "Error: resume patrol state not found at ${OUTPUT_DIR}/${PATROL_ID}/patrol-state.json"
    exit 2
  fi
else
  PATROL_ID="$(date +%Y%m%d-%H%M%S)-$(tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 12)"
fi

OUTPUT_ROOT="${OUTPUT_DIR}/${PATROL_ID}"
mkdir -p "${OUTPUT_ROOT}/raw"

# Write initial patrol state
cat > "${OUTPUT_ROOT}/patrol-state.json" <<EOF
{
  "patrol_id": "${PATROL_ID}",
  "status": "scanning",
  "current_phase": "discovery",
  "completed_phases": ["init"],
  "pending_files": [],
  "output_dir": "${OUTPUT_ROOT}",
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "[zeng-code-patrol] Patrol ID: ${PATROL_ID}"
echo "[zeng-code-patrol] Output: ${OUTPUT_ROOT}"
echo "[zeng-code-patrol] Scope: ${SCOPE}"
echo "[zeng-code-patrol] Paths: ${PATHS[*]}"

# Agent-driven execution protocol
# This skill is intentionally agent-facing and does not require a CLI façade.
# The executor agent reads SKILL.md + agents/executor.md and performs the
# 6-phase patrol protocol using the available tool set (ReadFile, Grep, Shell,
# Glob, WriteFile, Task).
#
# When running non-interactively, a wrapper may invoke the agent runtime
# with the payload assembled above. The canonical trigger is:
#   Agent reads skill bundle → executes per protocol → writes artifacts.
#
echo "[zeng-code-patrol] Agent execution context prepared."
echo "[zeng-code-patrol] Executor should now follow agents/executor.md protocol."

# Validate output if report.json exists
if [[ -f "${OUTPUT_ROOT}/report.json" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_ROOT}/report.json"
else
  echo "[zeng-code-patrol] Warning: report.json not found. Executor may need to be run manually."
fi

echo "[zeng-code-patrol] Done. Artifacts in: ${OUTPUT_ROOT}"
