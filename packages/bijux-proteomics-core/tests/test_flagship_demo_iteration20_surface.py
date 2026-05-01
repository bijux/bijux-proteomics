# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.external_credibility_iteration20 import (
    FlagshipDemoInput,
    build_final_flagship_proteomics_demo_report,
)


def test_build_final_flagship_proteomics_demo_report_detects_completion() -> None:
    report = build_final_flagship_proteomics_demo_report(
        FlagshipDemoInput(
            demo_id="flagship-01",
            input_artifacts=("raw.mzml", "ids.tsv"),
            completed_stages=("input-ingest", "evidence-graph", "review-packet", "lab-handoff"),
            evidence_graph_ref="evidence://graph/flagship-01",
            review_packet_ref="review://packet/flagship-01",
            lab_handoff_ref="lab://handoff/flagship-01",
        )
    )

    assert report.complete_demo is True
    assert report.input_artifacts == ("ids.tsv", "raw.mzml")
