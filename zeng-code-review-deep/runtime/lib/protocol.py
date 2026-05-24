"""Protocol handling for structured file requests and responses."""

from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.lib.errors import CommandError, EXIT_CODE_MAP, STATUS_SEMANTICS, ensure
from runtime.lib.fs import load_json, resolve_workspace_root, to_canonical_path, write_json


@dataclass
class CommandContext:
    request_path: Path
    response_path: Path
    evidence_path: Path | None
    request: dict[str, Any]
    workspace_root: Path
    group: str
    action: str
    command: str
    strict: bool

    @property
    def payload(self) -> dict[str, Any]:
        payload = self.request.get("payload", {})
        ensure(isinstance(payload, dict), "INVALID_REQUEST", "payload must be an object")
        return payload

    @property
    def trace(self) -> dict[str, Any]:
        trace = self.request.get("trace", {})
        ensure(isinstance(trace, dict), "INVALID_REQUEST", "trace must be an object")
        return trace


@dataclass(frozen=True)
class ExecutionRunnerStartRequest:
    runner_scope_ref: str
    entry_mode: str
    queue_ref: str
    runner_run_id: str

    @classmethod
    def from_command_context(cls, ctx: CommandContext, *, default_entry_mode: str | None = None) -> "ExecutionRunnerStartRequest | None":
        payload = ctx.payload
        runner_scope_ref = str(payload.get("runner_scope_ref") or "").strip()
        entry_mode = str(payload.get("entry_mode") or default_entry_mode or "").strip().lower()
        if not runner_scope_ref and not entry_mode:
            return None
        ensure(runner_scope_ref, "INVALID_REQUEST", "runner_scope_missing: runner_scope_ref is required")
        ensure(entry_mode in {"start", "resume"}, "INVALID_REQUEST", "entry_mode must be start or resume")
        queue_ref = str(payload.get("queue_ref") or "artifacts/jobs/ready").strip() or "artifacts/jobs/ready"
        runner_run_id = str(payload.get("runner_run_id") or ctx.trace.get("run_ref") or ctx.request["request_id"]).strip()
        ensure(runner_run_id, "INVALID_REQUEST", "runner_run_id is required")
        return cls(
            runner_scope_ref=runner_scope_ref,
            entry_mode=entry_mode,
            queue_ref=queue_ref,
            runner_run_id=runner_run_id,
        )


@dataclass(frozen=True)
class ExecutionRunnerRunRef:
    runner_run_ref: str
    runner_context_ref: str
    entry_receipt_ref: str
    runner_scope_ref: str
    entry_mode: str
    queue_ref: str
    started_at: str
    runner_run_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "runner_run_ref": self.runner_run_ref,
            "runner_context_ref": self.runner_context_ref,
            "entry_receipt_ref": self.entry_receipt_ref,
            "runner_scope_ref": self.runner_scope_ref,
            "entry_mode": self.entry_mode,
            "queue_ref": self.queue_ref,
            "started_at": self.started_at,
            "runner_run_id": self.runner_run_id,
        }


@dataclass(frozen=True)
class RunnerEntryReceipt:
    runner_run_ref: str
    runner_context_ref: str
    entry_receipt_ref: str
    entry_mode: str
    started_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "runner_run_ref": self.runner_run_ref,
            "runner_context_ref": self.runner_context_ref,
            "entry_receipt_ref": self.entry_receipt_ref,
            "entry_mode": self.entry_mode,
            "started_at": self.started_at,
        }


def load_context(args: Namespace) -> CommandContext:
    request_path = Path(args.request).resolve()
    request = load_json(request_path)
    for field in ("api_version", "command", "request_id", "workspace_root", "actor_ref", "trace", "payload"):
        ensure(field in request, "INVALID_REQUEST", f"missing request field: {field}")
    ensure(request.get("api_version") == "v1", "INVALID_REQUEST", "unsupported api_version")
    expected = f"{args.group}.{args.action}"
    ensure(request.get("command") == expected, "INVALID_REQUEST", f"request command must be {expected}")
    workspace_root = resolve_workspace_root(request.get("workspace_root"), args.workspace_root, request_path)
    response_path = Path(args.response_out)
    if not response_path.is_absolute():
        response_path = workspace_root / response_path
    evidence_path = Path(args.evidence_out) if args.evidence_out else None
    if evidence_path and not evidence_path.is_absolute():
        evidence_path = workspace_root / evidence_path
    return CommandContext(
        request_path=request_path,
        response_path=response_path.resolve(),
        evidence_path=evidence_path.resolve() if evidence_path else None,
        request=request,
        workspace_root=workspace_root,
        group=args.group,
        action=args.action,
        command=expected,
        strict=args.strict,
    )


def build_response(
    ctx: CommandContext,
    status_code: str,
    message: str,
    data: dict[str, Any] | None = None,
    diagnostics: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "api_version": "v1",
        "command": ctx.command,
        "request_id": ctx.request["request_id"],
        "result_status": STATUS_SEMANTICS[status_code],
        "status_code": status_code,
        "exit_code": EXIT_CODE_MAP[status_code],
        "message": message,
        "data": data or {},
        "diagnostics": diagnostics or [],
        "evidence_refs": evidence_refs or [],
    }
    if status_code == "OK":
        ensure("canonical_path" in payload["data"], "INVARIANT_VIOLATION", "successful response requires data.canonical_path")
    return payload


def persist_response(ctx: CommandContext, response: dict[str, Any]) -> int:
    write_json(ctx.response_path, response)
    if ctx.evidence_path:
        evidence = {
            "api_version": "v1",
            "command": ctx.command,
            "request_id": ctx.request["request_id"],
            "response_ref": to_canonical_path(ctx.response_path, ctx.workspace_root),
            "trace": ctx.trace,
        }
        write_json(ctx.evidence_path, evidence)
    return int(response["exit_code"])


def run_with_protocol(args: Namespace, handler) -> int:
    ctx = load_context(args)
    try:
        status_code, message, data, diagnostics, evidence_refs = handler(ctx)
        response = build_response(ctx, status_code, message, data, diagnostics, evidence_refs)
    except CommandError as exc:
        response = build_response(
            ctx,
            exc.status_code,
            exc.message,
            exc.data,
            exc.diagnostics,
            exc.evidence_refs,
        )
    return persist_response(ctx, response)
