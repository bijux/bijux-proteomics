# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.targeted as targeted
from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    calculate_peptide_mz,
)
from bijux_proteomics.identification.peptide_evidence import (
    PeptideEvidenceClass,
    PeptideEvidenceEntry,
)
from bijux_proteomics.identification.contracts import (
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
)
from bijux_proteomics.identification.cross_run_reproducibility import (
    CrossRunReproducibilityClass,
)
from bijux_proteomics.io import (
    ExperimentalDesignEntry,
    SpectralLibraryEntry,
    SpectralLibraryFormat,
    SpectrumModel,
    SpectrumPeak,
)
from bijux_proteomics.io import parse_experimental_design_table
from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideUniquenessClass,
    parse_fasta_document,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def _protein_records():
    return parse_fasta_document(
        ">sp|P00001|KIN1 GN=KIN1\nPEPTIDER\n"
    ).accepted_records


def test_targeted_package_exports_target_matrix_owner_surface() -> None:
    report = targeted.build_skyline_targeted_matrix_report(
        _format_fixture("skyline_targeted_results.tsv")
    )
    rendered = targeted.render_targeted_matrix_missingness_tsv(report)

    assert hasattr(targeted, "build_targeted_matrix_report")
    assert hasattr(targeted, "render_targeted_matrix_retained_transition_tsv")
    assert hasattr(targeted, "render_targeted_matrix_excluded_transition_tsv")
    assert hasattr(targeted, "render_targeted_matrix_missingness_tsv")
    assert report.summary.retained_transition_count == 4
    assert report.rows[1].total_intensity == 273000.0
    assert "no_observation" in rendered


def test_targeted_package_exports_assay_qc_owner_surface() -> None:
    import_report = targeted.build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_qc.design.tsv")
    ).accepted_entries
    report = targeted.build_targeted_assay_qc_report(import_report, design_entries)
    rendered = targeted.render_targeted_assay_qc_target_tsv(report)

    assert hasattr(targeted, "build_targeted_assay_qc_report")
    assert hasattr(targeted, "render_targeted_assay_qc_coelution_tsv")
    assert hasattr(targeted, "render_targeted_assay_qc_transition_coelution_tsv")
    assert hasattr(targeted, "render_targeted_assay_qc_target_tsv")
    assert hasattr(targeted, "render_targeted_assay_qc_transition_qc_tsv")
    assert report.summary.target_qc_entry_count == 8
    assert report.summary.reliable_target_entry_count == 1
    assert "fewer than two coeluting transitions support the target" in rendered


def test_targeted_package_exports_transition_coelution_owner_surface() -> None:
    report = targeted.build_skyline_targeted_transition_coelution_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    rendered = targeted.render_targeted_transition_coelution_target_tsv(report)
    raw_rows = targeted.score_transition_coelution(
        (
            targeted.TargetedTransitionTracePoint(
                target_id="PEPTIDEK/2",
                sample_id="treat_r2",
                transition_id="y7",
                rt=13.3,
                intensity=20000.0,
            ),
            targeted.TargetedTransitionTracePoint(
                target_id="PEPTIDEK/2",
                sample_id="treat_r2",
                transition_id="y8",
                rt=14.0,
                intensity=18000.0,
            ),
        )
    )
    raw_rendered = targeted.render_transition_coelution_tsv(raw_rows)

    assert hasattr(targeted, "build_targeted_transition_coelution_report")
    assert hasattr(targeted, "score_transition_coelution")
    assert hasattr(targeted, "render_transition_coelution_tsv")
    assert hasattr(targeted, "render_targeted_transition_coelution_target_tsv")
    assert hasattr(targeted, "render_targeted_transition_coelution_transition_tsv")
    assert report.summary.target_entry_count == 8
    assert report.summary.flagged_target_entry_count == 3
    assert raw_rows[0].coelution_tier.value == "insufficient"
    assert "passing_transition_count" in raw_rendered
    assert "fewer than two coeluting transitions support the target" in rendered


def test_targeted_package_exports_carryover_owner_surface() -> None:
    import_report = targeted.build_skyline_result_import_report(
        _format_fixture("skyline_targeted_carryover_results.tsv")
    )
    design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_carryover.design.tsv")
    ).accepted_entries
    report = targeted.build_targeted_carryover_report(import_report, design_entries)
    summary_tsv = targeted.render_targeted_carryover_summary_tsv(report)
    candidate_tsv = targeted.render_targeted_carryover_candidates_tsv(report)

    assert hasattr(targeted, "build_targeted_carryover_report")
    assert hasattr(targeted, "render_targeted_carryover_summary_tsv")
    assert hasattr(targeted, "render_targeted_carryover_candidates_tsv")
    assert report.summary.candidate_entry_count == 2
    assert "Skyline\t4\t2\t2\t2\t1" in summary_tsv
    assert "CARRYPEP/2" in candidate_tsv


def test_targeted_package_exports_discovery_peptide_selection_surface() -> None:
    report = targeted.build_discovery_targeted_peptide_selection_report(
        (
            targeted.DiscoveryTargetProteinEntry(
                protein_group_id="protein_group_1",
                representative_protein_ref="P00001",
                protein_refs=("P00001",),
                gene_symbol="KIN1",
                discovery_peptides=("PEPTIDER",),
            ),
        ),
        (
            PeptideEvidenceEntry(
                peptide="PEPTIDER",
                canonical_peptide="PEPTIDER",
                primary_class=PeptideEvidenceClass.STRONG,
                peptide_q_value=0.001,
                accepted=True,
                psm_count=5,
                spectrum_count=5,
                run_count=3,
                detection_frequency=1.0,
                replicate_consistency=0.9,
                condition_specificity=0.1,
                detected_condition_count=2,
                reproducibility_class=CrossRunReproducibilityClass.REPRODUCIBLE,
                best_score=120.0,
                charge_states=(2,),
                run_ids=("run1", "run2", "run3"),
                protein_refs=("P00001",),
                target_decoy_label=TargetDecoyLabel.TARGET,
                target_decoy_contaminant_class=TargetDecoyContaminantClass.TARGET,
                explanation="strong observed peptide support",
            ),
        ),
        _protein_records(),
        top_peptides_per_target=1,
    )
    rendered = targeted.render_discovery_targeted_peptide_selection_selected_tsv(report)

    assert hasattr(targeted, "build_discovery_targeted_peptide_selection_report")
    assert hasattr(targeted, "render_discovery_targeted_peptide_selection_summary_tsv")
    assert hasattr(targeted, "render_discovery_targeted_peptide_selection_selected_tsv")
    assert hasattr(targeted, "render_discovery_targeted_peptide_selection_rejected_tsv")
    assert report.summary.selected_entry_count == 1
    assert "P00001\tprotein_group_1\tKIN1\t1\tobserved_discovery\tPEPTIDER" in rendered


def test_targeted_package_exports_transition_selection_surface() -> None:
    precursor_mz = calculate_peptide_mz("PEPTIDER", charge=2)
    theoretical = calculate_fragment_ions(
        "PEPTIDER",
        charges=(1,),
        series=(FragmentIonSeries.Y,),
    )
    y7 = next(fragment for fragment in theoretical if fragment.ordinal == 7)
    report = targeted.build_targeted_transition_selection_report(
        (
            targeted.DiscoveryTargetedPeptideSelectionEntry(
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                gene_symbol="KIN1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                candidate_source=targeted.TargetedPeptideCandidateSource.OBSERVED_DISCOVERY,
                rank=1,
                observed_in_discovery=True,
                observed_psm_count=5,
                run_count=3,
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
            ),
        ),
        spectral_library_entries=(
            SpectralLibraryEntry(
                library_entry_id="mgf:1:SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P00001",
                source_format=SpectralLibraryFormat.MGF,
                spectrum_id="library:PEPTIDER",
                precursor_mz=precursor_mz,
                precursor_charge=2,
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                modification_count=0,
                protein_refs=("P00001",),
                target_decoy_label=TargetDecoyLabel.TARGET,
                spectrum=SpectrumModel(
                    spectrum_id="library:PEPTIDER",
                    precursor_mz=precursor_mz,
                    precursor_charge=2,
                    peaks=(
                        SpectrumPeak(mz=175.0, intensity=50.0),
                        SpectrumPeak(mz=y7.mz_monoisotopic, intensity=1000.0),
                    ),
                ),
            ),
        ),
        maximum_transition_count=3,
    )
    rendered = targeted.render_targeted_transition_selection_selected_tsv(report)

    assert hasattr(targeted, "build_targeted_transition_selection_report")
    assert hasattr(targeted, "render_targeted_transition_selection_summary_tsv")
    assert hasattr(targeted, "render_targeted_transition_selection_selected_tsv")
    assert hasattr(targeted, "render_targeted_transition_selection_rejected_tsv")
    assert report.summary.peptide_entry_count == 1
    assert "assay_entry_id" in rendered


def test_targeted_package_exports_assay_interference_surface() -> None:
    precursor_mz = calculate_peptide_mz("PEPTIDER", charge=2)
    theoretical = calculate_fragment_ions(
        "PEPTIDER",
        charges=(1,),
        series=(FragmentIonSeries.Y,),
    )
    y7 = next(fragment for fragment in theoretical if fragment.ordinal == 7)
    selected_peptides = (
        targeted.DiscoveryTargetedPeptideSelectionEntry(
            target_protein_ref="P00001",
            target_protein_group_id="protein_group_1",
            gene_symbol="KIN1",
            peptide_sequence="PEPTIDER",
            canonical_peptide="PEPTIDER",
            candidate_source=targeted.TargetedPeptideCandidateSource.OBSERVED_DISCOVERY,
            rank=1,
            observed_in_discovery=True,
            observed_psm_count=5,
            run_count=3,
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
        ),
    )
    spectral_library_entries = (
        SpectralLibraryEntry(
            library_entry_id="mgf:1:SEQ=PEPTIDER|PEPTIDE=PEPTIDER|PROTEINS=P00001",
            source_format=SpectralLibraryFormat.MGF,
            spectrum_id="library:PEPTIDER",
            precursor_mz=precursor_mz,
            precursor_charge=2,
            peptide_sequence="PEPTIDER",
            canonical_peptide="PEPTIDER",
            modification_count=0,
            protein_refs=("P00001",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            spectrum=SpectrumModel(
                spectrum_id="library:PEPTIDER",
                precursor_mz=precursor_mz,
                precursor_charge=2,
                peaks=(
                    SpectrumPeak(mz=175.0, intensity=50.0),
                    SpectrumPeak(mz=y7.mz_monoisotopic, intensity=1000.0),
                ),
            ),
        ),
    )
    transition_report = targeted.build_targeted_transition_selection_report(
        selected_peptides,
        spectral_library_entries=spectral_library_entries,
        maximum_transition_count=3,
    )
    report = targeted.build_targeted_assay_interference_report(
        selected_peptides,
        transition_report.peptide_entries,
        _protein_records(),
        spectral_library_entries=spectral_library_entries,
    )
    rendered = targeted.render_targeted_assay_interference_panel_tsv(report)

    assert hasattr(targeted, "build_targeted_assay_interference_report")
    assert hasattr(targeted, "render_targeted_assay_interference_summary_tsv")
    assert hasattr(targeted, "render_targeted_assay_interference_assay_tsv")
    assert hasattr(targeted, "render_targeted_assay_interference_transition_tsv")
    assert hasattr(targeted, "render_targeted_assay_interference_panel_tsv")
    assert report.summary.assay_entry_count == 1
    assert "transition_interference_risk_tier" in rendered


def test_targeted_package_exports_panel_design_surface() -> None:
    report = targeted.build_targeted_panel_design_report(
        biomarker_candidates=(
            targeted.TargetedPanelBiomarkerCandidateInput(
                candidate_id="protein:P00001",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="KIN1",
                target_protein_ref="P00001",
                priority_rank=1,
                final_score=0.9,
                penalty_total=0.0,
                rank_reason_codes=("assay_ready",),
            ),
        ),
        selected_peptides=(
            targeted.TargetedPanelSelectedPeptideInput(
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                gene_symbol="KIN1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                rank=1,
                observed_in_discovery=True,
                observed_psm_count=5,
                run_count=3,
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
                selection_reasons=("selected for targeted follow-up",),
            ),
        ),
        assay_entries=(
            targeted.TargetedPanelAssayInput(
                assay_entry_id="assay:P00001:PEPTIDER",
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                gene_symbol="KIN1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                peptide_rank=1,
                precursor_charge=2,
                precursor_mz=500.2,
                selected_transition_count=3,
                exported_transition_count=3,
                interference_risk_score=0.08,
                interference_risk_tier=targeted.TargetedAssayInterferenceRiskTier.LOW,
                downgrade_reasons=(),
                panel_export_allowed=True,
                panel_export_caveat="assay is retained for panel export because interference evidence remains below the governed refusal threshold",
                source_library_entry_id=None,
            ),
        ),
        transition_entries=(
            targeted.TargetedPanelTransitionInput(
                assay_entry_id="assay:P00001:PEPTIDER",
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                gene_symbol="KIN1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                precursor_charge=2,
                precursor_mz=500.2,
                fragment_label="y7+1",
                ion_type="y",
                fragment_ordinal=7,
                fragment_charge=1,
                fragment_sequence="PEPTIDER",
                fragment_mz=700.3,
                expected_relative_intensity=0.9,
                selected_transition_rank=1,
                interference_risk_score=0.05,
                interference_risk_tier=targeted.TargetedAssayInterferenceRiskTier.LOW,
                downgrade_reasons=(),
                export_allowed=True,
                export_caveat="transition is retained for targeted panel export",
            ),
        ),
    )
    rendered = targeted.render_targeted_panel_design_panel_tsv(report)

    assert hasattr(targeted, "build_targeted_panel_design_report")
    assert hasattr(targeted, "render_targeted_panel_design_summary_tsv")
    assert hasattr(targeted, "render_targeted_panel_design_assay_tsv")
    assert hasattr(targeted, "render_targeted_panel_design_panel_tsv")
    assert hasattr(targeted, "render_targeted_panel_design_omitted_candidate_tsv")
    assert report.summary.retained_assay_count == 1
    assert "transition_id" in rendered


def test_targeted_package_exports_validation_planning_surface() -> None:
    report = targeted.build_validation_experiment_planning_report(
        biomarker_candidates=(
            targeted.ValidationPlanningBiomarkerCandidateInput(
                candidate_id="protein:P00001",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="KIN1",
                target_protein_ref="P00001",
                priority_rank=1,
                final_score=0.9,
                penalty_total=0.0,
                uncertainty=0.1,
                effect_size=1.0,
                adjusted_p_value=0.01,
                support_count=4,
                robustness_score=0.85,
                assay_feasibility_score=0.9,
                rank_reason_codes=("assay_ready",),
                ranking_note="strong validation-ready candidate",
            ),
        ),
        selected_peptides=(
            targeted.ValidationPlanningSelectedPeptideInput(
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                gene_symbol="KIN1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                rank=1,
                observed_in_discovery=True,
                observed_psm_count=5,
                run_count=3,
                detection_frequency=0.95,
                replicate_consistency=0.9,
                primary_evidence_class=PeptideEvidenceClass.STRONG,
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                uniqueness_score=1.0,
                detectability_score=0.9,
                detectability_tier=PeptideDetectabilityTier.HIGH,
                suitability_score=0.9,
                liability_tier=PeptideChemicalLiabilityTier.PREFERRED,
                liability_codes=(),
            ),
        ),
        panel_assays=(
            targeted.ValidationPlanningPanelAssayInput(
                assay_entry_id="assay:P00001:PEPTIDER",
                biomarker_candidate_id="protein:P00001",
                biomarker_candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                biomarker_display_label="KIN1",
                biomarker_priority_rank=1,
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                gene_symbol="KIN1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                uniqueness_score=1.0,
                selected_transition_count=3,
                exported_transition_count=3,
                assay_interference_risk_tier=targeted.TargetedAssayInterferenceRiskTier.LOW,
                warning_codes=(),
                warning_note="assay retained for targeted panel review",
            ),
        ),
        pilot_variance_entries=(
            targeted.ValidationPlanningPilotVarianceInput(
                entity_id="protein:P00001",
                protein_refs=("P00001",),
                observed_sample_count=8,
                missing_fraction=0.1,
                contributing_condition_count=2,
                used_global_variance_fallback=False,
                pooled_log2_stddev=0.25,
            ),
        ),
        policy=targeted.ValidationExperimentPlanningPolicy(proposed_samples_per_group=6),
    )
    rendered = targeted.render_validation_experiment_planning_plan_tsv(report)

    assert hasattr(targeted, "build_validation_experiment_planning_report")
    assert hasattr(targeted, "render_validation_experiment_planning_summary_tsv")
    assert hasattr(targeted, "render_validation_experiment_planning_plan_tsv")
    assert hasattr(targeted, "render_validation_experiment_planning_warning_tsv")
    assert report.summary.planned_assay_count == 1
    assert "recommended_minimum_samples_per_group" in rendered


def test_targeted_package_exports_result_validation_surface(tmp_path: Path) -> None:
    skyline_path = tmp_path / "targeted_validation.skyline.tsv"
    skyline_path.write_text(
        "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t25000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t20000\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t27000\t12.48\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t21000\t12.55\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t120000\t12.51\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t98000\t12.57\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t118000\t12.52\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t95000\t12.58\tpass\n",
        encoding="utf-8",
    )

    import_report = targeted.build_skyline_result_import_report(skyline_path)
    design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_qc.design.tsv")
    ).accepted_entries
    report = targeted.build_targeted_result_validation_report(
        discovery_claims=(
            targeted.TargetedValidationDiscoveryClaimInput(
                candidate_id="protein:P11111",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="P11111 robust candidate",
                target_protein_ref="P11111",
                priority_rank=1,
                final_score=0.91,
                penalty_total=0.0,
                discovery_effect_size=1.0,
                support_count=4,
                robustness_score=0.85,
                assay_feasibility_score=0.92,
                rank_reason_codes=("assay_ready",),
                ranking_note="strong validation-ready candidate",
            ),
        ),
        panel_assays=(
            targeted.TargetedValidationPanelAssayInput(
                assay_entry_id="assay:P11111:PEPTIDER",
                biomarker_candidate_id="protein:P11111",
                biomarker_candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                biomarker_display_label="P11111 robust candidate",
                biomarker_priority_rank=1,
                target_protein_ref="P11111",
                target_protein_group_id="protein_group_1",
                gene_symbol="GENE1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                precursor_charge=2,
                selected_transition_count=3,
                exported_transition_count=3,
                warning_note="assay retained for panel export",
            ),
        ),
        import_report=import_report,
        design_entries=design_entries,
        policy=targeted.TargetedResultValidationPolicy(
            case_condition="treatment",
            control_condition="control",
        ),
    )
    confirmed_tsv = targeted.render_targeted_result_validation_tsv(
        report,
        targeted.TargetedValidationVerdict.CONFIRMED,
    )

    assert hasattr(targeted, "build_targeted_result_validation_report")
    assert hasattr(targeted, "render_targeted_result_validation_summary_tsv")
    assert hasattr(targeted, "render_targeted_result_validation_tsv")
    assert hasattr(targeted, "render_targeted_result_validation_evidence_tsv")
    assert report.summary.confirmed_count == 1
    assert "protein:P11111" in confirmed_tsv


def test_targeted_package_exports_biomarker_stability_surface(tmp_path: Path) -> None:
    skyline_path = tmp_path / "targeted_stability.skyline.tsv"
    skyline_path.write_text(
        "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_b1_r1\t10000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_b1_r1\t8200\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_b2_r2\t10200\t12.48\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_b2_r2\t8300\t12.55\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_b1_r1\t21000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_b1_r1\t17000\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_b2_r2\t20800\t12.48\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_b2_r2\t16800\t12.55\tpass\n",
        encoding="utf-8",
    )
    design_path = tmp_path / "targeted_stability.design.tsv"
    design_path.write_text(
        "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\ttimepoint\tsample_type\n"
        "control_b1_r1\tcontrol\t1\t1\tcontrol_b1_r1.raw\tcontrol_b1_r1.tsv\tb1\tt0\tplasma\n"
        "control_b2_r2\tcontrol\t2\t1\tcontrol_b2_r2.raw\tcontrol_b2_r2.tsv\tb2\tt0\tplasma\n"
        "treat_b1_r1\ttreatment\t1\t1\ttreat_b1_r1.raw\ttreat_b1_r1.tsv\tb1\tt1\tserum\n"
        "treat_b2_r2\ttreatment\t2\t1\ttreat_b2_r2.raw\ttreat_b2_r2.tsv\tb2\tt1\tserum\n",
        encoding="utf-8",
    )

    report = targeted.build_biomarker_stability_report(
        biomarker_candidates=(
            targeted.TargetedValidationDiscoveryClaimInput(
                candidate_id="protein:P11111",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="P11111 stable candidate",
                target_protein_ref="P11111",
                priority_rank=1,
                final_score=0.91,
                penalty_total=0.0,
                discovery_effect_size=1.0,
                support_count=4,
                robustness_score=0.85,
                assay_feasibility_score=0.92,
                rank_reason_codes=("assay_ready",),
                ranking_note="strong validation-ready candidate",
            ),
        ),
        panel_assays=(
            targeted.TargetedValidationPanelAssayInput(
                assay_entry_id="assay:P11111:PEPTIDER",
                biomarker_candidate_id="protein:P11111",
                biomarker_candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                biomarker_display_label="P11111 stable candidate",
                biomarker_priority_rank=1,
                target_protein_ref="P11111",
                target_protein_group_id="protein_group_1",
                gene_symbol="GENE1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                precursor_charge=2,
                selected_transition_count=2,
                exported_transition_count=2,
                warning_note="assay retained",
            ),
        ),
        import_report=targeted.build_skyline_result_import_report(skyline_path),
        design_entries=parse_experimental_design_table(design_path).accepted_entries,
    )
    rendered = targeted.render_biomarker_stability_candidate_tsv(report)

    assert hasattr(targeted, "build_biomarker_stability_report")
    assert hasattr(targeted, "render_biomarker_stability_summary_tsv")
    assert hasattr(targeted, "render_biomarker_stability_tsv")
    assert hasattr(targeted, "render_biomarker_stability_subgroup_tsv")
    assert hasattr(targeted, "render_biomarker_stability_candidate_tsv")
    assert report.summary.candidate_count == 1
    assert "protein:P11111" in rendered


def test_targeted_package_exports_panel_redundancy_surface(tmp_path: Path) -> None:
    skyline_path = tmp_path / "targeted_redundancy.skyline.tsv"
    skyline_path.write_text(
        "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t10000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t8200\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t10500\t12.49\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t8400\t12.55\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t22000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t17800\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t22500\t12.49\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t18100\t12.55\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r1\t8000\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r1\t6600\t18.47\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r2\t8400\t18.41\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r2\t6900\t18.48\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r1\t17600\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r1\t14400\t18.47\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r2\t18000\t18.41\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r2\t14700\t18.48\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\tcontrol_r1\t20000\t16.40\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\tcontrol_r1\t16200\t16.47\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\tcontrol_r2\t20500\t16.42\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\tcontrol_r2\t16600\t16.46\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_r1\t9000\t16.41\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_r1\t7300\t16.48\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_r2\t9200\t16.40\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_r2\t7500\t16.45\tpass\n",
        encoding="utf-8",
    )

    report = targeted.build_panel_redundancy_report(
        biomarker_candidates=(
            targeted.PanelRedundancyCandidateInput(
                candidate_id="protein:P11111",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="REP1",
                target_protein_ref="P11111",
                priority_rank=1,
                final_score=0.92,
                penalty_total=0.05,
                rank_reason_codes=("assay_ready",),
                ranking_note="primary candidate",
            ),
            targeted.PanelRedundancyCandidateInput(
                candidate_id="protein:P22222",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="RED2",
                target_protein_ref="P22222",
                priority_rank=2,
                final_score=0.81,
                penalty_total=0.09,
                rank_reason_codes=("assay_ready",),
                ranking_note="highly correlated neighbor",
            ),
            targeted.PanelRedundancyCandidateInput(
                candidate_id="protein:P33333",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="DISTINCT3",
                target_protein_ref="P33333",
                priority_rank=3,
                final_score=0.76,
                penalty_total=0.10,
                rank_reason_codes=("assay_ready",),
                ranking_note="distinct candidate",
            ),
        ),
        panel_assays=(
            targeted.TargetedValidationPanelAssayInput(
                assay_entry_id="assay:P11111:PEPTIDER",
                biomarker_candidate_id="protein:P11111",
                biomarker_candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                biomarker_display_label="REP1",
                biomarker_priority_rank=1,
                target_protein_ref="P11111",
                target_protein_group_id="protein_group_1",
                gene_symbol="REP1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                precursor_charge=2,
                selected_transition_count=2,
                exported_transition_count=2,
                warning_note="assay retained",
            ),
            targeted.TargetedValidationPanelAssayInput(
                assay_entry_id="assay:P22222:AAAAK",
                biomarker_candidate_id="protein:P22222",
                biomarker_candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                biomarker_display_label="RED2",
                biomarker_priority_rank=2,
                target_protein_ref="P22222",
                target_protein_group_id="protein_group_2",
                gene_symbol="RED2",
                peptide_sequence="AAAAK",
                canonical_peptide="AAAAK",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                precursor_charge=2,
                selected_transition_count=2,
                exported_transition_count=2,
                warning_note="assay retained",
            ),
            targeted.TargetedValidationPanelAssayInput(
                assay_entry_id="assay:P33333:BBBBK",
                biomarker_candidate_id="protein:P33333",
                biomarker_candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                biomarker_display_label="DISTINCT3",
                biomarker_priority_rank=3,
                target_protein_ref="P33333",
                target_protein_group_id="protein_group_3",
                gene_symbol="DISTINCT3",
                peptide_sequence="BBBBK",
                canonical_peptide="BBBBK",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                precursor_charge=2,
                selected_transition_count=2,
                exported_transition_count=2,
                warning_note="assay retained",
            ),
        ),
        import_report=targeted.build_skyline_result_import_report(skyline_path),
        design_entries=(
            ExperimentalDesignEntry(
                sample_id="control_r1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="control_r1.raw",
                identifications_file="control_r1.tsv",
                batch="b1",
            ),
            ExperimentalDesignEntry(
                sample_id="control_r2",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="control_r2.raw",
                identifications_file="control_r2.tsv",
                batch="b1",
            ),
            ExperimentalDesignEntry(
                sample_id="treat_r1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="treat_r1.raw",
                identifications_file="treat_r1.tsv",
                batch="b1",
            ),
            ExperimentalDesignEntry(
                sample_id="treat_r2",
                condition="treatment",
                replicate=2,
                fraction=1,
                spectra_file="treat_r2.raw",
                identifications_file="treat_r2.tsv",
                batch="b1",
            ),
        ),
        policy=targeted.PanelRedundancyPolicy(
            minimum_shared_samples=4,
            correlation_threshold=0.95,
        ),
    )
    rendered = targeted.render_panel_redundancy_candidate_tsv(report)

    assert hasattr(targeted, "build_panel_redundancy_report")
    assert hasattr(targeted, "render_panel_redundancy_summary_tsv")
    assert hasattr(targeted, "render_panel_redundancy_cluster_tsv")
    assert hasattr(targeted, "render_panel_redundancy_candidate_tsv")
    assert hasattr(targeted, "render_panel_redundancy_dropped_tsv")
    assert report.summary.cluster_count == 2
    assert report.summary.dropped_candidate_count == 1
    assert "protein:P22222" in rendered
    assert "high_signal_correlation" in rendered


def test_targeted_package_exports_validation_evidence_card_surface() -> None:
    report = targeted.build_validation_evidence_card_report(
        (
            targeted.ValidationEvidenceDiscoveryInput(
                candidate_id="protein:P11111",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="KIN1",
                target_protein_ref="P11111",
                priority_rank=1,
                final_score=0.92,
                weighted_evidence_total=0.92,
                penalty_total=0.02,
                uncertainty=0.04,
                effect_size=1.7,
                adjusted_p_value=0.002,
                support_count=4,
                annotation_labels=("pathway:stress_response", "domain:kinase"),
                rank_reason_codes=("assay_ready",),
                source_ids=("protein-card:KIN1",),
                ranking_note="strong kinase biomarker candidate",
            ),
            targeted.ValidationEvidenceDiscoveryInput(
                candidate_id="protein:P22222",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="KIN2",
                target_protein_ref="P22222",
                priority_rank=2,
                final_score=0.81,
                weighted_evidence_total=0.81,
                penalty_total=0.08,
                uncertainty=0.07,
                effect_size=1.2,
                adjusted_p_value=0.01,
                support_count=3,
                annotation_labels=("pathway:stress_response",),
                rank_reason_codes=("assay_ready",),
                source_ids=("protein-card:KIN2",),
                ranking_note="correlated neighbor candidate",
            ),
        ),
        panel_assays=(
            targeted.ValidationEvidencePanelAssayInput(
                assay_entry_id="assay:P11111:PEPTIDER",
                biomarker_candidate_id="protein:P11111",
                biomarker_candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                biomarker_display_label="KIN1",
                biomarker_priority_rank=1,
                target_protein_ref="P11111",
                target_protein_group_id="protein_group_1",
                gene_symbol="KIN1",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                uniqueness_score=1.0,
                precursor_charge=2,
                precursor_mz=501.25,
                expected_retention_time_minutes=12.5,
                retention_window_start_minutes=11.0,
                retention_window_end_minutes=14.0,
                selected_transition_count=3,
                exported_transition_count=3,
                assay_interference_risk_tier=targeted.TargetedAssayInterferenceRiskTier.LOW,
                warning_note="assay retained for panel export",
            ),
        ),
        targeted_validation_results=(
            targeted.ValidationEvidenceResultInput(
                candidate_id="protein:P11111",
                verdict=targeted.TargetedValidationVerdict.CONFIRMED,
                validation_log2_effect=1.5,
                assay_evidence_count=1,
                confirmed_assay_count=1,
                contradicted_assay_count=0,
                inconclusive_assay_count=0,
                reason_codes=(
                    targeted.TargetedValidationReasonCode.VALIDATION_EFFECT_MATCHES_DISCOVERY,
                ),
                note="targeted validation matches discovery direction and effect",
            ),
        ),
        targeted_validation_assay_evidence=(
            targeted.ValidationEvidenceResultAssayInput(
                candidate_id="protein:P11111",
                assay_entry_id="assay:P11111:PEPTIDER",
                peptide_sequence="PEPTIDER",
                canonical_peptide="PEPTIDER",
                precursor_charge=2,
                uniqueness_class=PeptideUniquenessClass.UNIQUE,
                validation_log2_effect=1.5,
                verdict=targeted.TargetedValidationVerdict.CONFIRMED,
                reason_codes=(
                    targeted.TargetedValidationReasonCode.VALIDATION_EFFECT_MATCHES_DISCOVERY,
                ),
                note="unique assay confirms the discovery signal",
            ),
        ),
        redundancy_entries=(
            targeted.ValidationEvidenceRedundancyInput(
                candidate_id="protein:P22222",
                cluster_id="cluster:001",
                representative_candidate_id="protein:P11111",
                representative=False,
                dropped=True,
                shared_sample_count=4,
                max_redundant_correlation=0.97,
                redundancy_reason_codes=(
                    "high_signal_correlation",
                    "lower_scoring_cluster_member",
                ),
                ranking_note="dropped in favor of the representative correlated marker",
            ),
        ),
    )
    rendered = targeted.render_validation_evidence_card_tsv(report)

    assert hasattr(targeted, "build_validation_evidence_card_report")
    assert hasattr(targeted, "render_validation_evidence_card_summary_tsv")
    assert hasattr(targeted, "render_validation_evidence_card_tsv")
    assert hasattr(targeted, "render_validation_evidence_card_assay_tsv")
    assert hasattr(targeted, "render_validation_evidence_card_warning_tsv")
    assert report.summary.candidate_count == 2
    assert report.summary.confirmed_count == 1
    assert report.summary.deprioritized_as_redundant_count == 1
    assert "protein:P11111" in rendered
    assert "deprioritized_as_redundant" in rendered
