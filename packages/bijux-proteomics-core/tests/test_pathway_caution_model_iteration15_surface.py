# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.intelligence_iteration15 import (
    PathwayInterpretationState,
    build_pathway_network_caution_report,
)


def test_build_pathway_network_caution_report_refuses_mechanistic_overreach() -> None:
    report = build_pathway_network_caution_report(
        pathway_id="pathway-egfr",
        supporting_evidence_count=3,
        contradiction_count=1,
        claims_mechanistic_truth=True,
    )

    assert (
        report.interpretation_state
        is PathwayInterpretationState.MECHANISTIC_CLAIM_REFUSED
    )
    codes = {issue.code for issue in report.issue_list}
    assert "mechanistic_overreach" in codes
