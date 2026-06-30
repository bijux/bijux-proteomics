# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Targeted validation and biomarker stability Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.io_and_dia import parse_experimental_design_table
from bijux_proteomics.interfaces.support.multiplex_targeted import (
    BiomarkerStabilityPolicy,
    PanelRedundancyPolicy,
    TargetedResultSourceKind,
    TargetedResultValidationPolicy,
    TargetedValidationVerdict,
    build_biomarker_stability_report,
    build_panel_redundancy_report,
    build_skyline_result_import_report,
    build_targeted_result_validation_report,
    build_transition_table_result_import_report,
    build_validation_evidence_card_report,
    render_biomarker_stability_candidate_tsv,
    render_biomarker_stability_subgroup_tsv,
    render_biomarker_stability_summary_tsv,
    render_biomarker_stability_tsv,
    render_panel_redundancy_candidate_tsv,
    render_panel_redundancy_cluster_tsv,
    render_panel_redundancy_dropped_tsv,
    render_panel_redundancy_summary_tsv,
    render_targeted_result_validation_evidence_tsv,
    render_targeted_result_validation_summary_tsv,
    render_targeted_result_validation_tsv,
    render_validation_evidence_card_assay_tsv,
    render_validation_evidence_card_summary_tsv,
    render_validation_evidence_card_tsv,
    render_validation_evidence_card_warning_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.targeted_panel_support.targeted_validation import (
    _load_panel_redundancy_candidates,
    _load_targeted_validation_discovery_claims,
)
from bijux_proteomics.interfaces.support.validation_evidence_support.candidate_quality import (
    _load_validation_evidence_redundancy_entries,
    _load_validation_evidence_stability_entries,
)
from bijux_proteomics.interfaces.support.validation_evidence_support.card_inputs.discovery_candidates import (
    _load_validation_evidence_discovery_candidates,
)
from bijux_proteomics.interfaces.support.validation_evidence_support.card_inputs.omitted_candidates import (
    _load_validation_evidence_omitted_candidates,
)
from bijux_proteomics.interfaces.support.validation_evidence_support.card_inputs.panel_assays import (
    _load_validation_evidence_panel_assays,
)
from bijux_proteomics.interfaces.support.validation_evidence_support.result_inputs.panel_assays import (
    _load_targeted_validation_panel_assays,
)
from bijux_proteomics.interfaces.support.validation_evidence_support.result_inputs.result_entries import (
    _load_validation_evidence_result_assays,
    _load_validation_evidence_results,
)


def run_targeted_result_validator_command(
    biomarker_candidate_tsv: Path,
    panel_assay_tsv: Path,
    targeted_result_tsv: Path,
    design_path: Path,
    source_kind: str,
    case_condition: str,
    control_condition: str,
    minimum_reliable_replicates_per_condition: int,
    minimum_absolute_validation_log2_effect: float,
    flat_validation_log2_threshold: float,
    summary_tsv_out: Path | None,
    confirmed_tsv_out: Path | None,
    contradicted_tsv_out: Path | None,
    inconclusive_tsv_out: Path | None,
    evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if minimum_reliable_replicates_per_condition < 1:
        raise click.ClickException(
            "minimum-reliable-replicates-per-condition must be at least 1"
        )
    if minimum_absolute_validation_log2_effect < 0.0:
        raise click.ClickException(
            "minimum-absolute-validation-log2-effect must be non-negative"
        )
    if flat_validation_log2_threshold < 0.0:
        raise click.ClickException(
            "flat-validation-log2-threshold must be non-negative"
        )

    discovery_claims = _load_targeted_validation_discovery_claims(
        biomarker_candidate_tsv
    )
    panel_assays = _load_targeted_validation_panel_assays(panel_assay_tsv)
    design_report = parse_experimental_design_table(design_path)
    source_kind_value = TargetedResultSourceKind(source_kind)
    if source_kind_value is TargetedResultSourceKind.SKYLINE_EXPORT:
        import_report = build_skyline_result_import_report(targeted_result_tsv)
    else:
        import_report = build_transition_table_result_import_report(targeted_result_tsv)

    try:
        report = build_targeted_result_validation_report(
            discovery_claims=discovery_claims,
            panel_assays=panel_assays,
            import_report=import_report,
            design_entries=design_report.accepted_entries,
            policy=TargetedResultValidationPolicy(
                case_condition=case_condition,
                control_condition=control_condition,
                minimum_reliable_replicates_per_condition=minimum_reliable_replicates_per_condition,
                minimum_absolute_validation_log2_effect=minimum_absolute_validation_log2_effect,
                flat_validation_log2_threshold=flat_validation_log2_threshold,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_targeted_result_validation_summary_tsv(report),
        )
    if confirmed_tsv_out is not None:
        _write_text_output(
            confirmed_tsv_out,
            render_targeted_result_validation_tsv(
                report,
                TargetedValidationVerdict.CONFIRMED,
            ),
        )
    if contradicted_tsv_out is not None:
        _write_text_output(
            contradicted_tsv_out,
            render_targeted_result_validation_tsv(
                report,
                TargetedValidationVerdict.CONTRADICTED,
            ),
        )
    if inconclusive_tsv_out is not None:
        _write_text_output(
            inconclusive_tsv_out,
            render_targeted_result_validation_tsv(
                report,
                TargetedValidationVerdict.INCONCLUSIVE,
            ),
        )
    if evidence_tsv_out is not None:
        _write_text_output(
            evidence_tsv_out,
            render_targeted_result_validation_evidence_tsv(report),
        )

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_name": report.source_name,
        "biomarker_candidate_count": len(discovery_claims),
        "panel_assay_count": len(panel_assays),
        "import_summary": import_report.summary.to_dict(),
        "design_summary": {
            "accepted_entry_count": len(design_report.accepted_entries),
            "rejected_row_count": len(design_report.rejected_rows),
        },
        "policy": report.policy.to_dict(),
        "summary": report.summary.to_dict(),
        "confirmed_targets": [
            entry.to_dict()
            for entry in report.entries
            if entry.verdict is TargetedValidationVerdict.CONFIRMED
        ],
        "contradicted_targets": [
            entry.to_dict()
            for entry in report.entries
            if entry.verdict is TargetedValidationVerdict.CONTRADICTED
        ],
        "inconclusive_targets": [
            entry.to_dict()
            for entry in report.entries
            if entry.verdict is TargetedValidationVerdict.INCONCLUSIVE
        ],
        "assay_evidence": [entry.to_dict() for entry in report.assay_evidence],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "confirmed_tsv": (
                None if confirmed_tsv_out is None else str(confirmed_tsv_out)
            ),
            "contradicted_tsv": (
                None if contradicted_tsv_out is None else str(contradicted_tsv_out)
            ),
            "inconclusive_tsv": (
                None if inconclusive_tsv_out is None else str(inconclusive_tsv_out)
            ),
            "evidence_tsv": (
                None if evidence_tsv_out is None else str(evidence_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_biomarker_stability_analysis_command(
    biomarker_candidate_tsv: Path,
    panel_assay_tsv: Path,
    targeted_result_tsv: Path,
    design_path: Path,
    source_kind: str,
    design_batch_field: str,
    design_timepoint_field: str,
    design_sample_type_field: str,
    minimum_reliable_samples_per_group: int,
    minimum_reliable_sample_fraction: float,
    subgroup_median_delta_threshold: float,
    batch_residual_delta_threshold: float,
    assay_disagreement_delta_threshold: float,
    downgrade_below_score: float,
    summary_tsv_out: Path | None,
    stability_tsv_out: Path | None,
    subgroup_tsv_out: Path | None,
    adjusted_candidate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if minimum_reliable_samples_per_group < 1:
        raise click.ClickException(
            "minimum-reliable-samples-per-group must be at least 1"
        )
    if not 0.0 <= minimum_reliable_sample_fraction <= 1.0:
        raise click.ClickException(
            "minimum-reliable-sample-fraction must be between 0.0 and 1.0"
        )
    if subgroup_median_delta_threshold < 0.0:
        raise click.ClickException(
            "subgroup-median-delta-threshold must be non-negative"
        )
    if batch_residual_delta_threshold < 0.0:
        raise click.ClickException(
            "batch-residual-delta-threshold must be non-negative"
        )
    if assay_disagreement_delta_threshold < 0.0:
        raise click.ClickException(
            "assay-disagreement-delta-threshold must be non-negative"
        )
    if not 0.0 <= downgrade_below_score <= 1.0:
        raise click.ClickException("downgrade-below-score must be between 0.0 and 1.0")

    biomarker_candidates = _load_targeted_validation_discovery_claims(
        biomarker_candidate_tsv
    )
    panel_assays = _load_targeted_validation_panel_assays(panel_assay_tsv)
    design_report = parse_experimental_design_table(design_path)
    source_kind_value = TargetedResultSourceKind(source_kind)
    if source_kind_value is TargetedResultSourceKind.SKYLINE_EXPORT:
        import_report = build_skyline_result_import_report(targeted_result_tsv)
    else:
        import_report = build_transition_table_result_import_report(targeted_result_tsv)

    try:
        report = build_biomarker_stability_report(
            biomarker_candidates=biomarker_candidates,
            panel_assays=panel_assays,
            import_report=import_report,
            design_entries=design_report.accepted_entries,
            policy=BiomarkerStabilityPolicy(
                batch_field=design_batch_field,
                timepoint_field=design_timepoint_field,
                sample_type_field=design_sample_type_field,
                minimum_reliable_samples_per_group=minimum_reliable_samples_per_group,
                minimum_reliable_sample_fraction=minimum_reliable_sample_fraction,
                subgroup_median_delta_threshold=subgroup_median_delta_threshold,
                batch_residual_delta_threshold=batch_residual_delta_threshold,
                assay_disagreement_delta_threshold=assay_disagreement_delta_threshold,
                downgrade_below_score=downgrade_below_score,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out, render_biomarker_stability_summary_tsv(report)
        )
    if stability_tsv_out is not None:
        _write_text_output(stability_tsv_out, render_biomarker_stability_tsv(report))
    if subgroup_tsv_out is not None:
        _write_text_output(
            subgroup_tsv_out, render_biomarker_stability_subgroup_tsv(report)
        )
    if adjusted_candidate_tsv_out is not None:
        _write_text_output(
            adjusted_candidate_tsv_out,
            render_biomarker_stability_candidate_tsv(report),
        )

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_name": report.source_name,
        "biomarker_candidate_count": len(biomarker_candidates),
        "panel_assay_count": len(panel_assays),
        "import_summary": import_report.summary.to_dict(),
        "design_summary": {
            "accepted_entry_count": len(design_report.accepted_entries),
            "rejected_row_count": len(design_report.rejected_rows),
        },
        "policy": report.policy.to_dict(),
        "summary": report.summary.to_dict(),
        "entries": [entry.to_dict() for entry in report.entries],
        "subgroup_behavior": [entry.to_dict() for entry in report.subgroup_behavior],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "stability_tsv": (
                None if stability_tsv_out is None else str(stability_tsv_out)
            ),
            "subgroup_tsv": (
                None if subgroup_tsv_out is None else str(subgroup_tsv_out)
            ),
            "adjusted_candidate_tsv": (
                None
                if adjusted_candidate_tsv_out is None
                else str(adjusted_candidate_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_biomarker_panel_redundancy_analysis_command(
    biomarker_candidate_tsv: Path,
    panel_assay_tsv: Path,
    targeted_result_tsv: Path,
    design_path: Path,
    source_kind: str,
    minimum_shared_samples: int,
    correlation_threshold: float,
    summary_tsv_out: Path | None,
    cluster_tsv_out: Path | None,
    reduced_candidate_tsv_out: Path | None,
    dropped_candidate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if minimum_shared_samples < 2:
        raise click.ClickException("minimum-shared-samples must be at least 2")
    if not 0.0 <= correlation_threshold <= 1.0:
        raise click.ClickException("correlation-threshold must be between 0.0 and 1.0")

    biomarker_candidates = _load_panel_redundancy_candidates(biomarker_candidate_tsv)
    panel_assays = _load_targeted_validation_panel_assays(panel_assay_tsv)
    design_report = parse_experimental_design_table(design_path)
    source_kind_value = TargetedResultSourceKind(source_kind)
    if source_kind_value is TargetedResultSourceKind.SKYLINE_EXPORT:
        import_report = build_skyline_result_import_report(targeted_result_tsv)
    else:
        import_report = build_transition_table_result_import_report(targeted_result_tsv)

    try:
        report = build_panel_redundancy_report(
            biomarker_candidates=biomarker_candidates,
            panel_assays=panel_assays,
            import_report=import_report,
            design_entries=design_report.accepted_entries,
            policy=PanelRedundancyPolicy(
                minimum_shared_samples=minimum_shared_samples,
                correlation_threshold=correlation_threshold,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_panel_redundancy_summary_tsv(report))
    if cluster_tsv_out is not None:
        _write_text_output(cluster_tsv_out, render_panel_redundancy_cluster_tsv(report))
    if reduced_candidate_tsv_out is not None:
        _write_text_output(
            reduced_candidate_tsv_out,
            render_panel_redundancy_candidate_tsv(report),
        )
    if dropped_candidate_tsv_out is not None:
        _write_text_output(
            dropped_candidate_tsv_out,
            render_panel_redundancy_dropped_tsv(report),
        )

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_name": report.source_name,
        "biomarker_candidate_count": len(biomarker_candidates),
        "panel_assay_count": len(panel_assays),
        "import_summary": import_report.summary.to_dict(),
        "design_summary": {
            "accepted_entry_count": len(design_report.accepted_entries),
            "rejected_row_count": len(design_report.rejected_rows),
        },
        "policy": report.policy.to_dict(),
        "summary": report.summary.to_dict(),
        "clusters": [entry.to_dict() for entry in report.clusters],
        "candidates": [entry.to_dict() for entry in report.candidates],
        "pairs": [entry.to_dict() for entry in report.pairs],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "cluster_tsv": None if cluster_tsv_out is None else str(cluster_tsv_out),
            "reduced_candidate_tsv": (
                None
                if reduced_candidate_tsv_out is None
                else str(reduced_candidate_tsv_out)
            ),
            "dropped_candidate_tsv": (
                None
                if dropped_candidate_tsv_out is None
                else str(dropped_candidate_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_validation_evidence_cards_command(
    biomarker_candidate_tsv: Path,
    panel_assay_tsv: Path,
    panel_omitted_tsv: Path | None,
    confirmed_tsv: Path | None,
    contradicted_tsv: Path | None,
    inconclusive_tsv: Path | None,
    validation_evidence_tsv: Path | None,
    stability_candidate_tsv: Path | None,
    redundancy_candidate_tsv: Path | None,
    summary_tsv_out: Path | None,
    card_tsv_out: Path | None,
    assay_tsv_out: Path | None,
    warning_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    discovery_candidates = _load_validation_evidence_discovery_candidates(
        biomarker_candidate_tsv
    )
    panel_assays = _load_validation_evidence_panel_assays(panel_assay_tsv)
    omitted_candidates = (
        ()
        if panel_omitted_tsv is None
        else _load_validation_evidence_omitted_candidates(panel_omitted_tsv)
    )
    targeted_validation_results = (
        *(
            ()
            if confirmed_tsv is None
            else _load_validation_evidence_results(confirmed_tsv)
        ),
        *(
            ()
            if contradicted_tsv is None
            else _load_validation_evidence_results(contradicted_tsv)
        ),
        *(
            ()
            if inconclusive_tsv is None
            else _load_validation_evidence_results(inconclusive_tsv)
        ),
    )
    validation_assay_evidence = (
        ()
        if validation_evidence_tsv is None
        else _load_validation_evidence_result_assays(validation_evidence_tsv)
    )
    stability_entries = (
        ()
        if stability_candidate_tsv is None
        else _load_validation_evidence_stability_entries(stability_candidate_tsv)
    )
    redundancy_entries = (
        ()
        if redundancy_candidate_tsv is None
        else _load_validation_evidence_redundancy_entries(redundancy_candidate_tsv)
    )

    result_ids = [entry.candidate_id for entry in targeted_validation_results]
    if len(result_ids) != len(set(result_ids)):
        raise click.ClickException(
            "validation result TSV inputs contain duplicate candidate_id rows"
        )

    report = build_validation_evidence_card_report(
        discovery_candidates,
        panel_assays=panel_assays,
        omitted_candidates=omitted_candidates,
        targeted_validation_results=tuple(targeted_validation_results),
        targeted_validation_assay_evidence=validation_assay_evidence,
        stability_entries=stability_entries,
        redundancy_entries=redundancy_entries,
    )

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_validation_evidence_card_summary_tsv(report),
        )
    if card_tsv_out is not None:
        _write_text_output(card_tsv_out, render_validation_evidence_card_tsv(report))
    if assay_tsv_out is not None:
        _write_text_output(
            assay_tsv_out,
            render_validation_evidence_card_assay_tsv(report),
        )
    if warning_tsv_out is not None:
        _write_text_output(
            warning_tsv_out,
            render_validation_evidence_card_warning_tsv(report),
        )

    payload = {
        "biomarker_candidate_count": len(discovery_candidates),
        "panel_assay_count": len(panel_assays),
        "omitted_candidate_count": len(omitted_candidates),
        "targeted_validation_result_count": len(targeted_validation_results),
        "targeted_validation_assay_evidence_count": len(validation_assay_evidence),
        "stability_entry_count": len(stability_entries),
        "redundancy_entry_count": len(redundancy_entries),
        "summary": report.summary.to_dict(),
        "cards": [entry.to_dict() for entry in report.cards],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "card_tsv": None if card_tsv_out is None else str(card_tsv_out),
            "assay_tsv": None if assay_tsv_out is None else str(assay_tsv_out),
            "warning_tsv": None if warning_tsv_out is None else str(warning_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_targeted_result_validator_command",
    "run_biomarker_stability_analysis_command",
    "run_biomarker_panel_redundancy_analysis_command",
    "run_validation_evidence_cards_command",
]
