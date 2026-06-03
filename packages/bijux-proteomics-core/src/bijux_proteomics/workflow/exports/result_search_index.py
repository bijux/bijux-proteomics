# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Searchable indexes over governed proteomics result objects."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
import json
from pathlib import Path
import re
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.exports.interactive_result_bundle import (
    InteractiveResultBundle,
    InteractiveResultPeptide,
    InteractiveResultSourceKind,
    build_interactive_result_bundle_from_artifacts,
)
from bijux_proteomics_foundation import JsonModel


class ResultSearchDocumentKind(StrEnum):
    """Stable result-object families included in the search index."""

    PROTEIN = "protein"
    PTM_SITE = "ptm_site"
    PATHWAY = "pathway"
    PEPTIDE = "peptide"


class ResultSearchField(StrEnum):
    """Stable search-field families preserved on indexed result objects."""

    ACCESSION = "accession"
    GENE_SYMBOL = "gene_symbol"
    PEPTIDE_SEQUENCE = "peptide_sequence"
    SITE_KEY = "site_key"
    PATHWAY = "pathway"
    ANNOTATION = "annotation"
    EVIDENCE_TIER = "evidence_tier"


FIELD_MATCH_PRIORITIES: dict[ResultSearchField, int] = {
    ResultSearchField.SITE_KEY: 14,
    ResultSearchField.ACCESSION: 12,
    ResultSearchField.GENE_SYMBOL: 11,
    ResultSearchField.PEPTIDE_SEQUENCE: 10,
    ResultSearchField.PATHWAY: 9,
    ResultSearchField.ANNOTATION: 8,
    ResultSearchField.EVIDENCE_TIER: 7,
}


class ResultSearchTerm(JsonModel):
    """One searchable field value preserved on an indexed result object."""

    model_config = ConfigDict(extra="forbid")

    field: ResultSearchField
    text: str = Field(..., min_length=1)


class ResultSearchDocument(JsonModel):
    """One indexed result object with stable search terms."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., min_length=1)
    object_id: str = Field(..., min_length=1)
    document_kind: ResultSearchDocumentKind
    title: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    search_terms: tuple[ResultSearchTerm, ...] = Field(default_factory=tuple)


class ResultSearchIndexSummary(JsonModel):
    """Compact summary over one result-object search index."""

    model_config = ConfigDict(extra="forbid")

    document_count: int = Field(..., ge=0)
    protein_document_count: int = Field(..., ge=0)
    ptm_site_document_count: int = Field(..., ge=0)
    pathway_document_count: int = Field(..., ge=0)
    peptide_document_count: int = Field(..., ge=0)
    indexed_token_count: int = Field(..., ge=0)


class ResultSearchIndex(JsonModel):
    """Searchable index over governed result objects."""

    model_config = ConfigDict(extra="forbid")

    documents: tuple[ResultSearchDocument, ...] = Field(default_factory=tuple)
    token_postings: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    summary: ResultSearchIndexSummary
    note: str = Field(..., min_length=1)


class _ArtifactSourceContext(TypedDict):
    report_dir: Path
    artifact_paths: dict[str, str]


class ResultSearchSnippet(JsonModel):
    """One evidence snippet explaining why a result object matched a query."""

    model_config = ConfigDict(extra="forbid")

    field: ResultSearchField
    text: str = Field(..., min_length=1)


class ResultSearchHit(JsonModel):
    """One search hit over governed result objects."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., min_length=1)
    object_id: str = Field(..., min_length=1)
    document_kind: ResultSearchDocumentKind
    title: str = Field(..., min_length=1)
    matched_fields: tuple[ResultSearchField, ...] = Field(default_factory=tuple)
    evidence_snippets: tuple[ResultSearchSnippet, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    score: int = Field(..., ge=0)


class ResultSearchReportSummary(JsonModel):
    """Compact summary over one governed result search."""

    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(..., min_length=1)
    indexed_document_count: int = Field(..., ge=0)
    indexed_token_count: int = Field(..., ge=0)
    hit_count: int = Field(..., ge=0)
    truncated: bool = False


class ResultSearchReport(JsonModel):
    """Search results over governed result-object indexes."""

    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(..., min_length=1)
    normalized_tokens: tuple[str, ...] = Field(default_factory=tuple)
    hits: tuple[ResultSearchHit, ...] = Field(default_factory=tuple)
    summary: ResultSearchReportSummary
    note: str = Field(..., min_length=1)


def build_result_search_index_from_artifacts(
    *,
    biological_report_dir: Path | None = None,
    ptm_report_dir: Path | None = None,
) -> ResultSearchIndex:
    """Build a searchable index over governed biological and PTM result objects."""

    if biological_report_dir is None and ptm_report_dir is None:
        raise ValueError(
            "result search index requires at least one governed biological report or PTM report input"
        )
    bundle = build_interactive_result_bundle_from_artifacts(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
    )
    artifact_context = _artifact_context_by_source_kind(bundle)
    protein_annotation_terms = _load_protein_annotation_terms(artifact_context)
    ptm_annotation_terms = _load_ptm_annotation_terms(artifact_context)
    pathway_names_by_id = {
        pathway.pathway_id: pathway.pathway_name or pathway.pathway_id
        for pathway in bundle.pathways
    }
    peptides_by_id = {
        peptide.peptide_id: peptide for peptide in bundle.peptides
    }
    documents = tuple(
        sorted(
            (
                *_build_protein_documents(
                    bundle=bundle,
                    peptides_by_id=peptides_by_id,
                    pathway_names_by_id=pathway_names_by_id,
                    protein_annotation_terms=protein_annotation_terms,
                ),
                *_build_ptm_site_documents(
                    bundle=bundle,
                    ptm_annotation_terms=ptm_annotation_terms,
                ),
                *_build_pathway_documents(bundle=bundle),
                *_build_peptide_documents(bundle=bundle),
            ),
            key=lambda entry: (entry.document_kind.value, entry.document_id),
        )
    )
    token_postings = _build_token_postings(documents)
    return ResultSearchIndex(
        documents=documents,
        token_postings=token_postings,
        summary=ResultSearchIndexSummary(
            document_count=len(documents),
            protein_document_count=sum(
                entry.document_kind is ResultSearchDocumentKind.PROTEIN
                for entry in documents
            ),
            ptm_site_document_count=sum(
                entry.document_kind is ResultSearchDocumentKind.PTM_SITE
                for entry in documents
            ),
            pathway_document_count=sum(
                entry.document_kind is ResultSearchDocumentKind.PATHWAY
                for entry in documents
            ),
            peptide_document_count=sum(
                entry.document_kind is ResultSearchDocumentKind.PEPTIDE
                for entry in documents
            ),
            indexed_token_count=len(token_postings),
        ),
        note=(
            "result search indexes preserve explicit searchable terms and inverted "
            "token postings over governed result objects instead of relying on filename grep"
        ),
    )


def search_result_index(
    index: ResultSearchIndex,
    query_text: str,
    *,
    limit: int = 20,
) -> ResultSearchReport:
    """Search one governed result-object index and return object ids with snippets."""

    normalized_query = _normalize_phrase(query_text)
    if not normalized_query:
        raise ValueError("search query must not be empty")
    if limit < 1:
        raise ValueError("search limit must be at least 1")
    query_tokens = _tokenize_search_text(query_text)
    candidate_ids = _candidate_document_ids(index, normalized_query, query_tokens)
    document_by_id = {entry.document_id: entry for entry in index.documents}
    scored_hits = [
        _build_search_hit(
            document_by_id[document_id],
            normalized_query=normalized_query,
            query_tokens=query_tokens,
        )
        for document_id in candidate_ids
    ]
    hits = tuple(
        sorted(
            (entry for entry in scored_hits if entry is not None),
            key=lambda entry: (-entry.score, entry.document_kind.value, entry.title),
        )
    )
    limited_hits = hits[:limit]
    return ResultSearchReport(
        query_text=query_text,
        normalized_tokens=query_tokens,
        hits=limited_hits,
        summary=ResultSearchReportSummary(
            query_text=query_text,
            indexed_document_count=index.summary.document_count,
            indexed_token_count=index.summary.indexed_token_count,
            hit_count=len(limited_hits),
            truncated=len(hits) > limit,
        ),
        note=(
            "result search returns indexed object ids and matched evidence snippets "
            "from governed result surfaces without free-text guessing"
        ),
    )


def render_result_search_summary_tsv(report: ResultSearchReport) -> str:
    """Render a compact TSV summary over one governed result search."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "query_text",
            "indexed_document_count",
            "indexed_token_count",
            "hit_count",
            "truncated",
        )
    )
    writer.writerow(
        (
            report.summary.query_text,
            report.summary.indexed_document_count,
            report.summary.indexed_token_count,
            report.summary.hit_count,
            str(report.summary.truncated).lower(),
        )
    )
    return buffer.getvalue()


def render_result_search_hit_tsv(report: ResultSearchReport) -> str:
    """Render governed result search hits as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "document_id",
            "object_id",
            "document_kind",
            "title",
            "matched_fields",
            "evidence_snippets",
            "graph_node_ids",
            "score",
        )
    )
    for hit in report.hits:
        writer.writerow(
            (
                hit.document_id,
                hit.object_id,
                hit.document_kind.value,
                hit.title,
                ";".join(field.value for field in hit.matched_fields),
                "; ".join(
                    f"{snippet.field.value}: {snippet.text}"
                    for snippet in hit.evidence_snippets
                ),
                ";".join(hit.graph_node_ids),
                hit.score,
            )
        )
    return buffer.getvalue()


def _artifact_context_by_source_kind(
    bundle: InteractiveResultBundle,
) -> dict[InteractiveResultSourceKind, _ArtifactSourceContext]:
    context: dict[InteractiveResultSourceKind, _ArtifactSourceContext] = {}
    for source_report in bundle.source_reports:
        context[source_report.source_kind] = {
            "report_dir": Path(source_report.report_dir),
            "artifact_paths": source_report.artifact_paths,
        }
    return context


def _load_protein_annotation_terms(
    artifact_context: dict[InteractiveResultSourceKind, _ArtifactSourceContext],
) -> dict[str, tuple[str, ...]]:
    context = artifact_context.get(InteractiveResultSourceKind.BIOLOGICAL_REPORT)
    if context is None:
        return {}
    grouped: dict[str, set[str]] = {}
    for row in _read_optional_rows(context, "annotation_tsv"):
        terms = {
            value
            for value in (
                row.get("description", ""),
                row.get("organism", ""),
                row.get("annotation_identifier", ""),
                row.get("annotation_source", ""),
                row.get("annotation_status", ""),
                row.get("source_identifier", ""),
                row.get("gene_symbol", ""),
            )
            if value.strip()
        }
        terms.update(_extract_json_text_values(row.get("custom_annotation", "")))
        keys = (
            row.get("protein_ref", "").strip(),
            row.get("input_protein_ref", "").strip(),
            *(
                alias.strip()
                for alias in row.get("accession_aliases", "").split(";")
                if alias.strip()
            ),
        )
        for key in keys:
            if key:
                grouped.setdefault(key, set()).update(terms)
    return {
        key: tuple(sorted(values))
        for key, values in grouped.items()
    }


def _load_ptm_annotation_terms(
    artifact_context: dict[InteractiveResultSourceKind, _ArtifactSourceContext],
) -> dict[str, tuple[str, ...]]:
    context = artifact_context.get(InteractiveResultSourceKind.PTM_REPORT)
    if context is None:
        return {}
    grouped: dict[str, set[str]] = {}
    for row in _read_optional_rows(context, "evidence_card_tsv"):
        terms = {
            value
            for value in (
                row.get("mechanism_class", ""),
                row.get("localization_tier", ""),
                row.get("protein_correction_status", ""),
                row.get("ortholog_conservation_status", ""),
            )
            if value.strip()
        }
        for field_name in (
            "functional_regions",
            "regulators",
            "crosstalk_shared_pathways",
            "ortholog_target_site_keys",
            "ortholog_target_protein_refs",
        ):
            terms.update(
                value.strip()
                for value in row.get(field_name, "").split(";")
                if value.strip()
            )
        grouped.setdefault(row["site_key"], set()).update(terms)
    return {
        key: tuple(sorted(values))
        for key, values in grouped.items()
    }


def _build_protein_documents(
    *,
    bundle: InteractiveResultBundle,
    peptides_by_id: dict[str, InteractiveResultPeptide],
    pathway_names_by_id: dict[str, str],
    protein_annotation_terms: dict[str, tuple[str, ...]],
) -> tuple[ResultSearchDocument, ...]:
    documents: list[ResultSearchDocument] = []
    for protein in bundle.proteins:
        terms: list[ResultSearchTerm] = [
            ResultSearchTerm(
                field=ResultSearchField.ACCESSION,
                text=protein.representative_protein_ref,
            )
        ]
        terms.extend(
            ResultSearchTerm(field=ResultSearchField.ACCESSION, text=value)
            for value in protein.protein_refs
            if value != protein.representative_protein_ref
        )
        if protein.gene_symbol is not None:
            terms.append(
                ResultSearchTerm(
                    field=ResultSearchField.GENE_SYMBOL,
                    text=protein.gene_symbol,
                )
            )
        for peptide_id in protein.peptide_ids:
            peptide = peptides_by_id.get(peptide_id)
            if peptide is None:
                continue
            if peptide.sequence:
                terms.append(
                    ResultSearchTerm(
                        field=ResultSearchField.PEPTIDE_SEQUENCE,
                        text=peptide.sequence,
                    )
                )
        for site_key in protein.ptm_site_keys:
            terms.append(
                ResultSearchTerm(
                    field=ResultSearchField.SITE_KEY,
                    text=site_key,
                )
            )
        for pathway_id in protein.pathway_ids:
            terms.append(
                ResultSearchTerm(
                    field=ResultSearchField.PATHWAY,
                    text=pathway_id,
                )
            )
            pathway_name = pathway_names_by_id.get(pathway_id)
            if pathway_name is not None:
                terms.append(
                    ResultSearchTerm(
                        field=ResultSearchField.PATHWAY,
                        text=pathway_name,
                    )
                )
        annotation_terms = {
            term
            for protein_ref in (protein.representative_protein_ref, *protein.protein_refs)
            for term in protein_annotation_terms.get(protein_ref, ())
        }
        terms.extend(
            ResultSearchTerm(field=ResultSearchField.ANNOTATION, text=term)
            for term in sorted(annotation_terms)
        )
        if protein.evidence_tier is not None:
            terms.append(
                ResultSearchTerm(
                    field=ResultSearchField.EVIDENCE_TIER,
                    text=protein.evidence_tier,
                )
            )
        documents.append(
            ResultSearchDocument(
                document_id=f"protein:{protein.object_id}",
                object_id=protein.object_id,
                document_kind=ResultSearchDocumentKind.PROTEIN,
                title=protein.gene_symbol or protein.representative_protein_ref,
                source_surface="interactive_result_bundle:proteins",
                graph_node_ids=protein.graph_node_ids,
                search_terms=_deduplicate_terms(tuple(terms)),
            )
        )
    return tuple(documents)


def _build_ptm_site_documents(
    *,
    bundle: InteractiveResultBundle,
    ptm_annotation_terms: dict[str, tuple[str, ...]],
) -> tuple[ResultSearchDocument, ...]:
    documents: list[ResultSearchDocument] = []
    peptides_by_site_key: dict[str, set[str]] = {}
    for peptide in bundle.peptides:
        peptide_values = {
            value
            for value in (
                peptide.sequence,
                peptide.localized_peptide,
                peptide.canonical_peptide,
            )
            if value
        }
        for site_key in peptide.site_keys:
            peptides_by_site_key.setdefault(site_key, set()).update(peptide_values)
    for site in bundle.ptm_sites:
        terms: list[ResultSearchTerm] = [
            ResultSearchTerm(field=ResultSearchField.SITE_KEY, text=site.site_key),
            ResultSearchTerm(field=ResultSearchField.ACCESSION, text=site.protein_ref),
        ]
        if site.modification_name and site.residue and site.position is not None:
            terms.append(
                ResultSearchTerm(
                    field=ResultSearchField.SITE_KEY,
                    text=f"{site.protein_ref}:{site.residue}{site.position}:{site.modification_name}",
                )
            )
        terms.extend(
            ResultSearchTerm(field=ResultSearchField.PEPTIDE_SEQUENCE, text=value)
            for value in sorted(peptides_by_site_key.get(site.site_key, set()))
        )
        terms.extend(
            ResultSearchTerm(field=ResultSearchField.ANNOTATION, text=term)
            for term in ptm_annotation_terms.get(site.site_key, ())
        )
        documents.append(
            ResultSearchDocument(
                document_id=f"ptm_site:{site.site_key}",
                object_id=site.site_key,
                document_kind=ResultSearchDocumentKind.PTM_SITE,
                title=site.site_key,
                source_surface="interactive_result_bundle:ptm_sites",
                graph_node_ids=(),
                search_terms=_deduplicate_terms(tuple(terms)),
            )
        )
    return tuple(documents)


def _build_pathway_documents(
    *,
    bundle: InteractiveResultBundle,
) -> tuple[ResultSearchDocument, ...]:
    return tuple(
        ResultSearchDocument(
            document_id=f"pathway:{pathway.pathway_id}",
            object_id=pathway.pathway_id,
            document_kind=ResultSearchDocumentKind.PATHWAY,
            title=pathway.pathway_name or pathway.pathway_id,
            source_surface="interactive_result_bundle:pathways",
            graph_node_ids=tuple(
                sorted(
                    node.node_id
                    for node in bundle.graph_nodes
                    if node.entity_ref in (pathway.pathway_id, pathway.source_accession or "")
                )
            ),
            search_terms=_deduplicate_terms(
                tuple(
                    term
                    for term in (
                        ResultSearchTerm(
                            field=ResultSearchField.PATHWAY,
                            text=pathway.pathway_id,
                        ),
                        None
                        if pathway.pathway_name is None
                        else ResultSearchTerm(
                            field=ResultSearchField.PATHWAY,
                            text=pathway.pathway_name,
                        ),
                        None
                        if pathway.source_accession is None
                        else ResultSearchTerm(
                            field=ResultSearchField.PATHWAY,
                            text=pathway.source_accession,
                        ),
                        None
                        if pathway.source_name is None
                        else ResultSearchTerm(
                            field=ResultSearchField.ANNOTATION,
                            text=pathway.source_name,
                        ),
                        *(
                            ResultSearchTerm(
                                field=ResultSearchField.ACCESSION,
                                text=value,
                            )
                            for value in pathway.supporting_protein_refs
                        ),
                    )
                    if term is not None
                )
            ),
        )
        for pathway in bundle.pathways
    )


def _build_peptide_documents(
    *,
    bundle: InteractiveResultBundle,
) -> tuple[ResultSearchDocument, ...]:
    documents: list[ResultSearchDocument] = []
    for peptide in bundle.peptides:
        terms: list[ResultSearchTerm] = [
            ResultSearchTerm(
                field=ResultSearchField.PEPTIDE_SEQUENCE,
                text=peptide.sequence,
            )
        ]
        if peptide.localized_peptide is not None:
            terms.append(
                ResultSearchTerm(
                    field=ResultSearchField.PEPTIDE_SEQUENCE,
                    text=peptide.localized_peptide,
                )
            )
        if peptide.canonical_peptide is not None:
            terms.append(
                ResultSearchTerm(
                    field=ResultSearchField.PEPTIDE_SEQUENCE,
                    text=peptide.canonical_peptide,
                )
            )
        terms.extend(
            ResultSearchTerm(field=ResultSearchField.ACCESSION, text=value)
            for value in peptide.protein_refs
        )
        terms.extend(
            ResultSearchTerm(field=ResultSearchField.SITE_KEY, text=value)
            for value in peptide.site_keys
        )
        terms.extend(
            ResultSearchTerm(field=ResultSearchField.ANNOTATION, text=value)
            for value in peptide.modification_names
        )
        documents.append(
            ResultSearchDocument(
                document_id=f"peptide:{peptide.peptide_id}",
                object_id=peptide.peptide_id,
                document_kind=ResultSearchDocumentKind.PEPTIDE,
                title=peptide.localized_peptide or peptide.canonical_peptide or peptide.sequence,
                source_surface=f"interactive_result_bundle:{peptide.source_surface}",
                graph_node_ids=(),
                search_terms=_deduplicate_terms(tuple(terms)),
            )
        )
    return tuple(documents)


def _build_token_postings(
    documents: tuple[ResultSearchDocument, ...],
) -> dict[str, tuple[str, ...]]:
    postings: dict[str, set[str]] = {}
    for document in documents:
        document_tokens = {
            token
            for term in document.search_terms
            for token in _index_terms_for_text(term.text)
        }
        for token in document_tokens:
            postings.setdefault(token, set()).add(document.document_id)
    return {
        token: tuple(sorted(document_ids))
        for token, document_ids in sorted(postings.items())
    }


def _candidate_document_ids(
    index: ResultSearchIndex,
    normalized_query: str,
    query_tokens: tuple[str, ...],
) -> tuple[str, ...]:
    postings = index.token_postings
    exact_documents = set(postings.get(normalized_query, ()))
    token_documents = [
        set(postings.get(token, ()))
        for token in query_tokens
    ]
    if token_documents:
        candidates = set.intersection(*token_documents)
    else:
        candidates = set()
    candidates.update(exact_documents)
    return tuple(sorted(candidates))


def _build_search_hit(
    document: ResultSearchDocument,
    *,
    normalized_query: str,
    query_tokens: tuple[str, ...],
) -> ResultSearchHit | None:
    matched_fields: set[ResultSearchField] = set()
    snippets: list[ResultSearchSnippet] = []
    score = 0
    if normalized_query:
        if _normalize_phrase(document.object_id) == normalized_query:
            score += 120
        if _normalize_phrase(document.title) == normalized_query:
            score += 60
    for term in document.search_terms:
        normalized_text = _normalize_phrase(term.text)
        term_tokens = set(_tokenize_search_text(term.text))
        exact_match = bool(normalized_query) and normalized_text == normalized_query
        phrase_match = bool(normalized_query and normalized_query in normalized_text)
        token_match = bool(query_tokens) and set(query_tokens).issubset(term_tokens)
        if not phrase_match and not token_match:
            continue
        matched_fields.add(term.field)
        snippets.append(
            ResultSearchSnippet(field=term.field, text=term.text)
        )
        if exact_match:
            score += 40
        elif phrase_match:
            score += 8
        score += FIELD_MATCH_PRIORITIES[term.field]
        score += len(set(query_tokens).intersection(term_tokens))
    if not snippets:
        return None
    deduplicated_snippets = tuple(
        snippet
        for _, snippet in sorted(
            {
                (snippet.field.value, snippet.text): snippet
                for snippet in snippets
            }.items()
        )
    )
    return ResultSearchHit(
        document_id=document.document_id,
        object_id=document.object_id,
        document_kind=document.document_kind,
        title=document.title,
        matched_fields=tuple(sorted(matched_fields, key=lambda entry: entry.value)),
        evidence_snippets=deduplicated_snippets,
        graph_node_ids=document.graph_node_ids,
        score=score,
    )


def _read_optional_rows(
    context: _ArtifactSourceContext,
    artifact_key: str,
) -> tuple[dict[str, str], ...]:
    artifact_paths = context["artifact_paths"]
    relative_path = artifact_paths.get(artifact_key)
    if not isinstance(relative_path, str) or not relative_path:
        return ()
    path = context["report_dir"] / relative_path
    if not path.exists():
        return ()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path.name!r} must include a header row")
        return tuple(
            {
                str(key or "").strip(): str(value or "").strip()
                for key, value in row.items()
            }
            for row in reader
        )


def _extract_json_text_values(raw_value: str) -> tuple[str, ...]:
    normalized = raw_value.strip()
    if not normalized:
        return ()
    try:
        payload = json.loads(normalized)
    except json.JSONDecodeError:
        return (normalized,)
    values: set[str] = set()
    _collect_json_strings(payload, values)
    return tuple(sorted(values))


def _collect_json_strings(payload: object, values: set[str]) -> None:
    if isinstance(payload, str):
        normalized = payload.strip()
        if normalized:
            values.add(normalized)
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            _collect_json_strings(key, values)
            _collect_json_strings(value, values)
        return
    if isinstance(payload, (list, tuple, set)):
        for value in payload:
            _collect_json_strings(value, values)


def _deduplicate_terms(
    terms: tuple[ResultSearchTerm, ...],
) -> tuple[ResultSearchTerm, ...]:
    return tuple(
        term
        for _, term in sorted(
            {
                (term.field.value, term.text): term
                for term in terms
                if term.text.strip()
            }.items()
        )
    )


def _index_terms_for_text(text: str) -> tuple[str, ...]:
    normalized_phrase = _normalize_phrase(text)
    tokens = _tokenize_search_text(text)
    values = {
        normalized_phrase,
        *tokens,
    }
    return tuple(sorted(value for value in values if value))


def _normalize_phrase(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _tokenize_search_text(text: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token
    )


__all__ = [
    "ResultSearchDocument",
    "ResultSearchDocumentKind",
    "ResultSearchField",
    "ResultSearchHit",
    "ResultSearchIndex",
    "ResultSearchIndexSummary",
    "ResultSearchReport",
    "ResultSearchReportSummary",
    "ResultSearchSnippet",
    "ResultSearchTerm",
    "build_result_search_index_from_artifacts",
    "render_result_search_hit_tsv",
    "render_result_search_summary_tsv",
    "search_result_index",
]
