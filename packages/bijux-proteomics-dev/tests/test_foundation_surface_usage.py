from __future__ import annotations

from bijux_proteomics_dev.api.foundation_surface_usage import (
    FOUNDATION_SURFACE_CONSUMERS_PATH,
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
