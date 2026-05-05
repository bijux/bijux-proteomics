from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.foundation_root_consumers import REPO_ROOT
from bijux_proteomics_dev.quality.benchmark_artifacts import (
    BenchmarkArtifactDefinition,
    load_benchmark_artifact_definitions,
)
from bijux_proteomics_dev.quality.benchmark_ownership import (
    BenchmarkOwnerEntry,
    load_benchmark_owners,
)

__all__ = [
    "FOUNDATION_BENCHMARK_SURFACES_PATH",
    "FoundationBenchmarkSurface",
    "build_foundation_benchmark_surfaces",
    "run",
    "validate_foundation_benchmark_surfaces",
]


@dataclass(frozen=True)
class FoundationBenchmarkSurface:
    """One release-governed foundation benchmark surface."""

    benchmark_id: str
    owner_focus_path: str
    metric_name: str
    unit: str
    test_path: str
    payload_record_count: int
    nested_measurement_fields: int
    nested_collection_fields: int


FOUNDATION_BENCHMARK_SURFACES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-benchmark-surfaces.toml"
)
_FOUNDATION_BENCHMARK_TEST_PATH = (
    "packages/bijux-proteomics-foundation/tests/performance/"
    "test_hashing_and_serialization_benchmark_surface.py"
)


def _foundation_owner() -> BenchmarkOwnerEntry:
    owners = {
        entry.package_name: entry for entry in load_benchmark_owners(REPO_ROOT)
    }
    return owners["bijux-proteomics-foundation"]


def _foundation_benchmark_artifacts() -> tuple[BenchmarkArtifactDefinition, ...]:
    return tuple(
        definition
        for definition in load_benchmark_artifact_definitions(REPO_ROOT)
        if definition.package_name == "bijux-proteomics-foundation"
    )


def build_foundation_benchmark_surfaces() -> tuple[FoundationBenchmarkSurface, ...]:
    """Build the governed benchmark surfaces for foundation hot paths."""

    owner = _foundation_owner()
    by_id = {definition.benchmark_id: definition for definition in _foundation_benchmark_artifacts()}
    payload_shape = {
        "payload_record_count": 160,
        "nested_measurement_fields": 6,
        "nested_collection_fields": 5,
    }
    return (
        FoundationBenchmarkSurface(
            benchmark_id="foundation-canonicalization-throughput",
            owner_focus_path=owner.focus_path,
            metric_name=by_id["foundation-canonicalization-throughput"].metric_name,
            unit=by_id["foundation-canonicalization-throughput"].unit,
            test_path=_FOUNDATION_BENCHMARK_TEST_PATH,
            **payload_shape,
        ),
        FoundationBenchmarkSurface(
            benchmark_id="foundation-hashing-throughput",
            owner_focus_path=owner.focus_path,
            metric_name=by_id["foundation-hashing-throughput"].metric_name,
            unit=by_id["foundation-hashing-throughput"].unit,
            test_path=_FOUNDATION_BENCHMARK_TEST_PATH,
            **payload_shape,
        ),
    )


def validate_foundation_benchmark_surfaces() -> tuple[str, ...]:
    """Validate that foundation benchmark governance stays explicit and owner-backed."""

    owner = _foundation_owner()
    surfaces = build_foundation_benchmark_surfaces()
    artifact_ids = {definition.benchmark_id for definition in _foundation_benchmark_artifacts()}
    failures: list[str] = []

    expected_ids = {
        "foundation-canonicalization-throughput",
        "foundation-hashing-throughput",
    }
    if artifact_ids != expected_ids:
        failures.append(
            "foundation benchmark artifact ids drifted away from the governed canonicalization and hashing pair"
        )
    owner_path = REPO_ROOT / owner.focus_path
    if not owner_path.is_dir():
        failures.append(
            "foundation benchmark owner focus path must resolve to the canonical serialization owner directory"
        )
    for surface in surfaces:
        if surface.owner_focus_path != owner.focus_path:
            failures.append(
                f"{surface.benchmark_id} does not point at the declared foundation benchmark owner path"
            )
        if not (REPO_ROOT / surface.test_path).exists():
            failures.append(f"{surface.benchmark_id} references missing benchmark test {surface.test_path}")
        if surface.payload_record_count < 100:
            failures.append(
                f"{surface.benchmark_id} no longer exercises a medium benchmark payload"
            )
    return tuple(failures)


def _toml_text(surfaces: tuple[FoundationBenchmarkSurface, ...]) -> str:
    lines = [
        "# Generated foundation benchmark surface inventory.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.foundation_benchmark_surfaces",
        "",
    ]
    for surface in surfaces:
        lines.extend(
            [
                "[[benchmark_surface]]",
                f'benchmark_id = "{surface.benchmark_id}"',
                f'owner_focus_path = "{surface.owner_focus_path}"',
                f'metric_name = "{surface.metric_name}"',
                f'unit = "{surface.unit}"',
                f'test_path = "{surface.test_path}"',
                f"payload_record_count = {surface.payload_record_count}",
                f"nested_measurement_fields = {surface.nested_measurement_fields}",
                f"nested_collection_fields = {surface.nested_collection_fields}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(surfaces: tuple[FoundationBenchmarkSurface, ...]) -> bool:
    if not FOUNDATION_BENCHMARK_SURFACES_PATH.exists():
        return False
    return FOUNDATION_BENCHMARK_SURFACES_PATH.read_text(encoding="utf-8") == _toml_text(
        surfaces
    )


def run(check: bool = False) -> int:
    surfaces = build_foundation_benchmark_surfaces()
    failures = validate_foundation_benchmark_surfaces()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(surfaces):
            print("foundation benchmark surfaces are up to date")
            return 0
        print("foundation benchmark surfaces are stale; regenerate them")
        return 1
    FOUNDATION_BENCHMARK_SURFACES_PATH.write_text(_toml_text(surfaces), encoding="utf-8")
    print(f"generated foundation benchmark surfaces for {len(surfaces)} cases")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate foundation benchmark surface governance."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the foundation benchmark surface inventory is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
