# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import IsotopeEnvelopeStatus
from bijux_proteomics.chemistry.isotope_adduct_annotation import (
    annotate_isotope_and_adduct_hypotheses,
)


def test_annotate_isotope_and_adduct_hypotheses_returns_advisory_candidates() -> None:
    report = annotate_isotope_and_adduct_hypotheses(
        sequence="PEPTIDE",
        charge=2,
        adducts=("H+", "Na+", "K+"),
    )

    assert report.sequence == "PEPTIDE"
    assert report.charge == 2
    assert report.envelope_status is IsotopeEnvelopeStatus.PREDICTED
    assert len(report.adduct_hypotheses) == 3
    assert all(hypothesis.advisory_only for hypothesis in report.adduct_hypotheses)
