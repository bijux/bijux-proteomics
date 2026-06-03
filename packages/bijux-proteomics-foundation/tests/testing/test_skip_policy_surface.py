# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math

import pytest

from bijux_proteomics_foundation.testing.skip_policy import (
    SkipCategory,
    format_skip_reason,
    import_or_skip,
    skip_test,
    validate_skip_reason,
)


def test_skip_policy_normalizes_and_formats_reasons() -> None:
    assert validate_skip_reason("  httpx is required for api tests  ") == (
        "httpx is required for api tests"
    )
    assert (
        format_skip_reason(
            category=SkipCategory.OPTIONAL_DEPENDENCY,
            reason="httpx is required for api tests",
        )
        == "optional_dependency: httpx is required for api tests"
    )


@pytest.mark.parametrize("reason", ("", "   ", "not ready", "Not-Ready", "not_ready"))
def test_skip_policy_rejects_hidden_placeholder_reasons(reason: str) -> None:
    with pytest.raises(ValueError, match="skip reason"):
        validate_skip_reason(reason)


def test_skip_test_raises_skip_with_category_and_reason() -> None:
    with pytest.raises(
        pytest.skip.Exception, match="hardware_requirement: GPU is required"
    ):
        skip_test(
            category=SkipCategory.HARDWARE_REQUIREMENT,
            reason="GPU is required",
        )


def test_import_or_skip_returns_module_when_dependency_exists() -> None:
    module = import_or_skip(
        "math",
        category=SkipCategory.OPTIONAL_DEPENDENCY,
        reason="math must be importable for this smoke test",
    )

    assert module is math


def test_import_or_skip_skips_missing_dependency_with_explicit_policy_reason() -> None:
    with pytest.raises(
        pytest.skip.Exception,
        match=(
            "optional_dependency: missing optional dependency fixture proves the "
            "skip message contract"
        ),
    ):
        import_or_skip(
            "bijux_missing_optional_dependency_for_skip_policy_surface",
            category=SkipCategory.OPTIONAL_DEPENDENCY,
            reason="missing optional dependency fixture proves the skip message contract",
        )
