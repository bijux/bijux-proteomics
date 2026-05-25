# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.support.charter import (
    DEFAULT_FOUNDATION_CHARTER,
    DEFAULT_FOUNDATION_CHARTER_ENTRIES,
    DEFAULT_FOUNDATION_MODULE_AUDIT,
    FoundationCharterCapability,
    FoundationModuleClassification,
    list_foundation_capabilities,
    list_foundation_charter_entries,
)

FOUNDATION_SRC_ROOT = Path(
    "packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation"
)


def test_foundation_charter_exposes_exact_shared_primitive_capabilities() -> None:
    assert list_foundation_capabilities() == (
        FoundationCharterCapability.IDENTIFIERS_AND_STATES,
        FoundationCharterCapability.HASHING_AND_ORDERING,
        FoundationCharterCapability.DOCUMENT_CONTRACTS,
        FoundationCharterCapability.REFUSALS_ERRORS_AND_RESULTS,
        FoundationCharterCapability.COMPATIBILITY_AND_MIGRATIONS,
    )


def test_foundation_charter_keeps_non_owned_surfaces_explicit() -> None:
    assert DEFAULT_FOUNDATION_CHARTER.package_name == "bijux-proteomics-foundation"
    assert "workflow execution, provider binding, and operator transport" in (
        DEFAULT_FOUNDATION_CHARTER.excluded_ownership
    )
    assert (
        "downstream package-owned scientific, analytical, runtime, and lab models"
        in (DEFAULT_FOUNDATION_CHARTER.required_inputs)
    )


def test_foundation_charter_entries_stay_release_blocking_and_module_backed() -> None:
    assert list_foundation_charter_entries() == DEFAULT_FOUNDATION_CHARTER_ENTRIES
    assert {entry.capability for entry in DEFAULT_FOUNDATION_CHARTER_ENTRIES} == set(
        DEFAULT_FOUNDATION_CHARTER.capabilities
    )
    assert all(entry.required_modules for entry in DEFAULT_FOUNDATION_CHARTER_ENTRIES)
    assert all(entry.release_blocker for entry in DEFAULT_FOUNDATION_CHARTER_ENTRIES)


def test_foundation_module_audit_covers_every_source_module() -> None:
    audited_paths = {entry.module_path for entry in DEFAULT_FOUNDATION_MODULE_AUDIT}
    source_paths = {
        path.relative_to(FOUNDATION_SRC_ROOT).as_posix()
        for path in FOUNDATION_SRC_ROOT.rglob("*.py")
    }

    assert audited_paths == source_paths


def test_foundation_module_audit_rejects_wrong_owner_and_dead_entries() -> None:
    invalid_entries = {
        entry.module_path: entry.classification
        for entry in DEFAULT_FOUNDATION_MODULE_AUDIT
        if entry.classification
        in {
            FoundationModuleClassification.WRONG_PACKAGE_LOGIC,
            FoundationModuleClassification.DEAD_WEIGHT,
        }
    }

    assert invalid_entries == {}


def test_foundation_thin_abstractions_stay_limited_to_curated_compatibility_paths() -> (
    None
):
    thin_paths = {
        entry.module_path
        for entry in DEFAULT_FOUNDATION_MODULE_AUDIT
        if entry.classification is FoundationModuleClassification.THIN_ABSTRACTION
    }

    assert thin_paths == {
        "__init__.py",
        "testing/__init__.py",
    }
