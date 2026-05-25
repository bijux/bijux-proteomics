# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.interpretation.regulator_inference import (
    RegulatorEvidenceRecord,
    RegulatorEvidenceType,
)
from bijux_proteomics_knowledge.kinases.substrates import (
    KinaseSubstrateMatchType,
    KinaseSubstrateResolutionEntry,
    render_kinase_substrate_resolution_tsv,
    resolve_kinase_substrates,
)


def test_resolve_kinase_substrates_prefers_exact_accession_site_to_gene_equivalent() -> None:
    report = resolve_kinase_substrates(
        (
            "P04637:S15:Phospho",
            "TP53:S15:Phospho",
            "TP53:S20:Phospho",
        ),
        _annotation_pack(),
    )

    assert report.entries == (
        KinaseSubstrateResolutionEntry(
            site_id="P04637:S15:Phospho",
            kinase="MAPK1",
            match_type=KinaseSubstrateMatchType.EXACT_ACCESSION_SITE,
            annotation_source="PSP:0001",
        ),
        KinaseSubstrateResolutionEntry(
            site_id="TP53:S15:Phospho",
            kinase="MAPK1",
            match_type=KinaseSubstrateMatchType.GENE_SYMBOL_SITE_EQUIVALENT,
            annotation_source="PSP:0001",
        ),
    )
    assert report.summary.site_count == 3
    assert report.summary.resolved_site_count == 2
    assert report.summary.exact_match_count == 1
    assert report.summary.gene_symbol_match_count == 1
    assert report.summary.annotation_identifier_match_count == 0


def test_resolve_kinase_substrates_supports_annotation_identifiers_and_tsv_output() -> None:
    report = resolve_kinase_substrates(
        (
            "UniProtKB:P04637:S15:Phospho",
            "P04637:S15:Phospho",
        ),
        _annotation_pack(),
    )

    assert report.entries == (
        KinaseSubstrateResolutionEntry(
            site_id="P04637:S15:Phospho",
            kinase="MAPK1",
            match_type=KinaseSubstrateMatchType.EXACT_ACCESSION_SITE,
            annotation_source="PSP:0001",
        ),
        KinaseSubstrateResolutionEntry(
            site_id="UniProtKB:P04637:S15:Phospho",
            kinase="MAPK1",
            match_type=KinaseSubstrateMatchType.ANNOTATION_IDENTIFIER_SITE_EQUIVALENT,
            annotation_source="PSP:0001",
        ),
    )

    rendered = render_kinase_substrate_resolution_tsv(report.entries)

    assert rendered.splitlines() == [
        "site_id\tkinase\tmatch_type\tannotation_source",
        "P04637:S15:Phospho\tMAPK1\texact_accession_site\tPSP:0001",
        "UniProtKB:P04637:S15:Phospho\tMAPK1\tannotation_identifier_site_equivalent\tPSP:0001",
    ]


def _annotation_pack() -> AnnotationPack:
    return AnnotationPack(
        source_path="test-kinase-pack.json",
        pack_name="kinase-substrate-test-pack",
        protein_features=(
            ProteinAnnotationRecord(
                protein_ref="P04637",
                gene_symbol="TP53",
                organism="human",
                annotation_identifier="UniProtKB:P04637",
                description="tumor protein p53",
            ),
        ),
        kinase_substrates=(
            RegulatorEvidenceRecord(
                regulator="MAPK1",
                evidence_type=RegulatorEvidenceType.KINASE_SUBSTRATE,
                site_key="P04637:S15:Phospho",
                source_name="PhosphoSitePlus",
                source_accession="PSP:0001",
            ),
        ),
        summary=AnnotationPackSummary(
            protein_feature_count=1,
            pathway_count=0,
            complex_count=0,
            compartment_count=0,
            drug_target_count=0,
            disease_term_count=0,
            kinase_substrate_count=1,
            ortholog_count=0,
        ),
    )
