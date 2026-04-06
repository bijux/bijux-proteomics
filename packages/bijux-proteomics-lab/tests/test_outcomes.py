# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab import (
    AssayOutcome,
    ExperimentOutcome,
    FailureClass,
    RerunPolicy,
    recommend_rerun_policy,
)


def test_recommend_rerun_policy_prefers_technical_reruns() -> None:
    outcome = ExperimentOutcome(
        batch_id="batch-1",
        assay_outcomes=[
            AssayOutcome(
                assay_id="assay-1",
                passed=False,
                observation_summary="Plate handling issue.",
                failure_class=FailureClass.TECHNICAL,
            )
        ],
        rerun_policy=RerunPolicy.NEVER,
    )

    assert recommend_rerun_policy(outcome) is RerunPolicy.ON_TECHNICAL_FAILURE
