from __future__ import annotations

from bijux_proteomics_dev.api.foundation_root_consumers import (
    FOUNDATION_ROOT_CONSUMERS_PATH,
    build_foundation_root_consumers,
    run,
    validate_foundation_root_consumers,
)


def test_foundation_root_consumer_matrix_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_foundation_root_consumer_matrix_covers_curated_exports() -> None:
    entries = build_foundation_root_consumers()
    consumers_by_symbol = {entry.symbol_name: entry for entry in entries}

    assert FOUNDATION_ROOT_CONSUMERS_PATH.exists()
    assert all(entry.consumer_modules for entry in entries)
    assert set(consumers_by_symbol["JsonModel"].consumer_distributions) == {
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    }
    assert {
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    } == set(consumers_by_symbol["DocumentSchema"].consumer_distributions)
    assert set(consumers_by_symbol["ProgramId"].consumer_distributions) == {
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
    }


def test_foundation_root_consumer_matrix_has_no_dead_exports() -> None:
    assert validate_foundation_root_consumers() == ()
