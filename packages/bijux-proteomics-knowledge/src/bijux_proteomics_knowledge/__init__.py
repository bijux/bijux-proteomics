# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evidence models for Bijux Proteomics."""

from __future__ import annotations

from bijux_proteomics_knowledge.adapters import (
    AssayResultIngestionAdapter,
    LiteratureIngestionAdapter,
    NormalizedEvidenceInput,
    StructureAnnotationIngestionAdapter,
    attach_evidence_inputs,
)
from bijux_proteomics_knowledge.claims import (
    ClaimStatus,
    DecisionLineage,
    EvidenceClaim,
    build_claim,
    build_decision_lineage,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics_knowledge.graph import (
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    EvidenceNodeType,
    build_evidence_graph,
)
from bijux_proteomics_knowledge.resolution import (
    ConflictResolution,
    ResolutionAction,
    resolve_conflicts,
)
from bijux_proteomics_knowledge.evidence import (
    BundleTrustReport,
    DecisionReadiness,
    EvidenceConflict,
    EvidenceCoverage,
    EvidenceBundle,
    EvidenceExtractionMethod,
    EvidenceKind,
    EvidenceOrigin,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    assess_decision_readiness,
    compute_bundle_trust,
    coverage_report,
    deduplicate_records,
    evidence_gaps,
    flag_conflicting_evidence,
    score_evidence_record,
    stale_records,
    summarize_bundle,
    weight_source_type,
)

__all__ = [
    "AssayResultIngestionAdapter",
    "BundleTrustReport",
    "ClaimStatus",
    "ConflictResolution",
    "DecisionReadiness",
    "DecisionLineage",
    "EvidenceClaim",
    "EvidenceConflict",
    "EvidenceCoverage",
    "EvidenceBundle",
    "EvidenceEdge",
    "EvidenceGraph",
    "EvidenceExtractionMethod",
    "EvidenceKind",
    "EvidenceNode",
    "EvidenceNodeType",
    "EvidenceOrigin",
    "EvidenceRecord",
    "EvidenceSourceType",
    "EvidenceStrength",
    "assess_decision_readiness",
    "attach_evidence_inputs",
    "build_evidence_graph",
    "build_claim",
    "build_decision_lineage",
    "compute_bundle_trust",
    "coverage_report",
    "deduplicate_records",
    "evidence_gaps",
    "flag_conflicting_evidence",
    "score_evidence_record",
    "stale_records",
    "summarize_bundle",
    "weight_source_type",
    "JsonModel",
    "LiteratureIngestionAdapter",
    "NormalizedEvidenceInput",
    "DocumentSchema",
    "ResolutionAction",
    "resolve_conflicts",
    "StructureAnnotationIngestionAdapter",
]
