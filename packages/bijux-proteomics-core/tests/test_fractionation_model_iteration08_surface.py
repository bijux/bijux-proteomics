# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study_metadata_iteration08 import (
    FractionationRecord,
    build_fractionation_aggregation_report,
)


def test_build_fractionation_aggregation_report_tracks_pooling_and_evidence_links() -> None:
    report = build_fractionation_aggregation_report(
        (
            FractionationRecord(
                sample_id="sample-01",
                fraction_id="F1",
                fraction_number=1,
                method="high_ph_reverse_phase",
                pooled=False,
                peptide_evidence_ids=("pep-1", "pep-2"),
                protein_evidence_ids=("prot-1",),
            ),
            FractionationRecord(
                sample_id="sample-01",
                fraction_id="F2",
                fraction_number=2,
                method="high_ph_reverse_phase",
                pooled=True,
                peptide_evidence_ids=("pep-2", "pep-3"),
                protein_evidence_ids=("prot-1", "prot-2"),
            ),
        )
    )

    assert report.fraction_count == 2
    assert report.pooled_fraction_count == 1
    assert report.methods == ("high_ph_reverse_phase",)
    assert report.peptide_evidence_count == 3
    assert report.protein_evidence_count == 2
