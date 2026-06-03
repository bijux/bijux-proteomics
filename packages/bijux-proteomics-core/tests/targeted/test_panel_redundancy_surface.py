# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io import ExperimentalDesignEntry
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.panel_design import TargetedPanelCandidateKind
from bijux_proteomics.targeted.panel_redundancy import (
    PanelRedundancyCandidateInput,
    PanelRedundancyPolicy,
    PanelRedundancyReasonCode,
    build_panel_redundancy_report,
    render_panel_redundancy_candidate_tsv,
)
from bijux_proteomics.targeted.result_import import build_skyline_result_import_report
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationPanelAssayInput,
)


def test_panel_redundancy_clusters_same_target_and_highly_correlated_candidates(
    tmp_path: Path,
) -> None:
    skyline_path = tmp_path / "panel_redundancy.skyline.tsv"
    skyline_path.write_text(_skyline_rows(), encoding="utf-8")
    report = build_panel_redundancy_report(
        biomarker_candidates=_candidates(),
        panel_assays=_panel_assays(),
        import_report=build_skyline_result_import_report(skyline_path),
        design_entries=_design_entries(),
        policy=PanelRedundancyPolicy(
            minimum_shared_samples=4,
            correlation_threshold=0.95,
        ),
    )

    assert report.summary.candidate_count == 3
    assert report.summary.cluster_count == 2
    assert report.summary.dropped_candidate_count == 1

    cluster_with_drop = next(
        cluster for cluster in report.clusters if cluster.dropped_count == 1
    )
    assert cluster_with_drop.representative_candidate_id == "protein:P11111"
    assert "protein:P22222" in cluster_with_drop.dropped_candidate_ids
    assert (
        PanelRedundancyReasonCode.HIGH_SIGNAL_CORRELATION
        in cluster_with_drop.shared_reason_codes
    )

    candidates_by_id = {entry.candidate_id: entry for entry in report.candidates}
    assert candidates_by_id["protein:P11111"].representative is True
    assert candidates_by_id["protein:P11111"].dropped is False
    assert candidates_by_id["protein:P22222"].representative is False
    assert candidates_by_id["protein:P22222"].dropped is True
    assert (
        PanelRedundancyReasonCode.LOWER_SCORING_CLUSTER_MEMBER
        in candidates_by_id["protein:P22222"].redundancy_reason_codes
    )
    assert candidates_by_id["protein:P33333"].representative is True
    assert (
        candidates_by_id["protein:P33333"].cluster_id
        != candidates_by_id["protein:P11111"].cluster_id
    )


def test_panel_redundancy_candidate_tsv_preserves_representative_and_dropped_markers(
    tmp_path: Path,
) -> None:
    skyline_path = tmp_path / "panel_redundancy.skyline.tsv"
    skyline_path.write_text(_skyline_rows(), encoding="utf-8")
    report = build_panel_redundancy_report(
        biomarker_candidates=_candidates(),
        panel_assays=_panel_assays(),
        import_report=build_skyline_result_import_report(skyline_path),
        design_entries=_design_entries(),
    )

    rendered = render_panel_redundancy_candidate_tsv(report)

    assert "candidate_id\tcandidate_kind\tdisplay_label" in rendered
    assert "protein:P11111" in rendered
    assert "protein:P22222" in rendered
    assert "high_signal_correlation" in rendered
    assert "lower_scoring_cluster_member" in rendered


def _candidates() -> tuple[PanelRedundancyCandidateInput, ...]:
    return (
        PanelRedundancyCandidateInput(
            candidate_id="protein:P11111",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="REP1",
            target_protein_ref="P11111",
            priority_rank=1,
            final_score=0.92,
            penalty_total=0.05,
            rank_reason_codes=("assay_ready",),
            ranking_note="primary candidate",
        ),
        PanelRedundancyCandidateInput(
            candidate_id="protein:P22222",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="RED2",
            target_protein_ref="P22222",
            priority_rank=2,
            final_score=0.81,
            penalty_total=0.09,
            rank_reason_codes=("assay_ready",),
            ranking_note="highly correlated neighbor",
        ),
        PanelRedundancyCandidateInput(
            candidate_id="protein:P33333",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="DISTINCT3",
            target_protein_ref="P33333",
            priority_rank=3,
            final_score=0.76,
            penalty_total=0.10,
            rank_reason_codes=("assay_ready",),
            ranking_note="distinct candidate",
        ),
    )


def _panel_assays() -> tuple[TargetedValidationPanelAssayInput, ...]:
    return (
        TargetedValidationPanelAssayInput(
            assay_entry_id="assay:P11111:PEPTIDER",
            biomarker_candidate_id="protein:P11111",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
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
        TargetedValidationPanelAssayInput(
            assay_entry_id="assay:P22222:AAAAK",
            biomarker_candidate_id="protein:P22222",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
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
        TargetedValidationPanelAssayInput(
            assay_entry_id="assay:P33333:BBBBK",
            biomarker_candidate_id="protein:P33333",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
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
    )


def _design_entries() -> tuple[ExperimentalDesignEntry, ...]:
    rows = (
        ("control_r1", "control", 1),
        ("control_r2", "control", 2),
        ("treat_r1", "treatment", 1),
        ("treat_r2", "treatment", 2),
        ("followup_r1", "followup", 1),
        ("followup_r2", "followup", 2),
    )
    return tuple(
        ExperimentalDesignEntry(
            sample_id=sample_id,
            condition=condition,
            replicate=replicate,
            fraction=1,
            spectra_file=f"{sample_id}.raw",
            identifications_file=f"{sample_id}.tsv",
            batch="b1",
        )
        for sample_id, condition, replicate in rows
    )


def _skyline_rows() -> str:
    return (
        "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t10000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t8200\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t10500\t12.49\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t8400\t12.55\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t22000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t17800\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t22500\t12.49\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t18100\t12.55\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tfollowup_r1\t16000\t12.51\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tfollowup_r1\t12900\t12.57\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tfollowup_r2\t15800\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tfollowup_r2\t12700\t12.56\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r1\t8000\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r1\t6600\t18.47\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r2\t8400\t18.41\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r2\t6900\t18.48\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r1\t17600\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r1\t14400\t18.47\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r2\t18000\t18.41\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r2\t14700\t18.48\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tfollowup_r1\t12800\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tfollowup_r1\t10400\t18.47\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tfollowup_r2\t12600\t18.41\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tfollowup_r2\t10200\t18.48\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\tcontrol_r1\t20000\t16.40\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\tcontrol_r1\t16200\t16.47\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\tcontrol_r2\t20500\t16.42\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\tcontrol_r2\t16600\t16.46\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_r1\t9000\t16.41\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_r1\t7300\t16.48\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_r2\t9200\t16.40\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_r2\t7500\t16.45\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\tfollowup_r1\t24000\t16.42\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\tfollowup_r1\t19500\t16.47\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\tfollowup_r2\t23600\t16.41\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\tfollowup_r2\t19100\t16.46\tpass\n"
    )
