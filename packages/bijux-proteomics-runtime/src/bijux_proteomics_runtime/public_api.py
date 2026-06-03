"""Machine-readable runtime root public API contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeRootApiBudget:
    """Budget for the durable runtime root surface."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class RuntimeRootApiEntry:
    """One stable runtime root export."""

    export_name: str
    owner_module: str
    classification: str
    rationale: str


RUNTIME_ROOT_API_BUDGET = RuntimeRootApiBudget(
    max_public_symbols=4,
    max_init_lines=26,
)


def list_runtime_root_api_entries() -> tuple[RuntimeRootApiEntry, ...]:
    """Return the curated public root API for the runtime package.

    Inputs:
    This function takes no runtime arguments and reads the in-module runtime
    root export ledger.

    Outputs:
    Returns the full tuple of ``RuntimeRootApiEntry`` records that describe the
    supported runtime package root exports.

    Failure Modes:
    This function does not raise governed public exceptions under normal
    package import conditions.

    Scientific Caveats:
    The ledger documents supported runtime integration surfaces; it does not
    execute workflows or validate scientific inputs.
    """

    return (
        RuntimeRootApiEntry(
            export_name="AppConfig",
            owner_module="bijux_proteomics_runtime.api",
            classification="stable_entrypoint",
            rationale="runtime app configuration is part of the supported integration boundary",
        ),
        RuntimeRootApiEntry(
            export_name="RunManager",
            owner_module="bijux_proteomics_runtime.runs.manager",
            classification="stable_entrypoint",
            rationale="canonical runtime orchestration belongs to the run-owned execution family",
        ),
        RuntimeRootApiEntry(
            export_name="cli",
            owner_module="bijux_proteomics_runtime.api.cli",
            classification="stable_entrypoint",
            rationale="the runtime CLI is a first-class operator entrypoint",
        ),
        RuntimeRootApiEntry(
            export_name="create_app",
            owner_module="bijux_proteomics_runtime.api",
            classification="stable_entrypoint",
            rationale="HTTP integrations need one canonical app factory at the runtime root",
        ),
    )


__all__ = [
    "RUNTIME_ROOT_API_BUDGET",
    "RuntimeRootApiBudget",
    "RuntimeRootApiEntry",
    "list_runtime_root_api_entries",
]
