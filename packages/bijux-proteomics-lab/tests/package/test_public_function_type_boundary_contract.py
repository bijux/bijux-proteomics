# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation.testing.public_function_type_boundaries import (
    build_public_function_type_boundary_report,
)
from bijux_proteomics_lab.handoffs.serialization import (
    build_canonical_artifact_envelope,
    diff_model_payloads,
    verify_canonical_artifact_envelope,
)


def test_lab_public_functions_avoid_free_dict_boundaries() -> None:
    report = build_public_function_type_boundary_report(
        (
            build_canonical_artifact_envelope,
            diff_model_payloads,
            verify_canonical_artifact_envelope,
        )
    )

    assert report.function_count == 3
    assert report.violating_observations == ()
