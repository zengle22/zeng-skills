#!/bin/bash
# Detect document package structure pattern
# Usage: detect-package-pattern.sh <package-path>

set -euo pipefail

PACKAGE_PATH="${1:-.}"

if [ ! -d "$PACKAGE_PATH" ]; then
  echo "ERROR: Not a directory: $PACKAGE_PATH"
  exit 1
fi

# Count markdown files (max depth 2 to avoid deep recursion)
MD_COUNT=$(find "$PACKAGE_PATH" -maxdepth 2 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')

# Check for blueprint-modular pattern
PATTERN="heuristic"
INDEX_FILE=""
if [ -f "$PACKAGE_PATH/00_blueprint.md" ] || [ -f "$PACKAGE_PATH/00-index.md" ]; then
  PATTERN="blueprint-modular"
  INDEX_FILE=$(ls "$PACKAGE_PATH"/00_*.md 2>/dev/null | head -1 || true)
# Check for PRD-standard pattern
elif [ -f "$PACKAGE_PATH/PRD.md" ]; then
  PATTERN="prd-standard"
  INDEX_FILE="$PACKAGE_PATH/PRD.md"
elif ls "$PACKAGE_PATH"/*-prd.md 1>/dev/null 2>&1; then
  PATTERN="prd-standard"
  INDEX_FILE=$(ls "$PACKAGE_PATH"/*-prd.md 2>/dev/null | head -1 || true)
fi

# Helper: check if any file matches keyword in content
has_content_match() {
  local path="$1"
  local keyword="$2"
  if grep -rlq "$keyword" "$path" --include="*.md" 2>/dev/null; then
    echo "yes"
  else
    echo "no"
  fi
}

# Helper: check if glob pattern matches any files
# Usage: has_glob_match <path> <pattern1> <pattern2> ...
has_glob_match() {
  local path="$1"
  shift
  local matched=0
  for pat in "$@"; do
    # Expand glob in the target directory
    for f in "$path"/$pat; do
      if [ -e "$f" ]; then
        matched=1
        break 2
      fi
    done
  done
  if [ "$matched" -eq 1 ]; then
    echo "yes"
  else
    echo "no"
  fi
}

# Content-based detection
HAS_USER_STORIES=$(has_content_match "$PACKAGE_PATH" "Given.*When.*Then")
HAS_IMPLEMENTATION_SCOPE=$(has_content_match "$PACKAGE_PATH" "implementation scope\|实施范围\|files to touch\|do not touch")

# File-name-based detection
HAS_UX_SPEC=$(has_glob_match "$PACKAGE_PATH" "*ux*" "*UX*" "*design-principle*" "*design_spec*")
HAS_TECH_DESIGN=$(has_glob_match "$PACKAGE_PATH" "*tech*" "*architecture*" "*arch*")
HAS_API_CONTRACT=$(has_glob_match "$PACKAGE_PATH" "*api*" "*contract*" "*endpoint*")
HAS_BLUEPRINT=$(has_glob_match "$PACKAGE_PATH" "*blueprint*" "*index*" "*overview*")

cat <<EOF
{
  "package_path": "$PACKAGE_PATH",
  "md_count": $MD_COUNT,
  "pattern": "$PATTERN",
  "index_file": "${INDEX_FILE#$PACKAGE_PATH/}",
  "has_user_stories": "$HAS_USER_STORIES",
  "has_implementation_scope": "$HAS_IMPLEMENTATION_SCOPE",
  "has_ux_spec": "$HAS_UX_SPEC",
  "has_tech_design": "$HAS_TECH_DESIGN",
  "has_api_contract": "$HAS_API_CONTRACT",
  "has_blueprint": "$HAS_BLUEPRINT"
}
EOF
