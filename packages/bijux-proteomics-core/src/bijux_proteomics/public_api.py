"""Machine-readable core root public API contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoreRootApiBudget:
    """Budget for the durable core root surface."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class CoreRootApiEntry:
    """One stable core root export."""

    export_name: str
    owner_module: str
    classification: str
    rationale: str


CORE_ROOT_API_BUDGET = CoreRootApiBudget(
    max_public_symbols=5,
    max_init_lines=57,
)


def list_core_root_api_entries() -> tuple[CoreRootApiEntry, ...]:
    """Return the curated public root API for the core package."""

    return (
        CoreRootApiEntry(
            export_name="DigestPolicy",
            owner_module="bijux_proteomics.sequences.digestion",
            classification="essential_scientific_contract",
            rationale="stable digestion policy entrypoint for public callers",
        ),
        CoreRootApiEntry(
            export_name="parse_fasta_document",
            owner_module="bijux_proteomics.sequences",
            classification="essential_scientific_contract",
            rationale="stable FASTA parsing entrypoint for public callers",
        ),
        CoreRootApiEntry(
            export_name="parse_experimental_design_table",
            owner_module="bijux_proteomics.io.formats",
            classification="essential_scientific_contract",
            rationale="stable design-table parsing entrypoint for public callers",
        ),
        CoreRootApiEntry(
            export_name="build_normalized_run_bundle",
            owner_module="bijux_proteomics.io.formats",
            classification="essential_scientific_contract",
            rationale="stable normalized run-bundle entrypoint for public callers",
        ),
        CoreRootApiEntry(
            export_name="build_fdr_audit_trail",
            owner_module="bijux_proteomics.identification",
            classification="essential_scientific_contract",
            rationale="stable FDR audit entrypoint for public callers",
        ),
    )


__all__ = [
    "CORE_ROOT_API_BUDGET",
    "CoreRootApiBudget",
    "CoreRootApiEntry",
    "list_core_root_api_entries",
]
