# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_foundation
from bijux_proteomics_foundation.public_api import (
    FOUNDATION_ROOT_API_BUDGET,
    FoundationRootApiCapability,
    FoundationRootApiEntry,
    list_foundation_root_api_entries,
)


def test_foundation_root_api_ledger_matches_curated_public_exports() -> None:
    entries = list_foundation_root_api_entries()

    assert all(isinstance(entry, FoundationRootApiEntry) for entry in entries)
    assert tuple(entry.export_name for entry in entries) == tuple(
        bijux_proteomics_foundation.__all__
    )


def test_foundation_root_api_ledger_uses_kernel_capabilities_only() -> None:
    entries = list_foundation_root_api_entries()
    observed = {entry.capability for entry in entries}

    assert observed <= {
        FoundationRootApiCapability.IDENTIFIER,
        FoundationRootApiCapability.DOCUMENT_CONTRACT,
        FoundationRootApiCapability.JSON_CONTRACT,
        FoundationRootApiCapability.CANONICAL_SERIALIZATION,
        FoundationRootApiCapability.STABLE_HASHING,
    }
    assert all(entry.kernel_rationale for entry in entries)


def test_foundation_root_api_ledger_names_durable_owner_modules() -> None:
    entries = list_foundation_root_api_entries()

    assert all(
        entry.owner_module.startswith("bijux_proteomics_foundation.")
        for entry in entries
    )
    assert not any("runtime" in entry.owner_module for entry in entries)
    assert not any("knowledge" in entry.owner_module for entry in entries)


def test_foundation_root_api_budget_matches_curated_public_surface() -> None:
    assert FOUNDATION_ROOT_API_BUDGET.max_public_symbols == len(
        bijux_proteomics_foundation.__all__
    )
