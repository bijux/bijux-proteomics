from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.governance.foundation.benchmark_surfaces import (
    FOUNDATION_BENCHMARK_SURFACES_PATH,
    build_foundation_benchmark_surfaces,
    run,
    validate_foundation_benchmark_surfaces,
)

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def test_foundation_benchmark_surface_inventory_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_foundation_benchmark_surface_inventory_tracks_canonicalization_and_hashing() -> None:
    surfaces = {surface.benchmark_id: surface for surface in build_foundation_benchmark_surfaces()}

    assert FOUNDATION_BENCHMARK_SURFACES_PATH.exists()
    assert set(surfaces) == {
        "foundation-canonicalization-throughput",
        "foundation-hashing-throughput",
    }
    assert all(surface.owner_focus_path.endswith("/serialization") for surface in surfaces.values())
    assert all(surface.test_path.endswith("test_hashing_and_serialization_benchmark_surface.py") for surface in surfaces.values())
    assert all(surface.payload_record_count == 160 for surface in surfaces.values())
    assert all(surface.nested_measurement_fields == 6 for surface in surfaces.values())
    assert all(surface.nested_collection_fields == 5 for surface in surfaces.values())
    assert all((REPO_ROOT / surface.owner_focus_path).exists() for surface in surfaces.values())


def test_foundation_benchmark_surface_inventory_is_release_clean() -> None:
    assert validate_foundation_benchmark_surfaces() == ()
