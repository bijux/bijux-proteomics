# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
)
from bijux_proteomics.interpretation.ortholog_mapping import OrthologRecord
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics_knowledge.orthologs.mapping import (
    CrossSpeciesOrthologAmbiguity,
    CrossSpeciesOrthologEvidenceStatus,
    map_cross_species_orthologs,
    render_cross_species_ortholog_tsv,
)


def test_map_cross_species_orthologs_preserves_one_to_many_and_many_to_many_edges() -> None:
    report = map_cross_species_orthologs(
        ("P11111", "KIN1"),
        _ortholog_pack(),
        source_species="Homo sapiens",
        target_species="Mus musculus",
    )

    assert report.entries == (
        _entry(
            source_protein="P11111",
            target_ortholog="M11111",
            evidence_status=CrossSpeciesOrthologEvidenceStatus.EXACT_ACCESSION,
            ambiguity=CrossSpeciesOrthologAmbiguity.ONE_TO_MANY,
        ),
        _entry(
            source_protein="P11111",
            target_ortholog="M11112",
            evidence_status=CrossSpeciesOrthologEvidenceStatus.EXACT_ACCESSION,
            ambiguity=CrossSpeciesOrthologAmbiguity.ONE_TO_MANY,
        ),
        _entry(
            source_protein="P22222",
            target_ortholog="M22221",
            evidence_status=CrossSpeciesOrthologEvidenceStatus.AMBIGUOUS_SOURCE_IDENTIFIER,
            ambiguity=CrossSpeciesOrthologAmbiguity.MANY_TO_MANY,
        ),
        _entry(
            source_protein="P22222",
            target_ortholog="M22222",
            evidence_status=CrossSpeciesOrthologEvidenceStatus.AMBIGUOUS_SOURCE_IDENTIFIER,
            ambiguity=CrossSpeciesOrthologAmbiguity.MANY_TO_MANY,
        ),
        _entry(
            source_protein="P33333",
            target_ortholog="M22221",
            evidence_status=CrossSpeciesOrthologEvidenceStatus.AMBIGUOUS_SOURCE_IDENTIFIER,
            ambiguity=CrossSpeciesOrthologAmbiguity.MANY_TO_MANY,
        ),
        _entry(
            source_protein="P33333",
            target_ortholog="M22222",
            evidence_status=CrossSpeciesOrthologEvidenceStatus.AMBIGUOUS_SOURCE_IDENTIFIER,
            ambiguity=CrossSpeciesOrthologAmbiguity.MANY_TO_MANY,
        ),
    )
    assert report.summary.one_to_many_count == 2
    assert report.summary.many_to_many_count == 4
    assert report.summary.ambiguous_source_identifier_count == 4
    assert render_cross_species_ortholog_tsv(report.entries).splitlines()[0] == (
        "source_protein\ttarget_ortholog\tevidence_status\tambiguity"
    )


def test_map_cross_species_orthologs_does_not_treat_gene_symbol_as_orthology() -> None:
    report = map_cross_species_orthologs(
        ("GENEONLY", "UNMAPPED1"),
        _ortholog_pack(),
        source_species="Homo sapiens",
        target_species="Mus musculus",
    )

    assert report.entries == (
        _entry(
            source_protein="GENEONLY",
            target_ortholog=None,
            evidence_status=CrossSpeciesOrthologEvidenceStatus.UNRESOLVED_SOURCE_IDENTIFIER,
            ambiguity=CrossSpeciesOrthologAmbiguity.UNMAPPED,
        ),
        _entry(
            source_protein="UNMAPPED1",
            target_ortholog=None,
            evidence_status=CrossSpeciesOrthologEvidenceStatus.UNRESOLVED_SOURCE_IDENTIFIER,
            ambiguity=CrossSpeciesOrthologAmbiguity.UNMAPPED,
        ),
    )
    assert report.summary.unresolved_source_identifier_count == 2


def _entry(
    *,
    source_protein: str,
    target_ortholog: str | None,
    evidence_status: CrossSpeciesOrthologEvidenceStatus,
    ambiguity: CrossSpeciesOrthologAmbiguity,
):
    from bijux_proteomics_knowledge.orthologs.mapping import CrossSpeciesOrthologEntry

    return CrossSpeciesOrthologEntry(
        source_protein=source_protein,
        target_ortholog=target_ortholog,
        evidence_status=evidence_status,
        ambiguity=ambiguity,
    )


def _ortholog_pack() -> AnnotationPack:
    return AnnotationPack(
        source_path="cross-species-ortholog-pack.json",
        pack_name="cross-species-ortholog-pack",
        protein_features=(
            ProteinAnnotationRecord(
                protein_ref="P11111",
                gene_symbol="ONEA",
                organism="Homo sapiens",
            ),
            ProteinAnnotationRecord(
                protein_ref="P22222",
                gene_symbol="KIN1",
                organism="Homo sapiens",
            ),
            ProteinAnnotationRecord(
                protein_ref="P33333",
                gene_symbol="KIN1",
                organism="Homo sapiens",
            ),
        ),
        orthologs=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="M11111",
                source_gene_symbol="ONEA",
                target_gene_symbol="Onea",
                evidence="curated",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="M11112",
                source_gene_symbol="ONEA",
                target_gene_symbol="Onea-like",
                evidence="curated",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P22222",
                target_species="Mus musculus",
                target_protein_ref="M22221",
                source_gene_symbol="KIN1",
                target_gene_symbol="Kin1a",
                evidence="curated",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P22222",
                target_species="Mus musculus",
                target_protein_ref="M22222",
                source_gene_symbol="KIN1",
                target_gene_symbol="Kin1b",
                evidence="curated",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P33333",
                target_species="Mus musculus",
                target_protein_ref="M22221",
                source_gene_symbol="KIN1",
                target_gene_symbol="Kin1a",
                evidence="curated",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P33333",
                target_species="Mus musculus",
                target_protein_ref="M22222",
                source_gene_symbol="KIN1",
                target_gene_symbol="Kin1b",
                evidence="curated",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P55555",
                target_species="Mus musculus",
                target_protein_ref="M55555",
                source_gene_symbol="GENEONLY",
                target_gene_symbol="Geneonly",
                evidence="curated",
            ),
        ),
        summary=AnnotationPackSummary(
            protein_feature_count=3,
            pathway_count=0,
            complex_count=0,
            compartment_count=0,
            drug_target_count=0,
            disease_term_count=0,
            kinase_substrate_count=0,
            ortholog_count=7,
        ),
    )
