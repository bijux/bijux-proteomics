# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.review_iteration09 import TrustScoreInput, decompose_trust_score


def test_decompose_trust_score_reports_components_penalties_and_final_score() -> None:
    decomposition = decompose_trust_score(
        TrustScoreInput(
            candidate_id="cand-1",
            evidence_inputs={"identification": 0.9, "quant": 0.7},
            weights={"identification": 0.6, "quant": 0.4},
            penalties={"qc": 0.1},
            contradiction_penalty=0.05,
            uncertainty=0.1,
        )
    )

    assert decomposition.candidate_id == "cand-1"
    assert decomposition.weighted_evidence_total == pytest.approx(0.82)
    assert decomposition.penalty_total == 0.1
    assert decomposition.final_score == pytest.approx(0.603)
    assert decomposition.components[0].name == "identification"
