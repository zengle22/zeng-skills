#!/usr/bin/env python3
"""Validate review output artifacts against JSON schemas.

Usage:
    python validate.py <batch_dir>
    python validate.py .cr-deep/CR-20260527-001

Exit codes:
    0 - All artifacts valid
    1 - Validation errors found
    2 - Missing required files
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


SCHEMAS_DIR = Path(__file__).parent / "schemas"

ARTIFACT_SCHEMAS = {
    "role-panel.json": "role-panel.schema.json",
    "batch-state.json": "batch-state.schema.json",
    "consolidated-review.json": "problem.schema.json",  # array wrapper
    "review-conflicts.json": "conflict.schema.json",     # array wrapper
    "review-consensus.json": "problem.schema.json",      # array wrapper
    "fix-tasks.json": "fix-task.schema.json",            # array wrapper
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

    # Some schemas wrap arrays (reviews, conflicts, tasks)
    if schema_name in ("problem.schema.json", "conflict.schema.json", "fix-task.schema.json"):
        if isinstance(data, list):
            for i, item in enumerate(data):
                try:
                    jsonschema.validate(item, schema)
                except jsonschema.ValidationError as e:
                    errors.append(f"[{i}] {e.message}")
        else:
            errors.append(f"Expected array, got {type(data).__name__}")
    else:
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            errors.append(e.message)

    return errors


def validate_batch(batch_dir: Path) -> int:
    """Validate all artifacts in a batch directory."""
    if not batch_dir.exists():
        print(f"ERROR: Batch directory not found: {batch_dir}", file=sys.stderr)
        return 2

    total_errors = 0
    checked = 0

    for artifact_name, schema_name in ARTIFACT_SCHEMAS.items():
        file_path = batch_dir / artifact_name
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

    # Check review files in reviews/ subdirectory
    reviews_dir = batch_dir / "reviews"
    if reviews_dir.exists():
        for review_file in reviews_dir.glob("*-review.json"):
            errors = validate_file(review_file, "problem.schema.json")
            checked += 1
            if errors:
                print(f"FAIL  reviews/{review_file.name}")
                for err in errors:
                    print(f"      - {err}")
                total_errors += len(errors)
            else:
                print(f"OK    reviews/{review_file.name}")

    print(f"\nChecked: {checked} files, Errors: {total_errors}")
    return 1 if total_errors > 0 else 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python validate.py <batch_dir>", file=sys.stderr)
        return 2

    batch_dir = Path(sys.argv[1]).resolve()
    return validate_batch(batch_dir)


if __name__ == "__main__":
    sys.exit(main())
