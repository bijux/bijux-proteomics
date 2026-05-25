# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted import (
    TargetedPanelCandidateKind,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
    TargetedValidationVerdict,
)
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.workflow import (
    AdvancedTargetedAssayReliabilityStatus,
    TargetedResultSourceKind,
    TargetedValidationWorkflowConfig,
    run_targeted_validation_workflow,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def _write_validation_design(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file",
                "control_r1\tcontrol\t1\t1\tcontrol_r1.raw\tcontrol_r1.tsv",
                "control_r2\tcontrol\t2\t1\tcontrol_r2.raw\tcontrol_r2.tsv",
                "treat_r1\ttreatment\t1\t1\ttreat_r1.raw\ttreat_r1.tsv",
                "treat_r2\ttreatment\t2\t1\ttreat_r2.raw\ttreat_r2.tsv",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_validation_results(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t25000\t12.50\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t20000\t12.56\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t27000\t12.48\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t21000\t12.55\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t120000\t12.51\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t98000\t12.57\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t118000\t12.52\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t95000\t12.58\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r1\t90000\t18.40\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r1\t87000\t18.47\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r2\t92000\t18.41\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r2\t86000\t18.48\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r1\t93000\t18.42\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r1\t85000\t18.46\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r2\t91500\t18.40\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r2\t85500\t18.45\tpass",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_run_targeted_validation_workflow_exports_confirmed_contradicted_and_inconclusive_claims(
    tmp_path: Path,
) -> None:
    result_path = tmp_path / "targeted_validation.skyline.tsv"
    design_path = tmp_path / "targeted_validation.design.tsv"
    _write_validation_results(result_path)
    _write_validation_design(design_path)

    report = run_targeted_validation_workflow(
        TargetedValidationWorkflowConfig(
            result_tsv_path=result_path,
            design_tsv_path=design_path,
            output_dir=tmp_path / "advanced_targeted_review",
            discovery_claims=(
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P11111",
                    candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    display_label="P11111 robust candidate",
                    target_protein_ref="P11111",
                    priority_rank=1,
                    final_score=0.92,
                    penalty_total=0.0,
                    discovery_effect_size=1.3,
                    support_count=4,
                    robustness_score=0.88,
                    assay_feasibility_score=0.91,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="strong discovery support",
                ),
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P22222",
                    candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    display_label="P22222 flat conflict candidate",
                    target_protein_ref="P22222",
                    priority_rank=2,
                    final_score=0.71,
                    penalty_total=0.0,
                    discovery_effect_size=0.9,
                    support_count=3,
                    robustness_score=0.73,
                    assay_feasibility_score=0.84,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="discovery claimed treatment increase",
                ),
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="ptm_site:P33333:S21",
                    candidate_kind=TargetedPanelCandidateKind.PTM_SITE,
                    display_label="P33333 S21 site candidate",
                    target_protein_ref="P33333",
                    site_key="P33333:S21:phosphorylation",
                    priority_rank=3,
                    final_score=0.67,
                    penalty_total=0.0,
                    discovery_effect_size=0.8,
                    support_count=2,
                    robustness_score=0.66,
                    assay_feasibility_score=0.40,
                    rank_reason_codes=("low_assay_feasibility",),
                    ranking_note="site candidate was not converted into a site-specific assay",
                ),
            ),
            panel_assays=(
                TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P11111:PEPTIDER",
                    biomarker_candidate_id="protein:P11111",
                    biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
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
                TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P22222:AAAAK",
                    biomarker_candidate_id="protein:P22222",
                    biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    biomarker_display_label="P22222 flat conflict candidate",
                    biomarker_priority_rank=2,
                    target_protein_ref="P22222",
                    target_protein_group_id="protein_group_2",
                    gene_symbol="GENE2",
                    peptide_sequence="AAAAK",
                    canonical_peptide="AAAAK",
                    uniqueness_class=PeptideUniquenessClass.UNIQUE,
                    precursor_charge=2,
                    selected_transition_count=3,
                    exported_transition_count=3,
                    warning_note="assay retained for panel export",
                ),
            ),
            case_condition="treatment",
            control_condition="control",
        )
    )

    output_dir = tmp_path / "advanced_targeted_review"
    confirmed_tsv = (
        output_dir / report.manifest.artifacts.confirmed_validation_tsv
    ).read_text(encoding="utf-8")
    contradicted_tsv = (
        output_dir / report.manifest.artifacts.contradicted_validation_tsv
    ).read_text(encoding="utf-8")
    inconclusive_tsv = (
        output_dir / report.manifest.artifacts.inconclusive_validation_tsv
    ).read_text(encoding="utf-8")
    evidence_card_tsv = (
        output_dir / report.manifest.artifacts.evidence_cards_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.confirmed_count == 1
    assert report.summary.contradicted_count == 1
    assert report.summary.inconclusive_count == 1
    assert report.summary.evidence_card_count == 3
    assert report.evidence_cards[0].validation_verdict is TargetedValidationVerdict.CONFIRMED
    assert report.evidence_cards[0].assay_reliability_status is (
        AdvancedTargetedAssayReliabilityStatus.RELIABLE
    )
    assert report.evidence_cards[1].validation_verdict is TargetedValidationVerdict.CONTRADICTED
    assert report.evidence_cards[2].validation_verdict is TargetedValidationVerdict.INCONCLUSIVE
    assert report.evidence_cards[2].assay_reliability_status is (
        AdvancedTargetedAssayReliabilityStatus.NOT_ASSAYED
    )
    assert "protein:P11111" in confirmed_tsv
    assert "protein:P22222" in contradicted_tsv
    assert "ptm_site:P33333:S21" in inconclusive_tsv
    assert "confirmed" in evidence_card_tsv
    assert "contradicted" in evidence_card_tsv
    assert "inconclusive" in evidence_card_tsv
    assert (
        output_dir / report.manifest.artifacts.targeted_assay_qc_workflow_manifest_json
    ).exists()
    assert (output_dir / report.manifest.artifacts.validation_evidence_tsv).exists()


def test_run_targeted_validation_workflow_preserves_assay_reliability_coelution_and_ratio_drift_surfaces(
    tmp_path: Path,
) -> None:
    report = run_targeted_validation_workflow(
        TargetedValidationWorkflowConfig(
            result_tsv_path=_format_fixture("skyline_targeted_qc_results.tsv"),
            design_tsv_path=_format_fixture("skyline_targeted_qc.design.tsv"),
            output_dir=tmp_path / "advanced_targeted_qc_review",
            discovery_claims=(
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P001",
                    candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    display_label="P001 targeted candidate",
                    target_protein_ref="P001",
                    priority_rank=1,
                    final_score=0.84,
                    penalty_total=0.0,
                    discovery_effect_size=-0.7,
                    support_count=3,
                    robustness_score=0.79,
                    assay_feasibility_score=0.90,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="discovery suggested a treatment decrease",
                ),
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P002",
                    candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    display_label="P002 targeted candidate",
                    target_protein_ref="P002",
                    priority_rank=2,
                    final_score=0.76,
                    penalty_total=0.0,
                    discovery_effect_size=-0.8,
                    support_count=2,
                    robustness_score=0.70,
                    assay_feasibility_score=0.83,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="discovery suggested a treatment decrease",
                ),
            ),
            panel_assays=(
                TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P001:PEPTIDEK",
                    biomarker_candidate_id="protein:P001",
                    biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    biomarker_display_label="P001 targeted candidate",
                    biomarker_priority_rank=1,
                    target_protein_ref="P001",
                    target_protein_group_id="protein_group_1",
                    gene_symbol="GENE1",
                    peptide_sequence="PEPTIDEK",
                    canonical_peptide="PEPTIDEK",
                    uniqueness_class=PeptideUniquenessClass.UNIQUE,
                    precursor_charge=2,
                    selected_transition_count=2,
                    exported_transition_count=2,
                    warning_note="assay retained for panel export",
                ),
                TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P002:ACDMPEP",
                    biomarker_candidate_id="protein:P002",
                    biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    biomarker_display_label="P002 targeted candidate",
                    biomarker_priority_rank=2,
                    target_protein_ref="P002",
                    target_protein_group_id="protein_group_2",
                    gene_symbol="GENE2",
                    peptide_sequence="ACDMPEP",
                    canonical_peptide="ACDMPEP",
                    uniqueness_class=PeptideUniquenessClass.UNIQUE,
                    precursor_charge=3,
                    selected_transition_count=2,
                    exported_transition_count=2,
                    warning_note="assay retained for panel export",
                ),
            ),
            case_condition="treatment",
            control_condition="control",
            source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
        )
    )

    output_dir = tmp_path / "advanced_targeted_qc_review"
    evidence_card_tsv = (
        output_dir / report.manifest.artifacts.evidence_cards_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.reliable_target_entry_count >= 1
    assert report.summary.unreliable_target_entry_count >= 1
    assert report.summary.flagged_coelution_target_entry_count >= 1
    assert report.summary.drift_flagged_fragment_ratio_observation_count >= 1
    assert any(card.coelution_issue_count > 0 for card in report.evidence_cards)
    assert any(card.ratio_drift_issue_count > 0 for card in report.evidence_cards)
    assert "coelution_issue_count" in evidence_card_tsv
    assert (output_dir / report.manifest.artifacts.matrix_targets_tsv).exists()
    assert (output_dir / report.manifest.artifacts.assay_qc_coelution_tsv).exists()
    assert (output_dir / report.manifest.artifacts.assay_qc_transition_coelution_tsv).exists()
    assert (output_dir / report.manifest.artifacts.assay_qc_fragment_ratios_tsv).exists()
    assert (output_dir / report.manifest.artifacts.assay_qc_targets_tsv).exists()
