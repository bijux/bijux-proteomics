# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    HeatmapPreparationPolicy,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
    build_peptide_intensity_matrix_from_features,
    build_protein_intensity_matrix_from_peptides,
    build_protein_lfq_report_from_peptides,
    build_sample_exploration_report,
    render_heatmap_column_metadata_tsv,
    render_heatmap_matrix_tsv,
    render_heatmap_row_metadata_tsv,
    render_peptide_intensity_matrix_tsv,
    render_peptide_intensity_missingness_tsv,
    render_protein_intensity_matrix_tsv,
    render_protein_intensity_missingness_tsv,
    render_protein_lfq_disconnected_components_tsv,
    render_protein_lfq_matrix_tsv,
    render_protein_lfq_missingness_tsv,
    render_protein_lfq_pairwise_ratios_tsv,
    render_protein_peptide_contribution_tsv,
    render_sample_cluster_tsv,
    render_sample_distance_tsv,
    render_sample_pca_variance_tsv,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="det-001",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P2", "P1"),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="det-002",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P1", "P2"),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="det-003",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=50.0,
            protein_refs=("P1", "P2"),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="det-004",
            sample_id="case-2",
            peptide="PEPTC",
            canonical_peptide="PEPTC",
            intensity=210.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="det-005",
            sample_id="case-1",
            peptide="PEPTC",
            canonical_peptide="PEPTC",
            intensity=205.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="det-006",
            sample_id="ctrl-1",
            peptide="PEPTC",
            canonical_peptide="PEPTC",
            intensity=95.0,
            protein_refs=("P3",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _design_entries() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
    )


def test_quant_matrix_renderers_ignore_scrambled_report_order() -> None:
    peptide_report = build_peptide_intensity_matrix_from_features(_records())
    protein_report = build_protein_intensity_matrix_from_peptides(peptide_report)
    protein_lfq_report = build_protein_lfq_report_from_peptides(peptide_report)

    scrambled_peptide = peptide_report.model_copy(
        update={
            "sample_ids": tuple(reversed(peptide_report.sample_ids)),
            "rows": tuple(
                row.model_copy(
                    update={
                        "modified_peptides": tuple(reversed(row.modified_peptides)),
                        "charge_states": tuple(reversed(row.charge_states)),
                        "protein_refs": tuple(reversed(row.protein_refs)),
                        "values": tuple(reversed(row.values)),
                    }
                )
                for row in reversed(peptide_report.rows)
            ),
            "missing_summary": peptide_report.missing_summary.model_copy(
                update={
                    "entries": tuple(reversed(peptide_report.missing_summary.entries))
                }
            ),
        }
    )
    scrambled_protein = protein_report.model_copy(
        update={
            "sample_ids": tuple(reversed(protein_report.sample_ids)),
            "rows": tuple(
                row.model_copy(
                    update={
                        "protein_refs": tuple(reversed(row.protein_refs)),
                        "contributing_peptides": tuple(
                            reversed(row.contributing_peptides)
                        ),
                        "values": tuple(reversed(row.values)),
                    }
                )
                for row in reversed(protein_report.rows)
            ),
            "missing_summary": protein_report.missing_summary.model_copy(
                update={
                    "entries": tuple(reversed(protein_report.missing_summary.entries))
                }
            ),
        }
    )
    scrambled_lfq = protein_lfq_report.model_copy(
        update={
            "sample_ids": tuple(reversed(protein_lfq_report.sample_ids)),
            "rows": tuple(
                row.model_copy(
                    update={
                        "protein_refs": tuple(reversed(row.protein_refs)),
                        "contributing_peptides": tuple(
                            reversed(row.contributing_peptides)
                        ),
                        "values": tuple(reversed(row.values)),
                        "pairwise_ratios": tuple(reversed(row.pairwise_ratios)),
                    }
                )
                for row in reversed(protein_lfq_report.rows)
            ),
            "missing_summary": protein_lfq_report.missing_summary.model_copy(
                update={
                    "entries": tuple(
                        reversed(protein_lfq_report.missing_summary.entries)
                    )
                }
            ),
            "disconnected_components": tuple(
                reversed(protein_lfq_report.disconnected_components)
            ),
        }
    )

    assert render_peptide_intensity_matrix_tsv(
        peptide_report
    ) == render_peptide_intensity_matrix_tsv(scrambled_peptide)
    assert render_peptide_intensity_missingness_tsv(
        peptide_report
    ) == render_peptide_intensity_missingness_tsv(scrambled_peptide)
    assert render_protein_intensity_matrix_tsv(
        protein_report
    ) == render_protein_intensity_matrix_tsv(scrambled_protein)
    assert render_protein_peptide_contribution_tsv(
        protein_report
    ) == render_protein_peptide_contribution_tsv(scrambled_protein)
    assert render_protein_intensity_missingness_tsv(
        protein_report
    ) == render_protein_intensity_missingness_tsv(scrambled_protein)
    assert render_protein_lfq_matrix_tsv(
        protein_lfq_report
    ) == render_protein_lfq_matrix_tsv(scrambled_lfq)
    assert render_protein_lfq_pairwise_ratios_tsv(
        protein_lfq_report
    ) == render_protein_lfq_pairwise_ratios_tsv(scrambled_lfq)
    assert render_protein_lfq_missingness_tsv(
        protein_lfq_report
    ) == render_protein_lfq_missingness_tsv(scrambled_lfq)
    assert render_protein_lfq_disconnected_components_tsv(
        protein_lfq_report
    ) == render_protein_lfq_disconnected_components_tsv(scrambled_lfq)


def test_heatmap_renderers_ignore_scrambled_report_order() -> None:
    table = build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    report = build_heatmap_preparation_report(
        table,
        design_entries=_design_entries(),
        policy=HeatmapPreparationPolicy(z_score_rows=False),
    )
    scrambled = report.model_copy(
        update={
            "sample_ids": tuple(reversed(report.sample_ids)),
            "rows": tuple(
                row.model_copy(update={"values": tuple(reversed(row.values))})
                for row in reversed(report.rows)
            ),
            "row_metadata": tuple(reversed(report.row_metadata)),
            "column_metadata": tuple(reversed(report.column_metadata)),
        }
    )

    assert render_heatmap_matrix_tsv(report) == render_heatmap_matrix_tsv(scrambled)
    assert render_heatmap_row_metadata_tsv(report) == render_heatmap_row_metadata_tsv(
        scrambled
    )
    assert render_heatmap_column_metadata_tsv(
        report
    ) == render_heatmap_column_metadata_tsv(scrambled)


def test_sample_exploration_renderers_ignore_scrambled_report_order() -> None:
    table = build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    report = build_sample_exploration_report(table, _design_entries())
    scrambled = report.model_copy(
        update={
            "explained_variance_report": report.explained_variance_report.model_copy(
                update={
                    "entries": tuple(reversed(report.explained_variance_report.entries))
                }
            ),
            "sample_distance_report": report.sample_distance_report.model_copy(
                update={
                    "entries": tuple(reversed(report.sample_distance_report.entries))
                }
            ),
            "sample_cluster_report": report.sample_cluster_report.model_copy(
                update={
                    "entries": tuple(reversed(report.sample_cluster_report.entries))
                }
            ),
        }
    )

    assert render_sample_pca_variance_tsv(report) == render_sample_pca_variance_tsv(
        scrambled
    )
    assert render_sample_distance_tsv(report) == render_sample_distance_tsv(scrambled)
    assert render_sample_cluster_tsv(report) == render_sample_cluster_tsv(scrambled)
