# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared missing-value policy helpers for missingness analysis."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueCorrectionPolicy,
    MissingValueKind,
)
from bijux_proteomics.quantification.contracts.missingness import (
    MissingValueSummaryPolicy,
)
from bijux_proteomics.quantification.matrix import (
    missing_value_kind_to_code,
)

_MISSING_VALUE_KINDS = (
    MissingValueKind.OBSERVED,
    MissingValueKind.ZERO,
    MissingValueKind.NOT_OBSERVED,
    MissingValueKind.FILTERED,
    MissingValueKind.IMPUTED,
    MissingValueKind.CENSORED,
    MissingValueKind.EXCLUDED,
    MissingValueKind.NOT_APPLICABLE,
)
_OBSERVED_VALUE_CODES = np.array(
    [
        missing_value_kind_to_code(MissingValueKind.OBSERVED),
        missing_value_kind_to_code(MissingValueKind.ZERO),
        missing_value_kind_to_code(MissingValueKind.IMPUTED),
    ],
    dtype=np.int8,
)
_MISSING_BURDEN_CODES = np.array(
    [
        missing_value_kind_to_code(MissingValueKind.NOT_OBSERVED),
        missing_value_kind_to_code(MissingValueKind.FILTERED),
        missing_value_kind_to_code(MissingValueKind.CENSORED),
        missing_value_kind_to_code(MissingValueKind.EXCLUDED),
    ],
    dtype=np.int8,
)


def empty_missing_value_counts() -> dict[MissingValueKind, int]:
    return dict.fromkeys(_MISSING_VALUE_KINDS, 0)


def is_missing_burden(kind: MissingValueKind) -> bool:
    return kind in {
        MissingValueKind.NOT_OBSERVED,
        MissingValueKind.FILTERED,
        MissingValueKind.CENSORED,
        MissingValueKind.EXCLUDED,
    }


def apply_missing_value_summary_policy(
    kind: MissingValueKind,
    *,
    policy: MissingValueSummaryPolicy,
) -> MissingValueKind:
    if (
        kind is MissingValueKind.ZERO
        and policy.zero_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED
    ):
        return MissingValueKind.NOT_OBSERVED
    if (
        kind is MissingValueKind.FILTERED
        and policy.filtered_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED
    ):
        return MissingValueKind.NOT_OBSERVED
    return kind


def apply_missing_value_summary_policy_codes(
    missing_kind_codes: np.ndarray,
    *,
    policy: MissingValueSummaryPolicy,
) -> np.ndarray:
    adjusted = missing_kind_codes.copy()
    if policy.zero_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED:
        adjusted[adjusted == missing_value_kind_to_code(MissingValueKind.ZERO)] = (
            missing_value_kind_to_code(MissingValueKind.NOT_OBSERVED)
        )
    if policy.filtered_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED:
        adjusted[adjusted == missing_value_kind_to_code(MissingValueKind.FILTERED)] = (
            missing_value_kind_to_code(MissingValueKind.NOT_OBSERVED)
        )
    return adjusted
