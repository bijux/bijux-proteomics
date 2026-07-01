# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic question-answer queries over exported proteomics result artifacts."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.review.claims.result_query_artifacts import (
    _find_protein_card,
    _find_ptm_card,
    _load_result_artifact_context,
    _node_ids_for_entity,
    _protein_card_graph_node_ids,
    _ProteinCardArtifact,
    _QcRunArtifact,
    _ResultArtifactContext,
    _sample_to_failed_qc_runs,
)
from bijux_proteomics.review.claims.result_query_models import (
    ResultQueryAnswer,
    ResultQueryEvidenceLink,
    ResultQueryKind,
    ResultQueryReport,
    ResultQueryRequest,
    ResultQueryStatus,
    ResultQuerySummary,
)
from bijux_proteomics.review.claims.result_query_rendering import (
    render_result_query_answer_tsv,
    render_result_query_evidence_tsv,
    render_result_query_summary_tsv,
)


def build_result_query_report_from_artifacts(
    requests: tuple[ResultQueryRequest, ...],
    *,
    biological_report_dir: Path | None = None,
    ptm_report_dir: Path | None = None,
    run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
) -> ResultQueryReport:
    """Answer deterministic result questions from governed artifact directories."""

    context = _load_result_artifact_context(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    answers = tuple(
        _answer_result_query(
            request,
            context=context,
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
        )
        for request in requests
    )
    return ResultQueryReport(
        answers=answers,
        summary=ResultQuerySummary(
            query_count=len(answers),
            answered_query_count=sum(
                entry.status is ResultQueryStatus.ANSWERED for entry in answers
            ),
            not_found_query_count=sum(
                entry.status is ResultQueryStatus.NOT_FOUND for entry in answers
            ),
            unsupported_query_count=sum(
                entry.status is ResultQueryStatus.UNSUPPORTED for entry in answers
            ),
        ),
        note=(
            "result queries remain deterministic and answer only from governed "
            "artifact rows, explicit graph node ids, and QC ledgers without free-text guessing"
        ),
    )


def _answer_result_query(
    request: ResultQueryRequest,
    *,
    context: _ResultArtifactContext,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
) -> ResultQueryAnswer:
    if request.query_kind is ResultQueryKind.PROTEIN_SIGNIFICANCE:
        if biological_report_dir is None:
            return _unsupported_answer(
                request,
                "protein significance queries require --biological-report-dir",
            )
        return _answer_protein_significance_query(request, context=context)
    if request.query_kind is ResultQueryKind.PROTEIN_PEPTIDE_SUPPORT:
        if biological_report_dir is None:
            return _unsupported_answer(
                request,
                "protein peptide-support queries require --biological-report-dir",
            )
        return _answer_protein_peptide_support_query(request, context=context)
    if request.query_kind is ResultQueryKind.SAMPLE_QC_FAILURE:
        if biological_report_dir is None:
            return _unsupported_answer(
                request,
                "sample QC queries require --biological-report-dir for graph node mapping",
            )
        if not context.qc_runs:
            return _unsupported_answer(
                request,
                "sample QC queries require at least one --run-qc-assessment-tsv ledger",
            )
        return _answer_sample_qc_failure_query(request, context=context)
    if request.query_kind is ResultQueryKind.PTM_SITE_DOWNGRADE:
        if biological_report_dir is None or ptm_report_dir is None:
            return _unsupported_answer(
                request,
                "PTM downgrade queries require both --biological-report-dir and --ptm-report-dir",
            )
        return _answer_ptm_site_downgrade_query(request, context=context)
    raise ValueError(f"unsupported query kind: {request.query_kind.value}")


def _answer_protein_significance_query(
    request: ResultQueryRequest,
    *,
    context: _ResultArtifactContext,
) -> ResultQueryAnswer:
    card = _find_protein_card(context.protein_card_index, request.subject_id)
    if card is None:
        return _not_found_answer(
            request,
            "no governed protein card matched the requested protein subject",
        )
    warning_text = (
        "" if not card.warning_codes else f" Caveats: {', '.join(card.warning_codes)}."
    )
    adjusted_text = (
        "unadjusted-only"
        if card.adjusted_p_value is None
        else f"adjusted p-value {card.adjusted_p_value:.4g}"
    )
    answer_text = (
        f"Protein {card.representative_protein_ref} is "
        f"{'significant' if card.significant else 'not significant'} for "
        f"{card.condition_a} vs {card.condition_b} because biological protein card "
        f"{card.card_id} reports log2 fold change {card.log2_fold_change:.4g} and "
        f"{adjusted_text}.{warning_text}"
    )
    evidence_link = _protein_card_evidence_link(
        request.query_id,
        card,
        note="protein significance is anchored on the governed biological protein card",
    )
    return ResultQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=ResultQueryStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=card.representative_protein_ref,
        answer_text=answer_text,
        result_row_ids=(card.card_id, *card.graph_source_row_refs),
        graph_node_ids=_protein_card_graph_node_ids(card),
        evidence_links=(evidence_link,),
        note="answer derived from biological protein card statistics and graph provenance",
    )


def _answer_protein_peptide_support_query(
    request: ResultQueryRequest,
    *,
    context: _ResultArtifactContext,
) -> ResultQueryAnswer:
    card = _find_protein_card(context.protein_card_index, request.subject_id)
    if card is None:
        return _not_found_answer(
            request,
            "no governed protein card matched the requested protein subject",
        )
    peptide_text = ", ".join(card.peptides) if card.peptides else "no peptides"
    answer_text = (
        f"Protein {card.representative_protein_ref} is supported by {len(card.peptides)} "
        f"peptides on biological protein card {card.card_id}: {peptide_text}. "
        f"Unique peptide count is {card.unique_peptide_count} and shared peptide count is "
        f"{card.shared_peptide_count}."
    )
    evidence_link = _protein_card_evidence_link(
        request.query_id,
        card,
        note="protein peptide support is preserved directly on the governed biological protein card",
    )
    return ResultQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=ResultQueryStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=card.representative_protein_ref,
        answer_text=answer_text,
        result_row_ids=(card.card_id, *card.graph_source_row_refs),
        graph_node_ids=_protein_card_graph_node_ids(card),
        evidence_links=(evidence_link,),
        note="answer derived from peptide membership and graph-backed support node ids",
    )


def _answer_sample_qc_failure_query(
    request: ResultQueryRequest,
    *,
    context: _ResultArtifactContext,
) -> ResultQueryAnswer:
    sample_to_runs = _sample_to_failed_qc_runs(context)
    if request.subject_id is None:
        failed_sample_ids = tuple(sorted(sample_to_runs))
        if not failed_sample_ids:
            return ResultQueryAnswer(
                query_id=request.query_id,
                query_kind=request.query_kind,
                status=ResultQueryStatus.ANSWERED,
                subject_id=None,
                subject_label=None,
                answer_text="No samples failed QC on the provided QC ledgers.",
                result_row_ids=(),
                graph_node_ids=(),
                evidence_links=(),
                note="answer derived from provided QC assessment ledgers",
            )
        evidence_links = tuple(
            link
            for sample_id in failed_sample_ids
            for link in _sample_qc_evidence_links(
                request.query_id,
                sample_id=sample_id,
                qc_runs=sample_to_runs[sample_id],
                context=context,
            )
        )
        return ResultQueryAnswer(
            query_id=request.query_id,
            query_kind=request.query_kind,
            status=ResultQueryStatus.ANSWERED,
            subject_id=None,
            subject_label=None,
            answer_text=(
                "Samples failing QC: "
                + ", ".join(failed_sample_ids)
                + ". Each cited run row preserves the failing QC status and reason codes."
            ),
            result_row_ids=tuple(link.row_id for link in evidence_links),
            graph_node_ids=tuple(
                dict.fromkeys(
                    node_id
                    for link in evidence_links
                    for node_id in link.graph_node_ids
                )
            ),
            evidence_links=evidence_links,
            note="answer derived from failed run-level QC rows mapped onto exported graph sample and run nodes",
        )

    qc_runs = sample_to_runs.get(request.subject_id)
    if qc_runs is None:
        return _not_found_answer(
            request,
            "no failed QC rows matched the requested sample id",
        )
    evidence_links = _sample_qc_evidence_links(
        request.query_id,
        sample_id=request.subject_id,
        qc_runs=qc_runs,
        context=context,
    )
    reason_codes = sorted(
        {reason for run in qc_runs for reason in run.status_reason_codes}
    )
    answer_text = (
        f"Sample {request.subject_id} failed QC because its mapped run assessments "
        f"carry fail status with reason codes {', '.join(reason_codes) or 'none'}."
    )
    return ResultQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=ResultQueryStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=request.subject_id,
        answer_text=answer_text,
        result_row_ids=tuple(link.row_id for link in evidence_links),
        graph_node_ids=tuple(
            dict.fromkeys(
                node_id for link in evidence_links for node_id in link.graph_node_ids
            )
        ),
        evidence_links=evidence_links,
        note="answer derived from failed run-level QC rows mapped through exported graph run contexts",
    )


def _answer_ptm_site_downgrade_query(
    request: ResultQueryRequest,
    *,
    context: _ResultArtifactContext,
) -> ResultQueryAnswer:
    card = _find_ptm_card(context.ptm_card_index, request.subject_id)
    if card is None:
        return _not_found_answer(
            request,
            "no governed PTM evidence card matched the requested site subject",
        )
    protein_card = _find_protein_card(context.protein_card_index, card.protein_ref)
    graph_node_ids = tuple(
        dict.fromkeys(
            (
                *(
                    ()
                    if protein_card is None
                    else _protein_card_graph_node_ids(protein_card)
                ),
                *tuple(
                    _node_ids_for_entity(
                        context.graph_node_index,
                        entity_type="protein",
                        entity_ref=card.protein_ref,
                    )
                ),
            )
        )
    )
    if not graph_node_ids:
        return _unsupported_answer(
            request,
            (
                "no exported graph node anchor matched the PTM parent protein, "
                "so this site downgrade cannot be cited with governed graph ids"
            ),
        )
    downgrade_components = [
        *card.warning_codes,
        *card.mechanism_reason_codes,
    ]
    if card.protein_correction_status != "not_requested":
        downgrade_components.append(card.protein_correction_status)
    if not downgrade_components:
        downgrade_text = "no explicit downgrade codes were preserved on this site"
    else:
        downgrade_text = ", ".join(dict.fromkeys(downgrade_components))
    answer_text = (
        f"PTM site {card.site_key} is explained by PTM evidence card {card.card_id}. "
        f"Downgrade-related evidence is {downgrade_text}; reported log2 fold change is "
        f"{card.log2_fold_change:.4g}"
        + (
            ""
            if card.corrected_log2_fold_change is None
            else f", corrected log2 fold change is {card.corrected_log2_fold_change:.4g}"
        )
        + (
            "."
            if card.adjusted_p_value is None
            else f", adjusted p-value is {card.adjusted_p_value:.4g}."
        )
    )
    evidence_links = (
        ResultQueryEvidenceLink(
            query_id=request.query_id,
            result_surface="ptm_evidence_cards",
            row_id=card.card_id,
            graph_node_ids=graph_node_ids,
            source_row_refs=card.claim_ids,
            note="PTM downgrade answer cites the PTM evidence card and linked claim ids",
        ),
    )
    return ResultQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=ResultQueryStatus.ANSWERED,
        subject_id=request.subject_id,
        subject_label=card.site_key,
        answer_text=answer_text,
        result_row_ids=(card.card_id, *card.claim_ids),
        graph_node_ids=graph_node_ids,
        evidence_links=evidence_links,
        note="answer derived from PTM evidence card downgrade fields and parent protein graph anchors",
    )


def _unsupported_answer(
    request: ResultQueryRequest,
    note: str,
) -> ResultQueryAnswer:
    return ResultQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=ResultQueryStatus.UNSUPPORTED,
        subject_id=request.subject_id,
        subject_label=request.subject_id,
        answer_text=note,
        result_row_ids=(),
        graph_node_ids=(),
        evidence_links=(),
        note=note,
    )


def _not_found_answer(
    request: ResultQueryRequest,
    note: str,
) -> ResultQueryAnswer:
    return ResultQueryAnswer(
        query_id=request.query_id,
        query_kind=request.query_kind,
        status=ResultQueryStatus.NOT_FOUND,
        subject_id=request.subject_id,
        subject_label=request.subject_id,
        answer_text=note,
        result_row_ids=(),
        graph_node_ids=(),
        evidence_links=(),
        note=note,
    )


def _protein_card_evidence_link(
    query_id: str,
    card: _ProteinCardArtifact,
    *,
    note: str,
) -> ResultQueryEvidenceLink:
    return ResultQueryEvidenceLink(
        query_id=query_id,
        result_surface="biological_protein_cards",
        row_id=card.card_id,
        graph_node_ids=_protein_card_graph_node_ids(card),
        source_row_refs=card.graph_source_row_refs,
        note=note,
    )


def _sample_qc_evidence_links(
    query_id: str,
    *,
    sample_id: str,
    qc_runs: tuple[_QcRunArtifact, ...],
    context: _ResultArtifactContext,
) -> tuple[ResultQueryEvidenceLink, ...]:
    sample_node_ids = _node_ids_for_entity(
        context.graph_node_index,
        entity_type="sample",
        entity_ref=sample_id,
    )
    links: list[ResultQueryEvidenceLink] = []
    for run in qc_runs:
        run_node_ids = _node_ids_for_entity(
            context.graph_node_index,
            entity_type="run",
            entity_ref=run.run_id,
        )
        links.append(
            ResultQueryEvidenceLink(
                query_id=query_id,
                result_surface="qc_assessment",
                row_id=run.run_id,
                graph_node_ids=tuple(dict.fromkeys((*sample_node_ids, *run_node_ids))),
                source_row_refs=run.metric_keys,
                note=(
                    f"QC run {run.run_id} is {run.qc_status} with reason codes "
                    f"{', '.join(run.status_reason_codes) or 'none'}"
                ),
            )
        )
    return tuple(links)


__all__ = [
    "ResultQueryAnswer",
    "ResultQueryEvidenceLink",
    "ResultQueryKind",
    "ResultQueryReport",
    "ResultQueryRequest",
    "ResultQueryStatus",
    "ResultQuerySummary",
    "build_result_query_report_from_artifacts",
    "render_result_query_answer_tsv",
    "render_result_query_evidence_tsv",
    "render_result_query_summary_tsv",
]
