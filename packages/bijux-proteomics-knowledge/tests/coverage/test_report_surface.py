# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
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
from bijux_proteomics_knowledge.coverage.report import (
    KnowledgeCoverageEntitySet,
    KnowledgeCoverageEntityType,
    KnowledgeCoverageEntry,
    compute_knowledge_coverage,
    render_knowledge_coverage_tsv,
)


def test_compute_knowledge_coverage_warns_when_pathway_ptm_and_regulator_coverage_is_sparse() -> (
    None
):
    report = compute_knowledge_coverage(
        (
            KnowledgeCoverageEntitySet(
                entity_type=KnowledgeCoverageEntityType.PROTEIN,
                entity_ids=("TP53", "UNMAPPED1"),
            ),
            KnowledgeCoverageEntitySet(
                entity_type=KnowledgeCoverageEntityType.PATHWAY,
                entity_ids=(
                    "pathway:guardian_response",
                    "pathway:stress_network",
                    "pathway:metabolism",
                    "pathway:cycle",
                ),
            ),
            KnowledgeCoverageEntitySet(
                entity_type=KnowledgeCoverageEntityType.PTM_SITE,
                entity_ids=(
                    "P04637:S15:Phospho",
                    "P04637:S20:Phospho",
                    "P04637:S46:Phospho",
                ),
            ),
            KnowledgeCoverageEntitySet(
                entity_type=KnowledgeCoverageEntityType.REGULATOR,
                entity_ids=("MAPK1", "AKT1", "ERK2"),
            ),
        ),
        (_pack_one(), _pack_two()),
    )

    assert report.entries == (
        KnowledgeCoverageEntry(
            entity_type=KnowledgeCoverageEntityType.PATHWAY,
            total_count=4,
            annotated_count=1,
            coverage_fraction=0.25,
            low_coverage_warning="low pathway annotation coverage downgrades biological interpretation",
        ),
        KnowledgeCoverageEntry(
            entity_type=KnowledgeCoverageEntityType.PROTEIN,
            total_count=2,
            annotated_count=1,
            coverage_fraction=0.5,
            low_coverage_warning=None,
        ),
        KnowledgeCoverageEntry(
            entity_type=KnowledgeCoverageEntityType.PTM_SITE,
            total_count=3,
            annotated_count=1,
            coverage_fraction=0.3333,
            low_coverage_warning="low ptm-site annotation coverage downgrades biological interpretation",
        ),
        KnowledgeCoverageEntry(
            entity_type=KnowledgeCoverageEntityType.REGULATOR,
            total_count=3,
            annotated_count=1,
            coverage_fraction=0.3333,
            low_coverage_warning="low regulator annotation coverage downgrades biological interpretation",
        ),
    )
    assert report.summary.entity_type_count == 4
    assert report.summary.low_coverage_entity_type_count == 3


def test_compute_knowledge_coverage_renders_stable_tsv_rows() -> None:
    report = compute_knowledge_coverage(
        (
            KnowledgeCoverageEntitySet(
                entity_type=KnowledgeCoverageEntityType.PROTEIN,
                entity_ids=("TP53", "UNMAPPED1"),
            ),
            KnowledgeCoverageEntitySet(
                entity_type=KnowledgeCoverageEntityType.PATHWAY,
                entity_ids=("pathway:guardian_response", "pathway:stress_network"),
            ),
        ),
        _pack_one(),
    )

    rendered = render_knowledge_coverage_tsv(report.entries)

    assert rendered.splitlines() == [
        "entity_type\ttotal_count\tannotated_count\tcoverage_fraction\tlow_coverage_warning",
        "pathway\t2\t1\t0.5\t",
        "protein\t2\t1\t0.5\t",
    ]


def _pack_one() -> AnnotationPack:
    return AnnotationPack(
        source_path="knowledge-coverage-pack-one.json",
        pack_name="knowledge-coverage-pack-one",
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
            pathway_count=1,
            complex_count=0,
            compartment_count=0,
            drug_target_count=0,
            disease_term_count=0,
            kinase_substrate_count=1,
            ortholog_count=0,
        ),
    )


def _pack_two() -> AnnotationPack:
    return AnnotationPack(
        source_path="knowledge-coverage-pack-two.json",
        pack_name="knowledge-coverage-pack-two",
        protein_features=(
            ProteinAnnotationRecord(
                protein_ref="Q15303",
                gene_symbol="ERBB2",
                description="erb-b2 receptor tyrosine kinase 2",
            ),
        ),
        summary=AnnotationPackSummary(
            protein_feature_count=1,
            pathway_count=0,
            complex_count=0,
            compartment_count=0,
            drug_target_count=0,
            disease_term_count=0,
            kinase_substrate_count=0,
            ortholog_count=0,
        ),
    )
