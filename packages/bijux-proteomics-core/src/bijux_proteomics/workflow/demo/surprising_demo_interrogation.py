# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic interrogation over shipped surprising-demo outputs."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.demo.surprising_demo import (
    SurprisingDemoConfig,
    SurprisingDemoReport,
    run_surprising_demo,
)
from bijux_proteomics_foundation import JsonModel


class SurprisingDemoQueryKind(StrEnum):
    """Supported deterministic query families over the shipped demo."""

    WHY_PROTEIN_CHANGED = "why_protein_changed"
    WHY_SITE_AMBIGUOUS = "why_site_ambiguous"
    WHY_SAMPLE_FAILED = "why_sample_failed"
    WHAT_VALIDATES_TARGET = "what_validates_target"


class SurprisingDemoQueryStatus(StrEnum):
    """Stable answer states for one shipped-demo query."""

    ANSWERED = "answered"
    NOT_FOUND = "not_found"


class SurprisingDemoQueryRequest(JsonModel):
    """One deterministic query over the shipped demo outputs."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(..., min_length=1)
    query_kind: SurprisingDemoQueryKind
    subject_id: str = Field(..., min_length=1)


class SurprisingDemoQueryAnswer(JsonModel):
    """One deterministic shipped-demo answer with explicit support fields."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(..., min_length=1)
    query_kind: SurprisingDemoQueryKind
    status: SurprisingDemoQueryStatus
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    answer_text: str = Field(..., min_length=1)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    confidence_reasons: tuple[str, ...] = Field(default_factory=tuple)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SurprisingDemoInterrogationSummary(JsonModel):
    """Summary over one deterministic interrogation pass."""

    model_config = ConfigDict(extra="forbid")

    query_count: int = Field(..., ge=0)
    answered_query_count: int = Field(..., ge=0)
    not_found_query_count: int = Field(..., ge=0)


class SurprisingDemoInterrogationReport(JsonModel):
    """Deterministic interrogation report over one shipped demo run."""

    model_config = ConfigDict(extra="forbid")

    demo_output_dir: str = Field(..., min_length=1)
    requests: tuple[SurprisingDemoQueryRequest, ...] = Field(default_factory=tuple)
    answers: tuple[SurprisingDemoQueryAnswer, ...] = Field(default_factory=tuple)
    summary: SurprisingDemoInterrogationSummary
    note: str = Field(..., min_length=1)


class _SurprisingDemoContext(JsonModel):
    """Internal artifact context for shipped-demo interrogation."""

    model_config = ConfigDict(extra="forbid")

    protein_cards: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    ambiguous_sites: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    ambiguity_group_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    localization_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    unreliable_target_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    target_evidence_cards: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    target_validation_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    assay_panel_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)


def ensure_surprising_demo_outputs(output_dir: Path) -> Path:
    """Ensure the shipped demo outputs exist at the requested directory."""

    report_path = output_dir / "surprising_demo_report.json"
    if report_path.exists():
        try:
            SurprisingDemoReport.model_validate_json(
                report_path.read_text(encoding="utf-8")
            )
            return output_dir
        except Exception:  # noqa: BLE001
            pass
    run_surprising_demo(SurprisingDemoConfig(output_dir=output_dir))
    return output_dir


def build_surprising_demo_example_requests(
    demo_output_dir: Path,
) -> tuple[SurprisingDemoQueryRequest, ...]:
    """Build the four shipped deterministic query examples from demo outputs."""

    context = _load_surprising_demo_context(demo_output_dir)
    protein_subject = next(
        (
            row["representative_protein_ref"]
            for row in context.protein_cards
            if row["significant"].lower() == "true"
        ),
        None,
    )
    site_subject = (
        None if not context.ambiguous_sites else context.ambiguous_sites[0]["site_key"]
    )
    sample_subject = next(
        (row["sample_id"] for row in context.unreliable_target_rows if row["sample_id"]),
        None,
    )
    target_subject = (
        None
        if not context.target_evidence_cards
        else context.target_evidence_cards[0]["candidate_id"]
    )
    if None in {
        protein_subject,
        site_subject,
        sample_subject,
        target_subject,
    }:
        raise ValueError(
            "shipped demo outputs are missing one or more deterministic query anchors"
        )
    return (
        SurprisingDemoQueryRequest(
            query_id="demo-why-protein-changed",
            query_kind=SurprisingDemoQueryKind.WHY_PROTEIN_CHANGED,
            subject_id=protein_subject,
        ),
        SurprisingDemoQueryRequest(
            query_id="demo-why-site-ambiguous",
            query_kind=SurprisingDemoQueryKind.WHY_SITE_AMBIGUOUS,
            subject_id=site_subject,
        ),
        SurprisingDemoQueryRequest(
            query_id="demo-why-sample-failed",
            query_kind=SurprisingDemoQueryKind.WHY_SAMPLE_FAILED,
            subject_id=sample_subject,
        ),
        SurprisingDemoQueryRequest(
            query_id="demo-what-validates-target",
            query_kind=SurprisingDemoQueryKind.WHAT_VALIDATES_TARGET,
            subject_id=target_subject,
        ),
    )


def build_surprising_demo_interrogation_report(
    demo_output_dir: Path,
    requests: tuple[SurprisingDemoQueryRequest, ...] = (),
) -> SurprisingDemoInterrogationReport:
    """Answer deterministic shipped-demo questions from governed demo artifacts."""

    context = _load_surprising_demo_context(demo_output_dir)
    effective_requests = (
        requests
        if requests
        else build_surprising_demo_example_requests(demo_output_dir)
    )
    answers = tuple(
        _answer_surprising_demo_query(request, context=context)
        for request in effective_requests
    )
    return SurprisingDemoInterrogationReport(
        demo_output_dir=str(demo_output_dir),
        requests=effective_requests,
        answers=answers,
        summary=SurprisingDemoInterrogationSummary(
            query_count=len(answers),
            answered_query_count=sum(
                answer.status is SurprisingDemoQueryStatus.ANSWERED
                for answer in answers
            ),
            not_found_query_count=sum(
                answer.status is SurprisingDemoQueryStatus.NOT_FOUND
                for answer in answers
            ),
        ),
        note=(
            "shipped demo interrogation answers only from governed demo artifacts "
            "and preserves explicit evidence ids, source rows, and confidence reasons"
        ),
    )


def render_surprising_demo_interrogation_summary_tsv(
    report: SurprisingDemoInterrogationReport,
) -> str:
    """Render the one-row interrogation summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "query_count",
            "answered_query_count",
            "not_found_query_count",
        )
    )
    writer.writerow(
        (
            report.summary.query_count,
            report.summary.answered_query_count,
            report.summary.not_found_query_count,
        )
    )
    return buffer.getvalue()


def render_surprising_demo_interrogation_answers_tsv(
    report: SurprisingDemoInterrogationReport,
) -> str:
    """Render deterministic shipped-demo answers as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "query_id",
            "query_kind",
            "status",
            "subject_id",
            "subject_label",
            "answer_text",
            "evidence_ids",
            "source_row_refs",
            "confidence_reasons",
            "artifact_paths",
            "note",
        )
    )
    for answer in report.answers:
        writer.writerow(
            (
                answer.query_id,
                answer.query_kind.value,
                answer.status.value,
                answer.subject_id,
                answer.subject_label,
                answer.answer_text,
                ";".join(answer.evidence_ids),
                ";".join(answer.source_row_refs),
                ";".join(answer.confidence_reasons),
                ";".join(answer.artifact_paths),
                answer.note,
            )
        )
    return buffer.getvalue()


def _answer_surprising_demo_query(
    request: SurprisingDemoQueryRequest,
    *,
    context: _SurprisingDemoContext,
) -> SurprisingDemoQueryAnswer:
    if request.query_kind is SurprisingDemoQueryKind.WHY_PROTEIN_CHANGED:
        return _answer_why_protein_changed(request, context=context)
    if request.query_kind is SurprisingDemoQueryKind.WHY_SITE_AMBIGUOUS:
        return _answer_why_site_ambiguous(request, context=context)
    if request.query_kind is SurprisingDemoQueryKind.WHY_SAMPLE_FAILED:
        return _answer_why_sample_failed(request, context=context)
    if request.query_kind is SurprisingDemoQueryKind.WHAT_VALIDATES_TARGET:
        return _answer_what_validates_target(request, context=context)
    raise ValueError(f"unsupported query kind: {request.query_kind.value}")


def _answer_why_protein_changed(
    request: SurprisingDemoQueryRequest,
    *,
    context: _SurprisingDemoContext,
) -> SurprisingDemoQueryAnswer:
    card = next(
        (
            row
            for row in context.protein_cards
            if request.subject_id
            in {
                row["representative_protein_ref"],
                row["card_id"],
                row["protein_group_id"],
            }
        ),
        None,
    )
    if card is None:
        return _not_found_answer(
            request,
            note="no governed biological protein card matched the requested protein",
        )
    peptides = _split_multi(card["peptides"])
    evidence_ids = tuple(
        dict.fromkeys(
            (
                card["graph_claim_node_id"],
                card["graph_subject_node_id"],
                *_split_multi(card["graph_support_node_ids"]),
            )
        )
    )
    source_row_refs = tuple(
        dict.fromkeys(
            (
                f"biological_protein_cards:{card['card_id']}",
                *(
                    f"biological_protein_cards:{entry}"
                    for entry in _split_multi(card["graph_source_row_refs"])
                ),
            )
        )
    )
    confidence_reasons = tuple(
        dict.fromkeys(
            (
                f"evidence_tier:{card['evidence_tier']}",
                *(
                    f"warning:{entry}"
                    for entry in _split_multi(card["warning_codes"])
                ),
            )
        )
    )
    adjusted_p_value = (
        card["adjusted_p_value"]
        if card["adjusted_p_value"]
        else "unadjusted-only evidence"
    )
    return SurprisingDemoQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=SurprisingDemoQueryStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=card["representative_protein_ref"],
        answer_text=(
            f"Protein {card['representative_protein_ref']} changed because biological "
            f"protein card {card['card_id']} reports log2 fold change "
            f"{float(card['log2_fold_change']):.4g} for {card['condition_a']} vs "
            f"{card['condition_b']} with adjusted p-value {adjusted_p_value} and "
            f"peptide support from {', '.join(peptides) or 'no retained peptides'}."
        ),
        evidence_ids=evidence_ids,
        source_row_refs=source_row_refs,
        confidence_reasons=confidence_reasons,
        artifact_paths=("biological_review/biological_protein_cards.tsv",),
        note=(
            "protein-change answer is anchored to one governed biological protein "
            "card and its graph-backed support rows"
        ),
    )


def _answer_why_site_ambiguous(
    request: SurprisingDemoQueryRequest,
    *,
    context: _SurprisingDemoContext,
) -> SurprisingDemoQueryAnswer:
    excluded_row = next(
        (
            row
            for row in context.ambiguous_sites
            if request.subject_id in {row["site_key"], row["group_key"]}
        ),
        None,
    )
    if excluded_row is None:
        return _not_found_answer(
            request,
            note="no excluded ambiguous-site row matched the requested PTM site",
        )
    group_row = next(
        (
            row
            for row in context.ambiguity_group_rows
            if row["group_key"] == excluded_row["group_key"]
        ),
        None,
    )
    localization_rows = tuple(
        row
        for row in context.localization_rows
        if row["localized_peptide"] == excluded_row["localized_peptides"]
        and row["sample_id"] in set(_split_multi(excluded_row["sample_ids"]))
        and row["ambiguous"].lower() == "true"
    )
    evidence_ids = tuple(
        dict.fromkeys(
            (
                excluded_row["group_key"],
                excluded_row["site_key"],
                *(row["spectrum_id"] for row in localization_rows),
            )
        )
    )
    source_row_refs = (
        f"advanced_ptm_excluded_ambiguous_sites:{excluded_row['site_key']}",
        f"advanced_ptm_site_group_matrix:{excluded_row['group_key']}",
        *(
            f"ptm_localization:{row['spectrum_id']}"
            for row in localization_rows
        ),
    )
    confidence_reasons = tuple(
        dict.fromkeys(
            (
                "ambiguity_group_matrix",
                "excluded_from_exact_site_matrix",
                f"candidate_positions:{excluded_row['candidate_positions']}",
                (
                    "confidence_tier:unknown"
                    if group_row is None
                    else f"confidence_tier:{group_row['confidence_tier']}"
                ),
                *(
                    f"localization_tier:{row['localization_tier']}"
                    for row in localization_rows
                ),
            )
        )
    )
    return SurprisingDemoQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=SurprisingDemoQueryStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=excluded_row["site_key"],
        answer_text=(
            f"Site {excluded_row['site_key']} remains ambiguous because localized "
            f"peptide {excluded_row['localized_peptides']} supports candidate "
            f"positions {excluded_row['candidate_positions']} rather than one exact "
            f"residue, so the signal is excluded from the exact-site matrix and kept "
            f"under ambiguity group {excluded_row['group_key']}."
        ),
        evidence_ids=evidence_ids,
        source_row_refs=source_row_refs,
        confidence_reasons=confidence_reasons,
        artifact_paths=(
            "ptm_review/advanced_ptm_excluded_ambiguous_sites.tsv",
            "ptm_review/advanced_ptm_site_group_matrix.tsv",
            "ptm_review/ptm_localization.tsv",
        ),
        note=(
            "site-ambiguity answer is anchored to the excluded ambiguous-site ledger, "
            "the ambiguity-group matrix row, and the originating localization spectra"
        ),
    )


def _answer_why_sample_failed(
    request: SurprisingDemoQueryRequest,
    *,
    context: _SurprisingDemoContext,
) -> SurprisingDemoQueryAnswer:
    rows = tuple(
        row
        for row in context.unreliable_target_rows
        if row["sample_id"] == request.subject_id
    )
    if not rows:
        return _not_found_answer(
            request,
            note="no shipped targeted-assay QC rows matched the requested sample",
        )
    evidence_ids = tuple(
        dict.fromkeys(
            (
                *(row["target_id"] for row in rows),
                *(
                    transition_id
                    for row in rows
                    for transition_id in _split_multi(row["flagged_transition_ids"])
                ),
            )
        )
    )
    source_row_refs = tuple(
        f"targeted_assay_qc_unreliable_targets:{row['target_id']}:{row['sample_id']}"
        for row in rows
    )
    confidence_reasons = tuple(
        dict.fromkeys(
            (
                *(
                    f"quality_flag:{row['quality_flags']}"
                    for row in rows
                    if row["quality_flags"]
                ),
                *(
                    f"reason:{reason.strip()}"
                    for row in rows
                    for reason in row["reasons"].split(";")
                    if reason.strip()
                ),
            )
        )
    )
    return SurprisingDemoQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=SurprisingDemoQueryStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=request.subject_id,
        answer_text=(
            f"Sample {request.subject_id} is flagged by shipped assay-QC review across "
            f"{len(rows)} target rows because the preserved QC evidence reports "
            f"{'; '.join(row['reasons'] for row in rows)}."
        ),
        evidence_ids=evidence_ids,
        source_row_refs=source_row_refs,
        confidence_reasons=confidence_reasons,
        artifact_paths=(
            "targeted_validation/targeted_assay_qc_unreliable_targets.tsv",
            "demo_qc_packets.tsv",
        ),
        note=(
            "sample-failure answer is anchored to sample-specific targeted assay-QC "
            "rows rather than a synthesized summary only"
        ),
    )


def _answer_what_validates_target(
    request: SurprisingDemoQueryRequest,
    *,
    context: _SurprisingDemoContext,
) -> SurprisingDemoQueryAnswer:
    card = next(
        (
            row
            for row in context.target_evidence_cards
            if request.subject_id
            in {
                row["candidate_id"],
                row["target_protein_ref"],
            }
        ),
        None,
    )
    if card is None:
        return _not_found_answer(
            request,
            note="no shipped targeted evidence card matched the requested validation target",
        )
    validation_rows = tuple(
        row
        for row in context.target_validation_rows
        if row["candidate_id"] == card["candidate_id"]
    )
    assay_rows = tuple(
        row
        for row in context.assay_panel_rows
        if row["candidate_id"] == card["candidate_id"]
    )
    evidence_ids = tuple(
        dict.fromkeys(
            (
                card["candidate_id"],
                *(row["assay_entry_id"] for row in validation_rows),
                *(row["matched_target_id"] for row in validation_rows if row["matched_target_id"]),
            )
        )
    )
    source_row_refs = tuple(
        dict.fromkeys(
            (
                f"advanced_targeted_evidence_cards:{card['candidate_id']}",
                *(
                    f"targeted_validation_evidence:{row['assay_entry_id']}"
                    for row in validation_rows
                ),
                *(
                    f"demo_assay_panel:{row['assay_entry_id']}"
                    for row in assay_rows
                ),
            )
        )
    )
    confidence_reasons = tuple(
        dict.fromkeys(
            (
                f"validation_verdict:{card['validation_verdict']}",
                f"assay_reliability:{card['assay_reliability_status']}",
                *(
                    f"reason:{entry}"
                    for entry in _split_multi(card["reason_codes"])
                ),
                *(
                    f"reason:{entry}"
                    for row in validation_rows
                    for entry in _split_multi(row["reason_codes"])
                ),
            )
        )
    )
    validation_effect = (
        "no retained validation effect"
        if card["validation_log2_effect"] == ""
        else f"validation log2 effect {float(card['validation_log2_effect']):.4g}"
    )
    return SurprisingDemoQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=SurprisingDemoQueryStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=card["display_label"],
        answer_text=(
            f"Target {card['candidate_id']} is interrogated by "
            f"{', '.join(row['assay_entry_id'] for row in validation_rows) or 'no assays'} "
            f"and currently stays {card['validation_verdict']} with "
            f"{card['assay_reliability_status']} assay reliability because "
            f"{'; '.join(row['note'] for row in validation_rows)}; "
            f"the discovery effect was {float(card['discovery_effect_size']):.4g} and "
            f"{validation_effect}."
        ),
        evidence_ids=evidence_ids,
        source_row_refs=source_row_refs,
        confidence_reasons=confidence_reasons,
        artifact_paths=(
            "targeted_validation/advanced_targeted_evidence_cards.tsv",
            "targeted_validation/targeted_validation_evidence.tsv",
            "demo_assay_panel.tsv",
        ),
        note=(
            "target-validation answer is anchored to the candidate evidence card, "
            "assay-level validation rows, and the shipped assay-panel export"
        ),
    )


def _not_found_answer(
    request: SurprisingDemoQueryRequest,
    *,
    note: str,
) -> SurprisingDemoQueryAnswer:
    return SurprisingDemoQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=SurprisingDemoQueryStatus.NOT_FOUND,
        subject_id=request.subject_id,
        subject_label=request.subject_id,
        answer_text=note,
        evidence_ids=(),
        source_row_refs=(),
        confidence_reasons=(),
        artifact_paths=(),
        note=note,
    )


def _load_surprising_demo_context(demo_output_dir: Path) -> _SurprisingDemoContext:
    return _SurprisingDemoContext(
        protein_cards=_read_tsv_rows(
            demo_output_dir / "biological_review" / "biological_protein_cards.tsv"
        ),
        ambiguous_sites=_read_tsv_rows(
            demo_output_dir
            / "ptm_review"
            / "advanced_ptm_excluded_ambiguous_sites.tsv"
        ),
        ambiguity_group_rows=_read_tsv_rows(
            demo_output_dir / "ptm_review" / "advanced_ptm_site_group_matrix.tsv"
        ),
        localization_rows=_read_tsv_rows(
            demo_output_dir / "ptm_review" / "ptm_localization.tsv"
        ),
        unreliable_target_rows=_read_tsv_rows(
            demo_output_dir
            / "targeted_validation"
            / "targeted_assay_qc_unreliable_targets.tsv"
        ),
        target_evidence_cards=_read_tsv_rows(
            demo_output_dir
            / "targeted_validation"
            / "advanced_targeted_evidence_cards.tsv"
        ),
        target_validation_rows=_read_tsv_rows(
            demo_output_dir
            / "targeted_validation"
            / "targeted_validation_evidence.tsv"
        ),
        assay_panel_rows=_read_tsv_rows(demo_output_dir / "demo_assay_panel.tsv"),
    )


def _read_tsv_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        raise ValueError(f"required surprising-demo artifact is missing: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle, delimiter="\t"))


def _split_multi(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part for part in value.split(";") if part)


__all__ = [
    "SurprisingDemoInterrogationReport",
    "SurprisingDemoInterrogationSummary",
    "SurprisingDemoQueryAnswer",
    "SurprisingDemoQueryKind",
    "SurprisingDemoQueryRequest",
    "SurprisingDemoQueryStatus",
    "build_surprising_demo_example_requests",
    "build_surprising_demo_interrogation_report",
    "ensure_surprising_demo_outputs",
    "render_surprising_demo_interrogation_answers_tsv",
    "render_surprising_demo_interrogation_summary_tsv",
]
