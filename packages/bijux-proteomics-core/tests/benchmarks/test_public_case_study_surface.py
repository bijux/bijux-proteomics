# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks import (
    build_lfq_cohort_biological_case_study,
    build_public_biological_case_study_catalog,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_lfq_cohort_biological_case_study_keeps_public_data_and_biology_inputs_visible() -> (
    None
):
    case_study = build_lfq_cohort_biological_case_study()

    assert (
        case_study.case_study_id == "public_case_study:lfq_cohort_biological_case_study"
    )
    assert case_study.workflow_family == "lfq"
    assert (
        case_study.source_package_id
        == "flagship_public_package:lfq_cohort_review_package"
    )
    assert case_study.input_paths.feature_table_path.endswith(
        "flagship-public-packages/lfq_cohort_review_package/"
        "evidence/study_scale_ms1_features.tsv"
    )
    assert case_study.input_paths.design_table_path.endswith(
        "flagship-public-packages/lfq_cohort_review_package/"
        "evidence/study_scale.design.tsv"
    )
    assert case_study.input_paths.go_annotation_tsv_path.endswith(
        "public-case-studies/lfq_cohort_biological_case_study/"
        "biology/go_annotations.tsv"
    )
    assert "bounded" in case_study.note


def test_public_biological_case_study_catalog_keeps_required_assets_present() -> None:
    catalog = build_public_biological_case_study_catalog()

    assert len(catalog.entries) == 1
    case_study = catalog.entries[0]
    required_paths = (
        case_study.readme_path,
        case_study.input_paths.feature_table_path,
        case_study.input_paths.design_table_path,
        case_study.input_paths.proteins_fasta_path,
        case_study.input_paths.annotation_tsv_path,
        case_study.input_paths.go_annotation_tsv_path,
        case_study.input_paths.pathway_membership_tsv_path,
        case_study.input_paths.complex_membership_tsv_path,
    )
    for repo_relative_path in required_paths:
        assert (REPO_ROOT / repo_relative_path).is_file()
