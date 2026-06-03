# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    BatchEffectDecisionPosture,
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantDecisionBlockingReasonCode,
    QuantDecisionReadinessState,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_quant_decision_readiness_report,
    build_replicate_structure_audit_report,
)


def _table(records: tuple[Ms1FeatureRecord, ...]) -> LabelFreeQuantTable:
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )


def _decision_grade_records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="dg-1",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dg-2",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=980.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dg-3",
            sample_id="s3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=620.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dg-4",
            sample_id="s4",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=640.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dg-5",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=800.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dg-6",
            sample_id="s2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=790.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dg-7",
            sample_id="s3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=520.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="dg-8",
            sample_id="s4",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=530.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _decision_grade_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="b2",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s4",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="s4.mzml",
            batch="b2",
        ),
    )


def _blocked_batch_records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="bb-1",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bb-2",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=8.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bb-3",
            sample_id="s3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=980.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bb-4",
            sample_id="s4",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=7.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bb-5",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=840.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bb-6",
            sample_id="s2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=6.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bb-7",
            sample_id="s3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=810.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bb-8",
            sample_id="s4",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=5.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _confounded_batch_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="b1",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="b2",
        ),
        ExperimentalDesignEntry(
            sample_id="s4",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="s4.mzml",
            batch="b2",
        ),
    )


def test_replicate_structure_audit_reports_balanced_support() -> None:
    audit = build_replicate_structure_audit_report(
        _decision_grade_design(),
        minimum_replicates_per_condition=2,
    )

    assert audit.balanced is True
    assert audit.underpowered_conditions == ()


def test_replicate_structure_audit_does_not_treat_technical_runs_as_biological_replicates() -> (
    None
):
    audit = build_replicate_structure_audit_report(
        (
            ExperimentalDesignEntry(
                sample_id="control-1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="control-1_run-1.mzml",
                technical_replicate_id="tech-1",
            ),
            ExperimentalDesignEntry(
                sample_id="control-1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="control-1_run-2.mzml",
                technical_replicate_id="tech-2",
            ),
            ExperimentalDesignEntry(
                sample_id="treated-1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="treated-1_run-1.mzml",
                technical_replicate_id="tech-3",
            ),
            ExperimentalDesignEntry(
                sample_id="treated-1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="treated-1_run-2.mzml",
                technical_replicate_id="tech-4",
            ),
        ),
        minimum_replicates_per_condition=2,
    )

    control = next(entry for entry in audit.entries if entry.condition == "control")
    treatment = next(entry for entry in audit.entries if entry.condition == "treatment")

    assert audit.underpowered_conditions == ("control", "treatment")
    assert control.replicate_count == 1
    assert control.biological_replicate_count == 1
    assert control.technical_replicate_count == 2
    assert treatment.replicate_count == 1
    assert treatment.biological_replicate_count == 1
    assert treatment.technical_replicate_count == 2


def test_quant_decision_readiness_report_supports_false_positive_free_design() -> None:
    report = build_quant_decision_readiness_report(
        _table(_decision_grade_records()),
        design_entries=_decision_grade_design(),
        minimum_replicates_per_condition=2,
        within_condition_warning_threshold=0.7,
        batch_shift_threshold=2.0,
    )

    assert report.readiness_state is QuantDecisionReadinessState.DECISION_GRADE
    assert report.batch_effect_posture is BatchEffectDecisionPosture.SUPPORTED
    assert not report.blocking_reasons


def test_quant_decision_readiness_report_blocks_true_positive_batch_shift() -> None:
    report = build_quant_decision_readiness_report(
        _table(_blocked_batch_records()),
        design_entries=_decision_grade_design(),
        minimum_replicates_per_condition=2,
        within_condition_warning_threshold=0.7,
        batch_shift_threshold=0.5,
    )

    assert report.readiness_state is QuantDecisionReadinessState.BLOCKED
    assert report.batch_effect_posture is BatchEffectDecisionPosture.BLOCKED
    assert report.flagged_batch_count >= 2


def test_quant_decision_readiness_report_blocks_fully_confounded_batch_correction() -> (
    None
):
    report = build_quant_decision_readiness_report(
        _table(_decision_grade_records()),
        design_entries=_confounded_batch_design(),
        minimum_replicates_per_condition=2,
        within_condition_warning_threshold=0.7,
        batch_shift_threshold=2.0,
    )

    assert report.readiness_state is QuantDecisionReadinessState.BLOCKED
    assert report.batch_effect_posture is BatchEffectDecisionPosture.BLOCKED
    assert (
        QuantDecisionBlockingReasonCode.BATCH_CONDITION_CONFOUNDING
        in report.blocking_reasons
    )
