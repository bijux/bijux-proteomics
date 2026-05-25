# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Workflow execution and runtime planning CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

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
    'Build one normalized run bundle from spectra, IDs, and optional design metadata.'
    return run_bundle_run_command(spectra_path, identifications_path, design_path, out_dir)

def run_bundle_run_command(
    spectra_path: Path,
    identifications_path: Path | None,
    design_path: Path | None,
    out_dir: Path,
) -> None:
    try:
        manifest = build_normalized_run_bundle(
            bundle_dir=out_dir,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            design_path=design_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(manifest)

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
    'Run one flagship proteomics workflow from engine output to final biology report.'
    return run_proteomics_run_command(engine, report_path, peptides_path, protein_groups_path, source_protein_tsv, metadata_path, proteins_fasta, contrast, config_path, annotation_tsv, go_annotation_tsv, pathway_membership_tsv, complex_membership_tsv, normalization, max_q_value, psm_q_value_threshold, max_adjusted_p_value, min_absolute_log2_fold_change, heatmap_max_entities, heatmap_min_observed_fraction, volcano_top_label_count, output_dir, json_out)

def run_proteomics_run_command(
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
    try:
        resolved_engine = ProteomicsRunEngine(engine)
        _validate_proteomics_run_inputs(
            engine=resolved_engine,
            report_path=report_path,
            peptides_path=peptides_path,
            protein_groups_path=protein_groups_path,
            source_protein_tsv=source_protein_tsv,
            config_path=config_path,
        )
        metadata_report = parse_experimental_design_table(metadata_path)
        if metadata_report.rejected_rows:
            raise click.ClickException("metadata table contains rejected rows")
        report = build_proteomics_run_bundle(
            engine=resolved_engine,
            metadata_entries=tuple(metadata_report.accepted_entries),
            proteins_fasta_path=proteins_fasta,
            report_tsv_path=report_path,
            contrast=contrast,
            peptides_tsv_path=peptides_path,
            protein_groups_tsv_path=protein_groups_path,
            source_protein_tsv_path=source_protein_tsv,
            config_path=config_path,
            annotation_tsv_path=annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            normalization_method=NormalizationMethod(normalization),
            max_q_value=max_q_value,
            psm_q_value_threshold=psm_q_value_threshold,
            selection_policy=BiologicalResultSelectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                heatmap_max_entity_count=heatmap_max_entities,
                heatmap_min_observed_fraction=heatmap_min_observed_fraction,
            ),
            volcano_policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=max_adjusted_p_value,
                absolute_log2_fold_change_threshold=min_absolute_log2_fold_change,
                top_label_count=volcano_top_label_count,
            ),
        )
        manifest = export_proteomics_run_bundle(report, output_dir)
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    manifest_path = output_dir / "proteomics_run_manifest.json"
    manifest_path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")

    _emit_json(
        {
            "metadata_rows": len(metadata_report.accepted_entries),
            "summary_tsv": render_proteomics_run_summary_tsv(report),
            "run": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": {
                "output_dir": str(output_dir),
                "manifest_json": str(manifest_path),
            },
        },
        out_path=json_out,
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
    'Build a workflow-runtime bundle for digest/search/FDR/quant/QC execution.'
    return run_workflow_plan_command(proteins_path, spectra_path, identifications_path, features_path, design_path, sample_id, search_adapter, scheduler, container_image, artifacts_dir, completed_steps, out_path, dag_out, job_out, checkpoint_out)

def run_workflow_plan_command(
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
    try:
        bundle = build_proteomics_workflow_runtime_bundle(
            proteins_path=proteins_path,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            features_path=features_path,
            design_path=design_path,
            sample_id=sample_id,
            search_adapter_kind=SearchAdapterKind(search_adapter),
            scheduler=WorkflowSchedulerKind(scheduler),
            default_container_image=container_image,
            artifacts_dir=artifacts_dir,
            completed_step_ids=tuple(completed_steps),
        )
        if dag_out is not None:
            dag_out.write_text(
                bundle.dag_plan.to_stable_json() + "\n", encoding="utf-8"
            )
        if job_out is not None:
            job_out.write_text(bundle.hpc_job.script_text, encoding="utf-8")
        if checkpoint_out is not None:
            checkpoint_out.write_text(
                bundle.checkpoint.to_stable_json() + "\n", encoding="utf-8"
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(bundle, out_path=out_path)

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
    'Validate workflow runtime integrity without executing the workflow.'
    return run_workflow_validate_command(proteins_path, spectra_path, identifications_path, features_path, design_path, sample_id, search_adapter, scheduler, container_image, artifacts_dir, completed_steps, out_path)

def run_workflow_validate_command(
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
    try:
        bundle = build_proteomics_workflow_runtime_bundle(
            proteins_path=proteins_path,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            features_path=features_path,
            design_path=design_path,
            sample_id=sample_id,
            search_adapter_kind=SearchAdapterKind(search_adapter),
            scheduler=WorkflowSchedulerKind(scheduler),
            default_container_image=container_image,
            artifacts_dir=artifacts_dir,
            completed_step_ids=tuple(completed_steps),
        )
        report = build_workflow_runtime_validation_report(bundle)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report, out_path=out_path)

COMMANDS = (
    bundle_run_command,
    proteomics_run_command,
    workflow_plan_command,
    workflow_validate_command,
)
