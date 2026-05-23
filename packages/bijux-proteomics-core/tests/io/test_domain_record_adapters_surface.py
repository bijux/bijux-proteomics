# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain import ContrastKind
from bijux_proteomics.io.formats import (
    ExperimentalDesignRejectedRow,
    FormatValidationIssue,
    build_pairwise_contrast_record,
)
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak
from bijux_proteomics.io.transition_table import (
    TransitionTableEntry,
    TransitionTableRejectedRow,
)


def test_io_contracts_convert_to_canonical_domain_records() -> None:
    spectrum = SpectrumModel(
        spectrum_id="scan=1",
        precursor_mz=523.2,
        peaks=(SpectrumPeak(mz=100.0, intensity=500.0),),
        precursor_charge=2,
    )
    transition = TransitionTableEntry(
        transition_id="y7",
        precursor_id="PEPTIDE/2",
        precursor_charge=2,
        sample_id="sample-a",
        intensity=1000.0,
        peptide_sequence="PEPTIDE",
        protein_ref="P001",
        retention_time_minutes=12.5,
    )
    contrast = build_pairwise_contrast_record(
        left_condition="treated",
        right_condition="control",
        kind=ContrastKind.CASE_CONTROL,
    )

    assert spectrum.to_domain_record().peak_count == 1
    assert transition.to_domain_record().protein_ref == "P001"
    assert transition.to_domain_record().precursor_charge == 2
    assert transition.to_domain_record().retention_time_minutes == 12.5
    assert contrast.kind is ContrastKind.CASE_CONTROL


def test_io_rejections_convert_to_canonical_rejected_evidence() -> None:
    design_rejected = ExperimentalDesignRejectedRow(
        row_number=4,
        values={"sample_id": "sample-a"},
        issues=(
            FormatValidationIssue(
                code="missing_condition",
                message="condition is required",
                line_number=4,
            ),
        ),
    )
    transition_rejected = TransitionTableRejectedRow(
        row_number=8,
        values={"transition_id": "y7"},
        reason="transition row requires intensity",
    )

    assert design_rejected.to_domain_record().record_kind == "sample_metadata"
    assert transition_rejected.to_domain_record().row_number == 8
