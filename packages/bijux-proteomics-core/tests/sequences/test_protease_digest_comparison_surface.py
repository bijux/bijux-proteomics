# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.sequences.protease_digest_comparison import (
    build_protease_digest_comparison_report,
)


def test_build_protease_digest_comparison_report_exposes_changed_peptide_space() -> (
    None
):
    report = build_protease_digest_comparison_report(
        sequence="MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGE",
        source_accession="ALBU_HUMAN",
        proteases=("trypsin", "gluc", "chymotrypsin"),
        min_length=2,
    )

    assert report.baseline_protease == "trypsin"
    assert len(report.entries) == 3
    assert report.entries[0].gained_vs_baseline == ()
    assert report.entries[0].lost_vs_baseline == ()
    assert report.entries[1].gained_vs_baseline or report.entries[1].lost_vs_baseline
