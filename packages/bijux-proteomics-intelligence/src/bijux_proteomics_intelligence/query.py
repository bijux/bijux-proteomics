# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic question answering over governed study results."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.study_result import (
    ProteomicsStudyConclusionKind,
    ProteomicsStudyResult,
)
from bijux_proteomics_foundation import JsonModel


class ResultQuestionKind(StrEnum):
    """Supported deterministic question families over one study result."""

    WHY_SIGNIFICANT = "why_significant"
    WHY_REJECTED = "why_rejected"
    WHAT_PEPTIDES_SUPPORT = "what_peptides_support"
    WHAT_SAMPLES_FAILED = "what_samples_failed"
    WHAT_WEAKENS_CLAIM = "what_weakens_claim"


class ResultQuestionStatus(StrEnum):
    """Stable answer status over one result question."""

    ANSWERED = "answered"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"


class ResultQuestionSpec(JsonModel):
    """One structured question over a governed study result."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(..., min_length=1)
    question_kind: ResultQuestionKind
    subject_id: str | None = None


class ResultQuestionAnswer(JsonModel):
    """One deterministic answer over a governed study result."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(..., min_length=1)
    question_kind: ResultQuestionKind
    status: ResultQuestionStatus
    subject_id: str | None = None
    answer_text: str = Field(..., min_length=1)
    referenced_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def answer_result_question(
    result: ProteomicsStudyResult,
    question_spec: ResultQuestionSpec,
) -> ResultQuestionAnswer:
    """Answer one deterministic question from a governed study result."""

    if question_spec.question_kind is ResultQuestionKind.WHAT_SAMPLES_FAILED:
        return _answer_what_samples_failed(result, question_spec)

    if question_spec.subject_id is None:
        return ResultQuestionAnswer(
            question_id=question_spec.question_id,
            question_kind=question_spec.question_kind,
            status=ResultQuestionStatus.NOT_FOUND,
            subject_id=None,
            answer_text="question requires a subject_id",
            referenced_ids=(),
            note="subject-scoped result question was asked without a subject id",
        )

    if question_spec.question_kind is ResultQuestionKind.WHY_SIGNIFICANT:
        return _answer_why_significant(result, question_spec)
    if question_spec.question_kind is ResultQuestionKind.WHY_REJECTED:
        return _answer_why_rejected(result, question_spec)
    if question_spec.question_kind is ResultQuestionKind.WHAT_PEPTIDES_SUPPORT:
        return _answer_what_peptides_support(result, question_spec)
    if question_spec.question_kind is ResultQuestionKind.WHAT_WEAKENS_CLAIM:
        return _answer_what_weakens_claim(result, question_spec)
    raise AssertionError(f"unsupported result question kind {question_spec.question_kind!r}")


def render_result_question_answers_tsv(
    answers: tuple[ResultQuestionAnswer, ...],
) -> str:
    """Render deterministic question answers as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "question_id",
            "question_kind",
            "status",
            "subject_id",
            "answer_text",
            "referenced_ids",
            "note",
        )
    )
    for answer in answers:
        writer.writerow(
            (
                answer.question_id,
                answer.question_kind.value,
                answer.status.value,
                "" if answer.subject_id is None else answer.subject_id,
                answer.answer_text,
                ";".join(answer.referenced_ids),
                answer.note,
            )
        )
    return handle.getvalue()


def _answer_why_significant(
    result: ProteomicsStudyResult,
    question_spec: ResultQuestionSpec,
) -> ResultQuestionAnswer:
    bundle = result.interactive_result_bundle
    if bundle is None:
        return _not_found(
            question_spec,
            "interactive result bundle is missing",
            note="why_significant requires interactive protein, PTM, or pathway rows",
        )

    subject_id = question_spec.subject_id or ""
    for protein in bundle.proteins:
        if subject_id not in {protein.object_id, protein.representative_protein_ref}:
            continue
        if protein.significant is not True:
            return _not_found(
                question_spec,
                f"{subject_id} is not retained as significant",
                note="matched protein row did not preserve significance",
            )
        referenced_ids = tuple(
            dict.fromkeys((protein.object_id, *protein.peptide_ids, *protein.graph_node_ids))
        )
        return ResultQuestionAnswer(
            question_id=question_spec.question_id,
            question_kind=question_spec.question_kind,
            status=ResultQuestionStatus.ANSWERED,
            subject_id=subject_id,
            answer_text=(
                f"{protein.object_id} stayed significant with adjusted p-value "
                f"{protein.adjusted_p_value} and retained peptide-backed support."
            ),
            referenced_ids=referenced_ids,
            note="significance answer is anchored to the retained protein row, peptides, and graph nodes",
        )

    for site in bundle.ptm_sites:
        if site.site_key != subject_id:
            continue
        if site.adjusted_p_value is None:
            return _not_found(
                question_spec,
                f"{subject_id} has no retained PTM significance row",
                note="matched PTM site is missing adjusted significance",
            )
        referenced_ids = tuple(dict.fromkeys((site.site_key, *site.claim_ids, *site.sample_ids)))
        return ResultQuestionAnswer(
            question_id=question_spec.question_id,
            question_kind=question_spec.question_kind,
            status=ResultQuestionStatus.ANSWERED,
            subject_id=subject_id,
            answer_text=(
                f"{site.site_key} stayed significant with adjusted p-value "
                f"{site.adjusted_p_value} and retained PTM claim support."
            ),
            referenced_ids=referenced_ids,
            note="significance answer is anchored to the retained PTM site row and claim ids",
        )

    for pathway in bundle.pathways:
        if pathway.pathway_id != subject_id:
            continue
        if pathway.adjusted_p_value is None:
            return _not_found(
                question_spec,
                f"{subject_id} has no retained pathway significance row",
                note="matched pathway is missing adjusted significance",
            )
        referenced_ids = tuple(
            dict.fromkeys((pathway.pathway_id, *pathway.supporting_protein_refs))
        )
        return ResultQuestionAnswer(
            question_id=question_spec.question_id,
            question_kind=question_spec.question_kind,
            status=ResultQuestionStatus.ANSWERED,
            subject_id=subject_id,
            answer_text=(
                f"{pathway.pathway_id} stayed significant with adjusted p-value "
                f"{pathway.adjusted_p_value} and retained supporting member overlap."
            ),
            referenced_ids=referenced_ids,
            note="significance answer is anchored to the retained pathway row and supporting protein refs",
        )

    return _not_found(
        question_spec,
        f"{subject_id} has no governed significant result row",
        note="no matching significant protein, PTM site, or pathway row was found",
    )


def _answer_why_rejected(
    result: ProteomicsStudyResult,
    question_spec: ResultQuestionSpec,
) -> ResultQuestionAnswer:
    subject_id = question_spec.subject_id or ""
    for conclusion in result.biological_conclusions:
        if conclusion.kind is not ProteomicsStudyConclusionKind.REJECTED_CLAIM:
            continue
        if subject_id not in {conclusion.conclusion_id, conclusion.subject_id}:
            continue
        return ResultQuestionAnswer(
            question_id=question_spec.question_id,
            question_kind=question_spec.question_kind,
            status=ResultQuestionStatus.ANSWERED,
            subject_id=subject_id,
            answer_text=conclusion.summary_text,
            referenced_ids=(conclusion.conclusion_id, conclusion.subject_id),
            note="rejection answer is anchored to the rejected governed conclusion row",
        )
    return _not_found(
        question_spec,
        f"{subject_id} has no rejected governed conclusion",
        note="why_rejected only answers from rejected conclusion rows",
    )


def _answer_what_peptides_support(
    result: ProteomicsStudyResult,
    question_spec: ResultQuestionSpec,
) -> ResultQuestionAnswer:
    bundle = result.interactive_result_bundle
    if bundle is None:
        return _not_found(
            question_spec,
            "interactive result bundle is missing",
            note="what_peptides_support requires protein or peptide bundle rows",
        )

    subject_id = question_spec.subject_id or ""
    for protein in bundle.proteins:
        if subject_id not in {protein.object_id, protein.representative_protein_ref}:
            continue
        if not protein.peptide_ids:
            return _not_found(
                question_spec,
                f"{subject_id} has no linked peptide ids",
                note="matched protein row preserved no peptide ids",
            )
        return ResultQuestionAnswer(
            question_id=question_spec.question_id,
            question_kind=question_spec.question_kind,
            status=ResultQuestionStatus.ANSWERED,
            subject_id=subject_id,
            answer_text=(
                f"{subject_id} is supported by {len(protein.peptide_ids)} peptide ids."
            ),
            referenced_ids=protein.peptide_ids,
            note="peptide-support answer is anchored to preserved peptide ids on the protein row",
        )

    peptide_ids = tuple(
        peptide.peptide_id
        for peptide in bundle.peptides
        if subject_id in peptide.site_keys
    )
    if peptide_ids:
        return ResultQuestionAnswer(
            question_id=question_spec.question_id,
            question_kind=question_spec.question_kind,
            status=ResultQuestionStatus.ANSWERED,
            subject_id=subject_id,
            answer_text=(
                f"{subject_id} is supported by {len(peptide_ids)} peptide observations."
            ),
            referenced_ids=peptide_ids,
            note="peptide-support answer is anchored to preserved peptide rows carrying the site id",
        )
    return _not_found(
        question_spec,
        f"{subject_id} has no preserved peptide support ids",
        note="no protein row or PTM-linked peptide rows matched the subject id",
    )


def _answer_what_samples_failed(
    result: ProteomicsStudyResult,
    question_spec: ResultQuestionSpec,
) -> ResultQuestionAnswer:
    bundle = result.interactive_result_bundle
    if bundle is None:
        return _not_found(
            question_spec,
            "interactive result bundle is missing",
            note="what_samples_failed requires sample and QC bundle rows",
        )

    failed_sample_ids = tuple(
        sample.sample_id
        for sample in bundle.samples
        if sample.outlier is True
    )
    failed_qc_ids = tuple(
        entry.qc_id
        for entry in bundle.qc_entries
        if entry.status.lower() in {"fail", "failed", "invalid"}
        or (entry.severity or "").lower() in {"fail", "failed", "invalid"}
    )
    referenced_ids = tuple(dict.fromkeys((*failed_sample_ids, *failed_qc_ids)))
    if not referenced_ids:
        return _not_found(
            question_spec,
            "result preserved no failed samples or failing qc rows",
            note="sample-failure answer only returns preserved sample or qc ids",
        )
    return ResultQuestionAnswer(
        question_id=question_spec.question_id,
        question_kind=question_spec.question_kind,
        status=ResultQuestionStatus.ANSWERED,
        subject_id=question_spec.subject_id,
        answer_text=(
            f"Result preserved {len(failed_sample_ids)} failed samples and "
            f"{len(failed_qc_ids)} failing QC rows."
        ),
        referenced_ids=referenced_ids,
        note="sample-failure answer is anchored to failed sample ids and qc entry ids",
    )


def _answer_what_weakens_claim(
    result: ProteomicsStudyResult,
    question_spec: ResultQuestionSpec,
) -> ResultQuestionAnswer:
    bundle = result.interactive_result_bundle
    subject_id = question_spec.subject_id or ""
    if bundle is not None:
        for protein in bundle.proteins:
            if subject_id not in {protein.object_id, protein.representative_protein_ref}:
                continue
            weakening_ids = tuple(dict.fromkeys((*protein.warning_codes, *protein.ptm_site_keys)))
            if weakening_ids:
                return ResultQuestionAnswer(
                    question_id=question_spec.question_id,
                    question_kind=question_spec.question_kind,
                    status=ResultQuestionStatus.ANSWERED,
                    subject_id=subject_id,
                    answer_text=f"{subject_id} is weakened by retained protein warnings.",
                    referenced_ids=weakening_ids,
                    note="claim-weakening answer is anchored to protein warning codes and linked ptm ids",
                )
        for site in bundle.ptm_sites:
            if site.site_key != subject_id:
                continue
            weakening_ids = tuple(dict.fromkeys((*site.warning_codes, *site.claim_ids)))
            if weakening_ids:
                return ResultQuestionAnswer(
                    question_id=question_spec.question_id,
                    question_kind=question_spec.question_kind,
                    status=ResultQuestionStatus.ANSWERED,
                    subject_id=subject_id,
                    answer_text=f"{subject_id} is weakened by retained PTM warnings.",
                    referenced_ids=weakening_ids,
                    note="claim-weakening answer is anchored to PTM warning codes and claim ids",
                )
        for pathway in bundle.pathways:
            if pathway.pathway_id != subject_id:
                continue
            weakening_ids = tuple(
                dict.fromkeys((*pathway.unresolved_member_ids, *pathway.supporting_protein_refs))
            )
            if weakening_ids:
                return ResultQuestionAnswer(
                    question_id=question_spec.question_id,
                    question_kind=question_spec.question_kind,
                    status=ResultQuestionStatus.ANSWERED,
                    subject_id=subject_id,
                    answer_text=f"{subject_id} is weakened by unresolved pathway support.",
                    referenced_ids=weakening_ids,
                    note="claim-weakening answer is anchored to unresolved member ids and supporting proteins",
                )

    for conclusion in result.biological_conclusions:
        if subject_id not in {conclusion.conclusion_id, conclusion.subject_id}:
            continue
        if conclusion.kind is ProteomicsStudyConclusionKind.REJECTED_CLAIM:
            return ResultQuestionAnswer(
                question_id=question_spec.question_id,
                question_kind=question_spec.question_kind,
                status=ResultQuestionStatus.ANSWERED,
                subject_id=subject_id,
                answer_text="Claim is weakened enough to remain rejected in the governed conclusions.",
                referenced_ids=(conclusion.conclusion_id, conclusion.subject_id),
                note="claim-weakening answer falls back to rejected conclusion ids when no richer bundle row is present",
            )
    return _not_found(
        question_spec,
        f"{subject_id} has no preserved weakening ids",
        note="what_weakens_claim requires warning, unresolved-member, or rejected-conclusion ids",
    )


def _not_found(
    question_spec: ResultQuestionSpec,
    answer_text: str,
    *,
    note: str,
) -> ResultQuestionAnswer:
    return ResultQuestionAnswer(
        question_id=question_spec.question_id,
        question_kind=question_spec.question_kind,
        status=ResultQuestionStatus.NOT_FOUND,
        subject_id=question_spec.subject_id,
        answer_text=answer_text,
        referenced_ids=(),
        note=note,
    )


__all__ = [
    "ResultQuestionAnswer",
    "ResultQuestionKind",
    "ResultQuestionSpec",
    "ResultQuestionStatus",
    "answer_result_question",
    "render_result_question_answers_tsv",
]
