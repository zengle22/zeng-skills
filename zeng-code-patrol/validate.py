#!/usr/bin/env python3
"""Validate patrol output artifacts against JSON schemas.

Usage:
    python validate.py <patrol_dir>

Examples:
    python validate.py .zeng-code-patrol/20260527-120000-abc123def456

Exit codes:
    0 - All artifacts valid
    1 - Validation errors found
    2 - Missing required files or dependencies
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)


SCHEMAS_DIR = Path(__file__).parent / "evidence"

ARTIFACT_SCHEMAS = {
    "report.json": "patrol-report.schema.json",
    "patrol-state.json": "patrol-state.schema.json",
}


def load_schema(schema_name: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / schema_name
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_file(file_path: Path, schema_name: str) -> list[str]:
    """Validate a JSON file against its schema. Returns list of errors."""
    if not file_path.exists():
        return [f"File not found: {file_path}"]

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    schema = load_schema(schema_name)
    errors: list[str] = []

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(e.message)

    return errors


def validate_issues(report_path: Path) -> list[str]:
    """Validate individual issues in report.json against issue schema."""
    if not report_path.exists():
        return []

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    issues = data.get("issues", [])
    if not issues:
        return []

    issue_schema = load_schema("issue.schema.json")
    errors: list[str] = []

    for i, issue in enumerate(issues):
        try:
            jsonschema.validate(issue, issue_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"[issue {i}] {e.message}")

    return errors


def validate_patrol(patrol_dir: Path) -> int:
    """Validate all artifacts in a patrol directory."""
    if not patrol_dir.exists():
        print(f"ERROR: Patrol directory not found: {patrol_dir}", file=sys.stderr)
        return 2

    total_errors = 0
    checked = 0

    # Validate main artifacts
    for artifact_name, schema_name in ARTIFACT_SCHEMAS.items():
        file_path = patrol_dir / artifact_name
        if not file_path.exists():
            print(f"SKIP  {artifact_name} (not found)")
            continue

        errors = validate_file(file_path, schema_name)
        checked += 1

        if errors:
            print(f"FAIL  {artifact_name}")
            for err in errors:
                print(f"      - {err}")
            total_errors += len(errors)
        else:
            print(f"OK    {artifact_name}")

    # Validate issues in report.json
    report_path = patrol_dir / "report.json"
    if report_path.exists():
        errors = validate_issues(report_path)
        checked += 1
        if errors:
            print(f"FAIL  report.json (issues validation)")
            for err in errors[:10]:  # Show first 10 errors
                print(f"      - {err}")
            if len(errors) > 10:
                print(f"      ... and {len(errors) - 10} more errors")
            total_errors += len(errors)
        else:
            print(f"OK    report.json (issues)")

    print(f"\nChecked: {checked} files, Errors: {total_errors}")
    return 1 if total_errors > 0 else 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python validate.py <patrol_dir>", file=sys.stderr)
        return 2

    patrol_dir = Path(sys.argv[1]).resolve()
    return validate_patrol(patrol_dir)


if __name__ == "__main__":
    sys.exit(main())
