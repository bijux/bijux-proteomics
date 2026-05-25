# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Workflow-specific biological report CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

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
    'Build one DIA-NN-to-biology report bundle.'
    return run_diann_biological_report_command(result_tsv, design_tsv, proteins_fasta, config_path, annotation_tsv, context_annotation_tsv, protocol_context_tsv, go_annotation_tsv, pathway_membership_tsv, complex_membership_tsv, max_q_value, peptide_rollup, target_kind, shared_peptide_policy, protein_rollup, normalization, condition_a, condition_b, max_adjusted_p_value, min_absolute_log2_fold_change, heatmap_max_entities, heatmap_min_observed_fraction, volcano_top_label_count, output_dir, out_path)

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
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change
                ),
                top_label_count=volcano_top_label_count,
            ),
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "design_rows": result.design_row_count,
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
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
    'Build one MaxQuant-to-biology report bundle.'
    return run_maxquant_biological_report_command(evidence_txt, peptides_txt, protein_groups_txt, design_tsv, proteins_fasta, config_path, annotation_tsv, context_annotation_tsv, protocol_context_tsv, go_annotation_tsv, pathway_membership_tsv, complex_membership_tsv, include_only_identified_by_site, allow_empty_lfq_signal, normalization, condition_a, condition_b, max_adjusted_p_value, min_absolute_log2_fold_change, heatmap_max_entities, heatmap_min_observed_fraction, volcano_top_label_count, output_dir, out_path)

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
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change
                ),
                top_label_count=volcano_top_label_count,
            ),
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "design_rows": result.design_row_count,
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )

COMMANDS = (
    diann_biological_report_command,
    maxquant_biological_report_command,
)
