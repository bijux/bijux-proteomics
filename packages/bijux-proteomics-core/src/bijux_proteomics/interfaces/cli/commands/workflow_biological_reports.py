# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Workflow-specific biological report CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.workflow_biological_reports import (
    run_diann_biological_report_command,
    run_maxquant_biological_report_command,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    DiaPeptideRollupMethod,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
)
from bijux_proteomics.interfaces.support.ptm_quantification.quantification import (
    NormalizationMethod,
)
from bijux_proteomics.interfaces.support.sequence_support.cli_choices import (
    _normalization_choice,
)


@click.command("diann-biological-report")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
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
    "--max-q-value",
    type=float,
    default=0.01,
    show_default=True,
)
@click.option(
    "--peptide-rollup",
    type=click.Choice([method.value for method in DiaPeptideRollupMethod]),
    default=DiaPeptideRollupMethod.MAX.value,
    show_default=True,
)
@click.option(
    "--target-kind",
    type=click.Choice([kind.value for kind in DiaProteinMatrixTargetKind]),
    default=DiaProteinMatrixTargetKind.PROTEIN_GROUP.value,
    show_default=True,
)
@click.option(
    "--shared-peptide-policy",
    type=click.Choice([policy.value for policy in DiaSharedPeptidePolicy]),
    default=DiaSharedPeptidePolicy.INCLUDE.value,
    show_default=True,
)
@click.option(
    "--protein-rollup",
    type=click.Choice([method.value for method in DiaProteinRollupMethod]),
    default=DiaProteinRollupMethod.SUM.value,
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
    default=Path("diann_biological_report"),
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_biological_report_command(
    result_tsv: Path,
    design_tsv: Path,
    proteins_fasta: Path,
    config_path: Path | None,
    annotation_tsv: Path | None,
    context_annotation_tsv: Path | None,
    protocol_context_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    max_q_value: float,
    peptide_rollup: str,
    target_kind: str,
    shared_peptide_policy: str,
    protein_rollup: str,
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
    """Build one DIA-NN-to-biology report bundle."""
    return run_diann_biological_report_command(
        result_tsv,
        design_tsv,
        proteins_fasta,
        config_path,
        annotation_tsv,
        context_annotation_tsv,
        protocol_context_tsv,
        go_annotation_tsv,
        pathway_membership_tsv,
        complex_membership_tsv,
        max_q_value,
        peptide_rollup,
        target_kind,
        shared_peptide_policy,
        protein_rollup,
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


@click.command("maxquant-biological-report")
@click.argument(
    "evidence_txt", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "peptides_txt", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "protein_groups_txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "design_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
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
    "--include-only-identified-by-site/--exclude-only-identified-by-site",
    default=False,
    show_default=True,
)
@click.option(
    "--allow-empty-lfq-signal/--require-lfq-signal",
    default=False,
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
    default=Path("maxquant_biological_report"),
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def maxquant_biological_report_command(
    evidence_txt: Path,
    peptides_txt: Path,
    protein_groups_txt: Path,
    design_tsv: Path,
    proteins_fasta: Path,
    config_path: Path | None,
    annotation_tsv: Path | None,
    context_annotation_tsv: Path | None,
    protocol_context_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    include_only_identified_by_site: bool,
    allow_empty_lfq_signal: bool,
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
    """Build one MaxQuant-to-biology report bundle."""
    return run_maxquant_biological_report_command(
        evidence_txt,
        peptides_txt,
        protein_groups_txt,
        design_tsv,
        proteins_fasta,
        config_path,
        annotation_tsv,
        context_annotation_tsv,
        protocol_context_tsv,
        go_annotation_tsv,
        pathway_membership_tsv,
        complex_membership_tsv,
        include_only_identified_by_site,
        allow_empty_lfq_signal,
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
    diann_biological_report_command,
    maxquant_biological_report_command,
)
