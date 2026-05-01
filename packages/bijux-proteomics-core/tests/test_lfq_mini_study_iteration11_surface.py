# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.corpus_iteration11 import build_complete_lfq_mini_study_bundle


def test_build_complete_lfq_mini_study_bundle_tracks_required_outputs() -> None:
    bundle = build_complete_lfq_mini_study_bundle(
        study_id="lfq-mini-01",
        feature_matrix_path="inputs/feature.tsv",
        peptide_matrix_path="inputs/peptide.tsv",
        protein_matrix_path="inputs/protein.tsv",
        normalization_method="median",
        missingness_summary_path="outputs/missingness.json",
        differential_abundance_report_path="outputs/da.json",
        review_packet_path="outputs/review.json",
    )

    assert bundle.normalization_method == "median"
    assert bundle.differential_abundance_report_path.endswith("da.json")
