# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Core biological report CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.biological_reports import (
    run_biological_report_command,
    run_dda_biological_report_command,
)
from bijux_proteomics.interfaces.support.identification import (
    ParsimonyVariant,
    SearchAdapterKind,
)
from bijux_proteomics.interfaces.support.ptm_quantification.quantification import (
    NormalizationMethod,
    QuantRollupMethod,
)
from bijux_proteomics.interfaces.support.sequence_support.cli_choices import (
    _normalization_choice,
    _quant_rollup_choice,
)


@click.command("biological-report")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--context-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--protocol-context-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--go-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--pathway-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--complex-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column",
    default="retention_time_seconds",
    show_default=True,
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=None,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=None,
)
@click.option(
    "--heatmap-max-entities",
    type=int,
    default=None,
)
@click.option(
    "--heatmap-min-observed-fraction",
    type=float,
    default=None,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("biological_report"),
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def biological_report_command(
    input_tsv: Path,
    design_tsv: Path,
    proteins_fasta: Path,
    annotation_tsv: Path | None,
    context_annotation_tsv: Path | None,
    protocol_context_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    condition_a: str | None,
    condition_b: str | None,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    heatmap_max_entities: int,
    heatmap_min_observed_fraction: float,
    volcano_top_label_count: int,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build one biological interpretation report bundle over governed LFQ results."""
    return run_biological_report_command(
        input_tsv,
        design_tsv,
        proteins_fasta,
        annotation_tsv,
        context_annotation_tsv,
        protocol_context_tsv,
        go_annotation_tsv,
        pathway_membership_tsv,
        complex_membership_tsv,
        aggregation,
        top_n,
        normalization,
        sample_column,
        feature_id_column,
        peptide_column,
        intensity_column,
        protein_refs_column,
        charge_column,
        mz_column,
        retention_time_column,
        missing_reason_column,
        protein_separator,
        condition_a,
        condition_b,
        max_adjusted_p_value,
        min_absolute_log2_fold_change,
        heatmap_max_entities,
        heatmap_min_observed_fraction,
        volcano_top_label_count,
        output_dir,
        out_path,
    )


@click.command("dda-biological-report")
@click.argument(
    "search_result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--adapter-kind",
    type=click.Choice(
        (
            SearchAdapterKind.COMET.value,
            SearchAdapterKind.MSFRAGGER.value,
            SearchAdapterKind.SAGE.value,
            SearchAdapterKind.MAXQUANT_EVIDENCE.value,
            SearchAdapterKind.GENERIC.value,
        )
    ),
    default=SearchAdapterKind.GENERIC.value,
    show_default=True,
)
@click.option("--dialect-id", default="default", show_default=True)
@click.option(
    "--mapping-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--source-protein-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--protocol-context-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--go-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--pathway-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--complex-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--psm-q-value-threshold",
    type=float,
    default=0.01,
    show_default=True,
)
@click.option(
    "--parsimony-variant",
    type=click.Choice([variant.value for variant in ParsimonyVariant]),
    default=ParsimonyVariant.GREEDY_COVERAGE.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--minimum-shared-peptides",
    type=int,
    default=1,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=None,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=None,
)
@click.option(
    "--heatmap-max-entities",
    type=int,
    default=None,
)
@click.option(
    "--heatmap-min-observed-fraction",
    type=float,
    default=None,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("dda_biological_report"),
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def dda_biological_report_command(
    search_result_tsv: Path,
    design_tsv: Path,
    proteins_fasta: Path,
    adapter_kind: str,
    dialect_id: str,
    mapping_path: Path | None,
    source_protein_tsv: Path | None,
    protocol_context_tsv: Path | None,
    annotation_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    psm_q_value_threshold: float,
    parsimony_variant: str,
    aggregation: str,
    top_n: int,
    minimum_shared_peptides: int,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    heatmap_max_entities: int,
    heatmap_min_observed_fraction: float,
    volcano_top_label_count: int,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build one DDA search-result-to-biology report bundle."""
    return run_dda_biological_report_command(
        search_result_tsv,
        design_tsv,
        proteins_fasta,
        adapter_kind,
        dialect_id,
        mapping_path,
        source_protein_tsv,
        protocol_context_tsv,
        annotation_tsv,
        go_annotation_tsv,
        pathway_membership_tsv,
        complex_membership_tsv,
        psm_q_value_threshold,
        parsimony_variant,
        aggregation,
        top_n,
        minimum_shared_peptides,
        normalization,
        condition_a,
        condition_b,
        max_adjusted_p_value,
        min_absolute_log2_fold_change,
        heatmap_max_entities,
        heatmap_min_observed_fraction,
        volcano_top_label_count,
        output_dir,
        out_path,
    )


COMMANDS = (
    biological_report_command,
    dda_biological_report_command,
)
