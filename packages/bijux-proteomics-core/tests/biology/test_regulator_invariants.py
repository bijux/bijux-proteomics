# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.biology.regulator import (
    ApprovalMode,
    LLMAction,
    LLMAuthorityBoundary,
    LLMFailureMode,
    LLMRegulator,
    PermissionMode,
)


def test_llm_regulator_accepts_valid_invariants() -> None:
    regulator = LLMRegulator(
        model_id="review-model",
        temperature=0.3,
        failure_modes=[LLMFailureMode.DRIFT, LLMFailureMode.OVERCONFIDENCE],
    )

    assert regulator.model_id == "review-model"
    assert regulator.temperature == 0.3


def test_llm_regulator_rejects_blank_model_id() -> None:
    with pytest.raises(ValueError, match="model_id must be non-empty"):
        LLMRegulator(model_id="  ")


def test_llm_regulator_rejects_out_of_range_temperature() -> None:
    with pytest.raises(ValueError, match="temperature must be between 0.0 and 2.0"):
        LLMRegulator(model_id="review-model", temperature=2.5)


def test_llm_regulator_rejects_manual_mode_without_hook() -> None:
    with pytest.raises(ValueError, match="manual approval requires a hook"):
        LLMRegulator(
            model_id="review-model",
            approval_mode=ApprovalMode.MANUAL_APPROVE,
        )


def test_llm_regulator_rejects_overlapping_authority_actions() -> None:
    with pytest.raises(
        ValueError, match="authority actions cannot be both allowed and forbidden"
    ):
        LLMRegulator(
            model_id="review-model",
            authority=LLMAuthorityBoundary(
                allowed_actions=(LLMAction.TUNE_PROBABILITY,),
                forbidden_actions=(LLMAction.TUNE_PROBABILITY,),
                permission=PermissionMode.READ_ONLY,
            ),
        )


def test_llm_regulator_rejects_duplicate_failure_modes() -> None:
    with pytest.raises(ValueError, match="failure_modes must not contain duplicates"):
        LLMRegulator(
            model_id="review-model",
            failure_modes=[LLMFailureMode.DRIFT, LLMFailureMode.DRIFT],
        )
