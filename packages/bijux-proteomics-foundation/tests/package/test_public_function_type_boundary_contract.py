# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import hash_payload, to_canonical_json
from bijux_proteomics_foundation.compatibility import compatibility_module_dir
from bijux_proteomics_foundation.testing.public_function_type_boundaries import (
    build_public_function_type_boundary_report,
)


def test_foundation_public_functions_avoid_free_dict_boundaries() -> None:
    report = build_public_function_type_boundary_report(
        (
            hash_payload,
            to_canonical_json,
            compatibility_module_dir,
        )
    )

    assert report.function_count == 3
    assert report.violating_observations == ()
