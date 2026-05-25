# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable charter for the scientific memory package boundary."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class KnowledgeCharterCapability(StrEnum):
    """Primary reference capabilities that justify the knowledge package."""

    REFERENCES = "references"
    ONTOLOGIES = "ontologies"
    BENCHMARK_MANIFESTS = "benchmark_manifests"
    CURATED_CORPORA = "curated_corpora"
    SCIENTIFIC_CONTEXT = "scientific_context"


class KnowledgeModuleClassification(StrEnum):
    """Allowed audit outcomes for knowledge source modules."""

    CURATED_REFERENCE_VALUE = "curated_reference_value"
    THIN_PLACEHOLDER = "thin_placeholder"
    DUPLICATE_MODEL = "duplicate_model"
    WRONG_PACKAGE_LOGIC = "wrong_package_logic"


class KnowledgeCharterEntry(JsonModel):
    """One durable capability owned by the knowledge package."""

    model_config = ConfigDict(extra="forbid")

    capability: KnowledgeCharterCapability
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    release_blocker: str = Field(..., min_length=1)


class KnowledgeModuleAuditEntry(JsonModel):
    """Audit record for one knowledge source module."""

    model_config = ConfigDict(extra="forbid")

    module_path: str = Field(..., min_length=1)
    classification: KnowledgeModuleClassification
    anchor_capabilities: tuple[KnowledgeCharterCapability, ...] = Field(
        default_factory=tuple
    )
    reason: str = Field(..., min_length=1)


DEFAULT_KNOWLEDGE_CHARTER: tuple[KnowledgeCharterEntry, ...] = (
    KnowledgeCharterEntry(
        capability=KnowledgeCharterCapability.REFERENCES,
        owned_surface="Curated scientific references that keep proteomics claims reviewable.",
        required_modules=(
            "references/grounding/citations.py",
            "references/grounding/literature.py",
            "references/grounding/problems.py",
            "references/grounding/rules.py",
        ),
        release_blocker="Knowledge cannot ship if scientific claims rely on package-local lore instead of explicit references.",
    ),
    KnowledgeCharterEntry(
        capability=KnowledgeCharterCapability.ONTOLOGIES,
        owned_surface="Ontology mappings and exact identity resolvers that normalize shared scientific language and curated entity naming across workflows.",
        required_modules=(
            "identity/proteins.py",
            "references/grounding/ontologies.py",
        ),
        release_blocker="Knowledge cannot ship if controlled scientific terms or curated identity aliases resolve through ad hoc local aliases.",
    ),
    KnowledgeCharterEntry(
        capability=KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
        owned_surface="Benchmark manifests that tie workflow claims to reproducible medium-scale fixtures.",
        required_modules=(
            "references/workflows/benchmarks.py",
            "references/workflows/briefings.py",
            "references/workflows/narratives.py",
            "references/workflows/lookups.py",
        ),
        release_blocker="Knowledge cannot ship if benchmark-backed workflow claims lose their manifest or citation grounding.",
    ),
    KnowledgeCharterEntry(
        capability=KnowledgeCharterCapability.CURATED_CORPORA,
        owned_surface="Curated corpus manifests that separate bundled fixtures from external scientific sources.",
        required_modules=(
            "references/grounding/corpora.py",
            "references/workflows/benchmarks.py",
        ),
        release_blocker="Knowledge cannot ship if bundled fixtures and external references blur into one unverifiable bucket.",
    ),
    KnowledgeCharterEntry(
        capability=KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        owned_surface="Scientific context entries, exact protein feature overlap queries, residue-specific kinase-substrate resolution, source-required disease and phenotype resolution, direct-versus-neighbor drug-target resolution, pathway coverage-aware membership resolution, sparse-complex confidence resolution, knowledge coverage downgrades for sparse pathway or regulator annotation, and workflow briefings that preserve caveats, scope, and interpretation boundaries.",
        required_modules=(
            "coverage/report.py",
            "complexes/members.py",
            "disease/terms.py",
            "drugs/targets.py",
            "features/overlaps.py",
            "kinases/substrates.py",
            "pathways/members.py",
            "references/grounding/contexts.py",
            "references/workflows/briefings.py",
            "reviews/decision_briefs.py",
            "reviews/explanations.py",
        ),
        release_blocker="Knowledge cannot ship if downstream packages would need to recreate caveats or scope context locally.",
    ),
)


DEFAULT_KNOWLEDGE_MODULE_AUDIT: tuple[KnowledgeModuleAuditEntry, ...] = (
    KnowledgeModuleAuditEntry(
        module_path="__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The package root is an export surface and deliberately forwards stable scientific memory entrypoints.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="governance/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The governance package root groups package-boundary audits without separate scientific-memory logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="governance/charter.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="The machine-readable charter keeps package ownership explicit and reviewable.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="contracts/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The contracts package root groups durable schema-owner modules without adding separate logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="contracts/schema.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.REFERENCES,),
        reason="Schema profiles preserve stable reviewable knowledge documents over time.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="coverage/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The coverage package root groups annotation-coverage owners without separate curated logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="coverage/report.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Knowledge coverage reporting keeps sparse pathway, PTM-site, and regulator annotation coverage explicit so downstream biological interpretation can be downgraded instead of overstated.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="complexes/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The complexes package root groups exact complex membership owners without separate curated logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="complexes/members.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Complex membership resolution keeps observed and missing subunits explicit and lets sparse assemblies degrade to low confidence instead of overstating partial evidence.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="disease/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The disease package root groups exact disease and phenotype resolver owners without separate curated logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="disease/terms.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Disease and phenotype resolution keeps source-less annotations out of emitted term rows instead of silently manufacturing unsupported disease claims.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="drugs/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The drugs package root groups exact drug-target resolver owners without separate curated logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="drugs/targets.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Drug-target resolution keeps explicitly direct targets separate from pathway-neighbor annotations instead of promoting all drug-related rows into one direct-target tier.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="features/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The features package root groups exact overlap owners without separate curated logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="features/overlaps.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Protein feature overlap resolution keeps inclusive protein-coordinate interpretation explicit instead of forcing downstream packages to reimplement boundary logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="identity/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The identity package root groups exact resolver owners without separate curated logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="identity/proteins.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.ONTOLOGIES,),
        reason="Protein identity resolution keeps curated accession, alias, and species normalization explicit instead of forcing ambiguous aliases into one winner.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="kinases/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The kinases package root groups exact kinase-substrate resolver owners without separate curated logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="kinases/substrates.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Kinase-substrate resolution keeps exact residue-position matches separate from weaker gene-equivalent aliases instead of collapsing all substrate evidence into one confidence tier.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="pathways/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The pathways package root groups exact pathway membership owners without separate curated logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="pathways/members.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Pathway membership resolution keeps matched, missing, and unresolved pathway coverage explicit and lets confidence degrade with sparse member support.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The memory package root groups durable owner modules without adding separate curation logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/models/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The memory models package root groups claim and evidence models without separate scientific-memory logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/models/claims.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Claim semantics are the reviewable memory layer built on curated references and caveats.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/models/evidence.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Evidence memory keeps benchmark and context provenance attached to scientific records.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/integrity/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The memory integrity package root groups graph validation and trace semantics without separate curation logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/integrity/graph.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Graph explanations turn curated evidence memory into reviewable decision traces.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/normalization/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The normalization package root groups external evidence normalization without separate scientific-memory logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/normalization/ingestion.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Ingestion normalizes external evidence into knowledge-owned memory records without runtime adapter ownership.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/reconciliation/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The reconciliation package root groups conflict-resolution surfaces without separate scientific-memory logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The references package root is an export surface over the grounded scientific registries.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/public.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The references public surface curates a small stable export set over deeper grounding and workflow owners.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The workflow references package root groups benchmark, briefing, narrative, and lookup owners without separate curation logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/benchmarks.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.CURATED_CORPORA,
        ),
        reason="Benchmark manifests are a core scientific-memory ownership surface.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/briefings.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Workflow briefings package grounded references into downstream-consumable scientific memory.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/lookups.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Workflow lookups provide read-only access to benchmark manifests and scoped workflow narratives.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/narratives.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Workflow narratives preserve claim and limitation framing with explicit references.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/benchmark_ledger.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.BENCHMARK_MANIFESTS,),
        reason="Benchmark ledger entries keep per-family benchmark authority and review state explicit instead of implicit in prose.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/claim_grounding.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Workflow claim grounding ties shipped claim language back to explicit benchmark evidence and scope limits.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/comparator_confrontations.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Comparator confrontation summaries keep external pressure visible instead of flattening disagreement into local success stories.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/comparator_failures.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Comparator failure surfaces keep blocked or downgraded public claims grounded in named external gaps.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/comparator_positions.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Comparator positions preserve the exact matched, partial, refused, and non-attempted workflow behaviors for each external tool.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/comparator_regressions.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Comparator regression tracking keeps formerly-supported workflow behavior from silently drifting backward.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/comparator_scorecards.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Comparator scorecards translate raw confrontation details into durable review-grade workflow pressure.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/comparators.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Comparator matrices are a first-class scientific memory surface for what the repository does and does not claim against external tools.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/contradiction_dossiers.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Contradiction dossiers keep workflow disagreements reviewable as governed scientific memory instead of ephemeral notes.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/contradiction_triage.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Contradiction triage preserves how conflicting evidence is prioritized and bounded before downstream review consumers act on it.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/evidence_sufficiency.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Evidence sufficiency rubrics keep current trust tiers explicit rather than letting release posture drift by implication.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/knowledge_deficits.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Knowledge deficit reports keep remaining public-data, comparator, literature, and runtime-proof gaps visible per workflow family.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/literature_audits.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Workflow literature audits make the breadth and concentration of citation support reviewable instead of assumed.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/literature_matrices.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Literature matrices keep workflow claims tied to explicit citation groups and contradiction coverage.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/reference_support.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
        ),
        reason="Reference-support lookups provide the governed routing between benchmark families and their grounded scientific briefings.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/registry.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Benchmark registry entries are a public scientific memory surface for what each benchmark currently authorizes.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/replay_proof.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Replay-proof reports keep benchmark reproduction boundaries and validating tests visible to downstream reviewers.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/scientific_reading_packs.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Scientific reading packs gather workflow-specific literature anchors into a durable review surface rather than an ad hoc reading list.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/scientific_release.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Scientific release packets define the explicit graduation and hostile-review posture for each workflow family.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/scientific_risk.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Scientific risk surfaces preserve unresolved workflow hazards as first-class reviewable evidence.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/workflows/scientific_thresholds.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Scientific threshold tables keep benchmark acceptance bars explicit and durable across release-facing consumers.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/grounding/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The grounding package root groups citations, contexts, corpora, ontologies, problems, and rules without separate curation logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/grounding/citations.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.REFERENCES,),
        reason="Primary citations are the anchor surface for grounded scientific claims.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/grounding/contexts.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Scientific context entries capture workflow caveats and interpretation scope.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/grounding/corpora.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.CURATED_CORPORA,),
        reason="Corpus manifests distinguish bundled fixtures from external scientific sources.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/grounding/literature.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
        ),
        reason="Literature groups tie benchmark and context claims back to curated papers and resources.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/grounding/ontologies.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.ONTOLOGIES,
        ),
        reason="Ontology mappings normalize curated scientific terms for the rest of the suite.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/grounding/problems.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Known-problem registries keep workflow caveats grounded and auditable.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="references/grounding/rules.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Scientific rules and grounded judgment ledgers translate reference provenance into reusable interpretation boundaries.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="reviews/__init__.py",
        classification=KnowledgeModuleClassification.THIN_PLACEHOLDER,
        reason="The reviews package root groups reviewer-facing owner modules without adding separate curation logic.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="reviews/explanations.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Decision-scoped review explanations turn existing knowledge packets into auditable graph-backed reviewer narratives.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="reviews/flagship_evidence.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Flagship evidence summaries keep cross-workflow scientific memory legible at the release-facing review layer.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="reviews/provenance.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Provenance disagreement surfaces preserve how reference scope pressure changes reviewer-facing confidence.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="reviews/trends.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,),
        reason="Review packet comparisons and trend summaries keep reviewer-facing knowledge changes explicit over time.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="memory/reconciliation/resolution.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.REFERENCES,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Resolution logic preserves how conflicting scientific memory gets reviewed instead of silently overwritten.",
    ),
    KnowledgeModuleAuditEntry(
        module_path="reviews/decision_briefs.py",
        classification=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE,
        anchor_capabilities=(
            KnowledgeCharterCapability.BENCHMARK_MANIFESTS,
            KnowledgeCharterCapability.SCIENTIFIC_CONTEXT,
        ),
        reason="Review packets are the package's downstream scientific-memory handoff surface.",
    ),
)


__all__ = [
    "DEFAULT_KNOWLEDGE_CHARTER",
    "DEFAULT_KNOWLEDGE_MODULE_AUDIT",
    "KnowledgeCharterCapability",
    "KnowledgeCharterEntry",
    "KnowledgeModuleAuditEntry",
    "KnowledgeModuleClassification",
]
