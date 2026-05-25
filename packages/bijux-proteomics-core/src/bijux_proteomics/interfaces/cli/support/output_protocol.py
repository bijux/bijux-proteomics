# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Output and protocol helper functions shared by CLI command modules."""

from __future__ import annotations

from .imports import *  # noqa: F401,F403

def _emit_json(payload: Any, *, out_path: Path | None = None) -> None:
    if hasattr(payload, "to_stable_json"):
        rendered = payload.to_stable_json()
    else:
        rendered = json.dumps(payload, indent=2, sort_keys=True)
    if out_path is not None:
        out_path.write_text(rendered + "\n")
    click.echo(rendered)

def _write_text_output(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

def _read_identifier_lines(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ()
    return tuple(
        line
        for raw_line in path.read_text(encoding="utf-8").splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    )

def _build_volcano_review_policy(
    *,
    adjusted_p_value_threshold: float,
    absolute_log2_fold_change_threshold: float,
    top_label_count: int,
) -> VolcanoReviewPolicy:
    return VolcanoReviewPolicy(
        adjusted_p_value_threshold=adjusted_p_value_threshold,
        absolute_log2_fold_change_threshold=absolute_log2_fold_change_threshold,
        top_label_count=top_label_count,
    )

def _load_protocol_context(protocol_context_tsv_path: Path | None):
    if protocol_context_tsv_path is None:
        return None
    return require_single_lab_protocol_context(
        parse_lab_protocol_context_table(protocol_context_tsv_path)
    )

def _build_protocol_consistency_report_from_inputs(
    *,
    protocol_context_tsv_path: Path,
    run_qc_report=None,
    reporter_table_path: Path | None = None,
    ptm_evidence_tsv_path: Path | None = None,
):
    protocol_context = _load_protocol_context(protocol_context_tsv_path)
    if protocol_context is None:  # pragma: no cover
        raise ValueError("protocol context is required")
    reporter_import_report = None
    reporter_input_issue = None
    if reporter_table_path is not None:
        try:
            reporter_import_report = parse_tmt_reporter_table(reporter_table_path)
        except Exception as exc:  # noqa: BLE001
            reporter_input_issue = str(exc)
    ptm_evidence_report = None
    ptm_input_issue = None
    if ptm_evidence_tsv_path is not None:
        try:
            ptm_evidence_report = parse_ptm_localization_tsv(ptm_evidence_tsv_path)
        except Exception as exc:  # noqa: BLE001
            ptm_input_issue = str(exc)
    return build_protocol_consistency_report(
        protocol_context,
        run_qc_report=run_qc_report,
        reporter_import_report=reporter_import_report,
        ptm_evidence_report=ptm_evidence_report,
        reporter_input_issue=reporter_input_issue,
        ptm_input_issue=ptm_input_issue,
    )

def _build_protocol_aware_selection_policy(
    *,
    protocol_context_tsv_path: Path | None,
    max_adjusted_p_value: float | None,
    min_absolute_log2_fold_change: float | None,
    heatmap_max_entity_count: int | None,
    heatmap_min_observed_fraction: float | None,
) -> BiologicalResultSelectionPolicy | None:
    if (
        protocol_context_tsv_path is None
        and max_adjusted_p_value is None
        and min_absolute_log2_fold_change is None
        and heatmap_max_entity_count is None
        and heatmap_min_observed_fraction is None
    ):
        return None

    baseline = BiologicalResultSelectionPolicy()
    protocol_context = _load_protocol_context(protocol_context_tsv_path)
    if protocol_context is not None:
        interpretation_profile = build_lab_protocol_interpretation_profile(
            protocol_context
        )
        baseline = baseline.model_copy(
            update={
                "max_adjusted_p_value": interpretation_profile.max_adjusted_p_value,
                "min_absolute_log2_fold_change": (
                    interpretation_profile.min_absolute_log2_fold_change
                ),
                "heatmap_max_entity_count": (
                    interpretation_profile.heatmap_max_entity_count
                ),
            }
        )
    return baseline.model_copy(
        update={
            "max_adjusted_p_value": (
                baseline.max_adjusted_p_value
                if max_adjusted_p_value is None
                else max_adjusted_p_value
            ),
            "min_absolute_log2_fold_change": (
                baseline.min_absolute_log2_fold_change
                if min_absolute_log2_fold_change is None
                else min_absolute_log2_fold_change
            ),
            "heatmap_max_entity_count": (
                baseline.heatmap_max_entity_count
                if heatmap_max_entity_count is None
                else heatmap_max_entity_count
            ),
            "heatmap_min_observed_fraction": (
                baseline.heatmap_min_observed_fraction
                if heatmap_min_observed_fraction is None
                else heatmap_min_observed_fraction
            ),
        }
    )

def _run_orchestrated_workflow(config):
    try:
        return run_proteomics_workflow(config)
    except Exception as exc:  # noqa: BLE001
        workflow_name = getattr(getattr(config, "mode", None), "value", None)
        report = build_failure_explanation_report(
            (
                FailureExplanationRequest(
                    failure_id="workflow_failure",
                    workflow_name=workflow_name,
                    failure_text=str(exc),
                ),
            )
        )
        raise click.ClickException(
            format_failure_explanation_for_cli(report.explanations[0])
        ) from exc

def _validate_proteomics_run_inputs(
    *,
    engine: ProteomicsRunEngine,
    report_path: Path | None,
    peptides_path: Path | None,
    protein_groups_path: Path | None,
    source_protein_tsv: Path | None,
    config_path: Path | None,
) -> None:
    if report_path is None:
        raise click.ClickException("--report is required")
    if engine is ProteomicsRunEngine.MAXQUANT:
        if peptides_path is None:
            raise click.ClickException(
                "MaxQuant runs require --peptides with peptides.txt"
            )
        if protein_groups_path is None:
            raise click.ClickException(
                "MaxQuant runs require --protein-groups with proteinGroups.txt"
            )
        return
    if peptides_path is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --peptides; that input is MaxQuant-specific"
        )
    if protein_groups_path is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --protein-groups; that input is MaxQuant-specific"
        )
    if engine is not ProteomicsRunEngine.FRAGPIPE and source_protein_tsv is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --source-protein-tsv; that input is FragPipe-specific"
        )
    if engine is ProteomicsRunEngine.FRAGPIPE and config_path is not None:
        raise click.ClickException(
            "fragpipe runs do not accept --config-path in the flagship command"
        )

def _export_volcano_review_assets(
    *,
    review_report: Any,
    json_out: Path | None,
    svg_out: Path | None,
    html_out: Path | None,
) -> None:
    if json_out is not None:
        export_volcano_review_json(review_report, json_out)
    if svg_out is not None:
        export_volcano_review_svg(review_report, svg_out)
    if html_out is not None:
        export_volcano_review_html(review_report, html_out)

__all__ = [name for name in globals() if not name.startswith("__")]
