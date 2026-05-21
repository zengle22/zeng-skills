#!/usr/bin/env bash
# validate_input.sh — Input validation for zeng-code-patrol
set -euo pipefail

PATHS=()
SCOPE=""
FORMAT=""
MAX_FILES=""
MAX_FILE_SIZE=""
MIN_SEVERITY=""
FIX_MODE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --paths) shift; while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do PATHS+=("$1"); shift; done;;
    --scope) SCOPE="$2"; shift 2;;
    --format) FORMAT="$2"; shift 2;;
    --max-files) MAX_FILES="$2"; shift 2;;
    --max-file-size) MAX_FILE_SIZE="$2"; shift 2;;
    --min-severity) MIN_SEVERITY="$2"; shift 2;;
    --fix-mode) FIX_MODE="$2"; shift 2;;
    *) shift;;
  esac
done

ERRORS=0

# Validate paths exist
if [[ ${#PATHS[@]} -eq 0 ]]; then
  echo "[ERROR] No paths provided"
  ERRORS=$((ERRORS + 1))
else
  for p in "${PATHS[@]}"; do
    if [[ ! -e "${p}" ]]; then
      echo "[ERROR] Path does not exist: ${p}"
      ERRORS=$((ERRORS + 1))
    fi
  done
fi

# Validate scope
if [[ -n "${SCOPE}" && ! "${SCOPE}" =~ ^(full|delta|staged|targeted)$ ]]; then
  echo "[ERROR] Invalid scope: ${SCOPE}"
  ERRORS=$((ERRORS + 1))
fi

# Validate format
if [[ -n "${FORMAT}" && ! "${FORMAT}" =~ ^(markdown|json)$ ]]; then
  echo "[ERROR] Invalid format: ${FORMAT}"
  ERRORS=$((ERRORS + 1))
fi

# Validate max_files
if [[ -n "${MAX_FILES}" ]]; then
  if ! [[ "${MAX_FILES}" =~ ^[0-9]+$ ]] || [[ "${MAX_FILES}" -le 0 ]] || [[ "${MAX_FILES}" -gt 10000 ]]; then
    echo "[ERROR] max-files must be 1-10000"
    ERRORS=$((ERRORS + 1))
  fi
fi

# Validate max_file_size
if [[ -n "${MAX_FILE_SIZE}" ]]; then
  if ! [[ "${MAX_FILE_SIZE}" =~ ^[0-9]+$ ]] || [[ "${MAX_FILE_SIZE}" -le 0 ]]; then
    echo "[ERROR] max-file-size must be > 0"
    ERRORS=$((ERRORS + 1))
  fi
fi

# Validate min_severity
if [[ -n "${MIN_SEVERITY}" && ! "${MIN_SEVERITY}" =~ ^(P0|P1|P2|P3)$ ]]; then
  echo "[ERROR] Invalid min-severity: ${MIN_SEVERITY}"
  ERRORS=$((ERRORS + 1))
fi

# Validate fix_mode
if [[ -n "${FIX_MODE}" && ! "${FIX_MODE}" =~ ^(report-only|suggest-fixes)$ ]]; then
  echo "[ERROR] Invalid fix-mode: ${FIX_MODE}"
  ERRORS=$((ERRORS + 1))
fi

if [[ ${ERRORS} -gt 0 ]]; then
  echo "[FAIL] ${ERRORS} input validation error(s)"
  exit 2
fi

echo "[OK] Input validation passed"
