"""Error taxonomy for the CLI runtime."""

from __future__ import annotations

from dataclasses import dataclass, field


STATUS_SEMANTICS = {
    "OK": "success",
    "INVALID_REQUEST": "fatal_failure",
    "POLICY_DENIED": "denied",
    "REGISTRY_MISS": "fatal_failure",
    "ELIGIBILITY_DENIED": "denied",
    "PRECONDITION_FAILED": "retryable_failure",
    "PROVISIONAL_SLICE_DISABLED": "denied",
    "INVARIANT_VIOLATION": "fatal_failure",
    "INTERNAL_ERROR": "fatal_failure",
}

EXIT_CODE_MAP = {
    "OK": 0,
    "INVALID_REQUEST": 2,
    "POLICY_DENIED": 3,
    "ELIGIBILITY_DENIED": 3,
    "PRECONDITION_FAILED": 4,
    "PROVISIONAL_SLICE_DISABLED": 4,
    "INVARIANT_VIOLATION": 5,
    "INTERNAL_ERROR": 10,
    "REGISTRY_MISS": 10,
}


@dataclass
class CommandError(Exception):
    """Structured error raised by command handlers."""

    status_code: str
    message: str
    diagnostics: list[str] = field(default_factory=list)
    data: dict[str, object] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)

    @property
    def result_status(self) -> str:
        return STATUS_SEMANTICS[self.status_code]

    @property
    def exit_code(self) -> int:
        return EXIT_CODE_MAP[self.status_code]


def ensure(condition: bool, status_code: str, message: str, diagnostics: list[str] | None = None) -> None:
    if not condition:
        raise CommandError(status_code, message, diagnostics or [])


def parse_int(value: object, *, field_name: str, minimum: int | None = None) -> int:
    if isinstance(value, bool):
        raise CommandError("INVALID_REQUEST", f"{field_name} must be an integer")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str):
        normalized = value.strip()
        try:
            parsed = int(normalized)
        except (TypeError, ValueError) as exc:
            raise CommandError("INVALID_REQUEST", f"{field_name} must be an integer") from exc
    else:
        raise CommandError("INVALID_REQUEST", f"{field_name} must be an integer")
    if minimum is not None and parsed < minimum:
        raise CommandError("INVALID_REQUEST", f"{field_name} must be >= {minimum}")
    return parsed
