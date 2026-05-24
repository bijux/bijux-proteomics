# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics.quantification as quantification
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.study import SampleRunAnalysisPolicy


def test_quantification_package_exports_model_rollup_owner_surface() -> None:
    peptide_matrix = quantification.build_peptide_intensity_matrix_from_features(
        (
            quantification.Ms1FeatureRecord(
                feature_id="rollup001",
                sample_id="control-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="rollup002",
                sample_id="case-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="rollup003",
                sample_id="control-1",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="rollup004",
                sample_id="case-1",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=1600.0,
                protein_refs=("P001",),
            ),
        )
    )

    report = quantification.fit_peptide_bias_model(
        peptide_matrix,
        (
            quantification.PeptideToProteinEntry(peptide_id="PEPA", protein_id="P001"),
            quantification.PeptideToProteinEntry(peptide_id="PEPG", protein_id="P001"),
        ),
    )
    abundance_tsv = quantification.render_protein_abundance_tsv(report)
    bias_tsv = quantification.render_peptide_bias_tsv(report)
    residual_tsv = quantification.render_rollup_residuals_tsv(report)

    assert hasattr(quantification, "fit_peptide_bias_model")
    assert hasattr(quantification, "render_protein_abundance_tsv")
    assert hasattr(quantification, "render_peptide_bias_tsv")
    assert hasattr(quantification, "render_rollup_residuals_tsv")
    assert len(report.protein_abundance) == 2
    assert report.protein_abundance[0].supporting_peptide_count == 2
    assert "supporting_peptide_count" in abundance_tsv
    assert "peptide_bias_log2" in bias_tsv
    assert "residual_log2" in residual_tsv


def test_quantification_package_exports_protein_uncertainty_owner_surface() -> None:
    peptide_matrix = quantification.build_peptide_intensity_matrix_from_features(
        (
            quantification.Ms1FeatureRecord(
                feature_id="uncertainty001",
                sample_id="sample-a",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="uncertainty002",
                sample_id="sample-b",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="uncertainty003",
                sample_id="sample-a",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="uncertainty004",
                sample_id="sample-b",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=1600.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="uncertainty005",
                sample_id="sample-a",
                peptide="QLTK",
                canonical_peptide="QLTK",
                intensity=220.0,
                protein_refs=("P002",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="uncertainty006",
                sample_id="sample-b",
                peptide="QLTK",
                canonical_peptide="QLTK",
                intensity=880.0,
                protein_refs=("P002",),
            ),
        )
    )
    rollup = quantification.fit_peptide_bias_model(
        peptide_matrix,
        (
            quantification.PeptideToProteinEntry(peptide_id="PEPA", protein_id="P001"),
            quantification.PeptideToProteinEntry(peptide_id="PEPG", protein_id="P001"),
            quantification.PeptideToProteinEntry(peptide_id="QLTK", protein_id="P002"),
        ),
    )

    report = quantification.estimate_protein_uncertainty(rollup)
    rendered = quantification.render_protein_uncertainty_tsv(report)
    entry_lookup = {(entry.protein_id, entry.sample_id): entry for entry in report.entries}

    assert hasattr(quantification, "estimate_protein_uncertainty")
    assert hasattr(quantification, "render_protein_uncertainty_tsv")
    assert (
        entry_lookup[("P002", "sample-a")].upper_ci
        - entry_lookup[("P002", "sample-a")].lower_ci
    ) > (
        entry_lookup[("P001", "sample-a")].upper_ci
        - entry_lookup[("P001", "sample-a")].lower_ci
    )
    assert "uncertainty_source" in rendered
    assert "supporting_peptide_count" in rendered


def test_quantification_package_exports_peptide_level_differential_owner_surface() -> (
    None
):
    peptide_matrix = quantification.build_peptide_intensity_matrix_from_features(
        (
            quantification.Ms1FeatureRecord(
                feature_id="peptide-da-001",
                sample_id="control-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="peptide-da-002",
                sample_id="control-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=110.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="peptide-da-003",
                sample_id="case-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="peptide-da-004",
                sample_id="case-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=440.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="peptide-da-005",
                sample_id="control-1",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="peptide-da-006",
                sample_id="control-2",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=440.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="peptide-da-007",
                sample_id="case-1",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=1600.0,
                protein_refs=("P001",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="peptide-da-008",
                sample_id="case-2",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=1760.0,
                protein_refs=("P001",),
            ),
        )
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="control-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="control-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="control-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="control-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
    )

    report = quantification.test_protein_effect_from_peptides(
        peptide_matrix,
        design,
        condition_a="control",
        condition_b="case",
    )
    rendered = quantification.render_peptide_level_differential_tsv(report)

    assert hasattr(quantification, "test_protein_effect_from_peptides")
    assert hasattr(quantification, "render_peptide_level_differential_tsv")
    assert len(report.entries) == 1
    assert report.entries[0].log2fc > 1.9
    assert report.entries[0].peptide_disagreement_score < 0.05
    assert (
        "protein_id\tlog2fc\tp_value\tq_value\tpeptide_count\tpeptide_disagreement_score"
        in rendered
    )


def test_quantification_package_exports_variance_model_owner_surface() -> None:
    table = quantification.build_label_free_intensity_table(
        (
            quantification.Ms1FeatureRecord(
                feature_id="variance-001",
                sample_id="s1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=8.0,
                protein_refs=("P_LOW",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="variance-002",
                sample_id="s2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=36.0,
                protein_refs=("P_LOW",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="variance-003",
                sample_id="s3",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=7.0,
                protein_refs=("P_LOW",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="variance-004",
                sample_id="s4",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=34.0,
                protein_refs=("P_LOW",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="variance-005",
                sample_id="s1",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=980.0,
                protein_refs=("P_HIGH",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="variance-006",
                sample_id="s2",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=1000.0,
                protein_refs=("P_HIGH",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="variance-007",
                sample_id="s3",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=1020.0,
                protein_refs=("P_HIGH",),
            ),
            quantification.Ms1FeatureRecord(
                feature_id="variance-008",
                sample_id="s4",
                peptide="PEPB",
                canonical_peptide="PEPB",
                intensity=1040.0,
                protein_refs=("P_HIGH",),
            ),
        ),
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )

    report = quantification.fit_mean_variance_trend(table)
    rendered = quantification.render_mean_variance_trend_tsv(report)
    entry_lookup = {entry.entity_id: entry for entry in report.entries}

    assert hasattr(quantification, "fit_mean_variance_trend")
    assert hasattr(quantification, "render_mean_variance_trend_tsv")
    assert entry_lookup["P_LOW"].quantitative_confidence < entry_lookup["P_HIGH"].quantitative_confidence
    assert (
        "entity_id\tmean_intensity\tobserved_variance\texpected_variance\tvariance_residual"
        in rendered
    )


def test_quantification_package_exports_missingness_classification_surface() -> None:
    table = quantification.build_label_free_intensity_table(
        (
            quantification.Ms1FeatureRecord(
                feature_id="missingness-001",
                sample_id="case-1",
                peptide="COND",
                canonical_peptide="COND",
                intensity=400.0,
                protein_refs=("P001",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="missingness-002",
                sample_id="case-2",
                peptide="COND",
                canonical_peptide="COND",
                intensity=420.0,
                protein_refs=("P001",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="missingness-003",
                sample_id="ctrl-1",
                peptide="COND",
                canonical_peptide="COND",
                intensity=None,
                protein_refs=("P001",),
                missing_value_kind=quantification.MissingValueKind.NOT_OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="missingness-004",
                sample_id="ctrl-2",
                peptide="COND",
                canonical_peptide="COND",
                intensity=None,
                protein_refs=("P001",),
                missing_value_kind=quantification.MissingValueKind.NOT_OBSERVED,
            ),
        ),
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
    )

    report = quantification.classify_missingness(table, design)
    rendered = quantification.render_missingness_classification_tsv(report)

    assert hasattr(quantification, "classify_missingness")
    assert hasattr(quantification, "render_missingness_classification_tsv")
    assert len(report.entries) == 1
    assert report.entries[0].label.value == "condition_specific"
    assert "entity_id\tlabel\tobserved_sample_count\tmissing_sample_count" in rendered


def test_quantification_package_exports_censored_differential_surface() -> None:
    table = quantification.build_label_free_intensity_table(
        (
            quantification.Ms1FeatureRecord(
                feature_id="censored-001",
                sample_id="case-1",
                peptide="LOWCASE",
                canonical_peptide="LOWCASE",
                intensity=18.0,
                protein_refs=("P_LOW_CASE",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-002",
                sample_id="case-2",
                peptide="LOWCASE",
                canonical_peptide="LOWCASE",
                intensity=20.0,
                protein_refs=("P_LOW_CASE",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-003",
                sample_id="ctrl-1",
                peptide="LOWCASE",
                canonical_peptide="LOWCASE",
                intensity=None,
                protein_refs=("P_LOW_CASE",),
                missing_value_kind=quantification.MissingValueKind.NOT_OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-004",
                sample_id="ctrl-2",
                peptide="LOWCASE",
                canonical_peptide="LOWCASE",
                intensity=None,
                protein_refs=("P_LOW_CASE",),
                missing_value_kind=quantification.MissingValueKind.NOT_OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-005",
                sample_id="case-1",
                peptide="STABLE",
                canonical_peptide="STABLE",
                intensity=400.0,
                protein_refs=("P_STABLE",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-006",
                sample_id="case-2",
                peptide="STABLE",
                canonical_peptide="STABLE",
                intensity=420.0,
                protein_refs=("P_STABLE",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-007",
                sample_id="ctrl-1",
                peptide="STABLE",
                canonical_peptide="STABLE",
                intensity=390.0,
                protein_refs=("P_STABLE",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-008",
                sample_id="ctrl-2",
                peptide="STABLE",
                canonical_peptide="STABLE",
                intensity=410.0,
                protein_refs=("P_STABLE",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-009",
                sample_id="case-1",
                peptide="LOWANCHOR",
                canonical_peptide="LOWANCHOR",
                intensity=6.0,
                protein_refs=("P_LOW_ANCHOR",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-010",
                sample_id="case-2",
                peptide="LOWANCHOR",
                canonical_peptide="LOWANCHOR",
                intensity=None,
                protein_refs=("P_LOW_ANCHOR",),
                missing_value_kind=quantification.MissingValueKind.NOT_OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-011",
                sample_id="ctrl-1",
                peptide="LOWANCHOR",
                canonical_peptide="LOWANCHOR",
                intensity=5.0,
                protein_refs=("P_LOW_ANCHOR",),
                missing_value_kind=quantification.MissingValueKind.OBSERVED,
            ),
            quantification.Ms1FeatureRecord(
                feature_id="censored-012",
                sample_id="ctrl-2",
                peptide="LOWANCHOR",
                canonical_peptide="LOWANCHOR",
                intensity=None,
                protein_refs=("P_LOW_ANCHOR",),
                missing_value_kind=quantification.MissingValueKind.NOT_OBSERVED,
            ),
        ),
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
    )

    missingness = quantification.classify_missingness(table, design)
    report = quantification.test_censored_two_group(
        table,
        missingness,
        design,
        condition_a="control",
        condition_b="case",
    )
    rendered = quantification.render_censored_differential_tsv(report)
    entry_lookup = {entry.entity_id: entry for entry in report.entries}

    assert hasattr(quantification, "test_censored_two_group")
    assert hasattr(quantification, "render_censored_differential_tsv")
    assert (
        entry_lookup["P_LOW_CASE"].censoring_status.value
        == "condition_specific_absence"
    )
    assert entry_lookup["P_STABLE"].censoring_status.value == "uncensored"
    assert (
        "entity_id\tlog2fc_estimate\tcensored_p_value\tq_value\tcensoring_status"
        in rendered
    )


def test_quantification_package_exports_time_course_differential_owner_surface() -> (
    None
):
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="pkg001",
            sample_id="c0",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg002",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=140.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg003",
            sample_id="t0",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg004",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=420.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg005",
            sample_id="c0",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=200.0,
            protein_refs=("P002",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg006",
            sample_id="c1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=240.0,
            protein_refs=("P002",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg007",
            sample_id="t0",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=205.0,
            protein_refs=("P002",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="pkg008",
            sample_id="t1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=245.0,
            protein_refs=("P002",),
        ),
    )
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="c0",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c0.mzml",
            metadata={"timepoint": "0"},
        ),
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c1.mzml",
            metadata={"timepoint": "1"},
        ),
        ExperimentalDesignEntry(
            sample_id="t0",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t0.mzml",
            metadata={"timepoint": "0"},
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t1.mzml",
            metadata={"timepoint": "1"},
        ),
    )
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )

    report = quantification.build_time_course_differential_report(
        table,
        design_entries,
    )
    rendered = quantification.render_time_course_differential_tsv(report)

    assert hasattr(quantification, "build_time_course_differential_report")
    assert hasattr(quantification, "build_time_course_differential_robustness_report")
    assert hasattr(quantification, "render_time_course_differential_tsv")
    assert hasattr(quantification, "export_time_course_differential_tsv")
    assert report.ordered_timepoints == ("0", "1")
    assert len(report.entries) == 4
    assert rendered.startswith("entity_id\tcondition\treference_condition")
    assert "robustness_score" in rendered


def test_quantification_package_exports_differential_result_robustness_surface() -> (
    None
):
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="robust001",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust002",
            sample_id="ctrl-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=120.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust003",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=105.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust004",
            sample_id="ctrl-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=118.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust005",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=260.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust006",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=290.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust007",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=275.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust008",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=300.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust009",
            sample_id="ctrl-1",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=90.0,
            protein_refs=("P002",),
            missing_value_kind=quantification.MissingValueKind.OBSERVED,
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust010",
            sample_id="ctrl-2",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=None,
            protein_refs=("P002",),
            missing_value_kind=quantification.MissingValueKind.NOT_OBSERVED,
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust011",
            sample_id="case-1",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=96.0,
            protein_refs=("P002",),
            missing_value_kind=quantification.MissingValueKind.OBSERVED,
        ),
        quantification.Ms1FeatureRecord(
            feature_id="robust012",
            sample_id="case-2",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=None,
            protein_refs=("P002",),
            missing_value_kind=quantification.MissingValueKind.FILTERED,
        ),
    )
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
    )
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )
    imputed = quantification.impute_label_free_table(
        table,
        method=quantification.ImputationMethod.LOW_INTENSITY,
    )
    report = quantification.build_differential_abundance_report(
        imputed,
        design_entries,
        condition_a="case",
        condition_b="control",
    )
    robustness = quantification.build_differential_abundance_robustness_report(
        report,
        imputed,
        design_entries,
    )

    assert hasattr(
        quantification,
        "build_differential_abundance_robustness_report",
    )
    assert hasattr(
        quantification,
        "build_differential_imputation_dependence_report",
    )
    assert report.entries[0].robustness_score is not None
    assert len(robustness.entries) == len(report.entries)
    assert "robustness_reason_codes" in quantification.render_differential_abundance_tsv(
        report
    )
    assert (
        "imputation_significance_change_reason"
        in quantification.render_differential_abundance_tsv(report)
    )


def test_quantification_package_exports_batch_effect_owner_surface() -> None:
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="batch001",
            sample_id="case-a",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="batch002",
            sample_id="ctrl-a",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=950.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="batch003",
            sample_id="case-b",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=120.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="batch004",
            sample_id="ctrl-b",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
        ),
    )
    design_entries = (
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
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )

    report = quantification.build_batch_effect_estimator_report(table, design_entries)
    rendered = quantification.render_batch_effect_summary_tsv(report)

    assert hasattr(quantification, "build_batch_effect_estimator_report")
    assert hasattr(quantification, "render_batch_effect_summary_tsv")
    assert hasattr(quantification, "export_batch_effect_principal_components_tsv")
    assert report.batch_field == "batch"
    assert rendered.startswith("batch_field\tdisposition")


def test_quantification_package_exports_sample_run_policy_surface() -> None:
    report = quantification.build_quant_design_matrix_report(
        (
            ExperimentalDesignEntry(
                sample_id="S1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="run-001",
                technical_replicate_id="tech-1",
            ),
            ExperimentalDesignEntry(
                sample_id="S1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="run-002",
                technical_replicate_id="tech-2",
            ),
            ExperimentalDesignEntry(
                sample_id="S2",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="run-003",
                technical_replicate_id="tech-3",
            ),
        ),
        batch_field="",
        sample_run_policy=SampleRunAnalysisPolicy.SEPARATE_TECHNICAL_RUNS,
    )

    assert hasattr(quantification, "build_quant_design_matrix_report")
    assert report.sample_count == 3
    assert report.rows[0].sample_id == "S1__technical_replicate_tech-1"


def test_quantification_package_exports_sample_exploration_owner_surface() -> None:
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="explore001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="explore002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=102.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="explore003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=20.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="explore004",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=22.0,
            protein_refs=("P001",),
        ),
    )
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
            batch="batch-b",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="ctrl",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
            batch="batch-b",
        ),
    )
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )

    report = quantification.build_sample_exploration_report(table, design_entries)
    rendered = quantification.render_sample_correlation_tsv(report)

    assert hasattr(quantification, "build_sample_exploration_report")
    assert hasattr(quantification, "render_sample_correlation_tsv")
    assert hasattr(quantification, "export_sample_outlier_tsv")
    assert report.summary.pairwise_correlation_count == 6
    assert rendered.startswith("sample_id_a\tsample_id_b\tcondition_a\tcondition_b")


def test_quantification_package_exports_heatmap_preparation_owner_surface() -> None:
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="heat001",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="heat002",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=120.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="heat003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=95.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="heat004",
            sample_id="case-1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=200.0,
            protein_refs=("P002",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="heat005",
            sample_id="case-2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=220.0,
            protein_refs=("P002",),
        ),
    )
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
            batch="batch-a",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
            batch="batch-b",
        ),
    )
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )

    report = quantification.build_heatmap_preparation_report(table, design_entries=design_entries)
    rendered = quantification.render_heatmap_row_metadata_tsv(report)

    assert hasattr(quantification, "build_heatmap_preparation_report")
    assert hasattr(quantification, "render_heatmap_row_metadata_tsv")
    assert hasattr(quantification, "export_heatmap_column_metadata_tsv")
    assert report.row_metadata[0].missing_value_policy.value == "fill_row_median"
    assert "missing_value_policy" in rendered


def test_quantification_package_exports_power_estimation_owner_surface() -> None:
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="power001",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="power002",
            sample_id="c2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="power003",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=140.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="power004",
            sample_id="t2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=150.0,
            protein_refs=("P001",),
        ),
    )
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="t2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzml",
        ),
    )
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )

    report = quantification.build_power_estimation_report(table, design_entries)
    rendered = quantification.render_power_effect_size_grid_tsv(report)

    assert hasattr(quantification, "build_power_estimation_report")
    assert hasattr(quantification, "render_power_effect_size_grid_tsv")
    assert hasattr(quantification, "export_power_variance_tsv")
    assert report.effect_size_grid
    assert rendered.startswith("replicates_per_condition\tevaluable_entity_count")


def test_quantification_package_exports_per_value_provenance_surface() -> None:
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="prov001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="prov002",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=80.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="prov003",
            sample_id="s1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=60.0,
            protein_refs=("P001",),
        ),
    )
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.TOP_N,
        top_n=2,
    )
    value = table.values[0]

    assert value.value_provenance is not None
    assert value.value_provenance.source_feature_ids == ("prov001", "prov002")
    assert value.value_provenance.source_peptides == ("PEPA", "PEPB")
    assert tuple(
        excluded.reason_code
        for excluded in value.value_provenance.excluded_contributors
    ) == ("excluded_by_top_n_rollup",)


def test_quantification_package_exports_protein_value_contributor_surface() -> None:
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="contrib001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="contrib002",
            sample_id="s1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=80.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="contrib003",
            sample_id="s1",
            peptide="PEPD",
            canonical_peptide="PEPD",
            intensity=60.0,
            protein_refs=("P001",),
        ),
    )
    report = quantification.build_protein_intensity_matrix_from_features(
        records,
        aggregation_method=quantification.QuantRollupMethod.TOP_N,
        top_n=2,
    )
    rendered = quantification.render_protein_peptide_contribution_tsv(report)
    top_entry = next(
        entry
        for entry in report.peptide_contribution_entries
        if entry.peptide_id == "PEPA"
    )
    excluded_entry = next(
        entry
        for entry in report.peptide_contribution_entries
        if entry.peptide_id == "PEPD"
    )

    assert hasattr(quantification, "build_protein_intensity_matrix_from_features")
    assert hasattr(quantification, "render_protein_peptide_contribution_tsv")
    assert top_entry.included_abundance_fraction == 0.5555555555555556
    assert excluded_entry.included_by_policy is False
    assert excluded_entry.abundance_rank == 3
    assert "included_abundance_fraction" in rendered


def test_quantification_package_exports_peptide_profile_inconsistency_surface() -> None:
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="ppi001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi002",
            sample_id="s2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=200.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi003",
            sample_id="s3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=400.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi004",
            sample_id="s1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=110.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi005",
            sample_id="s2",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=220.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi006",
            sample_id="s3",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=440.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi007",
            sample_id="s1",
            peptide="PEPD",
            canonical_peptide="PEPD",
            intensity=90.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi008",
            sample_id="s2",
            peptide="PEPD",
            canonical_peptide="PEPD",
            intensity=180.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi009",
            sample_id="s3",
            peptide="PEPD",
            canonical_peptide="PEPD",
            intensity=360.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi010",
            sample_id="s1",
            peptide="PEPVVK",
            canonical_peptide="PEPVVK",
            intensity=400.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi011",
            sample_id="s2",
            peptide="PEPVVK",
            canonical_peptide="PEPVVK",
            intensity=200.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="ppi012",
            sample_id="s3",
            peptide="PEPVVK",
            canonical_peptide="PEPVVK",
            intensity=100.0,
            protein_refs=("P001",),
        ),
    )
    peptide_matrix = quantification.build_peptide_intensity_matrix_from_features(records)
    report = quantification.build_peptide_profile_inconsistency_report(peptide_matrix)
    rendered = quantification.render_peptide_profile_inconsistency_tsv(report)
    inverted_entry = next(
        entry for entry in report.entries if entry.peptide_id == "PEPVVK"
    )

    assert hasattr(quantification, "build_peptide_profile_inconsistency_report")
    assert hasattr(quantification, "render_peptide_profile_inconsistency_tsv")
    assert inverted_entry.inconsistent_with_protein_profile is True
    assert inverted_entry.outlier_reason.value == "directional_profile_inversion"
    assert "directional_profile_inversion" in rendered


def test_quantification_package_exports_multi_contrast_consistency_surface() -> None:
    records = (
        quantification.Ms1FeatureRecord(
            feature_id="mcc001",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="mcc002",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="mcc003",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=420.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="mcc004",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=430.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="mcc005",
            sample_id="rescue-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=260.0,
            protein_refs=("P001",),
        ),
        quantification.Ms1FeatureRecord(
            feature_id="mcc006",
            sample_id="rescue-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=250.0,
            protein_refs=("P001",),
        ),
    )
    design_entries = (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="rescue-1",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="rescue-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="rescue-2",
            condition="rescue",
            replicate=2,
            fraction=1,
            spectra_file="rescue-2.mzml",
        ),
    )
    table = quantification.build_label_free_intensity_table(
        records,
        entity_level=quantification.QuantEntityLevel.PROTEIN,
        aggregation_method=quantification.QuantRollupMethod.SUM,
    )
    multi_condition = quantification.build_multi_condition_differential_abundance_report(
        table,
        design_entries,
    )
    report = quantification.build_multi_contrast_consistency_report(
        multi_condition,
        entity_protein_refs=table.entity_protein_refs,
    )
    rendered = quantification.render_multi_contrast_consistency_tsv(report)

    assert hasattr(quantification, "build_multi_contrast_consistency_report")
    assert hasattr(quantification, "render_multi_contrast_consistency_tsv")
    assert hasattr(quantification, "export_multi_contrast_consistency_tsv")
    assert report.summary.entity_count == 1
    assert report.entities[0].shared_hit is True
    assert "shared_hit" in rendered
