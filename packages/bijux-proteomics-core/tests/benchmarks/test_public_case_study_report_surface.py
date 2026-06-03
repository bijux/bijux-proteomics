# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks import build_lfq_cohort_biological_case_study_report


def test_lfq_cohort_biological_case_study_report_runs_to_biological_outputs() -> None:
    report = build_lfq_cohort_biological_case_study_report()

    assert report.summary.case_study_id == (
        "public_case_study:lfq_cohort_biological_case_study"
    )
    assert report.summary.workflow_family == "lfq"
    assert report.summary.condition_a == "control"
    assert report.summary.condition_b == "treatment"
    assert report.summary.protein_count == 3
    assert report.summary.significant_protein_count == 1
    assert report.summary.sample_count == 8
    assert report.summary.go_enriched_term_count == 1
    assert report.summary.pathway_enriched_entry_count == 1
    assert report.summary.complex_enriched_entry_count == 1
    assert report.biological_report.summary.heatmap_entity_count == 1
    assert report.biological_report.summary.pca_outlier_sample_count == 2
    assert "exploratory effect-size policy" in report.note
