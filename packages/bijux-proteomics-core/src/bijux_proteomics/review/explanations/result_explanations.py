# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic structured explanations over exported proteomics result artifacts."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain.confidence import ConfidenceTier, coerce_confidence_tier
from bijux_proteomics.review.explanations.result_explanation_artifacts import (
    _find_failed_qc_run,
    _find_pathway_comparison,
    _find_rejected_claim,
    _load_result_explanation_artifact_context,
    _pathway_unresolved_members,
    _rejected_claim_graph_node_ids,
    _rejected_claim_signal_summary,
    _ResultExplanationArtifactContext,
    _top_pathway_members,
    _PathwayComparisonArtifact,
    _RejectedClaimArtifact,
)
from bijux_proteomics.review.explanations.result_explanation_models import (
    ResultExplanation,
    ResultExplanationEvidenceRole,
    ResultExplanationKind,
    ResultExplanationPoint,
    ResultExplanationReport,
    ResultExplanationRequest,
    ResultExplanationStatus,
    ResultExplanationSummary,
)
from bijux_proteomics.review.explanations.result_explanation_rendering import (
    render_result_explanation_evidence_tsv,
    render_result_explanation_summary_tsv,
    render_result_explanation_tsv,
)
from bijux_proteomics.review.claims.result_queries import (
    _find_protein_card,
    _find_ptm_card,
    _node_ids_for_entity,
    _protein_card_graph_node_ids,
    _sample_to_failed_qc_runs,
)
from bijux_proteomics_foundation import JsonModel


def build_result_explanation_report_from_artifacts(
    requests: tuple[ResultExplanationRequest, ...],
    *,
    biological_report_dir: Path | None = None,
    ptm_report_dir: Path | None = None,
    run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
) -> ResultExplanationReport:
    """Explain governed protein, PTM, pathway, QC, and rejected-evidence decisions."""

    context = _load_result_explanation_artifact_context(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    explanations = tuple(
        _build_result_explanation(request, context=context) for request in requests
    )
    return ResultExplanationReport(
        explanations=explanations,
        summary=ResultExplanationSummary(
            explanation_count=len(explanations),
            answered_explanation_count=sum(
                entry.status is ResultExplanationStatus.ANSWERED
                for entry in explanations
            ),
            not_found_explanation_count=sum(
                entry.status is ResultExplanationStatus.NOT_FOUND
                for entry in explanations
            ),
            unsupported_explanation_count=sum(
                entry.status is ResultExplanationStatus.UNSUPPORTED
                for entry in explanations
            ),
        ),
        note=(
            "result explanations remain deterministic and preserve explicit claim, "
            "supporting evidence, opposing evidence, decision, and confidence from "
            "governed result artifacts"
        ),
    )


def _build_result_explanation(
    request: ResultExplanationRequest,
    *,
    context: _ResultExplanationArtifactContext,
) -> ResultExplanation:
    if request.explanation_kind is ResultExplanationKind.PROTEIN_RESULT:
        return _explain_protein_result(request, context=context)
    if request.explanation_kind is ResultExplanationKind.PTM_SITE_RESULT:
        return _explain_ptm_site_result(request, context=context)
    if request.explanation_kind is ResultExplanationKind.PATHWAY_RESULT:
        return _explain_pathway_result(request, context=context)
    if request.explanation_kind is ResultExplanationKind.SAMPLE_QC_DECISION:
        return _explain_sample_qc_decision(request, context=context)
    if request.explanation_kind is ResultExplanationKind.REJECTED_EVIDENCE_DECISION:
        return _explain_rejected_evidence_decision(request, context=context)
    raise ValueError(
        f"unsupported result explanation kind: {request.explanation_kind.value}"
    )


def _explain_protein_result(
    request: ResultExplanationRequest,
    *,
    context: _ResultExplanationArtifactContext,
) -> ResultExplanation:
    if not context.biological_report_available:
        return _unsupported_explanation(
            request,
            "protein explanations require an exported biological report directory",
        )
    card = _find_protein_card(
        context.base_context.protein_card_index,
        request.subject_id,
    )
    if card is None:
        return _not_found_explanation(
            request,
            "no governed protein evidence card matched the requested subject",
        )
    graph_node_ids = _protein_card_graph_node_ids(card)
    evidence = (
        _make_point(
            request.explanation_id,
            ResultExplanationEvidenceRole.SUPPORTING,
            "biological_protein_cards",
            card.card_id,
            graph_node_ids,
            card.graph_source_row_refs,
            (
                f"log2 fold change is {card.log2_fold_change:.4g}, adjusted p-value is "
                + (
                    "not available"
                    if card.adjusted_p_value is None
                    else f"{card.adjusted_p_value:.4g}"
                )
            ),
        ),
        _make_point(
            request.explanation_id,
            ResultExplanationEvidenceRole.SUPPORTING,
            "biological_protein_cards",
            card.card_id,
            graph_node_ids,
            card.graph_source_row_refs,
            (
                f"protein support comes from {card.peptide_count} peptides with "
                f"{card.unique_peptide_count} unique and {card.shared_peptide_count} shared"
            ),
        ),
    )
    opposing = list[ResultExplanationPoint]()
    for warning_code in card.warning_codes:
        opposing.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.OPPOSING,
                "biological_protein_cards",
                card.card_id,
                graph_node_ids,
                card.graph_source_row_refs,
                f"warning code {warning_code} reduced protein-card confidence",
            )
        )
    if not card.significant:
        opposing.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.OPPOSING,
                "biological_protein_cards",
                card.card_id,
                graph_node_ids,
                card.graph_source_row_refs,
                "final protein card preserved a non-significant decision on this subject",
            )
        )
    claim = (
        f"Protein {card.representative_protein_ref} changed between "
        f"{card.condition_a} and {card.condition_b}."
        if card.significant
        else (
            f"Protein {card.representative_protein_ref} was not retained as a changed "
            f"protein between {card.condition_a} and {card.condition_b}."
        )
    )
    decision = (
        "retained as a significant protein result"
        if card.significant
        else "not retained as a significant protein result"
    )
    return _answered_explanation(
        request,
        subject_label=card.representative_protein_ref,
        claim=claim,
        evidence=evidence,
        opposing_evidence=tuple(opposing),
        decision=decision,
        confidence=_protein_confidence(
            card.significant, card.evidence_tier, card.warning_codes
        ),
        result_row_ids=(card.card_id, *card.graph_source_row_refs),
        graph_node_ids=graph_node_ids,
        note="protein explanation derived from the exported protein evidence card",
    )


def _explain_ptm_site_result(
    request: ResultExplanationRequest,
    *,
    context: _ResultExplanationArtifactContext,
) -> ResultExplanation:
    if not context.ptm_report_available:
        return _unsupported_explanation(
            request,
            "PTM explanations require an exported PTM report directory",
        )
    card = _find_ptm_card(context.base_context.ptm_card_index, request.subject_id)
    if card is None:
        return _not_found_explanation(
            request,
            "no governed PTM evidence card matched the requested subject",
        )
    protein_card = _find_protein_card(
        context.base_context.protein_card_index,
        card.protein_ref,
    )
    graph_node_ids = (
        () if protein_card is None else _protein_card_graph_node_ids(protein_card)
    )
    evidence = [
        _make_point(
            request.explanation_id,
            ResultExplanationEvidenceRole.SUPPORTING,
            "ptm_evidence_cards",
            card.card_id,
            graph_node_ids,
            card.claim_ids,
            (
                f"log2 fold change is {card.log2_fold_change:.4g}, adjusted p-value is "
                + (
                    "not available"
                    if card.adjusted_p_value is None
                    else f"{card.adjusted_p_value:.4g}"
                )
            ),
        ),
        _make_point(
            request.explanation_id,
            ResultExplanationEvidenceRole.SUPPORTING,
            "ptm_evidence_cards",
            card.card_id,
            graph_node_ids,
            card.claim_ids,
            (
                f"localization tier is {card.localization_tier} with "
                f"{card.observed_sample_count} observed samples"
            ),
        ),
    ]
    opposing = list[ResultExplanationPoint]()
    if card.corrected_log2_fold_change is not None:
        opposing.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.OPPOSING,
                "ptm_evidence_cards",
                card.card_id,
                graph_node_ids,
                card.claim_ids,
                (
                    "protein correction preserved a corrected log2 fold change of "
                    f"{card.corrected_log2_fold_change:.4g}"
                ),
            )
        )
    if card.protein_correction_status != "not_requested":
        opposing.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.OPPOSING,
                "ptm_evidence_cards",
                card.card_id,
                graph_node_ids,
                card.claim_ids,
                f"protein correction status is {card.protein_correction_status}",
            )
        )
    for warning_code in card.warning_codes:
        opposing.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.OPPOSING,
                "ptm_evidence_cards",
                card.card_id,
                graph_node_ids,
                card.claim_ids,
                f"warning code {warning_code} reduced PTM-site confidence",
            )
        )
    claim = (
        f"PTM site {card.site_key} changed between {card.condition_a} and "
        f"{card.condition_b}."
    )
    decision = (
        "site was downgraded on the PTM evidence card"
        if opposing
        else "site retained a direct PTM evidence-card decision without downgrade"
    )
    return _answered_explanation(
        request,
        subject_label=card.site_key,
        claim=claim,
        evidence=tuple(evidence),
        opposing_evidence=tuple(opposing),
        decision=decision,
        confidence=_ptm_confidence(
            card.localization_tier,
            card.protein_correction_status,
            card.warning_codes,
        ),
        result_row_ids=(card.card_id, *card.claim_ids),
        graph_node_ids=graph_node_ids,
        note="PTM explanation derived from the exported PTM evidence card surface",
    )


def _explain_pathway_result(
    request: ResultExplanationRequest,
    *,
    context: _ResultExplanationArtifactContext,
) -> ResultExplanation:
    if not context.pathway_activity_available:
        return _unsupported_explanation(
            request,
            "pathway explanations require exported pathway activity comparison artifacts",
        )
    comparison = _find_pathway_comparison(
        context.pathway_comparisons,
        request.subject_id,
    )
    if comparison is None:
        return _not_found_explanation(
            request,
            "no governed pathway activity comparison matched the requested subject",
        )
    graph_node_ids = _node_ids_for_entity(
        context.base_context.graph_node_index,
        entity_type="pathway",
        entity_ref=comparison.pathway_id,
    )
    evidence = [
        _make_point(
            request.explanation_id,
            ResultExplanationEvidenceRole.SUPPORTING,
            "biological_pathway_activity_condition_comparisons",
            comparison.comparison_row_id,
            graph_node_ids,
            (),
            (
                f"activity delta is {_format_float(comparison.activity_score_delta)} with "
                f"comparison confidence {comparison.comparison_confidence_status}"
            ),
        )
    ]
    top_members = _top_pathway_members(
        context.pathway_member_contributions,
        comparison.pathway_id,
    )
    if top_members:
        evidence.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.SUPPORTING,
                "biological_pathway_activity_members",
                comparison.comparison_row_id,
                graph_node_ids,
                (),
                "top observed contributing members are " + ", ".join(top_members),
            )
        )
    opposing = list[ResultExplanationPoint]()
    if (
        coerce_confidence_tier(comparison.comparison_confidence_status)
        is not ConfidenceTier.HIGH
    ):
        opposing.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.OPPOSING,
                "biological_pathway_activity_condition_comparisons",
                comparison.comparison_row_id,
                graph_node_ids,
                (),
                (
                    "comparison confidence stayed at "
                    f"{comparison.comparison_confidence_status}"
                ),
            )
        )
    for unresolved in _pathway_unresolved_members(
        context.pathway_unresolved_members,
        comparison.pathway_id,
    ):
        opposing.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.OPPOSING,
                "biological_pathway_activity_unresolved",
                comparison.comparison_row_id,
                graph_node_ids,
                (),
                f"unresolved member {unresolved.member_id}: {unresolved.reason}",
            )
        )
    pathway_label = comparison.pathway_name or comparison.pathway_id
    direction = _pathway_direction(comparison.activity_score_delta)
    claim = (
        f"Pathway {pathway_label} shows {direction} activity in "
        f"{comparison.condition_b} relative to {comparison.condition_a}."
    )
    decision = (
        "retained as a directional pathway activity result"
        if comparison.activity_score_delta is not None
        else "not retained as a directional pathway activity result"
    )
    return _answered_explanation(
        request,
        subject_label=pathway_label,
        claim=claim,
        evidence=tuple(evidence),
        opposing_evidence=tuple(opposing),
        decision=decision,
        confidence=_normalize_confidence(comparison.comparison_confidence_status),
        result_row_ids=(comparison.comparison_row_id,),
        graph_node_ids=graph_node_ids,
        note="pathway explanation derived from exported pathway activity comparison artifacts",
    )


def _explain_sample_qc_decision(
    request: ResultExplanationRequest,
    *,
    context: _ResultExplanationArtifactContext,
) -> ResultExplanation:
    if not context.qc_available:
        return _unsupported_explanation(
            request,
            "sample QC explanations require at least one run QC assessment TSV",
        )
    sample_to_runs = _sample_to_failed_qc_runs(context.base_context)
    failed_runs = sample_to_runs.get(request.subject_id or "", ())
    if failed_runs:
        sample_subject_id = request.subject_id or failed_runs[0].run_id
        sample_node_ids = _node_ids_for_entity(
            context.base_context.graph_node_index,
            entity_type="sample",
            entity_ref=sample_subject_id,
        )
        graph_node_ids = tuple(
            dict.fromkeys(
                (
                    *sample_node_ids,
                    *(
                        node_id
                        for run in failed_runs
                        for node_id in _node_ids_for_entity(
                            context.base_context.graph_node_index,
                            entity_type="run",
                            entity_ref=run.run_id,
                        )
                    ),
                )
            )
        )
        evidence = tuple(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.SUPPORTING,
                "run_qc_assessment",
                run.run_id,
                graph_node_ids,
                (),
                (
                    f"failed run {run.run_id} carries reason codes "
                    f"{', '.join(run.status_reason_codes) or 'none'} and messages "
                    f"{'; '.join(run.messages) or 'none'}"
                ),
            )
            for run in failed_runs
        )
        return _answered_explanation(
            request,
            subject_label=sample_subject_id,
            claim=f"Sample {sample_subject_id} failed QC.",
            evidence=evidence,
            opposing_evidence=(),
            decision="sample failed run-level QC and should stay blocked or reviewed",
            confidence="high",
            result_row_ids=tuple(run.run_id for run in failed_runs),
            graph_node_ids=graph_node_ids,
            note="sample QC explanation derived from failed run assessments mapped through exported graph contexts",
        )
    run = _find_failed_qc_run(context.base_context, request.subject_id)
    if run is None:
        return _not_found_explanation(
            request,
            "no failed sample or run QC decision matched the requested subject",
        )
    run_node_ids = _node_ids_for_entity(
        context.base_context.graph_node_index,
        entity_type="run",
        entity_ref=run.run_id,
    )
    return _answered_explanation(
        request,
        subject_label=run.run_id,
        claim=f"Run {run.run_id} failed QC.",
        evidence=(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.SUPPORTING,
                "run_qc_assessment",
                run.run_id,
                run_node_ids,
                (),
                (
                    f"failed run carries reason codes {', '.join(run.status_reason_codes) or 'none'} "
                    f"and messages {'; '.join(run.messages) or 'none'}"
                ),
            ),
        ),
        opposing_evidence=(),
        decision="run failed QC and should remain excluded or reviewed",
        confidence="high",
        result_row_ids=(run.run_id,),
        graph_node_ids=run_node_ids,
        note="run QC explanation derived directly from failed run assessment rows",
    )


def _explain_rejected_evidence_decision(
    request: ResultExplanationRequest,
    *,
    context: _ResultExplanationArtifactContext,
) -> ResultExplanation:
    if not context.rejected_claims_available:
        return _unsupported_explanation(
            request,
            "rejected evidence explanations require exported rejected-claim artifacts",
        )
    claim = _find_rejected_claim(context.rejected_claim_index, request.subject_id)
    if claim is None:
        return _not_found_explanation(
            request,
            "no rejected evidence decision matched the requested claim subject",
        )
    graph_node_ids = _rejected_claim_graph_node_ids(claim, context.base_context)
    evidence = list[ResultExplanationPoint]()
    if claim.source_ids:
        evidence.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.SUPPORTING,
                "biological_rejected_claims",
                claim.claim_id,
                graph_node_ids,
                claim.source_ids,
                "candidate was supported by source ids " + ", ".join(claim.source_ids),
            )
        )
    if (
        claim.effect_size is not None
        or claim.pathway_delta is not None
        or claim.regulator_score is not None
    ):
        evidence.append(
            _make_point(
                request.explanation_id,
                ResultExplanationEvidenceRole.SUPPORTING,
                "biological_rejected_claims",
                claim.claim_id,
                graph_node_ids,
                claim.source_ids,
                _rejected_claim_signal_summary(claim),
            )
        )
    opposing = tuple(
        _make_point(
            request.explanation_id,
            ResultExplanationEvidenceRole.OPPOSING,
            "biological_rejected_claims",
            claim.claim_id,
            graph_node_ids,
            claim.source_ids,
            f"rejection code {reason_code} blocked narrative promotion",
        )
        for reason_code in claim.reason_codes
    )
    return _answered_explanation(
        request,
        subject_label=claim.subject_label,
        claim=claim.claim_text,
        evidence=tuple(evidence),
        opposing_evidence=opposing,
        decision=claim.validation_note,
        confidence=_rejected_claim_confidence(claim),
        result_row_ids=(claim.claim_id, *claim.source_ids),
        graph_node_ids=graph_node_ids,
        note="rejected-evidence explanation derived from exported rejected biological claim artifacts",
    )


def _unsupported_explanation(
    request: ResultExplanationRequest,
    note: str,
) -> ResultExplanation:
    return ResultExplanation(
        explanation_id=request.explanation_id,
        explanation_kind=request.explanation_kind,
        status=ResultExplanationStatus.UNSUPPORTED,
        subject_id=request.subject_id,
        subject_label=request.subject_id,
        claim=note,
        evidence=(),
        opposing_evidence=(),
        decision=note,
        confidence="low",
        result_row_ids=(),
        graph_node_ids=(),
        note=note,
    )


def _not_found_explanation(
    request: ResultExplanationRequest,
    note: str,
) -> ResultExplanation:
    return ResultExplanation(
        explanation_id=request.explanation_id,
        explanation_kind=request.explanation_kind,
        status=ResultExplanationStatus.NOT_FOUND,
        subject_id=request.subject_id,
        subject_label=request.subject_id,
        claim=note,
        evidence=(),
        opposing_evidence=(),
        decision=note,
        confidence="low",
        result_row_ids=(),
        graph_node_ids=(),
        note=note,
    )


def _answered_explanation(
    request: ResultExplanationRequest,
    *,
    subject_label: str,
    claim: str,
    evidence: tuple[ResultExplanationPoint, ...],
    opposing_evidence: tuple[ResultExplanationPoint, ...],
    decision: str,
    confidence: str,
    result_row_ids: tuple[str, ...],
    graph_node_ids: tuple[str, ...],
    note: str,
) -> ResultExplanation:
    return ResultExplanation(
        explanation_id=request.explanation_id,
        explanation_kind=request.explanation_kind,
        status=ResultExplanationStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=subject_label,
        claim=claim,
        evidence=evidence,
        opposing_evidence=opposing_evidence,
        decision=decision,
        confidence=confidence,
        result_row_ids=result_row_ids,
        graph_node_ids=graph_node_ids,
        note=note,
    )


def _make_point(
    explanation_id: str,
    role: ResultExplanationEvidenceRole,
    result_surface: str,
    row_id: str,
    graph_node_ids: tuple[str, ...],
    source_row_refs: tuple[str, ...],
    summary: str,
) -> ResultExplanationPoint:
    return ResultExplanationPoint(
        explanation_id=explanation_id,
        role=role,
        result_surface=result_surface,
        row_id=row_id,
        graph_node_ids=graph_node_ids,
        source_row_refs=source_row_refs,
        summary=summary,
    )


def _protein_confidence(
    significant: bool,
    evidence_tier: str,
    warning_codes: tuple[str, ...],
) -> str:
    if not significant:
        return "low"
    normalized = _normalize_confidence(evidence_tier)
    if warning_codes and normalized == "high":
        return "moderate"
    return normalized


def _ptm_confidence(
    localization_tier: str,
    protein_correction_status: str,
    warning_codes: tuple[str, ...],
) -> str:
    normalized = _normalize_confidence(localization_tier)
    if protein_correction_status != "not_requested" or warning_codes:
        if normalized == "high":
            return "moderate"
        return "low"
    return normalized


def _rejected_claim_confidence(claim: _RejectedClaimArtifact) -> str:
    if claim.confidence_tier is not None:
        return _normalize_confidence(claim.confidence_tier)
    if claim.pathway_confidence_status is not None:
        return _normalize_confidence(claim.pathway_confidence_status)
    if claim.evidence_tier is not None:
        return _normalize_confidence(claim.evidence_tier)
    return "low"


def _normalize_confidence(value: str | None) -> str:
    if value is None:
        return "low"
    normalized = value.strip().lower()
    if "high" in normalized:
        return "high"
    if "moderate" in normalized or "medium" in normalized:
        return "moderate"
    return "low"


def _pathway_direction(activity_score_delta: float | None) -> str:
    if activity_score_delta is None:
        return "no directional"
    if activity_score_delta > 0:
        return "higher"
    if activity_score_delta < 0:
        return "lower"
    return "unchanged"


def _format_float(value: float | None) -> str:
    return "not available" if value is None else f"{value:.4g}"


__all__ = [
    "ResultExplanation",
    "ResultExplanationEvidenceRole",
    "ResultExplanationKind",
    "ResultExplanationPoint",
    "ResultExplanationReport",
    "ResultExplanationRequest",
    "ResultExplanationStatus",
    "ResultExplanationSummary",
    "build_result_explanation_report_from_artifacts",
    "render_result_explanation_evidence_tsv",
    "render_result_explanation_summary_tsv",
    "render_result_explanation_tsv",
]
