# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted import (
    TargetedPanelCandidateKind,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
)
from bijux_proteomics.workflow import (
    AdvancedTmtWorkflowConfig,
    TargetedValidationWorkflowConfig,
    run_advanced_tmt_workflow,
    run_targeted_validation_workflow,
)

from .workflow_golden_support import assert_workflow_golden_outputs_match


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


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


def test_advanced_tmt_workflow_matches_reviewed_golden_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "advanced_tmt"
    run_advanced_tmt_workflow(
        AdvancedTmtWorkflowConfig(
            result_tsv_path=_multiplex_fixture("maxquant_tmt_interference.tsv"),
            design_tsv_path=_multiplex_fixture("tmt.design.tsv"),
            output_dir=output_dir,
            control_channel="126",
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert_workflow_golden_outputs_match("advanced_tmt", output_dir)


def test_advanced_targeted_workflow_matches_reviewed_golden_outputs(
    tmp_path: Path,
) -> None:
    result_path = tmp_path / "targeted_validation.skyline.tsv"
    design_path = tmp_path / "targeted_validation.design.tsv"
    _write_validation_results(result_path)
    _write_validation_design(design_path)

    output_dir = tmp_path / "advanced_targeted"
    run_targeted_validation_workflow(
        TargetedValidationWorkflowConfig(
            result_tsv_path=result_path,
            design_tsv_path=design_path,
            output_dir=output_dir,
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

    assert_workflow_golden_outputs_match("advanced_targeted", output_dir)
