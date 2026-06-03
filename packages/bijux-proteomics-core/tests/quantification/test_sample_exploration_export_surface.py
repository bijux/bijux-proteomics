# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.quantification import (
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_sample_exploration_report,
    export_sample_cluster_tsv,
    export_sample_correlation_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_outlier_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
)

from .test_sample_exploration_surface import _sample_exploration_inputs


def test_sample_exploration_exports_preserve_summary_scores_and_clusters(
    tmp_path: Path,
) -> None:
    records, design = _sample_exploration_inputs()
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    report = build_sample_exploration_report(table, design)

    summary_path = tmp_path / "sample_exploration.summary.tsv"
    scores_path = tmp_path / "sample_exploration.scores.tsv"
    variance_path = tmp_path / "sample_exploration.variance.tsv"
    correlations_path = tmp_path / "sample_exploration.correlations.tsv"
    distances_path = tmp_path / "sample_exploration.distances.tsv"
    clusters_path = tmp_path / "sample_exploration.clusters.tsv"
    outliers_path = tmp_path / "sample_exploration.outliers.tsv"

    export_sample_exploration_summary_tsv(report, summary_path)
    export_sample_pca_scores_tsv(report, scores_path)
    export_sample_pca_variance_tsv(report, variance_path)
    export_sample_correlation_tsv(report, correlations_path)
    export_sample_distance_tsv(report, distances_path)
    export_sample_cluster_tsv(report, clusters_path)
    export_sample_outlier_tsv(report, outliers_path)

    assert "entity_level\tmeasure_kind\taggregation_method" in summary_path.read_text(
        encoding="utf-8"
    )
    assert "sample_id\tcondition\tbatch\tpc1\tpc2" in scores_path.read_text(
        encoding="utf-8"
    )
    assert (
        "component_index\tcomponent_label\texplained_variance_ratio"
        in variance_path.read_text(encoding="utf-8")
    )
    assert (
        "sample_id_a\tsample_id_b\tcondition_a\tcondition_b"
        in correlations_path.read_text(encoding="utf-8")
    )
    assert (
        "sample_id_a\tsample_id_b\tcondition_a\tcondition_b"
        in distances_path.read_text(encoding="utf-8")
    )
    clusters_tsv = clusters_path.read_text(encoding="utf-8")
    assert (
        "merge_order\tmember_sample_ids\tleft_sample_ids\tright_sample_ids"
        in clusters_tsv
    )
    assert "case-1;case-2;ctrl-1;ctrl-2" in clusters_tsv
    assert "sample_id\tcondition\tbatch\toutlier_reasons" in outliers_path.read_text(
        encoding="utf-8"
    )
