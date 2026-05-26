# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable charter for the shared primitive boundary."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel


class FoundationCharterCapability(StrEnum):
    """Allowed shared primitive capabilities for foundation."""

    IDENTIFIERS_AND_STATES = "identifiers_and_states"
    HASHING_AND_ORDERING = "hashing_and_ordering"
    DOCUMENT_CONTRACTS = "document_contracts"
    REFUSALS_ERRORS_AND_RESULTS = "refusals_errors_and_results"
    COMPATIBILITY_AND_MIGRATIONS = "compatibility_and_migrations"


class FoundationModuleClassification(StrEnum):
    """Allowed audit outcomes for foundation source modules."""

    SHARED_CONTRACT_VALUE = "shared_contract_value"
    THIN_ABSTRACTION = "thin_abstraction"
    WRONG_PACKAGE_LOGIC = "wrong_package_logic"
    DEAD_WEIGHT = "dead_weight"


class FoundationProductCharter(JsonModel):
    """Durable primitive charter for foundation ownership."""

    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(..., min_length=1)
    value_statement: str = Field(..., min_length=1)
    capabilities: tuple[FoundationCharterCapability, ...] = Field(default_factory=tuple)
    required_inputs: tuple[str, ...] = Field(default_factory=tuple)
    excluded_ownership: tuple[str, ...] = Field(default_factory=tuple)


class FoundationCharterEntry(JsonModel):
    """One durable capability owned by foundation."""

    model_config = ConfigDict(extra="forbid")

    capability: FoundationCharterCapability
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    release_blocker: str = Field(..., min_length=1)


class FoundationModuleAuditEntry(JsonModel):
    """Audit record for one foundation source module."""

    model_config = ConfigDict(extra="forbid")

    module_path: str = Field(..., min_length=1)
    classification: FoundationModuleClassification
    anchor_capabilities: tuple[FoundationCharterCapability, ...] = Field(
        default_factory=tuple
    )
    reason: str = Field(..., min_length=1)


DEFAULT_FOUNDATION_CHARTER = FoundationProductCharter(
    package_name="bijux-proteomics-foundation",
    value_statement=(
        "own only the shared primitive layer for identifiers, canonical "
        "serialization, hashing, ordering, compatibility, refusals, errors, "
        "results, provenance, and durable document contracts that the other "
        "five real products reuse directly"
    ),
    capabilities=(
        FoundationCharterCapability.IDENTIFIERS_AND_STATES,
        FoundationCharterCapability.HASHING_AND_ORDERING,
        FoundationCharterCapability.DOCUMENT_CONTRACTS,
        FoundationCharterCapability.REFUSALS_ERRORS_AND_RESULTS,
        FoundationCharterCapability.COMPATIBILITY_AND_MIGRATIONS,
    ),
    required_inputs=(
        "downstream package-owned scientific, analytical, runtime, and lab models",
    ),
    excluded_ownership=(
        "scientific domain semantics and ontology curation",
        "workflow execution, provider binding, and operator transport",
        "recommendation, review, and analytical judgment logic",
        "laboratory planning, handoff, and observed-outcome logic",
    ),
)


DEFAULT_FOUNDATION_CHARTER_ENTRIES: tuple[FoundationCharterEntry, ...] = (
    FoundationCharterEntry(
        capability=FoundationCharterCapability.IDENTIFIERS_AND_STATES,
        owned_surface="Typed identifiers, provenance pointers, support states, and version primitives that multiple product packages must share exactly.",
        required_modules=(
            "identity/identifiers.py",
            "support/provenance.py",
            "support/public_api.py",
            "support/states.py",
            "compatibility/schema_versions.py",
        ),
        release_blocker="Foundation cannot ship if shared identifiers, states, or provenance drift into per-package variants.",
    ),
    FoundationCharterEntry(
        capability=FoundationCharterCapability.HASHING_AND_ORDERING,
        owned_surface="Canonical hashing, fingerprint, and ordering mechanics used to produce stable cross-package artifacts and comparisons.",
        required_modules=(
            "serialization/canonical_json.py",
            "serialization/fingerprints.py",
            "serialization/stable_hashes.py",
            "serialization/stable_values.py",
        ),
        release_blocker="Foundation cannot ship if canonical hashing or ordering is reimplemented differently in downstream packages.",
    ),
    FoundationCharterEntry(
        capability=FoundationCharterCapability.DOCUMENT_CONTRACTS,
        owned_surface="Shared JSON-backed document and model contracts for stable persisted payloads.",
        required_modules=(
            "serialization/document_schema.py",
            "serialization/json_contracts.py",
            "serialization/scientific_values.py",
        ),
        release_blocker="Foundation cannot ship if shared document contracts or JSON model behavior move into package-local semantics.",
    ),
    FoundationCharterEntry(
        capability=FoundationCharterCapability.REFUSALS_ERRORS_AND_RESULTS,
        owned_surface="Shared refusal, error-envelope, and operation-result contracts for deterministic cross-package failure semantics.",
        required_modules=(
            "outcomes/refusals.py",
            "outcomes/failures.py",
            "outcomes/exceptions.py",
            "outcomes/results.py",
        ),
        release_blocker="Foundation cannot ship if shared refusal or error semantics fragment into runtime-, intelligence-, or lab-local contracts.",
    ),
    FoundationCharterEntry(
        capability=FoundationCharterCapability.COMPATIBILITY_AND_MIGRATIONS,
        owned_surface="Version compatibility, import-alias forwarding, and migration primitives that keep persisted contracts evolvable without package-local hacks.",
        required_modules=(
            "compatibility/__init__.py",
            "package_aliases.py",
            "_package_aliases.py",
            "compatibility/import_migrations.py",
            "compatibility/schema_assessments.py",
            "compatibility/schema_migrations.py",
            "compatibility/schema_versions.py",
        ),
        release_blocker="Foundation cannot ship if document compatibility or migrations depend on ad hoc downstream exceptions.",
    ),
)


def _foundation_source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _shared_contract_entry(
    module_path: str,
    capabilities: tuple[FoundationCharterCapability, ...],
    reason: str,
) -> FoundationModuleAuditEntry:
    return FoundationModuleAuditEntry(
        module_path=module_path,
        classification=FoundationModuleClassification.SHARED_CONTRACT_VALUE,
        anchor_capabilities=capabilities,
        reason=reason,
    )


def _classify_foundation_module(module_path: str) -> FoundationModuleAuditEntry:
    if module_path == "__init__.py":
        return FoundationModuleAuditEntry(
            module_path=module_path,
            classification=FoundationModuleClassification.THIN_ABSTRACTION,
            reason="The package root is a constrained export surface over the shared primitive modules.",
        )

    if module_path == "testing/__init__.py":
        return FoundationModuleAuditEntry(
            module_path=module_path,
            classification=FoundationModuleClassification.THIN_ABSTRACTION,
            reason="The testing package root is a constrained private namespace over shared test-support helpers.",
        )

    if module_path == "support/charter.py":
        return _shared_contract_entry(
            module_path,
            (
                FoundationCharterCapability.IDENTIFIERS_AND_STATES,
                FoundationCharterCapability.HASHING_AND_ORDERING,
                FoundationCharterCapability.DOCUMENT_CONTRACTS,
                FoundationCharterCapability.REFUSALS_ERRORS_AND_RESULTS,
                FoundationCharterCapability.COMPATIBILITY_AND_MIGRATIONS,
            ),
            "The machine-readable charter keeps the allowed primitive surface explicit and release-blocking.",
        )

    if module_path == "public_api.py":
        return _shared_contract_entry(
            module_path,
            (FoundationCharterCapability.IDENTIFIERS_AND_STATES,),
            "The machine-readable root API contract keeps the supported shared primitive surface explicit and release-auditable.",
        )

    if module_path in {
        "identity/__init__.py",
        "identity/identifiers.py",
        "support/__init__.py",
        "support/charter.py",
        "support/provenance.py",
        "support/public_api.py",
        "support/states.py",
        "testing/source_tree_complexity.py",
        "testing/skip_policy.py",
        "testing/pytest_markers.py",
        "testing/source_tree_limits.py",
    }:
        return _shared_contract_entry(
            module_path,
            (FoundationCharterCapability.IDENTIFIERS_AND_STATES,),
            "Shared identifiers, provenance, state vocabulary, version primitives, skip and marker policy, audited source-tree quality helpers, and the audited root export ledger belong in foundation because every higher package must agree on them.",
        )

    if module_path in {
        "serialization/__init__.py",
        "serialization/canonical_json.py",
        "serialization/fingerprints.py",
        "serialization/stable_hashes.py",
        "serialization/stable_values.py",
    }:
        return _shared_contract_entry(
            module_path,
            (FoundationCharterCapability.HASHING_AND_ORDERING,),
            "Canonical hashing and ordering mechanics belong in foundation so reproducibility stays exact across packages.",
        )

    if module_path in {
        "serialization/document_schema.py",
        "serialization/json_contracts.py",
        "serialization/scientific_values.py",
    }:
        return _shared_contract_entry(
            module_path,
            (FoundationCharterCapability.DOCUMENT_CONTRACTS,),
            "Shared document and JSON model contracts are foundation ownership because they define the reusable persisted shape language.",
        )

    if module_path in {
        "outcomes/failures.py",
        "outcomes/exceptions.py",
        "outcomes/__init__.py",
        "outcomes/refusals.py",
        "outcomes/results.py",
    }:
        return _shared_contract_entry(
            module_path,
            (FoundationCharterCapability.REFUSALS_ERRORS_AND_RESULTS,),
            "Shared refusal, error, and result contracts belong in foundation so failure semantics stay reusable instead of package-local.",
        )

    if module_path in {
        "package_aliases.py",
        "_package_aliases.py",
        "compatibility/import_migrations.py",
        "compatibility/schema_versions.py",
        "compatibility/__init__.py",
        "compatibility/schema_assessments.py",
        "compatibility/schema_migrations.py",
    }:
        return _shared_contract_entry(
            module_path,
            (FoundationCharterCapability.COMPATIBILITY_AND_MIGRATIONS,),
            "Compatibility, import-alias forwarding, and migration primitives belong in foundation because persisted contracts and package bridges must evolve consistently across the suite.",
        )

    raise ValueError(f"unclassified foundation module: {module_path}")


DEFAULT_FOUNDATION_MODULE_AUDIT: tuple[FoundationModuleAuditEntry, ...] = tuple(
    sorted(
        (
            _classify_foundation_module(
                path.relative_to(_foundation_source_root()).as_posix()
            )
            for path in _foundation_source_root().rglob("*.py")
        ),
        key=lambda entry: entry.module_path,
    )
)


def list_foundation_capabilities() -> tuple[FoundationCharterCapability, ...]:
    """Return the exact foundation-owned primitive capabilities."""

    return DEFAULT_FOUNDATION_CHARTER.capabilities


def list_foundation_charter_entries() -> tuple[FoundationCharterEntry, ...]:
    """Return the release-blocking foundation charter entries."""

    return DEFAULT_FOUNDATION_CHARTER_ENTRIES
