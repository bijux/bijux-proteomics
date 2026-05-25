# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.ptm import (
    PtmSiteProteinCorrectionStatus,
    PtmSiteCorrectionCandidate,
    PtmProteinCorrectionReference,
    correct_site_by_protein,
    render_site_protein_correction_tsv,
)


def test_correct_site_by_protein_blocks_high_confidence_claims_without_matched_protein() -> None:
    rows = correct_site_by_protein(
        (
            PtmSiteCorrectionCandidate(
                site_id="P11111:S5:Phospho",
                protein_id="P11111",
                raw_site_log2fc=1.8,
            ),
            PtmSiteCorrectionCandidate(
                site_id="P22222:Y18:Phospho",
                protein_id="P22222",
                raw_site_log2fc=0.9,
            ),
            PtmSiteCorrectionCandidate(
                site_id="Q9DEC1:S5:Phospho",
                protein_id="Q9DEC1",
                raw_site_log2fc=1.2,
                low_localization=True,
            ),
        ),
        (
            PtmProteinCorrectionReference(
                protein_id="P11111",
                protein_log2fc=0.5,
            ),
            PtmProteinCorrectionReference(
                protein_id="Q9DEC1",
                protein_log2fc=0.4,
            ),
        ),
    )
    by_site = {row.site_id: row for row in rows}

    assert by_site["P11111:S5:Phospho"].corrected_site_log2fc == 1.3
    assert by_site["P11111:S5:Phospho"].correction_status is (
        PtmSiteProteinCorrectionStatus.HIGH_CONFIDENCE_CORRECTED
    )
    assert by_site["P22222:Y18:Phospho"].protein_log2fc is None
    assert by_site["P22222:Y18:Phospho"].corrected_site_log2fc is None
    assert by_site["P22222:Y18:Phospho"].correction_status is (
        PtmSiteProteinCorrectionStatus.MISSING_PROTEIN_BASELINE
    )
    assert by_site["Q9DEC1:S5:Phospho"].corrected_site_log2fc == 0.8
    assert by_site["Q9DEC1:S5:Phospho"].correction_status is (
        PtmSiteProteinCorrectionStatus.CORRECTED_LOW_LOCALIZATION
    )


def test_render_site_protein_correction_tsv_exposes_required_surface() -> None:
    rendered = render_site_protein_correction_tsv(
        correct_site_by_protein(
            (
                PtmSiteCorrectionCandidate(
                    site_id="P11111:S5:Phospho",
                    protein_id="P11111",
                    raw_site_log2fc=1.8,
                ),
            ),
            (
                PtmProteinCorrectionReference(
                    protein_id="P11111",
                    protein_log2fc=0.5,
                ),
            ),
        )
    )

    assert rendered.startswith(
        "site_id\traw_site_log2fc\tprotein_log2fc\tcorrected_site_log2fc\tcorrection_status\n"
    )
    assert (
        "\nP11111:S5:Phospho\t1.8\t0.5\t1.3\thigh_confidence_corrected\n"
        in rendered
    )
