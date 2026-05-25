# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceClaim,
    EvidenceRecord,
    KnowledgeDecisionBrief,
    ProteinFeatureType,
    ProteinIdentityResolutionStatus,
    evaluate_schema_compatibility,
    overlap_protein_features,
    render_protein_feature_overlaps_tsv,
    render_protein_id_resolution_tsv,
    resolve_protein_ids,
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
