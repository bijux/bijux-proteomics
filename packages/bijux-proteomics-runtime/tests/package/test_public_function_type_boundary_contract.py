# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation.testing.public_function_type_boundaries import (
    build_public_function_type_boundary_report,
)
from bijux_proteomics_runtime.providers.capabilities import (
    validate_runtime_capabilities,
)
from bijux_proteomics_runtime.runs.artifacts import (
    _sign_payload,
    compare_runs,
    load_artifact,
    selection_as_dict,
    validate_human_decision,
    write_artifact,
    write_failure_artifacts,
)
from bijux_proteomics_runtime.runs.manager import run_flow


def test_runtime_public_functions_avoid_free_dict_boundaries() -> None:
    report = build_public_function_type_boundary_report(
        (
            validate_runtime_capabilities,
            compare_runs,
            load_artifact,
            selection_as_dict,
            validate_human_decision,
            write_artifact,
            write_failure_artifacts,
            run_flow,
            _sign_payload,
        )
    )

    assert report.function_count == 9
    assert report.violating_observations == ()
