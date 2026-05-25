# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import PurePath

from bijux_proteomics_foundation.testing.pytest_markers import (
    derive_default_test_markers,
)


def test_default_test_markers_classify_benchmark_and_external_data_surfaces() -> None:
    derived = derive_default_test_markers(
        PurePath("packages/bijux-proteomics-core/tests/benchmarks/test_external_dda_trial_surface.py"),
        benchmark_dirs=("benchmarks", "performance"),
        external_data_name_tokens=("external_",),
    )

    assert derived == ("benchmark", "external_data")


def test_default_test_markers_classify_integration_surfaces_without_unit_fallback() -> (
    None
):
    derived = derive_default_test_markers(
        PurePath("packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py"),
        benchmark_dirs=("performance",),
        integration_dirs=("api", "execution", "workflows"),
    )

    assert derived == ("benchmark", "integration")


def test_default_test_markers_fall_back_to_unit_for_fast_local_surfaces() -> None:
    derived = derive_default_test_markers(
        PurePath("packages/bijux-proteomics-foundation/tests/serialization/test_canonical_json_surface.py"),
        benchmark_dirs=("performance",),
    )

    assert derived == ("unit",)
