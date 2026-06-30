# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic question-answer queries over exported proteomics result artifacts."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

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


@dataclass(frozen=True)
class _ProteinCardArtifact:
    card_id: str
    graph_claim_node_id: str
    graph_subject_node_id: str
    graph_support_node_ids: tuple[str, ...]
    graph_source_row_refs: tuple[str, ...]
    protein_group_id: str
    representative_protein_ref: str
    protein_refs: tuple[str, ...]
    gene_symbol: str | None
    peptides: tuple[str, ...]
    peptide_count: int
    unique_peptide_count: int
    shared_peptide_count: int
    observed_sample_count: int
    missing_sample_count: int
    condition_a: str
    condition_b: str
    log2_fold_change: float
    adjusted_p_value: float | None
    significant: bool
    evidence_tier: str
    warning_codes: tuple[str, ...]


@dataclass(frozen=True)
class _GraphNodeArtifact:
    node_id: str
    entity_type: str
    entity_ref: str
    context_refs: tuple[str, ...]


@dataclass(frozen=True)
class _PtmCardArtifact:
    card_id: str
    site_key: str
    protein_ref: str
    condition_a: str
    condition_b: str
    adjusted_p_value: float | None
    log2_fold_change: float
    corrected_log2_fold_change: float | None
    localization_tier: str
    observed_sample_count: int
    protein_correction_status: str
    mechanism_reason_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class _QcRunArtifact:
    run_id: str
    qc_status: str
    status_reason_codes: tuple[str, ...]
    metric_keys: tuple[str, ...]
    messages: tuple[str, ...]


@dataclass(frozen=True)
class _ProteinCardLookupIndex:
    cards_by_card_id: dict[str, _ProteinCardArtifact]
    cards_by_protein_group_id: dict[str, _ProteinCardArtifact]
    cards_by_representative_protein_ref: dict[str, _ProteinCardArtifact]
    cards_by_gene_symbol: dict[str, tuple[_ProteinCardArtifact, ...]]
    cards_by_protein_ref: dict[str, tuple[_ProteinCardArtifact, ...]]


@dataclass(frozen=True)
class _GraphNodeLookupIndex:
    node_ids_by_entity: dict[tuple[str, str], tuple[str, ...]]
    sample_ids_by_run_id: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class _PtmCardLookupIndex:
    cards_by_card_id: dict[str, _PtmCardArtifact]
    cards_by_site_key: dict[str, _PtmCardArtifact]
    cards_by_claim_id: dict[str, tuple[_PtmCardArtifact, ...]]
    cards_by_protein_ref: dict[str, tuple[_PtmCardArtifact, ...]]


@dataclass(frozen=True)
class _ResultArtifactContext:
    protein_cards: tuple[_ProteinCardArtifact, ...]
    protein_card_index: _ProteinCardLookupIndex
    graph_nodes: tuple[_GraphNodeArtifact, ...]
    graph_node_index: _GraphNodeLookupIndex
    ptm_cards: tuple[_PtmCardArtifact, ...]
    ptm_card_index: _PtmCardLookupIndex
    qc_runs: tuple[_QcRunArtifact, ...]
    failed_qc_runs_by_sample: dict[str, tuple[_QcRunArtifact, ...]]


class _QcRunEntry(TypedDict):
    qc_status: str
    status_reason_codes: set[str]
    metric_keys: list[str]
    messages: list[str]


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


def _load_result_artifact_context(
    *,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
) -> _ResultArtifactContext:
    protein_cards: tuple[_ProteinCardArtifact, ...] = ()
    graph_nodes: tuple[_GraphNodeArtifact, ...] = ()
    if biological_report_dir is not None:
        protein_cards = _load_biological_protein_cards(
            biological_report_dir / "biological_protein_cards.tsv"
        )
        graph_nodes = _load_graph_nodes(
            biological_report_dir / "biological_evidence_graph_nodes.tsv"
        )

    ptm_cards: tuple[_PtmCardArtifact, ...] = ()
    if ptm_report_dir is not None:
        ptm_cards = _load_ptm_cards(ptm_report_dir / "ptm_evidence_cards.tsv")

    qc_runs = _load_qc_runs(run_qc_assessment_tsv_paths)
    graph_node_index = _build_graph_node_lookup_index(graph_nodes)
    return _ResultArtifactContext(
        protein_cards=protein_cards,
        protein_card_index=_build_protein_card_lookup_index(protein_cards),
        graph_nodes=graph_nodes,
        graph_node_index=graph_node_index,
        ptm_cards=ptm_cards,
        ptm_card_index=_build_ptm_card_lookup_index(ptm_cards),
        qc_runs=qc_runs,
        failed_qc_runs_by_sample=_build_failed_qc_runs_by_sample(
            qc_runs=qc_runs,
            graph_node_index=graph_node_index,
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


def _find_protein_card(
    index: _ProteinCardLookupIndex,
    subject_id: str | None,
) -> _ProteinCardArtifact | None:
    if subject_id is None:
        return None
    card = index.cards_by_card_id.get(subject_id)
    if card is not None:
        return card
    card = index.cards_by_protein_group_id.get(subject_id)
    if card is not None:
        return card
    card = index.cards_by_representative_protein_ref.get(subject_id)
    if card is not None:
        return card
    protein_ref_matches = index.cards_by_protein_ref.get(subject_id)
    if protein_ref_matches:
        return protein_ref_matches[0]
    gene_symbol_matches = index.cards_by_gene_symbol.get(subject_id)
    if gene_symbol_matches:
        return gene_symbol_matches[0]
    return None


def _find_ptm_card(
    index: _PtmCardLookupIndex,
    subject_id: str | None,
) -> _PtmCardArtifact | None:
    if subject_id is None:
        return None
    card = index.cards_by_card_id.get(subject_id)
    if card is not None:
        return card
    card = index.cards_by_site_key.get(subject_id)
    if card is not None:
        return card
    claim_matches = index.cards_by_claim_id.get(subject_id)
    if claim_matches:
        return claim_matches[0]
    return None


def _protein_card_graph_node_ids(
    card: _ProteinCardArtifact,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                card.graph_subject_node_id,
                card.graph_claim_node_id,
                *card.graph_support_node_ids,
            )
        )
    )


def _sample_to_failed_qc_runs(
    context: _ResultArtifactContext,
) -> dict[str, tuple[_QcRunArtifact, ...]]:
    return context.failed_qc_runs_by_sample


def _node_ids_for_entity(
    graph_node_index: _GraphNodeLookupIndex,
    *,
    entity_type: str,
    entity_ref: str,
) -> tuple[str, ...]:
    return graph_node_index.node_ids_by_entity.get((entity_type, entity_ref), ())


def _build_protein_card_lookup_index(
    cards: tuple[_ProteinCardArtifact, ...],
) -> _ProteinCardLookupIndex:
    cards_by_gene_symbol: dict[str, list[_ProteinCardArtifact]] = {}
    cards_by_protein_ref: dict[str, list[_ProteinCardArtifact]] = {}
    for card in cards:
        if card.gene_symbol is not None:
            cards_by_gene_symbol.setdefault(card.gene_symbol, []).append(card)
        for protein_ref in card.protein_refs:
            cards_by_protein_ref.setdefault(protein_ref, []).append(card)
    return _ProteinCardLookupIndex(
        cards_by_card_id={card.card_id: card for card in cards},
        cards_by_protein_group_id={card.protein_group_id: card for card in cards},
        cards_by_representative_protein_ref={
            card.representative_protein_ref: card for card in cards
        },
        cards_by_gene_symbol={
            gene_symbol: tuple(matches)
            for gene_symbol, matches in cards_by_gene_symbol.items()
        },
        cards_by_protein_ref={
            protein_ref: tuple(matches)
            for protein_ref, matches in cards_by_protein_ref.items()
        },
    )


def _build_graph_node_lookup_index(
    nodes: tuple[_GraphNodeArtifact, ...],
) -> _GraphNodeLookupIndex:
    node_ids_by_entity: dict[tuple[str, str], list[str]] = {}
    sample_ids_by_run_id: dict[str, tuple[str, ...]] = {}
    for node in nodes:
        node_ids_by_entity.setdefault((node.entity_type, node.entity_ref), []).append(
            node.node_id
        )
        if node.entity_type == "run":
            sample_ids_by_run_id[node.entity_ref] = tuple(
                context_ref.split(":", maxsplit=1)[1]
                for context_ref in node.context_refs
                if context_ref.startswith("sample:")
            )
    return _GraphNodeLookupIndex(
        node_ids_by_entity={
            key: tuple(node_ids) for key, node_ids in node_ids_by_entity.items()
        },
        sample_ids_by_run_id=sample_ids_by_run_id,
    )


def _build_ptm_card_lookup_index(
    cards: tuple[_PtmCardArtifact, ...],
) -> _PtmCardLookupIndex:
    cards_by_claim_id: dict[str, list[_PtmCardArtifact]] = {}
    cards_by_protein_ref: dict[str, list[_PtmCardArtifact]] = {}
    for card in cards:
        for claim_id in card.claim_ids:
            cards_by_claim_id.setdefault(claim_id, []).append(card)
        cards_by_protein_ref.setdefault(card.protein_ref, []).append(card)
    return _PtmCardLookupIndex(
        cards_by_card_id={card.card_id: card for card in cards},
        cards_by_site_key={card.site_key: card for card in cards},
        cards_by_claim_id={
            claim_id: tuple(matches) for claim_id, matches in cards_by_claim_id.items()
        },
        cards_by_protein_ref={
            protein_ref: tuple(matches)
            for protein_ref, matches in cards_by_protein_ref.items()
        },
    )


def _build_failed_qc_runs_by_sample(
    *,
    qc_runs: tuple[_QcRunArtifact, ...],
    graph_node_index: _GraphNodeLookupIndex,
) -> dict[str, tuple[_QcRunArtifact, ...]]:
    sample_to_runs: dict[str, list[_QcRunArtifact]] = {}
    for run in qc_runs:
        if run.qc_status != "fail":
            continue
        for sample_id in graph_node_index.sample_ids_by_run_id.get(run.run_id, ()):
            sample_to_runs.setdefault(sample_id, []).append(run)
    return {
        sample_id: tuple(sorted(runs, key=lambda entry: entry.run_id))
        for sample_id, runs in sample_to_runs.items()
    }


def _load_biological_protein_cards(path: Path) -> tuple[_ProteinCardArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _ProteinCardArtifact(
            card_id=row["card_id"],
            graph_claim_node_id=row["graph_claim_node_id"],
            graph_subject_node_id=row["graph_subject_node_id"],
            graph_support_node_ids=_split_multi(row["graph_support_node_ids"]),
            graph_source_row_refs=_split_multi(row["graph_source_row_refs"]),
            protein_group_id=row["protein_group_id"],
            representative_protein_ref=row["representative_protein_ref"],
            protein_refs=_split_multi(row["protein_refs"]),
            gene_symbol=_empty_to_none(row["gene_symbol"]),
            peptides=_split_multi(row["peptides"]),
            peptide_count=int(
                row.get("peptide_count", len(_split_multi(row["peptides"])))
            ),
            unique_peptide_count=int(row["unique_peptide_count"]),
            shared_peptide_count=int(row["shared_peptide_count"]),
            observed_sample_count=int(row.get("observed_sample_count", "0")),
            missing_sample_count=int(row.get("missing_sample_count", "0")),
            condition_a=row["condition_a"],
            condition_b=row["condition_b"],
            log2_fold_change=float(row["log2_fold_change"]),
            adjusted_p_value=_parse_optional_float(row["adjusted_p_value"]),
            significant=_parse_bool(row["significant"]),
            evidence_tier=row.get("evidence_tier", "review"),
            warning_codes=_split_multi(row.get("warning_codes", "")),
        )
        for row in rows
    )


def _load_graph_nodes(path: Path) -> tuple[_GraphNodeArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _GraphNodeArtifact(
            node_id=row["node_id"],
            entity_type=row["entity_type"],
            entity_ref=row["entity_ref"],
            context_refs=_split_pipe_refs(row["context_refs"]),
        )
        for row in rows
    )


def _load_ptm_cards(path: Path) -> tuple[_PtmCardArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _PtmCardArtifact(
            card_id=row["card_id"],
            site_key=row["site_key"],
            protein_ref=row["protein_ref"],
            condition_a=row.get("condition_a", ""),
            condition_b=row.get("condition_b", ""),
            adjusted_p_value=_parse_optional_float(row["adjusted_p_value"]),
            log2_fold_change=float(row["log2_fold_change"]),
            corrected_log2_fold_change=_parse_optional_float(
                row["corrected_log2_fold_change"]
            ),
            localization_tier=row.get("localization_tier", "unknown"),
            observed_sample_count=int(row.get("observed_sample_count", "0")),
            protein_correction_status=row["protein_correction_status"],
            mechanism_reason_codes=_split_multi(row["mechanism_reason_codes"]),
            warning_codes=_split_multi(row["warning_codes"]),
            claim_ids=_split_multi(row["claim_ids"]),
        )
        for row in rows
    )


def _load_qc_runs(paths: tuple[Path, ...]) -> tuple[_QcRunArtifact, ...]:
    runs_by_id: dict[str, _QcRunEntry] = {}
    for path in paths:
        for row in _read_tsv_rows(path):
            if row["scope"] != "run":
                continue
            run_id = row["entity_id"]
            run_entry = runs_by_id.setdefault(
                run_id,
                {
                    "qc_status": row["qc_status"],
                    "status_reason_codes": set(
                        _split_multi(row["status_reason_codes"])
                    ),
                    "metric_keys": [],
                    "messages": [],
                },
            )
            run_entry["status_reason_codes"].update(
                _split_multi(row["status_reason_codes"])
            )
            if row["metric_key"]:
                run_entry["metric_keys"].append(row["metric_key"])
            if row["message"]:
                run_entry["messages"].append(row["message"])
    return tuple(
        _QcRunArtifact(
            run_id=run_id,
            qc_status=str(entry["qc_status"]),
            status_reason_codes=tuple(sorted(entry["status_reason_codes"])),
            metric_keys=tuple(dict.fromkeys(entry["metric_keys"])),
            messages=tuple(dict.fromkeys(entry["messages"])),
        )
        for run_id, entry in sorted(runs_by_id.items())
    )


def _read_tsv_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        raise ValueError(f"required result artifact is missing: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle, delimiter="\t"))


def _split_multi(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part for part in value.split(";") if part)


def _split_pipe_refs(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part for part in value.split("|") if part)


def _empty_to_none(value: str) -> str | None:
    return None if value == "" else value


def _parse_bool(value: str) -> bool:
    return value.lower() == "true"


def _parse_optional_float(value: str) -> float | None:
    return None if value == "" else float(value)


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
