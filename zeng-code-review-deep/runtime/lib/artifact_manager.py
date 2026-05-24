"""Artifact directory creation, batch-state management, and artifact I/O."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from runtime.lib.errors import CommandError, ensure
from runtime.lib.fs import ensure_parent, load_json, write_json, write_text


class ArtifactManager:
    """Manages the output directory structure for a single review batch."""

    def __init__(self, output_dir: Path, batch_id: str, workspace_root: Path) -> None:
        self.output_dir = output_dir
        self.batch_id = batch_id
        self.workspace_root = workspace_root
        self.batch_dir = output_dir / batch_id
        self._state: dict[str, Any] | None = None

    def init_batch_dir(self, mode: str, ref: str, base_ref: str | None = None) -> None:
        """Create the full directory skeleton and initial batch-state."""
        (self.batch_dir / "input-snapshot").mkdir(parents=True, exist_ok=True)
        (self.batch_dir / "reviews").mkdir(parents=True, exist_ok=True)
        (self.batch_dir / "discussion").mkdir(parents=True, exist_ok=True)
        (self.batch_dir / "auto-patches").mkdir(parents=True, exist_ok=True)

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state = {
            "batch_id": self.batch_id,
            "status": "initializing",
            "mode": mode,
            "ref": ref,
            "base_ref": base_ref,
            "created_at": now,
            "updated_at": now,
            "agents": [],
            "artifacts": [],
            "severity_summary": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
        }
        self._write_state(state)

    def load_state(self) -> dict[str, Any]:
        """Load existing batch-state.json; create if missing."""
        path = self.batch_dir / "batch-state.json"
        if path.exists():
            self._state = load_json(path)
            return self._state
        raise CommandError("PRECONDITION_FAILED", f"batch-state not found: {path}")

    def update_state(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Merge updates into batch-state and persist."""
        state = self.load_state()
        state.update(updates)
        state["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._write_state(state)
        return state

    def set_agent_status(self, agent_id: str, status: str, **extra: Any) -> None:
        """Update or append an agent entry in batch-state."""
        state = self.load_state()
        agents = list(state.get("agents", []))
        for entry in agents:
            if entry.get("agent_id") == agent_id:
                entry["status"] = status
                entry.update(extra)
                break
        else:
            entry = {"agent_id": agent_id, "status": status, **extra}
            agents.append(entry)
        state["agents"] = agents
        self._write_state(state)

    def register_artifact(self, relative_path: str) -> None:
        """Append an artifact path to batch-state artifacts list."""
        state = self.load_state()
        artifacts = list(state.get("artifacts", []))
        if relative_path not in artifacts:
            artifacts.append(relative_path)
        state["artifacts"] = artifacts
        self._write_state(state)

    def write_artifact(self, relative_path: str, payload: dict[str, Any]) -> Path:
        """Write a JSON artifact and register it in batch-state."""
        path = self.batch_dir / relative_path
        write_json(path, payload)
        self.register_artifact(relative_path)
        return path

    def write_text_artifact(self, relative_path: str, text: str) -> Path:
        """Write a text artifact and register it in batch-state."""
        path = self.batch_dir / relative_path
        write_text(path, text)
        self.register_artifact(relative_path)
        return path

    def read_review_json(self, agent_id: str) -> dict[str, Any] | None:
        """Read a single agent review.json if it exists."""
        path = self.batch_dir / "reviews" / f"{agent_id}-review.json"
        if path.exists():
            return load_json(path)
        return None

    def list_review_jsons(self) -> list[str]:
        """List agent IDs that have produced review.json files."""
        reviews_dir = self.batch_dir / "reviews"
        if not reviews_dir.exists():
            return []
        results = []
        for p in reviews_dir.glob("*-review.json"):
            stem = p.stem  # e.g. logic-verifier-review
            agent_id = stem.replace("-review", "")
            results.append(agent_id)
        return results

    def _write_state(self, state: dict[str, Any]) -> None:
        self._state = state
        path = self.batch_dir / "batch-state.json"
        write_json(path, state)


def generate_batch_id() -> str:
    """Generate a batch ID: CR-{YYYYMMDD}-{seq:003d}."""
    now = datetime.datetime.now(datetime.timezone.utc)
    date_prefix = now.strftime("CR-%Y%m%d")
    # Simple sequence based on existing directories for today
    seq = 1
    return f"{date_prefix}-{seq:03d}"
