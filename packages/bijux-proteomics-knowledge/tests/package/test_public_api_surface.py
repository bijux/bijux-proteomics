# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_knowledge import (
    ComplexMembershipConfidence,
    DiseaseTermResolutionEntry,
    DrugTargetRelationshipType,
    EvidenceBundle,
    EvidenceClaim,
    EvidenceRecord,
    KnowledgeDecisionBrief,
    KinaseSubstrateMatchType,
    PathwayCoverageConfidenceStatus,
    ProteinFeatureType,
    ProteinIdentityResolutionStatus,
    evaluate_schema_compatibility,
    overlap_protein_features,
    render_complex_membership_resolution_tsv,
    render_disease_term_resolution_tsv,
    render_drug_target_resolution_tsv,
    render_kinase_substrate_resolution_tsv,
    render_pathway_membership_resolution_tsv,
    render_protein_feature_overlaps_tsv,
    render_protein_id_resolution_tsv,
    resolve_complex_members,
    resolve_disease_terms,
    resolve_drug_targets,
    resolve_kinase_substrates,
    resolve_pathway_members,
    resolve_protein_ids,
)
from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
)
from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexMemberKind,
    ComplexMembershipRecord,
)
from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    BiologicalContextRecord,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMemberKind,
    PathwayMembershipRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.interpretation.regulator_inference import (
    RegulatorEvidenceRecord,
    RegulatorEvidenceType,
)
from bijux_proteomics.sequences.protein_region_context import ProteinRegionContextRecord
from bijux_proteomics_knowledge.memory.models.claims import ClaimStatus
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceKind,
    EvidenceStrength,
)
from bijux_proteomics_knowledge.features import ProteinFeatureQueryInterval


def test_knowledge_public_root_exposes_curated_memory_anchors() -> None:
    record = EvidenceRecord(
        evidence_id="public-root-record",
        kind=EvidenceKind.LITERATURE,
        title="public root record",
        source="PMID:1",
        claim="public root evidence stays typed",
        confidence=0.8,
        strength=EvidenceStrength.SUPPORTING,
    )
    bundle = EvidenceBundle(
        bundle_id="public-root-bundle",
        target_id="public-root-target",
        records=[record],
    )
    claim = EvidenceClaim(
        claim_id="public-root-claim",
        target_id="public-root-target",
        statement="public root claims stay typed",
        evidence_ids=[record.evidence_id],
        status=ClaimStatus.SUPPORTED,
    )

    report = evaluate_schema_compatibility(
        DocumentSchema(schema_version="1.0.0", created_by="public-root-test")
    )

    assert bundle.records[0].evidence_id == "public-root-record"
    assert claim.evidence_ids == ["public-root-record"]
    assert KnowledgeDecisionBrief.__name__ == "KnowledgeDecisionBrief"
    assert ProteinIdentityResolutionStatus.EXACT_ACCESSION.value == "exact_accession"
    assert resolve_protein_ids.__name__ == "resolve_protein_ids"
    assert render_protein_id_resolution_tsv.__name__ == "render_protein_id_resolution_tsv"
    assert report.compatible is True


def test_knowledge_public_root_exposes_protein_feature_overlap_surface() -> None:
    overlaps = overlap_protein_features(
        "P11111",
        (ProteinFeatureQueryInterval(start=1, end=1),),
        (
            ProteinRegionContextRecord(
                protein_ref="P11111",
                start=1,
                end=2,
                signal_peptide="leader",
                source_name="UniProt",
                source_accession="UP:P11111-1-2",
            ),
        ),
    )

    assert overlaps[0].feature_type is ProteinFeatureType.SIGNAL_PEPTIDE
    assert render_protein_feature_overlaps_tsv(overlaps).splitlines()[0] == (
        "protein_id\tquery_start\tquery_end\tfeature_id\tfeature_type\toverlap_start\toverlap_end"
    )


def test_knowledge_public_root_exposes_pathway_membership_surface() -> None:
    report = resolve_pathway_members(
        ("P04637",),
        AnnotationPack(
            source_path="public-root-pathway-pack.json",
            pack_name="public-root-pathway-pack",
            protein_features=(
                ProteinAnnotationRecord(
                    protein_ref="P04637",
                    gene_symbol="TP53",
                    description="tumor protein p53",
                ),
            ),
            pathways=(
                PathwayMembershipRecord(
                    pathway_id="pathway:guardian_response",
                    member_kind=PathwayMemberKind.PROTEIN,
                    member_id="P04637",
                ),
            ),
            summary=AnnotationPackSummary(
                protein_feature_count=1,
                pathway_count=1,
                complex_count=0,
                compartment_count=0,
                drug_target_count=0,
                disease_term_count=0,
                kinase_substrate_count=0,
                ortholog_count=0,
            ),
        ),
    )

    assert (
        report.confidence_entries[0].confidence_status
        is PathwayCoverageConfidenceStatus.HIGH_CONFIDENCE
    )
    assert render_pathway_membership_resolution_tsv(report.entries).splitlines()[0] == (
        "pathway_id\tmatched_members\tmissing_members\tcoverage_fraction\tunresolved_inputs"
    )


def test_knowledge_public_root_exposes_complex_membership_surface() -> None:
    report = resolve_complex_members(
        ("P04637",),
        AnnotationPack(
            source_path="public-root-complex-pack.json",
            pack_name="public-root-complex-pack",
            protein_features=(
                ProteinAnnotationRecord(
                    protein_ref="P04637",
                    gene_symbol="TP53",
                    description="tumor protein p53",
                ),
                ProteinAnnotationRecord(
                    protein_ref="Q9Y243",
                    gene_symbol="SIGB",
                    description="stress adaptor beta",
                ),
            ),
            complexes=(
                ComplexMembershipRecord(
                    complex_id="complex:guardian",
                    member_kind=ComplexMemberKind.PROTEIN,
                    member_id="P04637",
                ),
                ComplexMembershipRecord(
                    complex_id="complex:guardian",
                    member_kind=ComplexMemberKind.GENE,
                    member_id="SIGB",
                ),
            ),
            summary=AnnotationPackSummary(
                protein_feature_count=2,
                pathway_count=0,
                complex_count=2,
                compartment_count=0,
                drug_target_count=0,
                disease_term_count=0,
                kinase_substrate_count=0,
                ortholog_count=0,
            ),
        ),
    )

    assert (
        report.entries[0].complex_confidence
        is ComplexMembershipConfidence.LOW_CONFIDENCE
    )
    assert render_complex_membership_resolution_tsv(report.entries).splitlines()[0] == (
        "complex_id\tobserved_members\tmissing_members\tmember_coverage\tcomplex_confidence"
    )


def test_knowledge_public_root_exposes_kinase_substrate_resolution_surface() -> None:
    report = resolve_kinase_substrates(
        ("TP53:S15:Phospho", "P04637:S15:Phospho"),
        AnnotationPack(
            source_path="public-root-kinase-pack.json",
            pack_name="public-root-kinase-pack",
            protein_features=(
                ProteinAnnotationRecord(
                    protein_ref="P04637",
                    gene_symbol="TP53",
                    description="tumor protein p53",
                ),
            ),
            kinase_substrates=(
                RegulatorEvidenceRecord(
                    regulator="MAPK1",
                    evidence_type=RegulatorEvidenceType.KINASE_SUBSTRATE,
                    site_key="P04637:S15:Phospho",
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
        ),
    )

    assert report.entries[0].match_type is KinaseSubstrateMatchType.EXACT_ACCESSION_SITE
    assert report.entries[1].match_type is KinaseSubstrateMatchType.GENE_SYMBOL_SITE_EQUIVALENT
    assert render_kinase_substrate_resolution_tsv(report.entries).splitlines()[0] == (
        "site_id\tkinase\tmatch_type\tannotation_source"
    )


def test_knowledge_public_root_exposes_drug_target_resolution_surface() -> None:
    report = resolve_drug_targets(
        ("EGFR", "ERBB2"),
        AnnotationPack(
            source_path="public-root-drug-pack.json",
            pack_name="public-root-drug-pack",
            protein_features=(
                ProteinAnnotationRecord(
                    protein_ref="P00533",
                    gene_symbol="EGFR",
                    description="epidermal growth factor receptor",
                ),
                ProteinAnnotationRecord(
                    protein_ref="Q15303",
                    gene_symbol="ERBB2",
                    description="erb-b2 receptor tyrosine kinase 2",
                ),
            ),
            drug_targets=(
                BiologicalContextRecord(
                    protein_ref="P00533",
                    context_kind=BiologicalContextKind.DRUG_TARGET,
                    context_id="drug:erlotinib",
                    context_name="Erlotinib",
                    source_accession="DrugBank:DB00530",
                ),
                BiologicalContextRecord(
                    protein_ref="Q15303",
                    context_kind=BiologicalContextKind.DRUG_TARGET,
                    context_id="drug:erlotinib",
                    context_name="Erlotinib",
                    source_accession="DrugBank:DB00530",
                    metadata={"relationship_type": "pathway_neighbor"},
                ),
            ),
            summary=AnnotationPackSummary(
                protein_feature_count=2,
                pathway_count=0,
                complex_count=0,
                compartment_count=0,
                drug_target_count=2,
                disease_term_count=0,
                kinase_substrate_count=0,
                ortholog_count=0,
            ),
        ),
    )

    assert report.entries[0].relationship_type is DrugTargetRelationshipType.DIRECT_TARGET
    assert report.entries[1].relationship_type is DrugTargetRelationshipType.INDIRECT_PATHWAY_NEIGHBOR
    assert render_drug_target_resolution_tsv(report.entries).splitlines()[0] == (
        "protein_id\tdrug\trelationship_type\tdirect_target\tannotation_source"
    )


def test_knowledge_public_root_exposes_disease_term_resolution_surface() -> None:
    report = resolve_disease_terms(
        ("P04637", "P28482"),
        (
            BiologicalContextRecord(
                protein_ref="P04637",
                context_kind=BiologicalContextKind.DISEASE_TERM,
                context_id="DOID:162",
                context_name="cancer",
                source_name="Disease Ontology",
            ),
            BiologicalContextRecord(
                protein_ref="P28482",
                context_kind=BiologicalContextKind.PHENOTYPE_TERM,
                context_id="HP:0001250",
                context_name="seizures",
                source_name="HPO",
            ),
        ),
    )

    assert report.entries == (
        DiseaseTermResolutionEntry(
            protein_id="P04637",
            term_id="DOID:162",
            term_name="cancer",
            source="Disease Ontology",
            evidence_type="disease_term",
        ),
        DiseaseTermResolutionEntry(
            protein_id="P28482",
            term_id="HP:0001250",
            term_name="seizures",
            source="HPO",
            evidence_type="phenotype_term",
        ),
    )
    assert render_disease_term_resolution_tsv(report.entries).splitlines()[0] == (
        "protein_id\tterm_id\tterm_name\tsource\tevidence_type"
    )
