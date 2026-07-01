# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Workflow execution and runtime planning Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.identification import SearchAdapterKind
from bijux_proteomics.interfaces.support.io_and_dia import (
    WorkflowSchedulerKind,
    build_normalized_run_bundle,
    build_proteomics_workflow_runtime_bundle,
    build_workflow_runtime_validation_report,
    parse_experimental_design_table,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)
from bijux_proteomics.interfaces.support.output_protocol.volcano_review import (
    _build_volcano_review_policy,
)
from bijux_proteomics.interfaces.support.output_protocol.workflow_execution import (
    _validate_proteomics_run_inputs,
)
from bijux_proteomics.interfaces.support.ptm_quantification.quantification import (
    NormalizationMethod,
)
from bijux_proteomics.interfaces.support.workflow import (
    BiologicalResultSelectionPolicy,
    ProteomicsRunEngine,
    build_proteomics_run_bundle,
    render_proteomics_run_summary_tsv,
    write_proteomics_run_bundle,
)


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
        if report_path is None:
            raise click.ClickException(
                "proteomics run requires --report-path for the selected engine"
            )
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
        manifest = write_proteomics_run_bundle(report, output_dir)
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


__all__ = [
    "run_bundle_run_command",
    "run_proteomics_run_command",
    "run_workflow_plan_command",
    "run_workflow_validate_command",
]
