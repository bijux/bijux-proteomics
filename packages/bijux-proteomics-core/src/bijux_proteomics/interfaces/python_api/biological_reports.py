# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Core biological report Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.identification import (
    ParsimonyVariant,
    SearchAdapterKind,
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
from bijux_proteomics.interfaces.support.ptm_quantification.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantRollupMethod,
)
from bijux_proteomics.interfaces.support.workflow import (
    BiologicalResultSelectionPolicy,
    DdaWorkflowConfig,
    LabelFreeWorkflowConfig,
    WorkflowMode,
)
from bijux_proteomics.workflow.pipelines.dda_biological_workflow import (
    DdaBiologicalWorkflowBundle,
    DdaBiologicalWorkflowExportManifest,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
)


def run_biological_report_command(
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
        LabelFreeWorkflowConfig(
            input_tsv_path=input_tsv,
            design_tsv_path=design_tsv,
            proteins_fasta_path=proteins_fasta,
            protocol_context_tsv_path=protocol_context_tsv,
            annotation_tsv_path=annotation_tsv,
            context_annotation_tsv_path=context_annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            mapping=Ms1FeatureColumnMapping(
                sample_id=sample_column,
                feature_id=feature_id_column,
                peptide=peptide_column,
                intensity=intensity_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                mz=mz_column,
                retention_time_seconds=retention_time_column,
                missing_reason=missing_reason_column,
                protein_separator=protein_separator,
            ),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
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
    if not isinstance(report, BiologicalResultReportBundle):
        raise click.ClickException(
            "workflow did not produce the expected biological report bundle"
        )
    if not isinstance(manifest, BiologicalResultReportExportManifest):
        raise click.ClickException(
            "workflow did not produce the expected biological report manifest"
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


def run_dda_biological_report_command(
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
        DdaWorkflowConfig(
            mode=WorkflowMode.GENERIC_PSM,
            search_result_tsv_path=search_result_tsv,
            design_tsv_path=design_tsv,
            proteins_fasta_path=proteins_fasta,
            protocol_context_tsv_path=protocol_context_tsv,
            adapter_kind=SearchAdapterKind(adapter_kind),
            generic_mapping_path=mapping_path,
            dialect_id=dialect_id,
            source_protein_tsv_path=source_protein_tsv,
            annotation_tsv_path=annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            psm_q_value_threshold=psm_q_value_threshold,
            parsimony_variant=ParsimonyVariant(parsimony_variant),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
            minimum_shared_peptides=minimum_shared_peptides,
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
    if not isinstance(report, DdaBiologicalWorkflowBundle):
        raise click.ClickException(
            "workflow did not produce the expected DDA biological bundle"
        )
    if not isinstance(manifest, DdaBiologicalWorkflowExportManifest):
        raise click.ClickException(
            "workflow did not produce the expected DDA biological manifest"
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


__all__ = ["run_biological_report_command", "run_dda_biological_report_command"]
