"""Machine-readable lab root public API contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabRootApiBudget:
    """Budget for the durable lab root surface."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class LabRootApiEntry:
    """One stable lab root export."""

    export_name: str
    owner_module: str
    classification: str
    rationale: str


LAB_ROOT_API_BUDGET = LabRootApiBudget(
    max_public_symbols=3,
    max_init_lines=16,
)


def list_lab_root_api_entries() -> tuple[LabRootApiEntry, ...]:
    """Return the curated public root API for the lab package."""

    return (
        LabRootApiEntry(
            export_name="plan_experiment_batches",
            owner_module="bijux_proteomics_lab.planning.assays",
            classification="operational_planning_entrypoint",
            rationale="batch planning is the main package-level entrypoint that turns scientific requirements into executable lab work",
        ),
        LabRootApiEntry(
            export_name="build_advisory_assay_plan",
            owner_module="bijux_proteomics_lab.planning.assays",
            classification="advisory_planning_entrypoint",
            rationale="advisory assay planning remains public so downstream packages can preview follow-up shape before scheduling a concrete batch",
        ),
        LabRootApiEntry(
            export_name="build_executable_assay_plan",
            owner_module="bijux_proteomics_lab.planning.assays",
            classification="execution_planning_entrypoint",
            rationale="executable assay planning is the concrete package-level contract for lab-ready batch instructions",
        ),
    )


__all__ = [
    "LAB_ROOT_API_BUDGET",
    "LabRootApiBudget",
    "LabRootApiEntry",
    "list_lab_root_api_entries",
]
