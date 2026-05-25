# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated public entrypoints for knowledge scientific memory."""

from __future__ import annotations

from bijux_proteomics_knowledge.features import (
    ProteinFeatureOverlapEntry,
    ProteinFeatureQueryInterval,
    ProteinFeatureType,
    overlap_protein_features,
    render_protein_feature_overlaps_tsv,
)
from bijux_proteomics_knowledge.identity.proteins import (
    ProteinIdResolutionEntry,
    ProteinIdentityResolutionStatus,
    render_protein_id_resolution_tsv,
    resolve_protein_ids,
)
from bijux_proteomics_knowledge.pathways import (
    PathwayCoverageConfidenceEntry,
    PathwayCoverageConfidenceStatus,
    PathwayCoveragePolicy,
    PathwayMembershipResolutionEntry,
    PathwayMembershipResolutionReport,
    PathwayMembershipResolutionSummary,
    render_pathway_membership_resolution_tsv,
    resolve_pathway_members,
)
from bijux_proteomics_knowledge.complexes import (
    ComplexCoveragePolicy,
    ComplexMembershipConfidence,
    ComplexMembershipResolutionEntry,
    ComplexMembershipResolutionReport,
    ComplexMembershipResolutionSummary,
    render_complex_membership_resolution_tsv,
    resolve_complex_members,
)
from bijux_proteomics_knowledge.contracts.schema import evaluate_schema_compatibility
from bijux_proteomics_knowledge.memory.models.claims import EvidenceClaim
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceRecord,
)
from bijux_proteomics_knowledge.reviews.decision_briefs import KnowledgeDecisionBrief

__all__ = [
    "EvidenceBundle",
    "EvidenceClaim",
    "EvidenceRecord",
    "ComplexCoveragePolicy",
    "ComplexMembershipConfidence",
    "ComplexMembershipResolutionEntry",
    "ComplexMembershipResolutionReport",
    "ComplexMembershipResolutionSummary",
    "KnowledgeDecisionBrief",
    "PathwayCoverageConfidenceEntry",
    "PathwayCoverageConfidenceStatus",
    "PathwayCoveragePolicy",
    "PathwayMembershipResolutionEntry",
    "PathwayMembershipResolutionReport",
    "PathwayMembershipResolutionSummary",
    "ProteinFeatureOverlapEntry",
    "ProteinFeatureQueryInterval",
    "ProteinFeatureType",
    "ProteinIdResolutionEntry",
    "ProteinIdentityResolutionStatus",
    "evaluate_schema_compatibility",
    "overlap_protein_features",
    "render_complex_membership_resolution_tsv",
    "render_pathway_membership_resolution_tsv",
    "render_protein_feature_overlaps_tsv",
    "render_protein_id_resolution_tsv",
    "resolve_complex_members",
    "resolve_pathway_members",
    "resolve_protein_ids",
]
