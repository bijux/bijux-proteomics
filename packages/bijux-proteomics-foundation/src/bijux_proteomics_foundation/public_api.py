"""Machine-readable foundation root public API contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FoundationRootApiCapability(StrEnum):
    """Kernel-level capability classes allowed at the foundation package root."""

    IDENTIFIER = "identifier"
    DOCUMENT_CONTRACT = "document_contract"
    JSON_CONTRACT = "json_contract"
    CANONICAL_SERIALIZATION = "canonical_serialization"
    STABLE_HASHING = "stable_hashing"


@dataclass(frozen=True)
class FoundationRootApiBudget:
    """Budget for the durable foundation root surface."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class FoundationRootApiEntry:
    """One root export and the exact reason it is allowed to stay public."""

    export_name: str
    capability: FoundationRootApiCapability
    owner_module: str
    kernel_rationale: str


FOUNDATION_ROOT_API_BUDGET = FoundationRootApiBudget(
    max_public_symbols=15,
    max_init_lines=110,
)


def list_foundation_root_api_entries() -> tuple[FoundationRootApiEntry, ...]:
    """Return the curated root API ledger for kernel-quality exports."""

    return (
        FoundationRootApiEntry(
            export_name="AssayId",
            capability=FoundationRootApiCapability.IDENTIFIER,
            owner_module="bijux_proteomics_foundation.identity.identifiers",
            kernel_rationale="stable assay identity must be shareable across all downstream packages",
        ),
        FoundationRootApiEntry(
            export_name="BatchId",
            capability=FoundationRootApiCapability.IDENTIFIER,
            owner_module="bijux_proteomics_foundation.identity.identifiers",
            kernel_rationale="batch identity is a cross-package primitive rather than package-local business logic",
        ),
        FoundationRootApiEntry(
            export_name="CandidateId",
            capability=FoundationRootApiCapability.IDENTIFIER,
            owner_module="bijux_proteomics_foundation.identity.identifiers",
            kernel_rationale="candidate identity must remain uniform across runtime, intelligence, and lab surfaces",
        ),
        FoundationRootApiEntry(
            export_name="ClaimId",
            capability=FoundationRootApiCapability.IDENTIFIER,
            owner_module="bijux_proteomics_foundation.identity.identifiers",
            kernel_rationale="claim identity is a shared review primitive and not owned by one downstream package",
        ),
        FoundationRootApiEntry(
            export_name="DocumentSchema",
            capability=FoundationRootApiCapability.DOCUMENT_CONTRACT,
            owner_module="bijux_proteomics_foundation.serialization.document_schema",
            kernel_rationale="document provenance and schema envelopes are foundation-level contracts",
        ),
        FoundationRootApiEntry(
            export_name="EvidenceId",
            capability=FoundationRootApiCapability.IDENTIFIER,
            owner_module="bijux_proteomics_foundation.identity.identifiers",
            kernel_rationale="evidence identity must stay stable across core, knowledge, intelligence, and lab packages",
        ),
        FoundationRootApiEntry(
            export_name="fingerprint_model",
            capability=FoundationRootApiCapability.JSON_CONTRACT,
            owner_module="bijux_proteomics_foundation.serialization.json_contracts",
            kernel_rationale="model fingerprints are a repository-wide serialization primitive",
        ),
        FoundationRootApiEntry(
            export_name="GateId",
            capability=FoundationRootApiCapability.IDENTIFIER,
            owner_module="bijux_proteomics_foundation.identity.identifiers",
            kernel_rationale="gate identity is a shared lifecycle primitive used by review and execution packages",
        ),
        FoundationRootApiEntry(
            export_name="hash_model",
            capability=FoundationRootApiCapability.STABLE_HASHING,
            owner_module="bijux_proteomics_foundation.serialization.stable_hashes",
            kernel_rationale="stable hashing is a kernel primitive for provenance and replay contracts",
        ),
        FoundationRootApiEntry(
            export_name="hash_payload",
            capability=FoundationRootApiCapability.STABLE_HASHING,
            owner_module="bijux_proteomics_foundation.serialization.stable_hashes",
            kernel_rationale="payload hashing is needed by multiple packages for artifact integrity and replay",
        ),
        FoundationRootApiEntry(
            export_name="hash_text",
            capability=FoundationRootApiCapability.STABLE_HASHING,
            owner_module="bijux_proteomics_foundation.serialization.stable_hashes",
            kernel_rationale="text hashing is a minimal canonical helper that does not encode product logic",
        ),
        FoundationRootApiEntry(
            export_name="JsonModel",
            capability=FoundationRootApiCapability.JSON_CONTRACT,
            owner_module="bijux_proteomics_foundation.serialization.json_contracts",
            kernel_rationale="the shared JSON model base is a cross-package contract primitive",
        ),
        FoundationRootApiEntry(
            export_name="ProgramId",
            capability=FoundationRootApiCapability.IDENTIFIER,
            owner_module="bijux_proteomics_foundation.identity.identifiers",
            kernel_rationale="program identity must not fork across domain, runtime, and lab package boundaries",
        ),
        FoundationRootApiEntry(
            export_name="TargetId",
            capability=FoundationRootApiCapability.IDENTIFIER,
            owner_module="bijux_proteomics_foundation.identity.identifiers",
            kernel_rationale="target identity is a universal domain primitive across the repository",
        ),
        FoundationRootApiEntry(
            export_name="to_canonical_json",
            capability=FoundationRootApiCapability.CANONICAL_SERIALIZATION,
            owner_module="bijux_proteomics_foundation.serialization.canonical_json",
            kernel_rationale="canonical JSON serialization is a kernel-level interoperability primitive",
        ),
    )


__all__ = [
    "FOUNDATION_ROOT_API_BUDGET",
    "FoundationRootApiBudget",
    "FoundationRootApiCapability",
    "FoundationRootApiEntry",
    "list_foundation_root_api_entries",
]
