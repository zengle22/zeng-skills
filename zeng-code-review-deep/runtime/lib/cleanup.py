"""Artifact cleanup — remove old batch directories."""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path


def cleanup_old_batches(output_dir: Path, retention_days: int = 30) -> list[str]:
    """Remove batch directories older than retention_days.

    Returns list of removed directory names.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    removed: list[str] = []

    if not output_dir.exists():
        return removed

    for entry in output_dir.iterdir():
        if not entry.is_dir():
            continue
        if not entry.name.startswith("CR-"):
            continue
        try:
            state_file = entry / "batch-state.json"
            if state_file.exists():
                mtime = datetime.fromtimestamp(state_file.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    shutil.rmtree(entry)
                    removed.append(entry.name)
        except Exception:
            continue

    return removed
