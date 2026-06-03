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
    parse_fasta_document,
)
from bijux_proteomics.targeted import (
    DiscoveryTargetedPeptideSelectionEntry,
    TargetedAssayInterferenceReason,
    TargetedAssayInterferenceRiskTier,
    TargetedPeptideCandidateSource,
    build_targeted_assay_interference_report,
    build_targeted_transition_selection_report,
    render_targeted_assay_interference_assay_tsv,
    render_targeted_assay_interference_panel_tsv,
    render_targeted_assay_interference_transition_tsv,
)


def _selected_peptide(
    *,
    protein_ref: str,
    protein_group_id: str,
    peptide: str,
    rank: int = 1,
    uniqueness_class: PeptideUniquenessClass = PeptideUniquenessClass.UNIQUE,
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
        replicate_consistency=0.95,
        primary_evidence_class=PeptideEvidenceClass.STRONG,
        uniqueness_class=uniqueness_class,
        uniqueness_score=1.0
        if uniqueness_class is PeptideUniquenessClass.UNIQUE
        else 0.4,
        detectability_score=0.9,
        detectability_tier=PeptideDetectabilityTier.HIGH,
        suitability_score=0.9,
        liability_tier=PeptideChemicalLiabilityTier.PREFERRED,
        liability_codes=(),
        selection_score=0.9,
        selection_reasons=("selected for targeted follow-up",),
    )


def _library_entry(
    peptide: str,
    *,
    protein_ref: str,
    retention_time_minutes: float | None,
) -> SpectralLibraryEntry:
    precursor_mz = calculate_peptide_mz(peptide, charge=2)
    fragments = calculate_fragment_ions(
        peptide,
        charges=(1,),
        series=(FragmentIonSeries.Y, FragmentIonSeries.B),
    )
    mz_by_label = {
        f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}": fragment.mz_monoisotopic
        for fragment in fragments
    }
    peaks = (
        SpectrumPeak(mz=mz_by_label["y7+1"], intensity=1000.0),
        SpectrumPeak(mz=mz_by_label["y6+1"], intensity=850.0),
        SpectrumPeak(mz=mz_by_label["y5+1"], intensity=700.0),
        SpectrumPeak(mz=mz_by_label["b5+1"], intensity=300.0),
        SpectrumPeak(mz=175.0, intensity=200.0),
    )
    spectrum = SpectrumModel(
        spectrum_id=f"library:{peptide}",
        title=f"SEQ={peptide}|PEPTIDE={peptide}|PROTEINS={protein_ref}",
        precursor_mz=precursor_mz,
        precursor_charge=2,
        retention_time_seconds=(
            None if retention_time_minutes is None else retention_time_minutes * 60.0
        ),
        peaks=peaks,
    )
    return SpectralLibraryEntry(
        library_entry_id=f"mgf:1:SEQ={peptide}|PEPTIDE={peptide}|PROTEINS={protein_ref}",
        source_format=SpectralLibraryFormat.MGF,
        spectrum_id=spectrum.spectrum_id,
        precursor_mz=precursor_mz,
        precursor_charge=2,
        peptide_sequence=peptide,
        canonical_peptide=peptide,
        modification_count=0,
        protein_refs=(protein_ref,),
        target_decoy_label=TargetDecoyLabel.TARGET,
        spectrum=spectrum,
    )


def test_targeted_assay_interference_downgrades_isobaric_competitors_before_panel_export() -> (
    None
):
    selected_peptides = (
        _selected_peptide(
            protein_ref="P00001",
            protein_group_id="protein_group_1",
            peptide="AAALIGHTR",
        ),
        _selected_peptide(
            protein_ref="P00002",
            protein_group_id="protein_group_2",
            peptide="AAAIIGHTR",
        ),
        _selected_peptide(
            protein_ref="P00003",
            protein_group_id="protein_group_3",
            peptide="PEPTIDER",
        ),
    )
    spectral_library_entries = (
        _library_entry("AAALIGHTR", protein_ref="P00001", retention_time_minutes=10.0),
        _library_entry("AAAIIGHTR", protein_ref="P00002", retention_time_minutes=10.2),
        _library_entry("PEPTIDER", protein_ref="P00003", retention_time_minutes=25.0),
    )
    transition_selection_report = build_targeted_transition_selection_report(
        selected_peptides,
        spectral_library_entries=spectral_library_entries,
        maximum_transition_count=4,
    )
    protein_records = parse_fasta_document(
        ">sp|P00001|KIN1 GN=KIN1\nAAALIGHTR\n"
        ">sp|P00002|KIN2 GN=KIN2\nAAAIIGHTR\n"
        ">sp|P00003|KIN3 GN=KIN3\nPEPTIDER\n"
    ).accepted_records

    report = build_targeted_assay_interference_report(
        selected_peptides,
        transition_selection_report.peptide_entries,
        protein_records,
        spectral_library_entries=spectral_library_entries,
    )

    assert report.summary.assay_entry_count == 3
    assert report.summary.high_risk_assay_count >= 2
    assert report.summary.downgraded_assay_count >= 2
    assert report.summary.panel_export_assay_count == 1

    risky = {
        entry.peptide_sequence: entry
        for entry in report.assay_entries
        if entry.peptide_sequence in {"AAALIGHTR", "AAAIIGHTR"}
    }
    assert (
        risky["AAALIGHTR"].interference_risk_tier
        is TargetedAssayInterferenceRiskTier.HIGH
    )
    assert risky["AAALIGHTR"].panel_export_allowed is False
    assert (
        TargetedAssayInterferenceReason.PANEL_FRAGMENT_OVERLAP
        in risky["AAALIGHTR"].downgrade_reasons
    )
    assert (
        TargetedAssayInterferenceReason.BACKGROUND_PEPTIDE_OVERLAP
        in risky["AAALIGHTR"].downgrade_reasons
    )
    assert (
        TargetedAssayInterferenceReason.LIBRARY_FRAGMENT_OVERLAP
        in risky["AAALIGHTR"].downgrade_reasons
    )
    assert (
        TargetedAssayInterferenceReason.LIBRARY_COELUTION_COMPETITOR
        in risky["AAALIGHTR"].downgrade_reasons
    )

    safe = next(
        entry for entry in report.assay_entries if entry.peptide_sequence == "PEPTIDER"
    )
    assert safe.panel_export_allowed is True
    assert safe.exported_transition_count >= 3
    assert {entry.peptide_sequence for entry in report.panel_entries} == {"PEPTIDER"}

    assert "panel_export_allowed" in render_targeted_assay_interference_assay_tsv(
        report
    )
    assert "fragment_label" in render_targeted_assay_interference_transition_tsv(report)
    assert "PEPTIDER" in render_targeted_assay_interference_panel_tsv(report)


def test_targeted_assay_interference_keeps_shared_peptide_risk_visible_before_export() -> (
    None
):
    selected_peptides = (
        _selected_peptide(
            protein_ref="P00004",
            protein_group_id="protein_group_shared",
            peptide="AAASHALEDK",
            uniqueness_class=PeptideUniquenessClass.SHARED,
        ),
    )
    transition_selection_report = build_targeted_transition_selection_report(
        selected_peptides,
        spectral_library_entries=(),
        maximum_transition_count=3,
    )
    protein_records = parse_fasta_document(
        ">sp|P00004|KIN4 GN=KIN4\nAAASHALEDK\n>sp|O00005|OFF5 GN=OFF5\nAAASHALEDK\n"
    ).accepted_records

    report = build_targeted_assay_interference_report(
        selected_peptides,
        transition_selection_report.peptide_entries,
        protein_records,
        spectral_library_entries=(),
    )

    entry = report.assay_entries[0]
    assert entry.shared_peptide_penalty > 0.0
    assert TargetedAssayInterferenceReason.SHARED_PEPTIDE in entry.downgrade_reasons
    assert entry.panel_export_caveat
