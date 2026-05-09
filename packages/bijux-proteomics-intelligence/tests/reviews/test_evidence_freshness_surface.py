# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.boards import (
    ReviewEvidenceFreshnessState,
    build_evidence_freshness_report,
)


def test_build_evidence_freshness_report_flags_stale_and_superseded_entries() -> None:
    report = build_evidence_freshness_report(
        evidence_age_days={"ev-fresh": 4, "ev-old": 45},
        superseded_edges={"ev-old": "ev-new"},
        stale_after_days=30,
    )

    by_id = {entry.evidence_id: entry for entry in report.entries}
    assert by_id["ev-fresh"].freshness_state is ReviewEvidenceFreshnessState.FRESH
    assert (
        by_id["ev-old"].freshness_state
        is ReviewEvidenceFreshnessState.SUPERSEDED
    )
    assert by_id["ev-old"].requires_review is True
