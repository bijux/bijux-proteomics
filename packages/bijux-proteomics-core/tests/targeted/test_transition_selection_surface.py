# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    calculate_peptide_mz,
)
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.peptide_evidence import PeptideEvidenceClass
from bijux_proteomics.io import (
    SpectralLibraryEntry,
    SpectralLibraryFormat,
    SpectrumModel,
    SpectrumPeak,
)
from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted import (
    DiscoveryTargetedPeptideSelectionEntry,
    TargetedPeptideCandidateSource,
    TargetedTransitionSelectionRejectionCode,
    build_targeted_transition_selection_report,
    render_targeted_transition_selection_rejected_tsv,
    render_targeted_transition_selection_selected_tsv,
)


def _selected_peptide(
    *,
    protein_ref: str,
    protein_group_id: str,
    peptide: str,
    rank: int = 1,
) -> DiscoveryTargetedPeptideSelectionEntry:
    return DiscoveryTargetedPeptideSelectionEntry(
        target_protein_ref=protein_ref,
        target_protein_group_id=protein_group_id,
        gene_symbol=protein_ref,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        candidate_source=TargetedPeptideCandidateSource.OBSERVED_DISCOVERY,
        rank=rank,
        observed_in_discovery=True,
        observed_psm_count=6,
        run_count=4,
        detection_frequency=1.0,
        replicate_consistency=0.9,
        primary_evidence_class=PeptideEvidenceClass.STRONG,
        uniqueness_class=PeptideUniquenessClass.UNIQUE,
        uniqueness_score=1.0,
        detectability_score=0.9,
        detectability_tier=PeptideDetectabilityTier.HIGH,
        suitability_score=0.9,
        liability_tier=PeptideChemicalLiabilityTier.PREFERRED,
        liability_codes=(),
        selection_score=0.9,
        selection_reasons=("strong observed peptide support",),
    )


def _library_entry_for_peptide(peptide: str) -> SpectralLibraryEntry:
    precursor_mz = calculate_peptide_mz(peptide, charge=2)
    theoretical = calculate_fragment_ions(
        peptide, charges=(1,), series=(FragmentIonSeries.Y, FragmentIonSeries.B)
    )
    mz_by_label = {
        f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}": fragment.mz_monoisotopic
        for fragment in theoretical
    }
    spectrum = SpectrumModel(
        spectrum_id=f"library:{peptide}",
        title=f"SEQ={peptide}|PEPTIDE={peptide}|PROTEINS=P00001",
        precursor_mz=precursor_mz,
        precursor_charge=2,
        peaks=(
            SpectrumPeak(mz=mz_by_label["y7+1"], intensity=1000.0),
            SpectrumPeak(mz=mz_by_label["y6+1"], intensity=850.0),
            SpectrumPeak(mz=mz_by_label["y5+1"], intensity=700.0),
            SpectrumPeak(mz=mz_by_label["b5+1"], intensity=250.0),
            SpectrumPeak(mz=175.0, intensity=500.0),
        ),
    )
    return SpectralLibraryEntry(
        library_entry_id=f"mgf:1:SEQ={peptide}|PEPTIDE={peptide}|PROTEINS=P00001",
        source_format=SpectralLibraryFormat.MGF,
        spectrum_id=spectrum.spectrum_id,
        precursor_mz=precursor_mz,
        precursor_charge=2,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        modification_count=0,
        protein_refs=("P00001",),
        target_decoy_label=TargetDecoyLabel.TARGET,
        spectrum=spectrum,
    )


def test_targeted_transition_selection_produces_ranked_candidates_with_library_intensity() -> (
    None
):
    report = build_targeted_transition_selection_report(
        (
            _selected_peptide(
                protein_ref="P00001",
                protein_group_id="protein_group_1",
                peptide="PEPTIDER",
            ),
        ),
        spectral_library_entries=(_library_entry_for_peptide("PEPTIDER"),),
        maximum_transition_count=4,
    )

    assert report.summary.peptide_entry_count == 1
    assert report.summary.peptide_with_minimum_transition_count == 1
    assert report.summary.selected_transition_count == 4
    assert report.summary.library_backed_transition_count >= 2

    selected = report.peptide_entries[0]
    assert selected.target_protein_ref == "P00001"
    assert selected.sufficient_transition_support is True
    assert selected.selected_transition_count == 4
    assert selected.source_library_entry_id is not None
    assert [
        fragment.fragment_label for fragment in selected.selected_transitions[:2]
    ] == [
        "y7+1",
        "y6+1",
    ]
    assert selected.selected_transitions[0].expected_relative_intensity == 1.0
    assert (
        selected.selected_transitions[0].selection_score
        >= selected.selected_transitions[1].selection_score
    )

    rejected_codes = {
        code for entry in report.rejected_transitions for code in entry.rejection_codes
    }
    assert TargetedTransitionSelectionRejectionCode.FRAGMENT_TOO_SHORT in rejected_codes
    assert "fragment_label" in render_targeted_transition_selection_selected_tsv(report)
    assert "rejection_codes" in render_targeted_transition_selection_rejected_tsv(
        report
    )


def test_targeted_transition_selection_keeps_short_peptides_visible_when_chemistry_limits_support() -> (
    None
):
    report = build_targeted_transition_selection_report(
        (
            _selected_peptide(
                protein_ref="P00002", protein_group_id="protein_group_2", peptide="PEPT"
            ),
        ),
        spectral_library_entries=(),
        maximum_transition_count=5,
    )

    assert report.summary.peptide_entry_count == 1
    assert report.summary.peptide_with_minimum_transition_count == 0
    assert report.summary.peptide_without_minimum_transition_count == 1

    selected = report.peptide_entries[0]
    assert selected.target_protein_ref == "P00002"
    assert selected.sufficient_transition_support is False
    assert selected.selected_transition_count < 3
    assert any(
        "fewer than the requested minimum number of chemistry-supported transitions"
        in caveat
        for caveat in selected.instrument_caveats
    )
