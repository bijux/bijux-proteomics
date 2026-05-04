# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab.operations import (
    ValidationStageProgressionInput,
    evaluate_validation_stage_progression_policy,
)


def test_evaluate_validation_stage_progression_policy_requires_thresholds() -> None:
    decision = evaluate_validation_stage_progression_policy(
        payload=ValidationStageProgressionInput(
            candidate_id="cand-1",
            evidence_strength=0.55,
            replication_count=1,
            qc_pass_rate=0.7,
            contradiction_count=0,
        )
    )

    assert decision.eligible_for_validation is False
    assert decision.eligible_for_targeted_follow_up is True
    assert "evidence_strength below validation threshold" in decision.reasons
