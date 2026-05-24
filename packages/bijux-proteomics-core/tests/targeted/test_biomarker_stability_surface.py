# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io import ExperimentalDesignEntry
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.biomarker_stability import (
    BiomarkerStabilityDimension,
    BiomarkerStabilityPolicy,
    BiomarkerStabilityReasonCode,
    build_biomarker_stability_report,
    render_biomarker_stability_candidate_tsv,
)
from bijux_proteomics.targeted.panel_design import TargetedPanelCandidateKind
from bijux_proteomics.targeted.result_import import build_skyline_result_import_report
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
)


def test_biomarker_stability_downgrades_batch_sensitive_and_single_condition_candidates(
    tmp_path: Path,
) -> None:
    skyline_path = tmp_path / "targeted_stability.skyline.tsv"
    skyline_path.write_text(_skyline_rows(), encoding="utf-8")
    import_report = build_skyline_result_import_report(skyline_path)

    report = build_biomarker_stability_report(
        biomarker_candidates=_candidates(),
        panel_assays=_panel_assays(),
        import_report=import_report,
        design_entries=_design_entries(),
        policy=BiomarkerStabilityPolicy(
            minimum_reliable_samples_per_group=2,
            minimum_reliable_sample_fraction=0.5,
            subgroup_median_delta_threshold=0.8,
            batch_residual_delta_threshold=0.5,
            downgrade_below_score=0.8,
        ),
    )

    entries_by_id = {entry.candidate_id: entry for entry in report.entries}
    stable_entry = entries_by_id["protein:P11111"]
    batch_sensitive_entry = entries_by_id["protein:P22222"]
    single_condition_entry = entries_by_id["protein:P33333"]

    assert stable_entry.downgraded is False
    assert stable_entry.stability_score > 0.85
    assert stable_entry.adjusted_priority_rank == 1

    assert batch_sensitive_entry.downgraded is True
    assert (
        BiomarkerStabilityReasonCode.BATCH_SENSITIVE_SIGNAL
        in batch_sensitive_entry.instability_reasons
    )
    assert batch_sensitive_entry.stability_score < stable_entry.stability_score

    assert single_condition_entry.downgraded is True
    assert (
        BiomarkerStabilityReasonCode.SINGLE_CONDITION_SIGNAL_ONLY
        in single_condition_entry.instability_reasons
    )
    assert single_condition_entry.condition_count_with_signal == 1

    batch_rows = [
        entry
        for entry in report.subgroup_behavior
        if entry.candidate_id == "protein:P22222"
        and entry.dimension is BiomarkerStabilityDimension.BATCH
    ]
    assert {entry.subgroup_value for entry in batch_rows} == {"b1", "b2"}
    assert any(entry.residual_median_log2_intensity is not None for entry in batch_rows)


def test_biomarker_stability_candidate_tsv_preserves_downgraded_rankable_candidates(
    tmp_path: Path,
) -> None:
    skyline_path = tmp_path / "targeted_stability.skyline.tsv"
    skyline_path.write_text(_skyline_rows(), encoding="utf-8")
    report = build_biomarker_stability_report(
        biomarker_candidates=_candidates(),
        panel_assays=_panel_assays(),
        import_report=build_skyline_result_import_report(skyline_path),
        design_entries=_design_entries(),
    )

    rendered = render_biomarker_stability_candidate_tsv(report)

    assert "candidate_id\tcandidate_kind\tdisplay_label" in rendered
    assert "protein:P11111" in rendered
    assert "protein:P22222" in rendered
    assert "batch_sensitive_signal" in rendered
    assert "single_condition_signal_only" in rendered


def _candidates() -> tuple[TargetedValidationDiscoveryClaimInput, ...]:
    return (
        TargetedValidationDiscoveryClaimInput(
            candidate_id="protein:P11111",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="ROBUST1",
            target_protein_ref="P11111",
            priority_rank=1,
            final_score=0.92,
            penalty_total=0.0,
            discovery_effect_size=1.0,
            support_count=4,
            robustness_score=0.88,
            assay_feasibility_score=0.90,
            rank_reason_codes=("assay_ready",),
            ranking_note="strong candidate",
        ),
        TargetedValidationDiscoveryClaimInput(
            candidate_id="protein:P22222",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="BATCHY2",
            target_protein_ref="P22222",
            priority_rank=2,
            final_score=0.84,
            penalty_total=0.05,
            discovery_effect_size=0.8,
            support_count=3,
            robustness_score=0.79,
            assay_feasibility_score=0.86,
            rank_reason_codes=("assay_ready",),
            ranking_note="candidate with technical sensitivity",
        ),
        TargetedValidationDiscoveryClaimInput(
            candidate_id="protein:P33333",
            candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            display_label="ONECOND3",
            target_protein_ref="P33333",
            priority_rank=3,
            final_score=0.80,
            penalty_total=0.02,
            discovery_effect_size=0.7,
            support_count=2,
            robustness_score=0.72,
            assay_feasibility_score=0.84,
            rank_reason_codes=("assay_ready",),
            ranking_note="candidate visible only in one condition",
        ),
    )


def _panel_assays() -> tuple[TargetedValidationPanelAssayInput, ...]:
    return (
        TargetedValidationPanelAssayInput(
            assay_entry_id="assay:P11111:PEPTIDER",
            biomarker_candidate_id="protein:P11111",
            biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
            biomarker_display_label="ROBUST1",
            biomarker_priority_rank=1,
            target_protein_ref="P11111",
            target_protein_group_id="protein_group_1",
            gene_symbol="ROBUST1",
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
            biomarker_display_label="BATCHY2",
            biomarker_priority_rank=2,
            target_protein_ref="P22222",
            target_protein_group_id="protein_group_2",
            gene_symbol="BATCHY2",
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
            biomarker_display_label="ONECOND3",
            biomarker_priority_rank=3,
            target_protein_ref="P33333",
            target_protein_group_id="protein_group_3",
            gene_symbol="ONECOND3",
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
        ("control_t0_plasma_b1_r1", "control", 1, "b1", "t0", "plasma"),
        ("control_t0_plasma_b2_r2", "control", 2, "b2", "t0", "plasma"),
        ("control_t1_serum_b1_r1", "control", 3, "b1", "t1", "serum"),
        ("control_t1_serum_b2_r2", "control", 4, "b2", "t1", "serum"),
        ("treat_t0_plasma_b1_r1", "treatment", 1, "b1", "t0", "plasma"),
        ("treat_t0_plasma_b2_r2", "treatment", 2, "b2", "t0", "plasma"),
        ("treat_t1_serum_b1_r1", "treatment", 3, "b1", "t1", "serum"),
        ("treat_t1_serum_b2_r2", "treatment", 4, "b2", "t1", "serum"),
    )
    return tuple(
        ExperimentalDesignEntry(
            sample_id=sample_id,
            condition=condition,
            replicate=replicate,
            fraction=1,
            spectra_file=f"{sample_id}.raw",
            identifications_file=f"{sample_id}.tsv",
            batch=batch,
            metadata={"timepoint": timepoint, "sample_type": sample_type},
        )
        for sample_id, condition, replicate, batch, timepoint, sample_type in rows
    )


def _skyline_rows() -> str:
    return (
        "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_t0_plasma_b1_r1\t10000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_t0_plasma_b1_r1\t8200\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_t0_plasma_b2_r2\t10200\t12.48\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_t0_plasma_b2_r2\t8300\t12.55\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_t1_serum_b1_r1\t9800\t12.51\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_t1_serum_b1_r1\t7900\t12.57\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_t1_serum_b2_r2\t10100\t12.52\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_t1_serum_b2_r2\t8100\t12.58\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_t0_plasma_b1_r1\t21000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_t0_plasma_b1_r1\t17000\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_t0_plasma_b2_r2\t20800\t12.48\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_t0_plasma_b2_r2\t16800\t12.55\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_t1_serum_b1_r1\t21400\t12.51\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_t1_serum_b1_r1\t17100\t12.57\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_t1_serum_b2_r2\t21100\t12.52\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_t1_serum_b2_r2\t16950\t12.58\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_t0_plasma_b1_r1\t12000\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_t0_plasma_b1_r1\t10000\t18.47\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_t0_plasma_b2_r2\t36000\t18.41\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_t0_plasma_b2_r2\t30000\t18.48\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_t1_serum_b1_r1\t12200\t18.42\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_t1_serum_b1_r1\t10100\t18.46\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_t1_serum_b2_r2\t35500\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_t1_serum_b2_r2\t29500\t18.45\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_t0_plasma_b1_r1\t14000\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_t0_plasma_b1_r1\t11500\t18.47\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_t0_plasma_b2_r2\t37000\t18.41\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_t0_plasma_b2_r2\t30500\t18.48\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_t1_serum_b1_r1\t14100\t18.42\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_t1_serum_b1_r1\t11600\t18.46\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_t1_serum_b2_r2\t37200\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_t1_serum_b2_r2\t30700\t18.45\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_t0_plasma_b1_r1\t16000\t16.40\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_t0_plasma_b1_r1\t13500\t16.47\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_t0_plasma_b2_r2\t15800\t16.41\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_t0_plasma_b2_r2\t13300\t16.48\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_t1_serum_b1_r1\t16200\t16.42\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_t1_serum_b1_r1\t13650\t16.46\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty3\t460.2\ttreat_t1_serum_b2_r2\t16100\t16.40\tpass\n"
        "P33333\tBBBBK\t2\t551.25\ty4\t531.2\ttreat_t1_serum_b2_r2\t13700\t16.45\tpass\n"
    )
