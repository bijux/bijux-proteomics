"""Machine-readable knowledge root public API contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeRootApiBudget:
    """Budget for the durable knowledge root surface."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class KnowledgeRootApiEntry:
    """One stable knowledge root export."""

    export_name: str
    owner_module: str
    classification: str
    rationale: str


KNOWLEDGE_ROOT_API_BUDGET = KnowledgeRootApiBudget(
    max_public_symbols=61,
    max_init_lines=152,
)


def _entries(
    *,
    export_names: tuple[str, ...],
    owner_module: str,
    classification: str,
    rationale: str,
) -> tuple[KnowledgeRootApiEntry, ...]:
    return tuple(
        KnowledgeRootApiEntry(
            export_name=name,
            owner_module=owner_module,
            classification=classification,
            rationale=rationale,
        )
        for name in export_names
    )


def list_knowledge_root_api_entries() -> tuple[KnowledgeRootApiEntry, ...]:
    """Return the curated public root API for the knowledge package.

    Inputs:
    This function takes no runtime arguments and returns the in-module
    knowledge root export ledger.

    Outputs:
    Returns the full tuple of ``KnowledgeRootApiEntry`` records that define the
    supported knowledge package root exports.

    Failure Modes:
    This function does not raise governed public exceptions under normal
    package import conditions.

    Scientific Caveats:
    The ledger documents supported grounding and memory surfaces only; it does
    not prove that any underlying annotation source is complete or current.
    """

    return (
        _entries(
            export_names=("EvidenceBundle",),
            owner_module="bijux_proteomics_knowledge.memory.models.evidence",
            classification="shared_memory_anchor",
            rationale="shared evidence-memory anchors remain stable across cross-package scientific review and handoff surfaces",
        )
        + _entries(
            export_names=("EvidenceClaim",),
            owner_module="bijux_proteomics_knowledge.memory.models.claims",
            classification="shared_memory_anchor",
            rationale="shared claim-memory anchors remain stable across downstream decision, contradiction, and refusal workflows",
        )
        + _entries(
            export_names=("EvidenceRecord",),
            owner_module="bijux_proteomics_knowledge.memory.models.evidence",
            classification="shared_memory_anchor",
            rationale="shared evidence-memory anchors remain stable across cross-package scientific review and handoff surfaces",
        )
        + _entries(
            export_names=(
                "ComplexCoveragePolicy",
                "ComplexMembershipConfidence",
                "ComplexMembershipResolutionEntry",
                "ComplexMembershipResolutionReport",
                "ComplexMembershipResolutionSummary",
            ),
            owner_module="bijux_proteomics_knowledge.complexes",
            classification="complex_membership_resolution_surface",
            rationale="complex membership grounding stays public as a reusable biological-context resolution surface across review workflows",
        )
        + _entries(
            export_names=(
                "DiseaseTermResolutionEntry",
                "DiseaseTermResolutionReport",
                "DiseaseTermResolutionSummary",
            ),
            owner_module="bijux_proteomics_knowledge.disease",
            classification="disease_term_resolution_surface",
            rationale="disease-term grounding is a stable public knowledge review surface for biological consequence reporting",
        )
        + _entries(
            export_names=(
                "KnowledgeCoverageEntitySet",
                "KnowledgeCoverageEntityType",
                "KnowledgeCoverageEntry",
                "KnowledgeCoveragePolicy",
                "KnowledgeCoverageReport",
                "KnowledgeCoverageSummary",
            ),
            owner_module="bijux_proteomics_knowledge.coverage",
            classification="knowledge_coverage_surface",
            rationale="coverage reporting remains public because multiple downstream packages need one durable measure of scientific memory completeness",
        )
        + _entries(
            export_names=(
                "CrossSpeciesOrthologAmbiguity",
                "CrossSpeciesOrthologEntry",
                "CrossSpeciesOrthologEvidenceStatus",
                "CrossSpeciesOrthologReport",
                "CrossSpeciesOrthologSummary",
            ),
            owner_module="bijux_proteomics_knowledge.orthologs",
            classification="cross_species_ortholog_surface",
            rationale="cross-species ortholog resolution stays public because study comparison and transfer workflows need one stable grounding surface",
        )
        + _entries(
            export_names=(
                "DrugTargetRelationshipType",
                "DrugTargetResolutionEntry",
                "DrugTargetResolutionReport",
                "DrugTargetResolutionSummary",
            ),
            owner_module="bijux_proteomics_knowledge.drugs",
            classification="drug_target_resolution_surface",
            rationale="drug target grounding remains a public knowledge surface because it is a reusable downstream interpretation step",
        )
        + _entries(
            export_names=("KnowledgeDecisionBrief",),
            owner_module="bijux_proteomics_knowledge.reviews.decision_briefs",
            classification="decision_brief_handoff",
            rationale="knowledge decision briefs are the durable handoff packet from curated memory into downstream review and planning work",
        )
        + _entries(
            export_names=(
                "KinaseSubstrateMatchType",
                "KinaseSubstrateResolutionEntry",
                "KinaseSubstrateResolutionReport",
                "KinaseSubstrateResolutionSummary",
            ),
            owner_module="bijux_proteomics_knowledge.kinases",
            classification="kinase_substrate_resolution_surface",
            rationale="kinase-substrate grounding is a stable knowledge-facing review surface for PTM and signaling interpretation",
        )
        + _entries(
            export_names=(
                "PathwayCoverageConfidenceEntry",
                "PathwayCoverageConfidenceStatus",
                "PathwayCoveragePolicy",
                "PathwayMembershipResolutionEntry",
                "PathwayMembershipResolutionReport",
                "PathwayMembershipResolutionSummary",
            ),
            owner_module="bijux_proteomics_knowledge.pathways",
            classification="pathway_membership_resolution_surface",
            rationale="pathway membership grounding remains public because multiple biological consequence and comparison workflows depend on it directly",
        )
        + _entries(
            export_names=(
                "ProteinFeatureOverlapEntry",
                "ProteinFeatureQueryInterval",
                "ProteinFeatureType",
            ),
            owner_module="bijux_proteomics_knowledge.features",
            classification="protein_feature_resolution_surface",
            rationale="protein feature overlap review is a stable knowledge-facing surface for interval-based biological grounding",
        )
        + _entries(
            export_names=(
                "ProteinIdResolutionEntry",
                "ProteinIdentityResolutionStatus",
            ),
            owner_module="bijux_proteomics_knowledge.identity.proteins",
            classification="protein_identity_resolution_surface",
            rationale="protein identity resolution is a stable public knowledge task used before richer downstream annotation and evidence review",
        )
        + _entries(
            export_names=("evaluate_schema_compatibility",),
            owner_module="bijux_proteomics_knowledge.contracts.schema",
            classification="schema_contract",
            rationale="schema compatibility checks stay public so downstream packages can validate persisted knowledge artifacts without reaching into internals",
        )
        + _entries(
            export_names=("overlap_protein_features",),
            owner_module="bijux_proteomics_knowledge.features",
            classification="protein_feature_resolution_surface",
            rationale="protein feature overlap review is a stable knowledge-facing surface for interval-based biological grounding",
        )
        + _entries(
            export_names=("render_complex_membership_resolution_tsv",),
            owner_module="bijux_proteomics_knowledge.complexes",
            classification="complex_membership_resolution_surface",
            rationale="complex membership grounding stays public as a reusable biological-context resolution surface across review workflows",
        )
        + _entries(
            export_names=("render_disease_term_resolution_tsv",),
            owner_module="bijux_proteomics_knowledge.disease",
            classification="disease_term_resolution_surface",
            rationale="disease-term grounding is a stable public knowledge review surface for biological consequence reporting",
        )
        + _entries(
            export_names=("render_drug_target_resolution_tsv",),
            owner_module="bijux_proteomics_knowledge.drugs",
            classification="drug_target_resolution_surface",
            rationale="drug target grounding remains a public knowledge surface because it is a reusable downstream interpretation step",
        )
        + _entries(
            export_names=("render_kinase_substrate_resolution_tsv",),
            owner_module="bijux_proteomics_knowledge.kinases",
            classification="kinase_substrate_resolution_surface",
            rationale="kinase-substrate grounding is a stable knowledge-facing review surface for PTM and signaling interpretation",
        )
        + _entries(
            export_names=("render_knowledge_coverage_tsv",),
            owner_module="bijux_proteomics_knowledge.coverage",
            classification="knowledge_coverage_surface",
            rationale="coverage reporting remains public because multiple downstream packages need one durable measure of scientific memory completeness",
        )
        + _entries(
            export_names=("render_cross_species_ortholog_tsv",),
            owner_module="bijux_proteomics_knowledge.orthologs",
            classification="cross_species_ortholog_surface",
            rationale="cross-species ortholog resolution stays public because study comparison and transfer workflows need one stable grounding surface",
        )
        + _entries(
            export_names=("render_pathway_membership_resolution_tsv",),
            owner_module="bijux_proteomics_knowledge.pathways",
            classification="pathway_membership_resolution_surface",
            rationale="pathway membership grounding remains public because multiple biological consequence and comparison workflows depend on it directly",
        )
        + _entries(
            export_names=("render_protein_feature_overlaps_tsv",),
            owner_module="bijux_proteomics_knowledge.features",
            classification="protein_feature_resolution_surface",
            rationale="protein feature overlap review is a stable knowledge-facing surface for interval-based biological grounding",
        )
        + _entries(
            export_names=("render_protein_id_resolution_tsv",),
            owner_module="bijux_proteomics_knowledge.identity.proteins",
            classification="protein_identity_resolution_surface",
            rationale="protein identity resolution is a stable public knowledge task used before richer downstream annotation and evidence review",
        )
        + _entries(
            export_names=("compute_knowledge_coverage",),
            owner_module="bijux_proteomics_knowledge.coverage",
            classification="knowledge_coverage_surface",
            rationale="coverage reporting remains public because multiple downstream packages need one durable measure of scientific memory completeness",
        )
        + _entries(
            export_names=("map_cross_species_orthologs",),
            owner_module="bijux_proteomics_knowledge.orthologs",
            classification="cross_species_ortholog_surface",
            rationale="cross-species ortholog resolution stays public because study comparison and transfer workflows need one stable grounding surface",
        )
        + _entries(
            export_names=("resolve_complex_members",),
            owner_module="bijux_proteomics_knowledge.complexes",
            classification="complex_membership_resolution_surface",
            rationale="complex membership grounding stays public as a reusable biological-context resolution surface across review workflows",
        )
        + _entries(
            export_names=("resolve_disease_terms",),
            owner_module="bijux_proteomics_knowledge.disease",
            classification="disease_term_resolution_surface",
            rationale="disease-term grounding is a stable public knowledge review surface for biological consequence reporting",
        )
        + _entries(
            export_names=("resolve_drug_targets",),
            owner_module="bijux_proteomics_knowledge.drugs",
            classification="drug_target_resolution_surface",
            rationale="drug target grounding remains a public knowledge surface because it is a reusable downstream interpretation step",
        )
        + _entries(
            export_names=("resolve_kinase_substrates",),
            owner_module="bijux_proteomics_knowledge.kinases",
            classification="kinase_substrate_resolution_surface",
            rationale="kinase-substrate grounding is a stable knowledge-facing review surface for PTM and signaling interpretation",
        )
        + _entries(
            export_names=("resolve_pathway_members",),
            owner_module="bijux_proteomics_knowledge.pathways",
            classification="pathway_membership_resolution_surface",
            rationale="pathway membership grounding remains public because multiple biological consequence and comparison workflows depend on it directly",
        )
        + _entries(
            export_names=("resolve_protein_ids",),
            owner_module="bijux_proteomics_knowledge.identity.proteins",
            classification="protein_identity_resolution_surface",
            rationale="protein identity resolution is a stable public knowledge task used before richer downstream annotation and evidence review",
        )
    )


__all__ = [
    "KNOWLEDGE_ROOT_API_BUDGET",
    "KnowledgeRootApiBudget",
    "KnowledgeRootApiEntry",
    "list_knowledge_root_api_entries",
]
