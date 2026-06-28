# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Interpretation disease CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.interpretation_disease import (
    run_disease_phenotype_command,
)
from bijux_proteomics.interfaces.support.ptm_quantification import (
    NormalizationMethod,
    QuantRollupMethod,
)


@click.command("disease-phenotype")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "context_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--design-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
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
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=click.Choice([method.value for method in NormalizationMethod]),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--context-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--context-id-column", default="context_id", show_default=True)
@click.option("--context-kind-column", default="context_kind", show_default=True)
@click.option("--context-name-column", default="context_name", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--evidence-column", default="evidence", show_default=True)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--min-enrichment-ratio",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--high-confidence-min-supporting-protein-count",
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
    "--interpretation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unknown-annotation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-context-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def disease_phenotype_command(
    input_table: Path,
    context_tsv: Path,
    design_path: Path,
    condition_a: str | None,
    condition_b: str | None,
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
    top_n: int,
    normalization: str,
    context_protein_ref_column: str,
    context_id_column: str,
    context_kind_column: str,
    context_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    evidence_column: str,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    min_enrichment_ratio: float,
    high_confidence_min_supporting_protein_count: int,
    summary_tsv_out: Path | None,
    interpretation_tsv_out: Path | None,
    unknown_annotation_tsv_out: Path | None,
    rejected_context_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Interpret changed proteins through explicit disease and phenotype annotation."""
    return run_disease_phenotype_command(
        input_table,
        context_tsv,
        design_path,
        condition_a,
        condition_b,
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
        context_protein_ref_column,
        context_id_column,
        context_kind_column,
        context_name_column,
        source_name_column,
        source_accession_column,
        evidence_column,
        max_adjusted_p_value,
        min_absolute_log2_fold_change,
        min_enrichment_ratio,
        high_confidence_min_supporting_protein_count,
        summary_tsv_out,
        interpretation_tsv_out,
        unknown_annotation_tsv_out,
        rejected_context_tsv_out,
        out_path,
    )


COMMANDS = (disease_phenotype_command,)
