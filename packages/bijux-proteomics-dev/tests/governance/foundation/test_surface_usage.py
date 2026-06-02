from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.foundation.surface_usage import (
    FOUNDATION_COMPATIBILITY_ALIASES_PATH,
    FOUNDATION_DEAD_EXPORTS_PATH,
    FOUNDATION_SURFACE_CONSUMERS_PATH,
    build_foundation_compatibility_aliases,
    build_foundation_dead_exports,
    build_foundation_surface_consumers,
    public_foundation_surfaces,
    run,
)

pytestmark = pytest.mark.slow


def test_foundation_surface_consumer_matrix_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_foundation_surface_consumer_matrix_covers_public_surfaces() -> None:
    entries = build_foundation_surface_consumers()
    entry_by_module = {entry.module_name: entry for entry in entries}

    assert FOUNDATION_SURFACE_CONSUMERS_PATH.exists()
    assert FOUNDATION_DEAD_EXPORTS_PATH.exists()
    assert FOUNDATION_COMPATIBILITY_ALIASES_PATH.exists()
    assert [entry.module_name for entry in entries] == [
        surface.module_name for surface in public_foundation_surfaces()
    ]
    assert set(
        entry_by_module["bijux_proteomics_foundation"].consumer_distributions
    ) == {
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_foundation.identity.identifiers"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-core",
        "bijux-proteomics-lab",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_foundation.outcomes.refusals"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_foundation.serialization.stable_hashes"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-runtime",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_foundation.serialization.json_contracts"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-runtime",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_foundation.support.states"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_foundation.outcomes.exceptions"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-core",
        "bijux-proteomics-runtime",
    }


def test_foundation_dead_export_report_marks_directly_unused_exports() -> None:
    entries = build_foundation_dead_exports()
    entry_by_module = {entry.module_name: entry for entry in entries}

    assert entry_by_module["bijux_proteomics_foundation"].dead_symbols == ()
    assert entry_by_module[
        "bijux_proteomics_foundation.serialization.stable_hashes"
    ].live_symbols == (
        "StableHashPolicy",
        "default_hash_policy",
    )
    assert entry_by_module[
        "bijux_proteomics_foundation.serialization.stable_hashes"
    ].dead_symbols == (
        "StableHashAlgorithm",
        "hash_model",
        "hash_payload",
        "hash_text",
    )


def test_foundation_compatibility_aliases_only_require_live_wrapper_coverage() -> None:
    entries = build_foundation_compatibility_aliases()

    assert entries == ()
