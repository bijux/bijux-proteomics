# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bijux_proteomics_foundation.testing.public_function_type_boundaries import (
    build_public_function_type_boundary_report,
)


def test_public_function_type_boundary_report_accepts_typed_boundaries() -> None:
    def typed_boundary(
        payload: Mapping[str, Any],
    ) -> tuple[str, ...]:
        return tuple(payload)

    report = build_public_function_type_boundary_report((typed_boundary,))

    assert report.function_count == 1
    assert report.violating_observations == ()


def test_public_function_type_boundary_report_flags_free_dicts_except_raw_json_names() -> (
    None
):
    def free_dict_input(payload: dict[str, Any]) -> str:
        return ""

    def free_dict_return() -> dict[str, Any]:
        return {}

    def explicit_raw_json(raw_json_payload: dict[str, Any]) -> dict[str, Any]:
        return raw_json_payload

    report = build_public_function_type_boundary_report(
        (free_dict_input, free_dict_return, explicit_raw_json)
    )

    observations = {item.qualified_name: item for item in report.violating_observations}
    input_observation = observations[
        f"{__name__}.test_public_function_type_boundary_report_flags_free_dicts_except_raw_json_names.<locals>.free_dict_input"
    ]
    assert input_observation.offending_parameter_names == ("payload",)
    assert input_observation.has_offending_return_type is False
    return_observation = observations[
        f"{__name__}.test_public_function_type_boundary_report_flags_free_dicts_except_raw_json_names.<locals>.free_dict_return"
    ]
    assert return_observation.offending_parameter_names == ()
    assert return_observation.has_offending_return_type is True
    assert (
        f"{__name__}.test_public_function_type_boundary_report_flags_free_dicts_except_raw_json_names.<locals>.explicit_raw_json"
        not in observations
    )
