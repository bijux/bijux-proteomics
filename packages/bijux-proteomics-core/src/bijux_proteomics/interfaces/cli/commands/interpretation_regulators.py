# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation regulator CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.interpretation_regulators import (
    run_ppi_modules_command,
    run_regulator_inference_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("regulator-inference")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "regulator_evidence_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--design-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
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
@click.option(
    "--pathway-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--site-differential-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
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
@click.option("--regulator-column", default="regulator", show_default=True)
@click.option("--evidence-type-column", default="evidence_type", show_default=True)
@click.option("--target-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--target-gene-symbol-column", default="gene_symbol", show_default=True)
@click.option("--target-pathway-id-column", default="pathway_id", show_default=True)
@click.option("--target-site-key-column", default="site_key", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
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
@click.option("--site-key-column", default="site_key", show_default=True)
@click.option("--site-protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--site-log2-fold-change-column", default="log2_fold_change", show_default=True
)
@click.option(
    "--site-adjusted-p-value-column",
    default="adjusted_p_value",
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--inference-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unresolved-target-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-evidence-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-site-signal-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def regulator_inference_command(
    input_table: Path,
    regulator_evidence_tsv: Path,
    design_path: Path,
    fasta: Path | None,
    annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    site_differential_tsv: Path | None,
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
    regulator_column: str,
    evidence_type_column: str,
    target_protein_ref_column: str,
    target_gene_symbol_column: str,
    target_pathway_id_column: str,
    target_site_key_column: str,
    source_name_column: str,
    source_accession_column: str,
    pathway_id_column: str,
    pathway_name_column: str,
    pathway_source_name_column: str,
    pathway_source_accession_column: str,
    pathway_protein_ref_column: str,
    pathway_gene_symbol_column: str,
    site_key_column: str,
    site_protein_ref_column: str,
    site_log2_fold_change_column: str,
    site_adjusted_p_value_column: str,
    summary_tsv_out: Path | None,
    inference_tsv_out: Path | None,
    unresolved_target_tsv_out: Path | None,
    rejected_evidence_tsv_out: Path | None,
    rejected_site_signal_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Infer upstream regulators from explicit target evidence and observed signal."""
    return run_regulator_inference_command(
        input_table,
        regulator_evidence_tsv,
        design_path,
        fasta,
        annotation_tsv,
        pathway_membership_tsv,
        site_differential_tsv,
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
        regulator_column,
        evidence_type_column,
        target_protein_ref_column,
        target_gene_symbol_column,
        target_pathway_id_column,
        target_site_key_column,
        source_name_column,
        source_accession_column,
        pathway_id_column,
        pathway_name_column,
        pathway_source_name_column,
        pathway_source_accession_column,
        pathway_protein_ref_column,
        pathway_gene_symbol_column,
        site_key_column,
        site_protein_ref_column,
        site_log2_fold_change_column,
        site_adjusted_p_value_column,
        summary_tsv_out,
        inference_tsv_out,
        unresolved_target_tsv_out,
        rejected_evidence_tsv_out,
        rejected_site_signal_tsv_out,
        out_path,
    )


@click.command("ppi-modules")
@click.argument(
    "significant_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "ppi_edge_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--protein-set-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--edge-protein-ref-a-column", default="protein_ref_a", show_default=True)
@click.option("--edge-protein-ref-b-column", default="protein_ref_b", show_default=True)
@click.option("--edge-source-name-column", default="source_name", show_default=True)
@click.option(
    "--edge-source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--edge-score-column", default="interaction_score", show_default=True)
@click.option("--set-id-column", default="set_id", show_default=True)
@click.option("--set-name-column", default="set_name", show_default=True)
@click.option("--set-category-column", default="set_category", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--set-protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--edge-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--module-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--isolated-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--module-enrichment-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-edge-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def ppi_modules_command(
    significant_tsv: Path,
    ppi_edge_tsv: Path,
    protein_set_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    edge_protein_ref_a_column: str,
    edge_protein_ref_b_column: str,
    edge_source_name_column: str,
    edge_source_accession_column: str,
    edge_score_column: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    summary_tsv_out: Path | None,
    edge_tsv_out: Path | None,
    module_tsv_out: Path | None,
    isolated_tsv_out: Path | None,
    module_enrichment_tsv_out: Path | None,
    rejected_edge_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a significant-protein PPI subnetwork and connected modules."""
    return run_ppi_modules_command(
        significant_tsv,
        ppi_edge_tsv,
        protein_set_tsv,
        protein_ref_column,
        row_id_column,
        edge_protein_ref_a_column,
        edge_protein_ref_b_column,
        edge_source_name_column,
        edge_source_accession_column,
        edge_score_column,
        set_id_column,
        set_name_column,
        set_category_column,
        source_name_column,
        source_accession_column,
        set_protein_ref_column,
        summary_tsv_out,
        edge_tsv_out,
        module_tsv_out,
        isolated_tsv_out,
        module_enrichment_tsv_out,
        rejected_edge_tsv_out,
        out_path,
    )


COMMANDS = (
    regulator_inference_command,
    ppi_modules_command,
)
