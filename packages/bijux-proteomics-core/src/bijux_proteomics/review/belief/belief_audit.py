# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic belief audits over governed proteomics conclusion artifacts."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.review.belief.belief_audit_artifacts import (
    _biomarker_confidence,
    _biomarker_falsifier,
    _load_regulator_inferences,
    _load_unresolved_regulator_targets,
    _load_validation_evidence_cards,
    _load_validation_warnings,
    _regulator_confidence,
    _ValidationWarningArtifact,
)
from bijux_proteomics.review.belief.belief_audit_models import (
    BeliefAuditEntry,
    BeliefAuditReport,
    BeliefAuditSubjectKind,
    BeliefAuditSummary,
)
from bijux_proteomics.review.belief.belief_audit_rendering import (
    render_belief_audit_html,
    render_belief_audit_summary_tsv,
    render_belief_audit_tsv,
)
from bijux_proteomics.review.claims.result_query_artifacts import (
    _node_ids_for_entity,
    _sample_to_failed_qc_runs,
)
from bijux_proteomics.review.explanations.result_explanation_artifacts import (
    _load_result_explanation_artifact_context,
    _ResultExplanationArtifactContext,
)
from bijux_proteomics.review.explanations.result_explanations import (
    ResultExplanation,
    ResultExplanationKind,
    ResultExplanationRequest,
    ResultExplanationStatus,
    build_result_explanation_report_from_artifacts,
)


def build_belief_audit_report_from_artifacts(
    *,
    biological_report_dir: Path | None = None,
    ptm_report_dir: Path | None = None,
    validation_evidence_card_tsv: Path | None = None,
    validation_evidence_warning_tsv: Path | None = None,
    run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
) -> BeliefAuditReport:
    """Audit final scientific conclusions from governed biological, PTM, QC, and biomarker artifacts."""

    explanation_context = _load_result_explanation_artifact_context(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    explanation_entries = _build_explanation_entries(
        explanation_context=explanation_context,
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    regulator_entries = _build_regulator_entries(
        explanation_context=explanation_context,
        biological_report_dir=biological_report_dir,
    )
    biomarker_entries = _build_biomarker_entries(
        explanation_context=explanation_context,
        validation_evidence_card_tsv=validation_evidence_card_tsv,
        validation_evidence_warning_tsv=validation_evidence_warning_tsv,
    )
    entries = (*explanation_entries, *regulator_entries, *biomarker_entries)
    return BeliefAuditReport(
        entries=entries,
        summary=BeliefAuditSummary(
            entry_count=len(entries),
            protein_entry_count=sum(
                entry.subject_kind is BeliefAuditSubjectKind.PROTEIN
                for entry in entries
            ),
            ptm_site_entry_count=sum(
                entry.subject_kind is BeliefAuditSubjectKind.PTM_SITE
                for entry in entries
            ),
            pathway_entry_count=sum(
                entry.subject_kind is BeliefAuditSubjectKind.PATHWAY
                for entry in entries
            ),
            regulator_entry_count=sum(
                entry.subject_kind is BeliefAuditSubjectKind.REGULATOR
                for entry in entries
            ),
            biomarker_entry_count=sum(
                entry.subject_kind is BeliefAuditSubjectKind.BIOMARKER
                for entry in entries
            ),
            qc_decision_entry_count=sum(
                entry.subject_kind is BeliefAuditSubjectKind.QC_DECISION
                for entry in entries
            ),
        ),
        note=(
            "belief audits remain deterministic and preserve why each scientific "
            "conclusion was retained, what weakens it, and what evidence would "
            "falsify it directly from governed result artifacts"
        ),
    )


def _build_explanation_entries(
    *,
    explanation_context: _ResultExplanationArtifactContext,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
) -> tuple[BeliefAuditEntry, ...]:
    requests = list[ResultExplanationRequest]()
    if biological_report_dir is not None:
        for protein_card in explanation_context.base_context.protein_cards:
            requests.append(
                ResultExplanationRequest(
                    explanation_id=f"protein:{protein_card.card_id}",
                    explanation_kind=ResultExplanationKind.PROTEIN_RESULT,
                    subject_id=protein_card.card_id,
                )
            )
        for comparison in explanation_context.pathway_comparisons:
            requests.append(
                ResultExplanationRequest(
                    explanation_id=f"pathway:{comparison.comparison_row_id}",
                    explanation_kind=ResultExplanationKind.PATHWAY_RESULT,
                    subject_id=comparison.comparison_row_id,
                )
            )
    if biological_report_dir is not None and ptm_report_dir is not None:
        for ptm_card in explanation_context.base_context.ptm_cards:
            requests.append(
                ResultExplanationRequest(
                    explanation_id=f"ptm:{ptm_card.card_id}",
                    explanation_kind=ResultExplanationKind.PTM_SITE_RESULT,
                    subject_id=ptm_card.card_id,
                )
            )
    if biological_report_dir is not None and run_qc_assessment_tsv_paths:
        for sample_id in sorted(
            _sample_to_failed_qc_runs(explanation_context.base_context)
        ):
            requests.append(
                ResultExplanationRequest(
                    explanation_id=f"qc:{sample_id}",
                    explanation_kind=ResultExplanationKind.SAMPLE_QC_DECISION,
                    subject_id=sample_id,
                )
            )
    if not requests:
        return ()
    report = build_result_explanation_report_from_artifacts(
        tuple(requests),
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    return tuple(
        _belief_entry_from_explanation(explanation)
        for explanation in report.explanations
        if explanation.status is ResultExplanationStatus.ANSWERED
        and explanation.explanation_kind
        is not ResultExplanationKind.REJECTED_EVIDENCE_DECISION
    )


def _belief_entry_from_explanation(explanation: ResultExplanation) -> BeliefAuditEntry:
    subject_kind = _subject_kind_for_explanation(explanation.explanation_kind)
    points = (*explanation.evidence, *explanation.opposing_evidence)
    result_surfaces = tuple(dict.fromkeys(point.result_surface for point in points))
    why_believed = _join_summaries(
        tuple(point.summary for point in explanation.evidence),
        empty_text="no explicit supporting evidence rows were preserved on the governed artifacts",
    )
    what_weakens = _join_summaries(
        tuple(point.summary for point in explanation.opposing_evidence),
        empty_text="no explicit weakening evidence was preserved on the governed artifacts",
    )
    return BeliefAuditEntry(
        audit_id=explanation.explanation_id,
        subject_kind=subject_kind,
        subject_id=explanation.subject_id or explanation.explanation_id,
        subject_label=explanation.subject_label
        or explanation.subject_id
        or explanation.explanation_id,
        claim=explanation.claim,
        decision=explanation.decision,
        confidence=explanation.confidence,
        why_believed=why_believed,
        what_weakens=what_weakens,
        what_would_falsify=_falsifier_for_explanation(explanation),
        result_surfaces=result_surfaces,
        result_row_ids=explanation.result_row_ids,
        graph_node_ids=explanation.graph_node_ids,
        note=explanation.note,
    )


def _build_regulator_entries(
    *,
    explanation_context: _ResultExplanationArtifactContext,
    biological_report_dir: Path | None,
) -> tuple[BeliefAuditEntry, ...]:
    if biological_report_dir is None:
        return ()
    inference_path = biological_report_dir / "biological_regulator_inference.tsv"
    if not inference_path.exists():
        return ()
    unresolved_path = (
        biological_report_dir / "biological_regulator_inference_unresolved.tsv"
    )
    inferences = _load_regulator_inferences(inference_path)
    unresolved = (
        ()
        if not unresolved_path.exists()
        else _load_unresolved_regulator_targets(unresolved_path)
    )
    entries = []
    for inference in inferences:
        related_unresolved = tuple(
            entry
            for entry in unresolved
            if entry.regulator == inference.regulator
            and entry.evidence_type == inference.evidence_type
            and entry.source_accession == inference.source_accession
            and entry.source_name == inference.source_name
        )
        weakening_points = []
        if inference.coverage_fraction < 1.0:
            weakening_points.append(
                f"only {inference.matched_target_count} of {inference.target_count} "
                f"targets matched the current study surface "
                f"({inference.coverage_fraction:.0%} coverage)"
            )
        for entry in related_unresolved:
            weakening_points.append(
                f"unresolved target {entry.target_value} remained unresolved because {entry.reason}"
            )
        if inference.note:
            weakening_points.append(inference.note)
        graph_node_ids = tuple(
            dict.fromkeys(
                (
                    *(
                        node_id
                        for protein_ref in inference.supporting_protein_refs
                        for node_id in _node_ids_for_entity(
                            explanation_context.base_context.graph_node_index,
                            entity_type="protein",
                            entity_ref=protein_ref,
                        )
                    ),
                    *(
                        node_id
                        for pathway_id in inference.supporting_pathway_ids
                        for node_id in _node_ids_for_entity(
                            explanation_context.base_context.graph_node_index,
                            entity_type="pathway",
                            entity_ref=pathway_id,
                        )
                    ),
                )
            )
        )
        result_row_ids = (
            inference.row_id,
            *tuple(entry.row_id for entry in related_unresolved),
        )
        surfaces: tuple[str, ...] = ("biological_regulator_inference",)
        if related_unresolved:
            surfaces = (
                "biological_regulator_inference",
                "biological_regulator_inference_unresolved",
            )
        entries.append(
            BeliefAuditEntry(
                audit_id=f"regulator:{inference.row_id}",
                subject_kind=BeliefAuditSubjectKind.REGULATOR,
                subject_id=inference.row_id,
                subject_label=inference.regulator,
                claim=(
                    f"Regulator {inference.regulator} is inferred as "
                    f"{(inference.direction or 'directionally supported')} from "
                    f"{inference.signal_surface} evidence."
                ),
                decision=(
                    f"retained as a regulator conclusion from {inference.evidence_type} "
                    f"evidence"
                ),
                confidence=_regulator_confidence(inference),
                why_believed=_join_parts(
                    (
                        (
                            f"{inference.matched_target_count} of {inference.target_count} "
                            f"targets matched the study surface "
                            f"({inference.coverage_fraction:.0%} coverage)"
                        ),
                        _optional_metric_text(
                            "regulator score",
                            inference.score,
                        ),
                        _optional_metric_text(
                            "mean log2 fold change",
                            inference.mean_log2_fold_change,
                        ),
                        _optional_metric_text(
                            "mean pathway activity delta",
                            inference.mean_activity_score_delta,
                        ),
                        _optional_collection_text(
                            "supporting proteins",
                            inference.supporting_protein_refs,
                        ),
                        _optional_collection_text(
                            "supporting PTM sites",
                            inference.supporting_site_keys,
                        ),
                        _optional_collection_text(
                            "supporting pathways",
                            inference.supporting_pathway_ids,
                        ),
                    )
                ),
                what_weakens=_join_parts(weakening_points)
                or "no explicit weakening evidence was preserved for this regulator inference",
                what_would_falsify=(
                    "A rerun that removes the matched targets, reverses the retained "
                    "directional support, or collapses the preserved target coverage "
                    "would falsify this regulator conclusion."
                ),
                result_surfaces=surfaces,
                result_row_ids=result_row_ids,
                graph_node_ids=graph_node_ids,
                note="regulator belief audit derived from retained regulator inference rows and unresolved target ledgers",
            )
        )
    return tuple(entries)


def _build_biomarker_entries(
    *,
    explanation_context: _ResultExplanationArtifactContext,
    validation_evidence_card_tsv: Path | None,
    validation_evidence_warning_tsv: Path | None,
) -> tuple[BeliefAuditEntry, ...]:
    if validation_evidence_card_tsv is None:
        return ()
    cards = _load_validation_evidence_cards(validation_evidence_card_tsv)
    warnings = (
        ()
        if validation_evidence_warning_tsv is None
        or not validation_evidence_warning_tsv.exists()
        else _load_validation_warnings(validation_evidence_warning_tsv)
    )
    warnings_by_candidate: dict[str, tuple[_ValidationWarningArtifact, ...]] = {}
    for warning in warnings:
        warnings_by_candidate.setdefault(warning.candidate_id, ())
        warnings_by_candidate[warning.candidate_id] = (
            *warnings_by_candidate[warning.candidate_id],
            warning,
        )
    entries = []
    for card in cards:
        candidate_warnings = warnings_by_candidate.get(card.candidate_id, ())
        weakening_points = list[str]()
        if card.omitted_reason is not None:
            weakening_points.append(
                f"candidate omission reason was preserved as {card.omitted_reason}"
            )
        if card.contradicted_assay_count > 0:
            weakening_points.append(
                f"{card.contradicted_assay_count} targeted assays contradicted the candidate"
            )
        if card.inconclusive_assay_count > 0:
            weakening_points.append(
                f"{card.inconclusive_assay_count} targeted assays remained inconclusive"
            )
        for reason_code in card.targeted_validation_reason_codes:
            weakening_points.append(
                f"targeted validation reason code {reason_code} remained attached to the candidate"
            )
        for warning_code in card.warning_codes:
            weakening_points.append(
                f"validation warning code {warning_code} weakened the final candidate status"
            )
        for warning in candidate_warnings:
            weakening_points.append(
                f"warning {warning.warning_code} remained on the candidate because {warning.note}"
            )
        if card.stability_downgraded:
            weakening_points.append(
                "stability review downgraded the candidate"
                + (
                    ""
                    if not card.stability_reason_codes
                    else f" ({', '.join(card.stability_reason_codes)})"
                )
            )
        if card.redundancy_dropped:
            weakening_points.append(
                "redundancy review dropped the candidate"
                + (
                    ""
                    if not card.redundancy_reason_codes
                    else f" ({', '.join(card.redundancy_reason_codes)})"
                )
            )
        graph_node_ids = tuple(
            dict.fromkeys(
                (
                    *(
                        ()
                        if card.target_protein_ref is None
                        else _node_ids_for_entity(
                            explanation_context.base_context.graph_node_index,
                            entity_type="protein",
                            entity_ref=card.target_protein_ref,
                        )
                    ),
                )
            )
        )
        result_row_ids = (
            card.candidate_id,
            *tuple(warning.warning_id for warning in candidate_warnings),
        )
        result_surfaces: tuple[str, ...] = ("validation_evidence_cards",)
        if candidate_warnings:
            result_surfaces = (
                "validation_evidence_cards",
                "validation_evidence_card_warnings",
            )
        entries.append(
            BeliefAuditEntry(
                audit_id=f"biomarker:{card.candidate_id}",
                subject_kind=BeliefAuditSubjectKind.BIOMARKER,
                subject_id=card.candidate_id,
                subject_label=card.display_label,
                claim=(
                    f"Biomarker candidate {card.display_label} ended with final status "
                    f"{card.final_status}."
                ),
                decision=(
                    f"targeted validation verdict is {card.targeted_validation_verdict}"
                ),
                confidence=_biomarker_confidence(card, candidate_warnings),
                why_believed=_join_parts(
                    (
                        _optional_metric_text(
                            "discovery final score",
                            card.discovery_final_score,
                        ),
                        _optional_metric_text(
                            "discovery adjusted p-value",
                            card.discovery_adjusted_p_value,
                        ),
                        (
                            f"discovery support count is {card.discovery_support_count}"
                            if card.discovery_support_count > 0
                            else None
                        ),
                        (
                            f"targeted validation retained {card.confirmed_assay_count} "
                            f"confirming assays from {card.assay_entry_count} assay entries"
                        ),
                        _optional_metric_text(
                            "targeted validation log2 effect",
                            card.targeted_validation_log2_effect,
                        ),
                        _optional_collection_text(
                            "biological role labels",
                            card.biological_role_labels,
                        ),
                        _optional_collection_text(
                            "biological source ids",
                            card.biological_source_ids,
                        ),
                        card.note,
                    )
                ),
                what_weakens=_join_parts(weakening_points)
                or "no explicit weakening evidence was preserved for this biomarker conclusion",
                what_would_falsify=_biomarker_falsifier(card),
                result_surfaces=result_surfaces,
                result_row_ids=result_row_ids,
                graph_node_ids=graph_node_ids,
                note="biomarker belief audit derived from retained validation evidence cards and warning ledgers",
            )
        )
    return tuple(entries)


def _subject_kind_for_explanation(
    explanation_kind: ResultExplanationKind,
) -> BeliefAuditSubjectKind:
    if explanation_kind is ResultExplanationKind.PROTEIN_RESULT:
        return BeliefAuditSubjectKind.PROTEIN
    if explanation_kind is ResultExplanationKind.PTM_SITE_RESULT:
        return BeliefAuditSubjectKind.PTM_SITE
    if explanation_kind is ResultExplanationKind.PATHWAY_RESULT:
        return BeliefAuditSubjectKind.PATHWAY
    if explanation_kind is ResultExplanationKind.SAMPLE_QC_DECISION:
        return BeliefAuditSubjectKind.QC_DECISION
    raise ValueError(
        f"unsupported explanation kind for belief audit: {explanation_kind.value}"
    )


def _falsifier_for_explanation(explanation: ResultExplanation) -> str:
    if explanation.explanation_kind is ResultExplanationKind.PROTEIN_RESULT:
        return (
            "A rerun that removes statistical support, reverses the retained direction, "
            "or shows the cited peptide support was not protein-specific would falsify "
            "this protein conclusion."
        )
    if explanation.explanation_kind is ResultExplanationKind.PTM_SITE_RESULT:
        return (
            "A rerun that drops localization confidence, removes the site effect after "
            "protein correction, or produces contradictory site-level validation would "
            "falsify this PTM-site conclusion."
        )
    if explanation.explanation_kind is ResultExplanationKind.PATHWAY_RESULT:
        return (
            "A rerun that removes the retained pathway activity delta, fails the pathway "
            "confidence check, or loses the key contributing members would falsify this "
            "pathway conclusion."
        )
    if explanation.explanation_kind is ResultExplanationKind.SAMPLE_QC_DECISION:
        return (
            "A regenerated QC ledger that clears the cited failing run assessments or "
            "shows those runs do not belong to this sample would falsify this QC decision."
        )
    raise ValueError(
        f"unsupported explanation kind for falsifier: {explanation.explanation_kind.value}"
    )


def _optional_metric_text(label: str, value: float | None) -> str | None:
    if value is None:
        return None
    return f"{label} is {_format_float(value)}"


def _optional_collection_text(label: str, values: tuple[str, ...]) -> str | None:
    if not values:
        return None
    return f"{label}: {', '.join(values)}"


def _join_parts(parts: tuple[str | None, ...] | list[str]) -> str:
    retained = [part for part in parts if part]
    return "; ".join(retained)


def _join_summaries(
    summaries: tuple[str, ...],
    *,
    empty_text: str,
) -> str:
    retained = tuple(summary for summary in summaries if summary)
    if not retained:
        return empty_text
    return "; ".join(retained)


def _format_float(value: float) -> str:
    return f"{value:.4g}"


__all__ = (
    "BeliefAuditEntry",
    "BeliefAuditReport",
    "BeliefAuditSubjectKind",
    "BeliefAuditSummary",
    "build_belief_audit_report_from_artifacts",
    "render_belief_audit_html",
    "render_belief_audit_summary_tsv",
    "render_belief_audit_tsv",
)
