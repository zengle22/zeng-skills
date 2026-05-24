#!/usr/bin/env python3
"""Standalone CLI entry point for zeng-code-review-deep.

Usage:
    python run.py --mode commit --ref HEAD~1
    python run.py --mode pr --base main --head feature/x
    python run.py --mode module --path src/services/order/
    python run.py --mode commit --ref HEAD~1 --output-dir .cr-deep --mock
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add runtime to path
_RUNTIME_DIR = Path(__file__).parent / "runtime"
sys.path.insert(0, str(_RUNTIME_DIR))

from runtime.lib.errors import CommandError  # noqa: E402


@dataclass
class StandaloneContext:
    """Minimal CommandContext for standalone execution."""
    workspace_root: Path
    action: str
    payload: dict[str, Any]


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python run.py",
        description="zeng-code-review-deep standalone runtime",
    )
    parser.add_argument("--mode", default="commit", choices=["commit", "pr", "module", "frz"])
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--path")
    parser.add_argument("--frz-ref")
    parser.add_argument("--output-dir", default=".cr-deep")
    parser.add_argument("--mock", action="store_true", help="Run with mock agents")
    parser.add_argument("--pr-description")
    parser.add_argument("--workspace-root", default=Path.cwd().resolve().as_posix())

    args = parser.parse_args()

    payload: dict[str, Any] = {
        "mode": args.mode,
        "ref": args.ref,
        "base": args.base,
        "head": args.head,
        "path": args.path,
        "frz_ref": args.frz_ref,
        "output_dir": args.output_dir,
        "mock": args.mock,
        "pr_description": args.pr_description,
    }

    ctx = StandaloneContext(
        workspace_root=Path(args.workspace_root).resolve(),
        action="run",
        payload=payload,
    )

    # Import here to avoid circular issues after path setup
    from runtime.commands.command import _run_review  # noqa: E402

    try:
        status, message, data, diagnostics, evidence_refs = _run_review(ctx)
        print(f"[{status}] {message}")
        if data:
            for k, v in data.items():
                print(f"  {k}: {v}")
        if diagnostics:
            for d in diagnostics:
                print(f"  DIAG: {d}")
        return 0 if status == "OK" else 1
    except CommandError as exc:
        print(f"[{exc.status_code}] {exc.message}", file=sys.stderr)
        if exc.data:
            for k, v in exc.data.items():
                print(f"  {k}: {v}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())