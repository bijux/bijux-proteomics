# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic belief audits over governed proteomics conclusion artifacts."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from html import escape
from io import StringIO
from pathlib import Path

from bijux_proteomics.review.claims.result_query_artifacts import (
    _empty_to_none,
    _node_ids_for_entity,
    _parse_bool,
    _parse_optional_float,
    _read_tsv_rows,
    _sample_to_failed_qc_runs,
    _split_multi,
)
from bijux_proteomics.review.explanations.result_explanations import (
    ResultExplanation,
    ResultExplanationKind,
    ResultExplanationRequest,
    ResultExplanationStatus,
    _load_result_explanation_artifact_context,
    _ResultExplanationArtifactContext,
    build_result_explanation_report_from_artifacts,
)
from bijux_proteomics.review.belief.belief_audit_models import (
    BeliefAuditEntry,
    BeliefAuditReport,
    BeliefAuditSubjectKind,
    BeliefAuditSummary,
)


_SECTION_TITLES = {
    BeliefAuditSubjectKind.PROTEIN: "Proteins",
    BeliefAuditSubjectKind.PTM_SITE: "PTM Sites",
    BeliefAuditSubjectKind.PATHWAY: "Pathways",
    BeliefAuditSubjectKind.REGULATOR: "Regulators",
    BeliefAuditSubjectKind.BIOMARKER: "Biomarkers",
    BeliefAuditSubjectKind.QC_DECISION: "QC Decisions",
}

@dataclass(frozen=True)
class _RegulatorInferenceArtifact:
    row_id: str
    regulator: str
    evidence_type: str
    signal_surface: str
    source_name: str | None
    source_accession: str | None
    target_count: int
    matched_target_count: int
    coverage_fraction: float
    supporting_protein_refs: tuple[str, ...]
    supporting_site_keys: tuple[str, ...]
    supporting_pathway_ids: tuple[str, ...]
    direction: str | None
    score: float | None
    mean_log2_fold_change: float | None
    mean_activity_score_delta: float | None
    note: str


@dataclass(frozen=True)
class _UnresolvedRegulatorTargetArtifact:
    row_id: str
    regulator: str
    evidence_type: str
    target_field: str
    target_value: str
    source_name: str | None
    source_accession: str | None
    reason: str


@dataclass(frozen=True)
class _ValidationEvidenceCardArtifact:
    candidate_id: str
    candidate_kind: str
    display_label: str
    target_protein_ref: str | None
    site_key: str | None
    discovery_final_score: float | None
    discovery_adjusted_p_value: float | None
    discovery_support_count: int
    biological_role_labels: tuple[str, ...]
    biological_source_ids: tuple[str, ...]
    assay_entry_count: int
    omitted_reason: str | None
    targeted_validation_verdict: str
    targeted_validation_log2_effect: float | None
    confirmed_assay_count: int
    contradicted_assay_count: int
    inconclusive_assay_count: int
    targeted_validation_reason_codes: tuple[str, ...]
    stability_score: float | None
    stability_downgraded: bool
    stability_reason_codes: tuple[str, ...]
    redundancy_dropped: bool
    redundancy_reason_codes: tuple[str, ...]
    final_status: str
    warning_codes: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class _ValidationWarningArtifact:
    warning_id: str
    candidate_id: str
    warning_code: str
    note: str


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


def render_belief_audit_summary_tsv(report: BeliefAuditReport) -> str:
    """Render belief-audit summary counts as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field, value in (
        ("entry_count", report.summary.entry_count),
        ("protein_entry_count", report.summary.protein_entry_count),
        ("ptm_site_entry_count", report.summary.ptm_site_entry_count),
        ("pathway_entry_count", report.summary.pathway_entry_count),
        ("regulator_entry_count", report.summary.regulator_entry_count),
        ("biomarker_entry_count", report.summary.biomarker_entry_count),
        ("qc_decision_entry_count", report.summary.qc_decision_entry_count),
        ("note", report.note),
    ):
        writer.writerow((field, value))
    return buffer.getvalue()


def render_belief_audit_tsv(report: BeliefAuditReport) -> str:
    """Render belief-audit entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "audit_id",
            "subject_kind",
            "subject_id",
            "subject_label",
            "claim",
            "decision",
            "confidence",
            "why_believed",
            "what_weakens",
            "what_would_falsify",
            "result_surfaces",
            "result_row_ids",
            "graph_node_ids",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.audit_id,
                entry.subject_kind.value,
                entry.subject_id,
                entry.subject_label,
                entry.claim,
                entry.decision,
                entry.confidence,
                entry.why_believed,
                entry.what_weakens,
                entry.what_would_falsify,
                ";".join(entry.result_surfaces),
                ";".join(entry.result_row_ids),
                ";".join(entry.graph_node_ids),
                entry.note,
            )
        )
    return buffer.getvalue()


def render_belief_audit_html(report: BeliefAuditReport) -> str:
    """Render the belief audit as a report section with grouped conclusion entries."""

    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Belief Audit</title>",
        "</head>",
        "<body>",
        "<section>",
        "<h1>Belief Audit</h1>",
        "<p>Each conclusion records why it was retained, what weakens it, and what would falsify it.</p>",
    ]
    for subject_kind in BeliefAuditSubjectKind:
        entries = [
            entry for entry in report.entries if entry.subject_kind is subject_kind
        ]
        if not entries:
            continue
        lines.append(f"<section><h2>{escape(_SECTION_TITLES[subject_kind])}</h2>")
        for entry in entries:
            lines.extend(
                (
                    "<article>",
                    (
                        "<h3>"
                        f"{escape(entry.subject_label)} "
                        f"[{escape(entry.confidence)}]"
                        "</h3>"
                    ),
                    f"<p><strong>Claim:</strong> {escape(entry.claim)}</p>",
                    f"<p><strong>Decision:</strong> {escape(entry.decision)}</p>",
                    f"<p><strong>Why believed:</strong> {escape(entry.why_believed)}</p>",
                    f"<p><strong>What weakens it:</strong> {escape(entry.what_weakens)}</p>",
                    (
                        "<p><strong>What would falsify it:</strong> "
                        f"{escape(entry.what_would_falsify)}</p>"
                    ),
                    (
                        "<p><strong>Citations:</strong> surfaces="
                        f"{escape(';'.join(entry.result_surfaces))}, rows="
                        f"{escape(';'.join(entry.result_row_ids))}, graph nodes="
                        f"{escape(';'.join(entry.graph_node_ids))}</p>"
                    ),
                    "</article>",
                )
            )
        lines.append("</section>")
    if not report.entries:
        lines.append(
            "<p>No governed conclusion artifacts were provided for belief auditing.</p>"
        )
    lines.extend(("</section>", "</body>", "</html>"))
    return "\n".join(lines) + "\n"


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


def _load_regulator_inferences(path: Path) -> tuple[_RegulatorInferenceArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _RegulatorInferenceArtifact(
            row_id=(
                f"{row['regulator']}:{row['evidence_type']}:{row['signal_surface']}:"
                f"{_source_locator(row.get('source_accession', ''), row.get('source_name', ''))}"
            ),
            regulator=row["regulator"],
            evidence_type=row["evidence_type"],
            signal_surface=row["signal_surface"],
            source_name=_empty_to_none(row["source_name"]),
            source_accession=_empty_to_none(row["source_accession"]),
            target_count=int(row["target_count"]),
            matched_target_count=int(row["matched_target_count"]),
            coverage_fraction=_parse_optional_float(row["coverage_fraction"]) or 0.0,
            supporting_protein_refs=_split_multi(row["supporting_protein_refs"]),
            supporting_site_keys=_split_multi(row["supporting_site_keys"]),
            supporting_pathway_ids=_split_multi(row["supporting_pathway_ids"]),
            direction=_empty_to_none(row["direction"]),
            score=_parse_optional_float(row["score"]),
            mean_log2_fold_change=_parse_optional_float(row["mean_log2_fold_change"]),
            mean_activity_score_delta=_parse_optional_float(
                row["mean_activity_score_delta"]
            ),
            note=row["note"],
        )
        for row in rows
    )


def _load_unresolved_regulator_targets(
    path: Path,
) -> tuple[_UnresolvedRegulatorTargetArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _UnresolvedRegulatorTargetArtifact(
            row_id=(
                f"{row['regulator']}:{row['evidence_type']}:{row['target_field']}:"
                f"{row['target_value']}:{_source_locator(row.get('source_accession', ''), row.get('source_name', ''))}"
            ),
            regulator=row["regulator"],
            evidence_type=row["evidence_type"],
            target_field=row["target_field"],
            target_value=row["target_value"],
            source_name=_empty_to_none(row["source_name"]),
            source_accession=_empty_to_none(row["source_accession"]),
            reason=row["reason"],
        )
        for row in rows
    )


def _load_validation_evidence_cards(
    path: Path,
) -> tuple[_ValidationEvidenceCardArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _ValidationEvidenceCardArtifact(
            candidate_id=row["candidate_id"],
            candidate_kind=row["candidate_kind"],
            display_label=row["display_label"],
            target_protein_ref=_empty_to_none(row["target_protein_ref"]),
            site_key=_empty_to_none(row["site_key"]),
            discovery_final_score=_parse_optional_float(row["discovery_final_score"]),
            discovery_adjusted_p_value=_parse_optional_float(
                row["discovery_adjusted_p_value"]
            ),
            discovery_support_count=int(row["discovery_support_count"]),
            biological_role_labels=_split_multi(row["biological_role_labels"]),
            biological_source_ids=_split_multi(row["biological_source_ids"]),
            assay_entry_count=int(row["assay_entry_count"]),
            omitted_reason=_empty_to_none(row["omitted_reason"]),
            targeted_validation_verdict=row["targeted_validation_verdict"],
            targeted_validation_log2_effect=_parse_optional_float(
                row["targeted_validation_log2_effect"]
            ),
            confirmed_assay_count=int(row["confirmed_assay_count"]),
            contradicted_assay_count=int(row["contradicted_assay_count"]),
            inconclusive_assay_count=int(row["inconclusive_assay_count"]),
            targeted_validation_reason_codes=_split_multi(
                row["targeted_validation_reason_codes"]
            ),
            stability_score=_parse_optional_float(row["stability_score"]),
            stability_downgraded=_parse_bool(row["stability_downgraded"]),
            stability_reason_codes=_split_multi(row["stability_reason_codes"]),
            redundancy_dropped=_parse_bool(row["redundancy_dropped"]),
            redundancy_reason_codes=_split_multi(row["redundancy_reason_codes"]),
            final_status=row["final_status"],
            warning_codes=_split_multi(row["warning_codes"]),
            note=row["note"],
        )
        for row in rows
    )


def _load_validation_warnings(path: Path) -> tuple[_ValidationWarningArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _ValidationWarningArtifact(
            warning_id=f"{row['candidate_id']}:{row['warning_code']}",
            candidate_id=row["candidate_id"],
            warning_code=row["warning_code"],
            note=row["note"],
        )
        for row in rows
    )


def _regulator_confidence(entry: _RegulatorInferenceArtifact) -> str:
    if (
        entry.coverage_fraction >= 0.6
        and entry.matched_target_count >= 3
        and (entry.score or 0.0) >= 1.0
    ):
        return "high"
    if entry.coverage_fraction >= 0.3 and entry.matched_target_count >= 2:
        return "moderate"
    if entry.matched_target_count >= 1:
        return "weak"
    return "exploratory"


def _biomarker_confidence(
    card: _ValidationEvidenceCardArtifact,
    warnings: tuple[_ValidationWarningArtifact, ...],
) -> str:
    if (
        card.final_status in {"confirmed", "validated"}
        and not warnings
        and not card.warning_codes
        and not card.stability_downgraded
        and not card.redundancy_dropped
        and card.contradicted_assay_count == 0
    ):
        return "high"
    if card.final_status in {"confirmed", "ready", "retained"}:
        return "moderate"
    if card.final_status in {"blocked", "contradicted", "dropped", "omitted"}:
        return "weak"
    return "exploratory"


def _biomarker_falsifier(card: _ValidationEvidenceCardArtifact) -> str:
    if card.final_status in {"confirmed", "validated", "ready", "retained"}:
        return (
            "Independent targeted assays that reverse the retained effect, fail the "
            "assay-quality review, or reproduce the preserved warning conditions would "
            "falsify this biomarker conclusion."
        )
    return (
        "Independent targeted assays that reproduce the candidate effect without the "
        "preserved contradiction, instability, redundancy, or warning burden would "
        "falsify this current biomarker conclusion."
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


def _source_locator(source_accession: str, source_name: str) -> str:
    accession = source_accession.strip()
    if accession:
        return accession
    name = source_name.strip()
    if name:
        return name
    return "source"


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
