# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.io.formats.proteomics_formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_report_bundle,
    export_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    ResultSearchDocumentKind,
    ResultSearchField,
    build_biological_result_report_bundle,
    build_result_search_index_from_artifacts,
    export_biological_result_report_bundle,
    render_result_search_hit_tsv,
    render_result_search_summary_tsv,
    search_result_index,
)
from bijux_proteomics.workflow.exports.result_search_index import ResultSearchIndex


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _fasta_fixture("ptm_sites.fasta").read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _ptm_design_entries() -> tuple[ExperimentalDesignEntry, ...]:
    return tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )


def _build_real_result_search_index(tmp_path: Path) -> ResultSearchIndex:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    biological_report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture(
            "biological_report_complexes.tsv"
        ),
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    biological_dir = tmp_path / "biological_report"
    biological_manifest = export_biological_result_report_bundle(
        biological_report,
        biological_dir,
    )
    (biological_dir / "biological_report_manifest.json").write_text(
        biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    ptm_evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    ptm_features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    ptm_annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
    ptm_report = build_ptm_report_bundle(
        ptm_evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=ptm_features.accepted_records,
        design_entries=_ptm_design_entries(),
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        condition_a="control",
        condition_b="treated",
        annotation_records=ptm_annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )
    ptm_dir = tmp_path / "ptm_report"
    ptm_manifest = export_ptm_report_bundle(ptm_report, ptm_dir)
    (ptm_dir / "ptm_report_manifest.json").write_text(
        ptm_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    return cast(
        ResultSearchIndex,
        build_result_search_index_from_artifacts(
            biological_report_dir=biological_dir,
            ptm_report_dir=ptm_dir,
        ),
    )


def test_result_search_index_preserves_real_result_documents_and_postings(
    tmp_path: Path,
) -> None:
    index = _build_real_result_search_index(tmp_path)

    assert index.summary.document_count > 0
    assert index.summary.protein_document_count >= 3
    assert index.summary.ptm_site_document_count >= 3
    assert index.summary.pathway_document_count >= 1
    assert index.summary.peptide_document_count >= 3
    assert index.summary.indexed_token_count > 0
    assert any(
        document.document_kind is ResultSearchDocumentKind.PROTEIN
        for document in index.documents
    )
    assert any(
        document.document_kind is ResultSearchDocumentKind.PTM_SITE
        for document in index.documents
    )
    assert any(
        document.document_kind is ResultSearchDocumentKind.PATHWAY
        for document in index.documents
    )
    assert any(
        document.document_kind is ResultSearchDocumentKind.PEPTIDE
        for document in index.documents
    )
    assert "p04637" in index.token_postings
    assert "stress" in index.token_postings


def test_result_search_index_returns_object_ids_and_evidence_snippets(
    tmp_path: Path,
) -> None:
    index = _build_real_result_search_index(tmp_path)

    accession_report = search_result_index(index, "P04637")
    assert any(
        hit.document_kind is ResultSearchDocumentKind.PROTEIN
        and any(
            snippet.field is ResultSearchField.ACCESSION and "P04637" in snippet.text
            for snippet in hit.evidence_snippets
        )
        for hit in accession_report.hits
    )

    gene_report = search_result_index(index, "SIGA")
    assert any(
        hit.document_kind is ResultSearchDocumentKind.PROTEIN
        and ResultSearchField.GENE_SYMBOL in hit.matched_fields
        for hit in gene_report.hits
    )

    peptide_report = search_result_index(index, "SPEPTIDEK")
    assert any(
        hit.document_kind is ResultSearchDocumentKind.PEPTIDE
        and ResultSearchField.PEPTIDE_SEQUENCE in hit.matched_fields
        for hit in peptide_report.hits
    )

    site_report = search_result_index(index, "P11111:S5:Phospho")
    assert any(
        hit.document_kind is ResultSearchDocumentKind.PTM_SITE
        and hit.object_id == "P11111:S5:Phospho"
        for hit in site_report.hits
    )

    pathway_report = search_result_index(index, "Stress response pathway")
    assert any(
        hit.document_kind is ResultSearchDocumentKind.PATHWAY
        and ResultSearchField.PATHWAY in hit.matched_fields
        for hit in pathway_report.hits
    )

    annotation_query = next(
        term.text
        for document in index.documents
        for term in document.search_terms
        if term.field is ResultSearchField.ANNOTATION
    )
    annotation_report = search_result_index(index, annotation_query)
    assert any(
        ResultSearchField.ANNOTATION in hit.matched_fields
        for hit in annotation_report.hits
    )

    tier_query = next(
        term.text
        for document in index.documents
        if document.document_kind is ResultSearchDocumentKind.PROTEIN
        for term in document.search_terms
        if term.field is ResultSearchField.EVIDENCE_TIER
    )
    tier_report = search_result_index(index, tier_query)
    assert any(
        ResultSearchField.EVIDENCE_TIER in hit.matched_fields
        for hit in tier_report.hits
    )

    assert "indexed_document_count" in render_result_search_summary_tsv(pathway_report)
    assert "evidence_snippets" in render_result_search_hit_tsv(pathway_report)
