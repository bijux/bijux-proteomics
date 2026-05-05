from __future__ import annotations

from bijux_proteomics_dev.api.foundation_surface_usage import (
    FOUNDATION_COMPATIBILITY_ALIASES_PATH,
    FOUNDATION_DEAD_EXPORTS_PATH,
    FOUNDATION_SURFACE_CONSUMERS_PATH,
    build_foundation_compatibility_aliases,
    build_foundation_dead_exports,
    build_foundation_surface_consumers,
    public_foundation_surfaces,
    run,
)


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
    assert set(entry_by_module["bijux_proteomics_foundation"].consumer_distributions) == {
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    }
    assert set(entry_by_module["bijux_proteomics_foundation.ids"].consumer_distributions) == {
        "bijux-proteomics-core",
        "bijux-proteomics-lab",
    }
    assert set(
        entry_by_module["bijux_proteomics_foundation.refusals"].consumer_distributions
    ) == {
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
    }
    assert set(entry_by_module["bijux_proteomics_foundation.hashing"].consumer_distributions) == {
        "bijux-proteomics-runtime",
    }
    assert set(entry_by_module["bijux_proteomics_foundation.states"].consumer_distributions) == {
        "bijux-proteomics-intelligence",
    }
    assert entry_by_module["bijux_proteomics_foundation.identity"].consumer_modules == ()
    assert entry_by_module["bijux_proteomics_foundation.support"].consumer_modules == ()


def test_foundation_dead_export_report_marks_directly_unused_exports() -> None:
    entries = build_foundation_dead_exports()
    entry_by_module = {entry.module_name: entry for entry in entries}

    assert entry_by_module["bijux_proteomics_foundation"].dead_symbols == ()
    assert entry_by_module["bijux_proteomics_foundation.canonicalization"].dead_symbols == (
        "flatten_tsv_mapping",
        "normalize_json_value",
        "to_canonical_json",
    )
    assert entry_by_module["bijux_proteomics_foundation.hashing"].live_symbols == (
        "StableHashPolicy",
        "default_hash_policy",
    )
    assert entry_by_module["bijux_proteomics_foundation.hashing"].dead_symbols == (
        "StableHashAlgorithm",
        "hash_model",
        "hash_payload",
        "hash_text",
    )


def test_foundation_compatibility_aliases_only_require_live_wrapper_coverage() -> None:
    entries = build_foundation_compatibility_aliases()
    entry_by_module = {entry.module_name: entry for entry in entries}
    required = {
        entry.module_name for entry in entries if entry.requires_alias_test
    }

    assert required == {
        "bijux_proteomics_foundation.hashing",
        "bijux_proteomics_foundation.ids",
        "bijux_proteomics_foundation.refusals",
        "bijux_proteomics_foundation.results",
        "bijux_proteomics_foundation.states",
    }
    assert entry_by_module["bijux_proteomics_foundation.canonicalization"].consumer_modules == ()
    assert entry_by_module["bijux_proteomics_foundation.provenance"].consumer_modules == ()
