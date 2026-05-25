# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.domain.errors import DesignError
from bijux_proteomics.io import ExperimentalDesignEntry
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted import (
    TargetedPanelCandidateKind,
    TargetedResultValidationPolicy,
    TargetedValidationDirection,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
    TargetedValidationReasonCode,
    TargetedValidationVerdict,
    build_skyline_result_import_report,
    build_targeted_result_validation_report,
    render_targeted_result_validation_evidence_tsv,
    render_targeted_result_validation_tsv,
)


def test_targeted_result_validation_preserves_confirmation_contradiction_and_unassayed_conflict(
    tmp_path: Path,
) -> None:
    skyline_path = tmp_path / "targeted.skyline.tsv"
    skyline_path.write_text(
        "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t25000\t12.50\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t20000\t12.56\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t27000\t12.48\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t21000\t12.55\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t120000\t12.51\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t98000\t12.57\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t118000\t12.52\tpass\n"
        "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t95000\t12.58\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r1\t90000\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r1\t87000\t18.47\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r2\t92000\t18.41\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r2\t86000\t18.48\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r1\t93000\t18.42\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r1\t85000\t18.46\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r2\t91500\t18.40\tpass\n"
        "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r2\t85500\t18.45\tpass\n",
        encoding="utf-8",
    )
    import_report = build_skyline_result_import_report(skyline_path)
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="control_r1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="control_r1.raw",
            identifications_file="control_r1.tsv",
        ),
        ExperimentalDesignEntry(
            sample_id="control_r2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="control_r2.raw",
            identifications_file="control_r2.tsv",
        ),
        ExperimentalDesignEntry(
            sample_id="treat_r1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="treat_r1.raw",
            identifications_file="treat_r1.tsv",
        ),
        ExperimentalDesignEntry(
            sample_id="treat_r2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="treat_r2.raw",
            identifications_file="treat_r2.tsv",
        ),
    )
    report = build_targeted_result_validation_report(
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
        import_report=import_report,
        design_entries=design_entries,
        policy=TargetedResultValidationPolicy(
            case_condition="treatment",
            control_condition="control",
        ),
    )

    assert report.summary.discovery_claim_count == 3
    assert report.summary.confirmed_count == 1
    assert report.summary.contradicted_count == 1
    assert report.summary.inconclusive_count == 1
    assert report.summary.unassayed_candidate_count == 1

    confirmed_entry = next(
        entry for entry in report.entries if entry.candidate_id == "protein:P11111"
    )
    contradicted_entry = next(
        entry for entry in report.entries if entry.candidate_id == "protein:P22222"
    )
    inconclusive_entry = next(
        entry for entry in report.entries if entry.candidate_id == "ptm_site:P33333:S21"
    )

    assert confirmed_entry.verdict is TargetedValidationVerdict.CONFIRMED
    assert confirmed_entry.validation_direction is TargetedValidationDirection.UP
    assert (
        TargetedValidationReasonCode.VALIDATION_EFFECT_MATCHES_DISCOVERY
        in confirmed_entry.reason_codes
    )

    assert contradicted_entry.verdict is TargetedValidationVerdict.CONTRADICTED
    assert contradicted_entry.validation_direction is TargetedValidationDirection.FLAT
    assert (
        TargetedValidationReasonCode.VALIDATION_EFFECT_FLAT_AGAINST_DISCOVERY
        in contradicted_entry.reason_codes
    )

    assert inconclusive_entry.verdict is TargetedValidationVerdict.INCONCLUSIVE
    assert (
        TargetedValidationReasonCode.SITE_SPECIFIC_VALIDATION_NOT_AVAILABLE
        in inconclusive_entry.reason_codes
    )

    evidence_tsv = render_targeted_result_validation_evidence_tsv(report)
    contradicted_tsv = render_targeted_result_validation_tsv(
        report,
        TargetedValidationVerdict.CONTRADICTED,
    )
    assert "assay:P11111:PEPTIDER" in evidence_tsv
    assert "validation_effect_flat_against_discovery" in contradicted_tsv


def test_targeted_result_validation_keeps_shared_peptide_assays_inconclusive(
    tmp_path: Path,
) -> None:
    skyline_path = tmp_path / "shared.skyline.tsv"
    skyline_path.write_text(
        "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
        "P44444\tSHAREDK\t2\t480.20\ty5\t550.2\tcontrol_r1\t18000\t15.10\tpass\n"
        "P44444\tSHAREDK\t2\t480.20\ty6\t663.3\tcontrol_r1\t15000\t15.15\tpass\n"
        "P44444\tSHAREDK\t2\t480.20\ty5\t550.2\tcontrol_r2\t18500\t15.11\tpass\n"
        "P44444\tSHAREDK\t2\t480.20\ty6\t663.3\tcontrol_r2\t15200\t15.16\tpass\n"
        "P44444\tSHAREDK\t2\t480.20\ty5\t550.2\ttreat_r1\t90000\t15.12\tpass\n"
        "P44444\tSHAREDK\t2\t480.20\ty6\t663.3\ttreat_r1\t82000\t15.17\tpass\n"
        "P44444\tSHAREDK\t2\t480.20\ty5\t550.2\ttreat_r2\t91000\t15.13\tpass\n"
        "P44444\tSHAREDK\t2\t480.20\ty6\t663.3\ttreat_r2\t81500\t15.18\tpass\n",
        encoding="utf-8",
    )
    import_report = build_skyline_result_import_report(skyline_path)
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="control_r1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="control_r1.raw",
            identifications_file="control_r1.tsv",
        ),
        ExperimentalDesignEntry(
            sample_id="control_r2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="control_r2.raw",
            identifications_file="control_r2.tsv",
        ),
        ExperimentalDesignEntry(
            sample_id="treat_r1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="treat_r1.raw",
            identifications_file="treat_r1.tsv",
        ),
        ExperimentalDesignEntry(
            sample_id="treat_r2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="treat_r2.raw",
            identifications_file="treat_r2.tsv",
        ),
    )
    report = build_targeted_result_validation_report(
        discovery_claims=(
            TargetedValidationDiscoveryClaimInput(
                candidate_id="protein:P44444",
                candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                display_label="shared-peptide candidate",
                target_protein_ref="P44444",
                priority_rank=1,
                final_score=0.81,
                penalty_total=0.0,
                discovery_effect_size=1.0,
                support_count=3,
                robustness_score=0.76,
                assay_feasibility_score=0.72,
                rank_reason_codes=("assay_ready",),
                ranking_note="targeted assay uses a shared peptide",
            ),
        ),
        panel_assays=(
            TargetedValidationPanelAssayInput(
                assay_entry_id="assay:P44444:SHAREDK",
                biomarker_candidate_id="protein:P44444",
                biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                biomarker_display_label="shared-peptide candidate",
                biomarker_priority_rank=1,
                target_protein_ref="P44444",
                target_protein_group_id="protein_group_4",
                gene_symbol="GENE4",
                peptide_sequence="SHAREDK",
                canonical_peptide="SHAREDK",
                uniqueness_class=PeptideUniquenessClass.SHARED,
                precursor_charge=2,
                selected_transition_count=3,
                exported_transition_count=3,
                warning_note="shared peptide assay cannot isolate one protein",
            ),
        ),
        import_report=import_report,
        design_entries=design_entries,
        policy=TargetedResultValidationPolicy(
            case_condition="treatment",
            control_condition="control",
        ),
    )

    entry = report.entries[0]
    evidence = report.assay_evidence[0]
    assert entry.verdict is TargetedValidationVerdict.INCONCLUSIVE
    assert (
        TargetedValidationReasonCode.NON_UNIQUE_VALIDATION_ASSAY in entry.reason_codes
    )
    assert evidence.verdict is TargetedValidationVerdict.INCONCLUSIVE
    assert evidence.validation_direction is TargetedValidationDirection.UP


def test_targeted_result_validation_rejects_invalid_case_control_design(
    tmp_path: Path,
) -> None:
    skyline_path = tmp_path / "invalid.skyline.tsv"
    skyline_path.write_text(
        "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality\n"
        "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t25000\t12.50\tpass\n",
        encoding="utf-8",
    )
    import_report = build_skyline_result_import_report(skyline_path)
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="control_r1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="control_r1.raw",
            identifications_file="control_r1.tsv",
        ),
    )

    with pytest.raises(
        DesignError, match="case_condition and control_condition must differ"
    ):
        build_targeted_result_validation_report(
            discovery_claims=(),
            panel_assays=(),
            import_report=import_report,
            design_entries=design_entries,
            policy=TargetedResultValidationPolicy(
                case_condition="control",
                control_condition="control",
            ),
        )
