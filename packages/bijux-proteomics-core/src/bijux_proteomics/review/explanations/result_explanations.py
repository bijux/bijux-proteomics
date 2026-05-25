# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic structured explanations over exported proteomics result artifacts."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.review.claims.result_queries import (
    _ResultArtifactContext,
    _empty_to_none,
    _find_protein_card,
    _find_ptm_card,
    _load_result_artifact_context,
    _node_ids_for_entity,
    _parse_bool,
    _parse_optional_float,
    _protein_card_graph_node_ids,
    _read_tsv_rows,
    _sample_to_failed_qc_runs,
    _split_multi,
)
from bijux_proteomics_foundation import JsonModel


class ResultExplanationKind(StrEnum):
    """Stable explanation families over governed result artifacts."""

    PROTEIN_RESULT = "protein_result"
    PTM_SITE_RESULT = "ptm_site_result"
    PATHWAY_RESULT = "pathway_result"
    SAMPLE_QC_DECISION = "sample_qc_decision"
    REJECTED_EVIDENCE_DECISION = "rejected_evidence_decision"


class ResultExplanationStatus(StrEnum):
    """Stable answer states for one deterministic explanation request."""

    ANSWERED = "answered"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"


class ResultExplanationEvidenceRole(StrEnum):
    """Whether one structured explanation point supports or opposes the decision."""

    SUPPORTING = "supporting"
    OPPOSING = "opposing"


class ResultExplanationRequest(JsonModel):
    """One deterministic result-explanation request."""

    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(..., min_length=1)
    explanation_kind: ResultExplanationKind
    subject_id: str | None = None


class ResultExplanationPoint(JsonModel):
    """One structured evidence point inside a deterministic explanation."""

    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(..., min_length=1)
    role: ResultExplanationEvidenceRole
    result_surface: str = Field(..., min_length=1)
    row_id: str = Field(..., min_length=1)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    summary: str = Field(..., min_length=1)


class ResultExplanation(JsonModel):
    """One deterministic structured explanation over exported result artifacts."""

    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(..., min_length=1)
    explanation_kind: ResultExplanationKind
    status: ResultExplanationStatus
    subject_id: str | None = None
    subject_label: str | None = None
    claim: str = Field(..., min_length=1)
    evidence: tuple[ResultExplanationPoint, ...] = Field(default_factory=tuple)
    opposing_evidence: tuple[ResultExplanationPoint, ...] = Field(default_factory=tuple)
    decision: str = Field(..., min_length=1)
    confidence: str = Field(..., min_length=1)
    result_row_ids: tuple[str, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ResultExplanationSummary(JsonModel):
    """Summary over one deterministic explanation pass."""

    model_config = ConfigDict(extra="forbid")

    explanation_count: int = Field(..., ge=0)
    answered_explanation_count: int = Field(..., ge=0)
    not_found_explanation_count: int = Field(..., ge=0)
    unsupported_explanation_count: int = Field(..., ge=0)


class ResultExplanationReport(JsonModel):
    """Deterministic structured explanation report over result artifacts."""

    model_config = ConfigDict(extra="forbid")

    explanations: tuple[ResultExplanation, ...] = Field(default_factory=tuple)
    summary: ResultExplanationSummary
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _PathwayComparisonArtifact:
    comparison_row_id: str
    pathway_id: str
    pathway_name: str | None
    source_name: str | None
    source_accession: str | None
    condition_a: str
    condition_b: str
    condition_a_confidence_status: str
    condition_b_confidence_status: str
    comparison_confidence_status: str
    mean_activity_score_a: float | None
    mean_activity_score_b: float | None
    activity_score_delta: float | None


@dataclass(frozen=True)
class _PathwayMemberContributionArtifact:
    pathway_id: str
    member_id: str
    observed_protein_refs: tuple[str, ...]
    member_activity_score: float | None
    observed: bool


@dataclass(frozen=True)
class _PathwayUnresolvedMemberArtifact:
    pathway_id: str
    member_id: str
    reason: str


@dataclass(frozen=True)
class _RejectedClaimArtifact:
    claim_id: str
    claim_kind: str
    subject_id: str
    subject_label: str
    claim_text: str
    condition_a: str
    condition_b: str
    asserted_direction: str
    adjusted_p_value: float | None
    effect_size: float | None
    robustness_score: float | None
    imputation_dependent: bool
    evidence_tier: str | None
    confidence_tier: str | None
    pathway_confidence_status: str | None
    pathway_delta: float | None
    regulator_evidence_type: str | None
    regulator_signal_surface: str | None
    regulator_score: float | None
    reason_codes: tuple[str, ...]
    source_ids: tuple[str, ...]
    validation_note: str


@dataclass(frozen=True)
class _ResultExplanationArtifactContext:
    base_context: _ResultArtifactContext
    pathway_comparisons: tuple[_PathwayComparisonArtifact, ...]
    pathway_member_contributions: tuple[_PathwayMemberContributionArtifact, ...]
    pathway_unresolved_members: tuple[_PathwayUnresolvedMemberArtifact, ...]
    rejected_claims: tuple[_RejectedClaimArtifact, ...]
    biological_report_available: bool
    ptm_report_available: bool
    pathway_activity_available: bool
    rejected_claims_available: bool
    qc_available: bool


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


def render_result_explanation_summary_tsv(report: ResultExplanationReport) -> str:
    """Render one-row deterministic explanation summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "explanation_count",
            "answered_explanation_count",
            "not_found_explanation_count",
            "unsupported_explanation_count",
        )
    )
    writer.writerow(
        (
            report.summary.explanation_count,
            report.summary.answered_explanation_count,
            report.summary.not_found_explanation_count,
            report.summary.unsupported_explanation_count,
        )
    )
    return buffer.getvalue()


def render_result_explanation_tsv(report: ResultExplanationReport) -> str:
    """Render deterministic explanations as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "explanation_id",
            "explanation_kind",
            "status",
            "subject_id",
            "subject_label",
            "claim",
            "decision",
            "confidence",
            "result_row_ids",
            "graph_node_ids",
            "note",
        )
    )
    for explanation in report.explanations:
        writer.writerow(
            (
                explanation.explanation_id,
                explanation.explanation_kind.value,
                explanation.status.value,
                "" if explanation.subject_id is None else explanation.subject_id,
                "" if explanation.subject_label is None else explanation.subject_label,
                explanation.claim,
                explanation.decision,
                explanation.confidence,
                ";".join(explanation.result_row_ids),
                ";".join(explanation.graph_node_ids),
                explanation.note,
            )
        )
    return buffer.getvalue()


def render_result_explanation_evidence_tsv(report: ResultExplanationReport) -> str:
    """Render deterministic explanation points as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "explanation_id",
            "explanation_kind",
            "evidence_role",
            "result_surface",
            "row_id",
            "graph_node_ids",
            "source_row_refs",
            "summary",
        )
    )
    for explanation in report.explanations:
        for point in (*explanation.evidence, *explanation.opposing_evidence):
            writer.writerow(
                (
                    explanation.explanation_id,
                    explanation.explanation_kind.value,
                    point.role.value,
                    point.result_surface,
                    point.row_id,
                    ";".join(point.graph_node_ids),
                    ";".join(point.source_row_refs),
                    point.summary,
                )
            )
    return buffer.getvalue()


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
    card = _find_protein_card(context.base_context.protein_cards, request.subject_id)
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
        confidence=_protein_confidence(card.significant, card.evidence_tier, card.warning_codes),
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
    card = _find_ptm_card(context.base_context.ptm_cards, request.subject_id)
    if card is None:
        return _not_found_explanation(
            request,
            "no governed PTM evidence card matched the requested subject",
        )
    protein_card = _find_protein_card(context.base_context.protein_cards, card.protein_ref)
    graph_node_ids = (
        ()
        if protein_card is None
        else _protein_card_graph_node_ids(protein_card)
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
        context.base_context.graph_nodes,
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
    if comparison.comparison_confidence_status != "high_confidence":
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
        sample_node_ids = _node_ids_for_entity(
            context.base_context.graph_nodes,
            entity_type="sample",
            entity_ref=request.subject_id or "",
        )
        graph_node_ids = tuple(
            dict.fromkeys(
                (
                    *sample_node_ids,
                    *(
                        node_id
                        for run in failed_runs
                        for node_id in _node_ids_for_entity(
                            context.base_context.graph_nodes,
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
            subject_label=request.subject_id,
            claim=f"Sample {request.subject_id} failed QC.",
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
        context.base_context.graph_nodes,
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
    claim = _find_rejected_claim(context.rejected_claims, request.subject_id)
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
    if claim.effect_size is not None or claim.pathway_delta is not None or claim.regulator_score is not None:
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


def _load_result_explanation_artifact_context(
    *,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
) -> _ResultExplanationArtifactContext:
    base_context = _load_result_artifact_context(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    pathway_comparison_path = None
    pathway_member_path = None
    pathway_unresolved_path = None
    rejected_claim_path = None
    if biological_report_dir is not None:
        candidate = (
            biological_report_dir / "biological_pathway_activity_condition_comparisons.tsv"
        )
        if candidate.exists():
            pathway_comparison_path = candidate
        candidate = biological_report_dir / "biological_pathway_activity_members.tsv"
        if candidate.exists():
            pathway_member_path = candidate
        candidate = biological_report_dir / "biological_pathway_activity_unresolved.tsv"
        if candidate.exists():
            pathway_unresolved_path = candidate
        candidate = biological_report_dir / "biological_rejected_claims.tsv"
        if candidate.exists():
            rejected_claim_path = candidate
    return _ResultExplanationArtifactContext(
        base_context=base_context,
        pathway_comparisons=()
        if pathway_comparison_path is None
        else _load_pathway_comparisons(pathway_comparison_path),
        pathway_member_contributions=()
        if pathway_member_path is None
        else _load_pathway_member_contributions(pathway_member_path),
        pathway_unresolved_members=()
        if pathway_unresolved_path is None
        else _load_pathway_unresolved_members(pathway_unresolved_path),
        rejected_claims=()
        if rejected_claim_path is None
        else _load_rejected_claims(rejected_claim_path),
        biological_report_available=biological_report_dir is not None,
        ptm_report_available=ptm_report_dir is not None,
        pathway_activity_available=pathway_comparison_path is not None,
        rejected_claims_available=rejected_claim_path is not None,
        qc_available=bool(run_qc_assessment_tsv_paths),
    )


def _load_pathway_comparisons(path: Path) -> tuple[_PathwayComparisonArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _PathwayComparisonArtifact(
            comparison_row_id=(
                f"{row['pathway_id']}:{row['condition_a']}:{row['condition_b']}"
            ),
            pathway_id=row["pathway_id"],
            pathway_name=_empty_to_none(row["pathway_name"]),
            source_name=_empty_to_none(row["source_name"]),
            source_accession=_empty_to_none(row["source_accession"]),
            condition_a=row["condition_a"],
            condition_b=row["condition_b"],
            condition_a_confidence_status=row["condition_a_confidence_status"],
            condition_b_confidence_status=row["condition_b_confidence_status"],
            comparison_confidence_status=row["comparison_confidence_status"],
            mean_activity_score_a=_parse_optional_float(row["mean_activity_score_a"]),
            mean_activity_score_b=_parse_optional_float(row["mean_activity_score_b"]),
            activity_score_delta=_parse_optional_float(row["activity_score_delta"]),
        )
        for row in rows
    )


def _load_pathway_member_contributions(
    path: Path,
) -> tuple[_PathwayMemberContributionArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _PathwayMemberContributionArtifact(
            pathway_id=row["pathway_id"],
            member_id=row["member_id"],
            observed_protein_refs=_split_multi(row["observed_protein_refs"]),
            member_activity_score=_parse_optional_float(row["member_activity_score"]),
            observed=_parse_bool(row["observed"]),
        )
        for row in rows
    )


def _load_pathway_unresolved_members(
    path: Path,
) -> tuple[_PathwayUnresolvedMemberArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _PathwayUnresolvedMemberArtifact(
            pathway_id=row["pathway_id"],
            member_id=row["member_id"],
            reason=row["reason"],
        )
        for row in rows
    )


def _load_rejected_claims(path: Path) -> tuple[_RejectedClaimArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _RejectedClaimArtifact(
            claim_id=row["claim_id"],
            claim_kind=row["claim_kind"],
            subject_id=row["subject_id"],
            subject_label=row["subject_label"],
            claim_text=row["claim_text"],
            condition_a=row["condition_a"],
            condition_b=row["condition_b"],
            asserted_direction=row["asserted_direction"],
            adjusted_p_value=_parse_optional_float(row["adjusted_p_value"]),
            effect_size=_parse_optional_float(row["effect_size"]),
            robustness_score=_parse_optional_float(row["robustness_score"]),
            imputation_dependent=_parse_bool(row["imputation_dependent"]),
            evidence_tier=_empty_to_none(row["evidence_tier"]),
            confidence_tier=_empty_to_none(row["confidence_tier"]),
            pathway_confidence_status=_empty_to_none(row["pathway_confidence_status"]),
            pathway_delta=_parse_optional_float(row["pathway_delta"]),
            regulator_evidence_type=_empty_to_none(row["regulator_evidence_type"]),
            regulator_signal_surface=_empty_to_none(row["regulator_signal_surface"]),
            regulator_score=_parse_optional_float(row["regulator_score"]),
            reason_codes=_split_multi(row["reason_codes"]),
            source_ids=_split_multi(row["source_ids"]),
            validation_note=row["validation_note"],
        )
        for row in rows
    )


def _find_pathway_comparison(
    comparisons: tuple[_PathwayComparisonArtifact, ...],
    subject_id: str | None,
) -> _PathwayComparisonArtifact | None:
    if subject_id is None:
        return None
    exact = next(
        (
            entry
            for entry in comparisons
            if subject_id in {entry.comparison_row_id, entry.pathway_id}
            and subject_id == entry.comparison_row_id
        ),
        None,
    )
    if exact is not None:
        return exact
    pathway_matches = [entry for entry in comparisons if entry.pathway_id == subject_id]
    if len(pathway_matches) == 1:
        return pathway_matches[0]
    return None


def _top_pathway_members(
    entries: tuple[_PathwayMemberContributionArtifact, ...],
    pathway_id: str,
) -> tuple[str, ...]:
    ranked = sorted(
        (
            entry
            for entry in entries
            if entry.pathway_id == pathway_id and entry.observed
        ),
        key=lambda entry: (
            entry.member_activity_score is None,
            0.0 if entry.member_activity_score is None else -abs(entry.member_activity_score),
            entry.member_id,
        ),
    )
    labels = [
        entry.member_id
        if not entry.observed_protein_refs
        else f"{entry.member_id} ({','.join(entry.observed_protein_refs)})"
        for entry in ranked[:3]
    ]
    return tuple(labels)


def _pathway_unresolved_members(
    entries: tuple[_PathwayUnresolvedMemberArtifact, ...],
    pathway_id: str,
) -> tuple[_PathwayUnresolvedMemberArtifact, ...]:
    return tuple(entry for entry in entries if entry.pathway_id == pathway_id)


def _find_failed_qc_run(
    context: _ResultArtifactContext,
    subject_id: str | None,
):
    if subject_id is None:
        return None
    return next(
        (
            entry
            for entry in context.qc_runs
            if entry.qc_status == "fail" and entry.run_id == subject_id
        ),
        None,
    )


def _find_rejected_claim(
    claims: tuple[_RejectedClaimArtifact, ...],
    subject_id: str | None,
) -> _RejectedClaimArtifact | None:
    if subject_id is None:
        return None
    matches = [
        entry
        for entry in claims
        if subject_id in {entry.claim_id, entry.subject_id, entry.subject_label}
    ]
    if len(matches) == 1:
        return matches[0]
    exact = next((entry for entry in matches if entry.claim_id == subject_id), None)
    return exact


def _rejected_claim_graph_node_ids(
    claim: _RejectedClaimArtifact,
    context: _ResultArtifactContext,
) -> tuple[str, ...]:
    if claim.claim_kind == "protein_abundance_change":
        return _node_ids_for_entity(
            context.graph_nodes,
            entity_type="protein",
            entity_ref=claim.subject_id,
        )
    if claim.claim_kind == "pathway_activity_change":
        return _node_ids_for_entity(
            context.graph_nodes,
            entity_type="pathway",
            entity_ref=claim.subject_id,
        )
    return ()


def _rejected_claim_signal_summary(claim: _RejectedClaimArtifact) -> str:
    if claim.effect_size is not None:
        return (
            f"candidate effect size was {claim.effect_size:.4g} with adjusted p-value "
            + (
                "not available"
                if claim.adjusted_p_value is None
                else f"{claim.adjusted_p_value:.4g}"
            )
        )
    if claim.pathway_delta is not None:
        return (
            f"candidate pathway delta was {claim.pathway_delta:.4g} with pathway "
            f"confidence {claim.pathway_confidence_status or 'unknown'}"
        )
    if claim.regulator_score is not None:
        return (
            f"candidate regulator score was {claim.regulator_score:.4g} on "
            f"{claim.regulator_signal_surface or 'unknown'}"
        )
    return "candidate carried source evidence but still failed validation checks"


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
