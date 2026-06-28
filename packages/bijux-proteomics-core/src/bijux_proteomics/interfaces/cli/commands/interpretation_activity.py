# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Interpretation activity CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.interpretation_activity import (
    run_complex_activity_command,
    run_pathway_activity_command,
)
from bijux_proteomics.interfaces.support.ptm_quantification import (
    NormalizationMethod,
    QuantRollupMethod,
)


@click.command("pathway-activity")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "pathway_membership_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--design-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--aggregation",
    type=click.Choice(["sum", "top_n"]),
    default="sum",
    show_default=True,
)
@click.option("--top-n", default=3, show_default=True, type=int)
@click.option(
    "--normalization",
    type=click.Choice(["none", "median", "mean"]),
    default="median",
    show_default=True,
)
@click.option("--pathway-id-column", default="pathway_id", show_default=True)
@click.option("--pathway-name-column", default="pathway_name", show_default=True)
@click.option("--pathway-source-name-column", default="source_name", show_default=True)
@click.option(
    "--pathway-source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--pathway-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--pathway-gene-symbol-column", default="gene_symbol", show_default=True)
@click.option("--minimum-observed-member-count", default=2, show_default=True, type=int)
@click.option(
    "--summary-tsv-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--matrix-tsv-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--sample-score-tsv-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--condition-score-tsv-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--condition-comparison-tsv-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--member-contribution-tsv-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--unresolved-member-tsv-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--rejected-pathway-tsv-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out-path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
def pathway_activity_command(
    input_table: Path,
    pathway_membership_tsv: Path,
    design_path: Path | None,
    fasta: Path | None,
    annotation_tsv: Path | None,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str,
    charge_column: str,
    mz_column: str,
    retention_time_column: str,
    missing_reason_column: str,
    protein_separator: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    pathway_id_column: str,
    pathway_name_column: str,
    pathway_source_name_column: str,
    pathway_source_accession_column: str,
    pathway_protein_ref_column: str,
    pathway_gene_symbol_column: str,
    minimum_observed_member_count: int,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    sample_score_tsv_out: Path | None,
    condition_score_tsv_out: Path | None,
    condition_comparison_tsv_out: Path | None,
    member_contribution_tsv_out: Path | None,
    unresolved_member_tsv_out: Path | None,
    rejected_pathway_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score pathway activity across normalized study samples."""
    return run_pathway_activity_command(
        input_table,
        pathway_membership_tsv,
        design_path,
        fasta,
        annotation_tsv,
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
        aggregation,
        top_n,
        normalization,
        pathway_id_column,
        pathway_name_column,
        pathway_source_name_column,
        pathway_source_accession_column,
        pathway_protein_ref_column,
        pathway_gene_symbol_column,
        minimum_observed_member_count,
        summary_tsv_out,
        matrix_tsv_out,
        sample_score_tsv_out,
        condition_score_tsv_out,
        condition_comparison_tsv_out,
        member_contribution_tsv_out,
        unresolved_member_tsv_out,
        rejected_pathway_tsv_out,
        out_path,
    )


@click.command("complex-activity")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "complex_membership_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--design-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--aggregation",
    type=click.Choice([method.value for method in QuantRollupMethod]),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option(
    "--normalization",
    type=click.Choice([method.value for method in NormalizationMethod]),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option("--complex-id-column", default="complex_id", show_default=True)
@click.option("--complex-name-column", default="complex_name", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--complex-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--gene-symbol-column", default="gene_symbol", show_default=True)
@click.option(
    "--minimum-observed-member-count",
    type=int,
    default=2,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--sample-score-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--condition-score-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--condition-comparison-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--member-contribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unresolved-member-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-complex-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def complex_activity_command(
    input_table: Path,
    complex_membership_tsv: Path,
    design_path: Path | None,
    fasta: Path | None,
    annotation_tsv: Path | None,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    aggregation: str,
    normalization: str,
    top_n: int | None,
    complex_id_column: str,
    complex_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    complex_protein_ref_column: str,
    gene_symbol_column: str,
    minimum_observed_member_count: int,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    sample_score_tsv_out: Path | None,
    condition_score_tsv_out: Path | None,
    condition_comparison_tsv_out: Path | None,
    member_contribution_tsv_out: Path | None,
    unresolved_member_tsv_out: Path | None,
    rejected_complex_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score protein complex activity across normalized study samples."""
    return run_complex_activity_command(
        input_table,
        complex_membership_tsv,
        design_path,
        fasta,
        annotation_tsv,
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
        aggregation,
        normalization,
        top_n,
        complex_id_column,
        complex_name_column,
        source_name_column,
        source_accession_column,
        complex_protein_ref_column,
        gene_symbol_column,
        minimum_observed_member_count,
        summary_tsv_out,
        matrix_tsv_out,
        sample_score_tsv_out,
        condition_score_tsv_out,
        condition_comparison_tsv_out,
        member_contribution_tsv_out,
        unresolved_member_tsv_out,
        rejected_complex_tsv_out,
        out_path,
    )


COMMANDS = (
    pathway_activity_command,
    complex_activity_command,
)
