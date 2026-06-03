# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantAssessmentDisposition,
    QuantEntityLevel,
    QuantRollupMethod,
    build_batch_effect_estimator_report,
    build_label_free_intensity_table,
    render_batch_effect_principal_components_tsv,
    render_batch_effect_summary_tsv,
)


def _table(records: tuple[Ms1FeatureRecord, ...]) -> LabelFreeQuantTable:
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_batch_effect_estimator_reports_batch_associated_pcs_without_confounding() -> (
    None
):
    records = (
        Ms1FeatureRecord(
            feature_id="be-001",
            sample_id="case-a",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="be-002",
            sample_id="ctrl-a",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=900.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="be-003",
            sample_id="case-b",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=140.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="be-004",
            sample_id="ctrl-b",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=130.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="be-005",
            sample_id="case-a",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=800.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="be-006",
            sample_id="ctrl-a",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=720.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="be-007",
            sample_id="case-b",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=120.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="be-008",
            sample_id="ctrl-b",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=115.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="case-a",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-a.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-a",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-a.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="case-b",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-b.mzml",
            batch="batch-b",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-b",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-b.mzml",
            batch="batch-b",
        ),
    )

    report = build_batch_effect_estimator_report(
        _table(records),
        design,
        shift_threshold=0.5,
        component_association_threshold=0.2,
    )

    assert report.disposition is QuantAssessmentDisposition.ADVISORY
    assert report.batch_variance_proxy > 0.0
    assert report.batch_associated_component_count >= 1
    assert report.fully_confounded_with_condition is False
    assert report.batch_correction_blocked is False
    assert report.batch_warning is not None
    assert any(entry.flagged for entry in report.batches)
    assert any(entry.associated_with_batch for entry in report.principal_components)
    assert "batch_variance_proxy" in render_batch_effect_summary_tsv(report)
    assert "associated_with_batch" in render_batch_effect_principal_components_tsv(
        report
    )


def test_batch_effect_estimator_blocks_fully_confounded_batch_correction() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="bc-001",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bc-002",
            sample_id="c2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=990.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bc-003",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=8.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bc-004",
            sample_id="t2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=7.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
            batch="batch-b",
        ),
        ExperimentalDesignEntry(
            sample_id="t2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzml",
            batch="batch-b",
        ),
    )

    report = build_batch_effect_estimator_report(_table(records), design)

    assert report.disposition is QuantAssessmentDisposition.ENFORCED
    assert report.fully_confounded_with_condition is True
    assert report.batch_correction_blocked is True
    assert report.batch_warning == (
        "batch is fully confounded with condition; batch correction is blocked"
    )


def test_batch_effect_estimator_returns_empty_report_without_batch_metadata() -> None:
    records = (
        Ms1FeatureRecord(
            feature_id="bn-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="bn-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s2.mzml",
        ),
    )

    report = build_batch_effect_estimator_report(_table(records), design)

    assert report.batches == ()
    assert report.principal_components == ()
    assert report.batch_variance_proxy == 0.0
    assert report.batch_warning is None
