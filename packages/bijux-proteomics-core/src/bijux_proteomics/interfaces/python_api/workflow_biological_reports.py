# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Workflow-specific biological report Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
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
from bijux_proteomics.interfaces.support.workflow import (
    BiologicalResultSelectionPolicy,
    DiannWorkflowConfig,
    MaxquantWorkflowConfig,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)
from bijux_proteomics.interfaces.support.output_protocol.protocol_policy import (
    _build_protocol_aware_selection_policy,
)
from bijux_proteomics.interfaces.support.output_protocol.volcano_review import (
    _build_volcano_review_policy,
)
from bijux_proteomics.interfaces.support.output_protocol.workflow_execution import (
    _run_orchestrated_workflow,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
    DiannBiologicalWorkflowExportManifest,
)
from bijux_proteomics.workflow.pipelines.maxquant_biological_workflow import (
    MaxquantBiologicalWorkflowBundle,
    MaxquantBiologicalWorkflowExportManifest,
)


def run_diann_biological_report_command(
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
    selection_policy = _build_protocol_aware_selection_policy(
        protocol_context_tsv_path=protocol_context_tsv,
        max_adjusted_p_value=max_adjusted_p_value,
        min_absolute_log2_fold_change=min_absolute_log2_fold_change,
        heatmap_max_entity_count=heatmap_max_entities,
        heatmap_min_observed_fraction=heatmap_min_observed_fraction,
    )
    volcano_adjusted_p_value = (
        BiologicalResultSelectionPolicy().max_adjusted_p_value
        if max_adjusted_p_value is None
        else max_adjusted_p_value
    )
    volcano_absolute_log2_fold_change = (
        BiologicalResultSelectionPolicy().min_absolute_log2_fold_change
        if min_absolute_log2_fold_change is None
        else min_absolute_log2_fold_change
    )
    result = _run_orchestrated_workflow(
        DiannWorkflowConfig(
            result_tsv_path=result_tsv,
            design_tsv_path=design_tsv,
            proteins_fasta_path=proteins_fasta,
            protocol_context_tsv_path=protocol_context_tsv,
            config_path=config_path,
            annotation_tsv_path=annotation_tsv,
            context_annotation_tsv_path=context_annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            max_q_value=max_q_value,
            peptide_rollup_method=DiaPeptideRollupMethod(peptide_rollup),
            target_kind=DiaProteinMatrixTargetKind(target_kind),
            shared_peptide_policy=DiaSharedPeptidePolicy(shared_peptide_policy),
            protein_rollup_method=DiaProteinRollupMethod(protein_rollup),
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            selection_policy=selection_policy,
            volcano_policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value,
                absolute_log2_fold_change_threshold=(volcano_absolute_log2_fold_change),
                top_label_count=volcano_top_label_count,
            ),
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if not isinstance(report, DiannBiologicalWorkflowBundle):
        raise click.ClickException(
            "workflow did not produce the expected DIA-NN biological bundle"
        )
    if not isinstance(manifest, DiannBiologicalWorkflowExportManifest):
        raise click.ClickException(
            "workflow did not produce the expected DIA-NN biological manifest"
        )
    _emit_json(
        {
            "design_rows": result.design_row_count,
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


def run_maxquant_biological_report_command(
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
    selection_policy = _build_protocol_aware_selection_policy(
        protocol_context_tsv_path=protocol_context_tsv,
        max_adjusted_p_value=max_adjusted_p_value,
        min_absolute_log2_fold_change=min_absolute_log2_fold_change,
        heatmap_max_entity_count=heatmap_max_entities,
        heatmap_min_observed_fraction=heatmap_min_observed_fraction,
    )
    volcano_adjusted_p_value = (
        BiologicalResultSelectionPolicy().max_adjusted_p_value
        if max_adjusted_p_value is None
        else max_adjusted_p_value
    )
    volcano_absolute_log2_fold_change = (
        BiologicalResultSelectionPolicy().min_absolute_log2_fold_change
        if min_absolute_log2_fold_change is None
        else min_absolute_log2_fold_change
    )
    result = _run_orchestrated_workflow(
        MaxquantWorkflowConfig(
            evidence_txt_path=evidence_txt,
            peptides_txt_path=peptides_txt,
            protein_groups_txt_path=protein_groups_txt,
            design_tsv_path=design_tsv,
            proteins_fasta_path=proteins_fasta,
            protocol_context_tsv_path=protocol_context_tsv,
            config_path=config_path,
            annotation_tsv_path=annotation_tsv,
            context_annotation_tsv_path=context_annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            include_only_identified_by_site=include_only_identified_by_site,
            allow_empty_lfq_signal=allow_empty_lfq_signal,
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            selection_policy=selection_policy,
            volcano_policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value,
                absolute_log2_fold_change_threshold=(volcano_absolute_log2_fold_change),
                top_label_count=volcano_top_label_count,
            ),
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if not isinstance(report, MaxquantBiologicalWorkflowBundle):
        raise click.ClickException(
            "workflow did not produce the expected MaxQuant biological bundle"
        )
    if not isinstance(manifest, MaxquantBiologicalWorkflowExportManifest):
        raise click.ClickException(
            "workflow did not produce the expected MaxQuant biological manifest"
        )
    _emit_json(
        {
            "design_rows": result.design_row_count,
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


__all__ = [
    "run_diann_biological_report_command",
    "run_maxquant_biological_report_command",
]
