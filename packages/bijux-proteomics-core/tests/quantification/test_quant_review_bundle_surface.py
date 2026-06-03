# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    ImputationMethod,
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.review import build_quant_review_bundle


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="qb-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=950.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-003",
            sample_id="s3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=120.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-004",
            sample_id="s4",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-005",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=700.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-006",
            sample_id="s2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=690.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-007",
            sample_id="s3",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=660.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-008",
            sample_id="s4",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=640.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s4",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="s4.mzml",
            batch="batch-a",
        ),
    )


def _time_course_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="batch-a",
            metadata={"timepoint": "0"},
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="batch-a",
            metadata={"timepoint": "1"},
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="batch-a",
            metadata={"timepoint": "0"},
        ),
        ExperimentalDesignEntry(
            sample_id="s4",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="s4.mzml",
            batch="batch-a",
            metadata={"timepoint": "1"},
        ),
    )


def test_quant_review_bundle_includes_expected_surfaces_and_pointers() -> None:
    bundle = build_quant_review_bundle(
        _records(),
        design_entries=_design(),
        normalization_method=NormalizationMethod.MEDIAN,
        imputation_method=ImputationMethod.LOW_INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert len(bundle.artifact_bundle_hash) == 64
    assert bundle.effect_size_da_report is not None
    assert bundle.normalization_comparison.after
    assert bundle.normalization_comparison.method is NormalizationMethod.MEDIAN
    assert bundle.imputation_report.method is ImputationMethod.LOW_INTENSITY
    assert bundle.imputation_report.imputed_value_count == 0
    assert bundle.imputation_sensitivity is not None
    assert bundle.missingness_entity_summary.entries
    assert bundle.missingness_condition_summary.entries
    assert bundle.missingness_intensity_dependence.plot_points
    assert len(bundle.evidence_pointers) >= 14
    assert bundle.rollup_strategy_comparison.entries
    assert bundle.limma_compatible_package.sample_annotations
    assert bundle.msstats_compatible_input_report.rows
    assert bundle.design_matrix_report.columns
    assert bundle.design_model_fit_report.coefficient_entries
    assert bundle.missingness_profile.entries
    assert bundle.qc_report.replicate_correlation_report.entries
    assert bundle.qc_report.replicate_cv_report.entries
    assert bundle.qc_report.sample_pca_report is not None
    assert bundle.qc_report.condition_clustering_report is not None
    assert "quant_artifact_bundle.limma_compatible_package" in bundle.evidence_pointers
    assert (
        "quant_artifact_bundle.msstats_compatible_input_report"
        in bundle.evidence_pointers
    )
    assert "quant_artifact_bundle.design_matrix_report" in bundle.evidence_pointers
    assert "quant_artifact_bundle.design_model_fit_report" in bundle.evidence_pointers
    assert "qc_report.replicate_cv_report.entries" in bundle.evidence_pointers
    assert "qc_report.outlier_samples" in bundle.evidence_pointers
    assert bundle.decision_readiness.readiness_state.value in {
        "decision_grade",
        "review_grade",
        "blocked",
    }


def test_quant_review_bundle_preserves_time_course_differential_report() -> None:
    bundle = build_quant_review_bundle(
        _records(),
        design_entries=_time_course_design(),
        normalization_method=NormalizationMethod.MEDIAN,
        imputation_method=ImputationMethod.NONE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert bundle.time_course_differential_report is not None
    assert bundle.time_course_differential_report.ordered_timepoints == ("0", "1")
    assert (
        "quant_artifact_bundle.time_course_differential_report"
        in bundle.evidence_pointers
    )


def test_quant_review_bundle_preserves_multi_condition_differential_collection() -> (
    None
):
    records = _records() + (
        Ms1FeatureRecord(
            feature_id="qb-009",
            sample_id="s5",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=500.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-010",
            sample_id="s6",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=520.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-011",
            sample_id="s5",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=350.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="qb-012",
            sample_id="s6",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=360.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    design = _design() + (
        ExperimentalDesignEntry(
            sample_id="s5",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="s5.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s6",
            condition="rescue",
            replicate=2,
            fraction=1,
            spectra_file="s6.mzml",
            batch="batch-a",
        ),
    )

    bundle = build_quant_review_bundle(
        records,
        design_entries=design,
        normalization_method=NormalizationMethod.MEDIAN,
        imputation_method=ImputationMethod.NONE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert bundle.effect_size_da_report is None
    assert bundle.design_matrix_report.contrasts
    assert bundle.design_model_fit_report.contrast_estimates
    assert bundle.differential_abundance_multi_condition_report is not None
    assert bundle.multi_contrast_consistency_report is not None
    assert len(bundle.differential_abundance_multi_condition_report.reports) == 3
    assert bundle.multi_contrast_consistency_report.summary.shared_hit_count >= 1
    assert (
        "quant_artifact_bundle.differential_abundance_multi_condition_report"
        in bundle.evidence_pointers
    )
    assert (
        "quant_review_bundle.multi_contrast_consistency_report.entities"
        in bundle.evidence_pointers
    )


def test_quant_review_bundle_skips_infeasible_multi_condition_statistics() -> None:
    design = (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="s2.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="s4",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="s4.mzml",
            batch="batch-a",
        ),
    )

    bundle = build_quant_review_bundle(
        _records(),
        design_entries=design,
        normalization_method=NormalizationMethod.MEDIAN,
        imputation_method=ImputationMethod.NONE,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert bundle.differential_abundance_multi_condition_report is None
    assert bundle.multi_contrast_consistency_report is None
