# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics.quantification as quantification
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.study import SampleRunAnalysisPolicy


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
    assert hasattr(quantification, "render_time_course_differential_tsv")
    assert hasattr(quantification, "export_time_course_differential_tsv")
    assert report.ordered_timepoints == ("0", "1")
    assert len(report.entries) == 4
    assert rendered.startswith("entity_id\tcondition\treference_condition")


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
