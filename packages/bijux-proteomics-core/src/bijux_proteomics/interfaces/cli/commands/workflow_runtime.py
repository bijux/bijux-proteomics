# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Workflow execution and runtime planning CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.workflow_runtime import (
    run_bundle_run_command,
    run_proteomics_run_command,
    run_workflow_plan_command,
    run_workflow_validate_command,
)
from bijux_proteomics.interfaces.support.identification import SearchAdapterKind
from bijux_proteomics.interfaces.support.io_and_dia import WorkflowSchedulerKind
from bijux_proteomics.interfaces.support.ptm_quantification import NormalizationMethod
from bijux_proteomics.interfaces.support.workflow import ProteomicsRunEngine
from bijux_proteomics.interfaces.support.sequence_support import (
    _normalization_choice,
    _search_adapter_choice,
    _workflow_scheduler_choice,
)


@click.command("bundle-run")
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out-dir",
    "out_dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
    help="Directory where the normalized run bundle should be written.",
)
def bundle_run_command(
    spectra_path: Path,
    identifications_path: Path | None,
    design_path: Path | None,
    out_dir: Path,
) -> None:
    """Build one normalized run bundle from spectra, IDs, and optional design metadata."""
    return run_bundle_run_command(
        spectra_path, identifications_path, design_path, out_dir
    )


@click.command("run")
@click.option(
    "--engine",
    type=click.Choice([engine.value for engine in ProteomicsRunEngine]),
    required=True,
)
@click.option(
    "--report",
    "report_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Primary engine result table: DIA-NN report.tsv, MaxQuant evidence.txt, or FragPipe psm.tsv.",
)
@click.option(
    "--peptides",
    "peptides_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="MaxQuant-only peptides.txt input.",
)
@click.option(
    "--protein-groups",
    "protein_groups_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="MaxQuant-only proteinGroups.txt input.",
)
@click.option(
    "--source-protein-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional FragPipe or DDA source protein table for discrepancy review.",
)
@click.option(
    "--metadata",
    "metadata_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--proteins-fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--contrast", required=True)
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
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=0.01, show_default=True)
@click.option(
    "--psm-q-value-threshold",
    type=float,
    default=0.01,
    show_default=True,
)
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
    "--heatmap-max-entities",
    type=int,
    default=50,
    show_default=True,
)
@click.option(
    "--heatmap-min-observed-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--out",
    "output_dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
    help="Directory where the final flagship result package should be written.",
)
@click.option(
    "--json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON summary output path.",
)
def proteomics_run_command(
    engine: str,
    report_path: Path | None,
    peptides_path: Path | None,
    protein_groups_path: Path | None,
    source_protein_tsv: Path | None,
    metadata_path: Path,
    proteins_fasta: Path,
    contrast: str,
    config_path: Path | None,
    annotation_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    normalization: str,
    max_q_value: float,
    psm_q_value_threshold: float,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    heatmap_max_entities: int,
    heatmap_min_observed_fraction: float,
    volcano_top_label_count: int,
    output_dir: Path,
    json_out: Path | None,
) -> None:
    """Run one flagship proteomics workflow from engine output to final biology report."""
    return run_proteomics_run_command(
        engine,
        report_path,
        peptides_path,
        protein_groups_path,
        source_protein_tsv,
        metadata_path,
        proteins_fasta,
        contrast,
        config_path,
        annotation_tsv,
        go_annotation_tsv,
        pathway_membership_tsv,
        complex_membership_tsv,
        normalization,
        max_q_value,
        psm_q_value_threshold,
        max_adjusted_p_value,
        min_absolute_log2_fold_change,
        heatmap_max_entities,
        heatmap_min_observed_fraction,
        volcano_top_label_count,
        output_dir,
        json_out,
    )


@click.command("workflow-plan")
@click.option(
    "--proteins",
    "proteins_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--features",
    "features_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-id", default=None)
@click.option(
    "--search-adapter",
    type=_search_adapter_choice(),
    default=SearchAdapterKind.GENERIC.value,
    show_default=True,
)
@click.option(
    "--scheduler",
    type=_workflow_scheduler_choice(),
    default=WorkflowSchedulerKind.SLURM.value,
    show_default=True,
)
@click.option(
    "--container-image",
    default="ghcr.io/bijux/proteomics-runtime:stable",
    show_default=True,
)
@click.option(
    "--artifacts-dir", type=click.Path(path_type=Path, file_okay=False), default=None
)
@click.option("--completed-step", "completed_steps", multiple=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--dag-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--job-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--checkpoint-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def workflow_plan_command(
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None,
    features_path: Path | None,
    design_path: Path | None,
    sample_id: str | None,
    search_adapter: str,
    scheduler: str,
    container_image: str,
    artifacts_dir: Path | None,
    completed_steps: tuple[str, ...],
    out_path: Path | None,
    dag_out: Path | None,
    job_out: Path | None,
    checkpoint_out: Path | None,
) -> None:
    """Build a workflow-runtime bundle for digest/search/FDR/quant/QC execution."""
    return run_workflow_plan_command(
        proteins_path,
        spectra_path,
        identifications_path,
        features_path,
        design_path,
        sample_id,
        search_adapter,
        scheduler,
        container_image,
        artifacts_dir,
        completed_steps,
        out_path,
        dag_out,
        job_out,
        checkpoint_out,
    )


@click.command("workflow-validate")
@click.option(
    "--proteins",
    "proteins_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--features",
    "features_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-id", default=None)
@click.option(
    "--search-adapter",
    type=_search_adapter_choice(),
    default=SearchAdapterKind.GENERIC.value,
    show_default=True,
)
@click.option(
    "--scheduler",
    type=_workflow_scheduler_choice(),
    default=WorkflowSchedulerKind.SLURM.value,
    show_default=True,
)
@click.option(
    "--container-image",
    default="ghcr.io/bijux/proteomics-runtime:stable",
    show_default=True,
)
@click.option(
    "--artifacts-dir", type=click.Path(path_type=Path, file_okay=False), default=None
)
@click.option("--completed-step", "completed_steps", multiple=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def workflow_validate_command(
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None,
    features_path: Path | None,
    design_path: Path | None,
    sample_id: str | None,
    search_adapter: str,
    scheduler: str,
    container_image: str,
    artifacts_dir: Path | None,
    completed_steps: tuple[str, ...],
    out_path: Path | None,
) -> None:
    """Validate workflow runtime integrity without executing the workflow."""
    return run_workflow_validate_command(
        proteins_path,
        spectra_path,
        identifications_path,
        features_path,
        design_path,
        sample_id,
        search_adapter,
        scheduler,
        container_image,
        artifacts_dir,
        completed_steps,
        out_path,
    )


COMMANDS = (
    bundle_run_command,
    proteomics_run_command,
    workflow_plan_command,
    workflow_validate_command,
)
