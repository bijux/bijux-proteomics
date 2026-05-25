# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable charter for intelligence-owned analytical behavior."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class IntelligenceCharterCapability(StrEnum):
    """Capabilities intelligence must own as a real analytical product."""

    PRIORITIZATION = "prioritization"
    CONTRADICTION_HANDLING = "contradiction_handling"
    REVIEW_REASONING = "review_reasoning"
    INTERPRETATION_DISCIPLINE = "interpretation_discipline"
    RECOMMENDATION = "recommendation"


class IntelligenceAnalyticalBand(StrEnum):
    """Stable analytical bands that organize intelligence owner modules."""

    CANDIDATES = "candidates"
    CLAIMS = "claims"
    CONTRADICTIONS = "contradictions"
    FALSIFIERS = "falsifiers"
    REFUSAL = "refusal"
    QUERY = "query"
    JUDGMENT = "judgment"
    POSTURE = "posture"
    INTERPRETATION = "interpretation"
    REVIEWS = "reviews"
    LEARNING = "learning"


class IntelligenceModuleClassification(StrEnum):
    """Allowed audit outcomes for intelligence source modules."""

    ANALYTICAL_VALUE = "analytical_value"
    THIN_ABSTRACTION = "thin_abstraction"
    DUPLICATE_MODEL = "duplicate_model"
    WRONG_PACKAGE_LOGIC = "wrong_package_logic"


class IntelligenceProductCharter(JsonModel):
    """Durable product charter for intelligence package ownership."""

    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(..., min_length=1)
    value_statement: str = Field(..., min_length=1)
    capabilities: tuple[IntelligenceCharterCapability, ...] = Field(
        default_factory=tuple
    )
    required_inputs: tuple[str, ...] = Field(default_factory=tuple)
    excluded_ownership: tuple[str, ...] = Field(default_factory=tuple)


class IntelligenceCharterEntry(JsonModel):
    """One durable capability owned by the intelligence package."""

    model_config = ConfigDict(extra="forbid")

    capability: IntelligenceCharterCapability
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    release_blocker: str = Field(..., min_length=1)


class IntelligenceModuleAuditEntry(JsonModel):
    """Audit record for one intelligence source module."""

    model_config = ConfigDict(extra="forbid")

    module_path: str = Field(..., min_length=1)
    classification: IntelligenceModuleClassification
    anchor_capabilities: tuple[IntelligenceCharterCapability, ...] = Field(
        default_factory=tuple
    )
    reason: str = Field(..., min_length=1)


class IntelligenceCapabilityMapEntry(JsonModel):
    """One stable analytical band and the modules it owns."""

    model_config = ConfigDict(extra="forbid")

    band: IntelligenceAnalyticalBand
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    decision_scope: tuple[str, ...] = Field(default_factory=tuple)
    refusal_scope: tuple[str, ...] = Field(default_factory=tuple)


DEFAULT_INTELLIGENCE_CHARTER = IntelligenceProductCharter(
    package_name="bijux-proteomics-intelligence",
    value_statement=(
        "turn ranked evidence, contradiction posture, and workflow interpretation into "
        "explicit analytical judgment without taking over scientific truth, runtime "
        "execution, knowledge curation, or lab scheduling"
    ),
    capabilities=(
        IntelligenceCharterCapability.PRIORITIZATION,
        IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        IntelligenceCharterCapability.REVIEW_REASONING,
        IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
        IntelligenceCharterCapability.RECOMMENDATION,
    ),
    required_inputs=(
        "core-owned scientific models",
        "knowledge-owned evidence bundles and references",
        "lab-owned assay feasibility and operational constraints",
    ),
    excluded_ownership=(
        "scientific parsing and normalization",
        "runtime execution and artifact transport",
        "knowledge curation and reference registry maintenance",
        "lab queueing and operational handoff authority",
    ),
)

DEFAULT_INTELLIGENCE_CAPABILITY_MAP: tuple[IntelligenceCapabilityMapEntry, ...] = (
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.CANDIDATES,
        owned_surface=(
            "candidate framing, ranking, lifecycle, and candidate-specific "
            "quality semantics that make later judgment analyzable instead of ad hoc"
        ),
        required_modules=(
            "candidates/ranking.py",
            "candidates/lifecycle.py",
            "candidates/quality.py",
            "candidates/validation.py",
        ),
        decision_scope=(
            "rank candidates against explicit policy factors",
            "publish machine-readable rejection and tie-break reasoning",
            "keep candidate lifecycle and quality posture explicit before review synthesis",
        ),
        refusal_scope=(
            "refuse opaque score-only ordering",
            "refuse package-root convenience exports as a substitute for candidate ownership",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.CLAIMS,
        owned_surface=(
            "graph-backed claim-support validation that keeps unsupported or "
            "contradicted analytical claims explicit before downstream judgment and review"
        ),
        required_modules=("claims/support.py",),
        decision_scope=(
            "invalidate claims that are not anchored to explicit evidence-graph support",
            "keep contradicting graph evidence visible before contradiction summaries",
        ),
        refusal_scope=(
            "refuse free-text claim support that is not linked to the evidence graph",
            "do not take over knowledge-owned claim curation or evidence-graph construction",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.CONTRADICTIONS,
        owned_surface=(
            "pairwise contradiction detection that distinguishes direct disagreement "
            "from site-specific PTM residuals after protein-abundance correction"
        ),
        required_modules=("contradictions.py",),
        decision_scope=(
            "keep direct target disagreements explicit before recommendation synthesis",
            "treat protein-steady and PTM-shifted pairs as site-specific only when corrected residual site evidence remains strong",
        ),
        refusal_scope=(
            "refuse to collapse corrected site-specific PTM residuals into protein-level contradiction",
            "do not take over knowledge-owned claim curation or PTM correction generation",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.FALSIFIERS,
        owned_surface=(
            "claim challenge generation that states what evidence would overturn "
            "protein, PTM, pathway, regulator, and biomarker interpretations"
        ),
        required_modules=("falsifiers.py",),
        decision_scope=(
            "emit claim-specific falsifier types instead of one generic challenge template",
            "tie required evidence to the biological surface that currently carries the claim",
        ),
        refusal_scope=(
            "refuse generic falsifiers that ignore whether the claim is protein, PTM, pathway, regulator, and biomarker scoped",
            "do not take over lab scheduling or knowledge-owned assay catalog curation",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.REFUSAL,
        owned_surface=(
            "claim refusal boundaries that block strong analytical claims when "
            "design validity, qc posture, peptide depth, or PTM localization is too weak"
        ),
        required_modules=("refusal.py",),
        decision_scope=(
            "block strong claims when experimental design validity is absent or QC has failed",
            "refuse strong protein and PTM claims when peptide support or site localization does not meet governed evidence thresholds",
        ),
        refusal_scope=(
            "refuse to let weak peptide support or low PTM localization pass as strong evidence",
            "do not take over core-owned QC generation, localization scoring, or design normalization",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.QUERY,
        owned_surface=(
            "deterministic result-question answering that returns governed IDs for "
            "significance, rejection, peptide support, failed samples, and claim weakness"
        ),
        required_modules=("query.py",),
        decision_scope=(
            "answer supported result questions from preserved study-result objects without free-text guessing",
            "return explicit IDs alongside prose so answers stay machine-actionable",
        ),
        refusal_scope=(
            "refuse prose-only answers that omit referenced IDs",
            "do not take over artifact parsing or core-owned result-query artifact loaders",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.JUDGMENT,
        owned_surface=(
            "scenario evaluation, decision paths, and recommendation semantics that "
            "turn typed evidence into explicit analytical judgment"
        ),
        required_modules=(
            "judgment/policies.py",
            "judgment/scenarios.py",
            "judgment/recommendations.py",
            "judgment/paths.py",
        ),
        decision_scope=(
            "rank candidates against explicit policy factors",
            "compare scenario actions such as advance, hold, redesign, and scale-up",
            "publish machine-readable rejection and tie-break reasoning",
        ),
        refusal_scope=(
            "refuse implied decisions when evidence posture is unresolved",
            "refuse package-root convenience exports as a substitute for owner-module judgment",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.POSTURE,
        owned_surface=(
            "contradiction pressure, freshness pressure, and readiness gating over "
            "knowledge-owned evidence bundles"
        ),
        required_modules=("posture/evidence.py", "posture/skeptical.py"),
        decision_scope=(
            "downgrade confidence when evidence is aging",
            "refuse recommendations when contradictions remain unresolved",
        ),
        refusal_scope=(
            "do not decide evidence truth or curation ownership",
            "do not bypass knowledge-owned trust and refresh contracts",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.INTERPRETATION,
        owned_surface=(
            "typed biological interpretation and caution-aware analytical summaries "
            "over already-normalized proteomics evidence"
        ),
        required_modules=(
            "interpretation/runs.py",
            "interpretation/quantitative.py",
            "interpretation/ptm.py",
            "interpretation/contaminants.py",
            "interpretation/contrasts.py",
            "interpretation/pathways.py",
            "interpretation/structures.py",
        ),
        decision_scope=(
            "summarize run-level interpretation posture",
            "recommend contrasts and enrichment summaries with explicit caveats",
        ),
        refusal_scope=(
            "refuse mechanistic overclaim without convergent contradiction-free support",
            "do not own raw parsing, quantification, PTM mapping, or QC generation",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.REVIEWS,
        owned_surface=(
            "decision briefs, skeptical challenge reports, benchmark-backed review, "
            "and end-to-end decision paths"
        ),
        required_modules=(
            "reviews/boards.py",
            "reviews/candidates.py",
            "reviews/pathways.py",
            "reviews/decision_briefs.py",
            "reviews/benchmarks.py",
        ),
        decision_scope=(
            "state whether a recommendation is ready for review scrutiny",
            "publish unresolved questions and benchmark-backed challenge signals",
        ),
        refusal_scope=(
            "do not overclaim release readiness without benchmark-backed review",
            "do not hide unresolved questions behind polished narrative",
        ),
    ),
    IntelligenceCapabilityMapEntry(
        band=IntelligenceAnalyticalBand.LEARNING,
        owned_surface=(
            "outcome-informed prioritization updates and design-loop feedback that "
            "adjust future analytical posture without rewriting history"
        ),
        required_modules=("learning/adaptation.py", "learning/refinement/"),
        decision_scope=(
            "adjust future prioritization from observed outcomes",
            "track convergence and stagnation in iterative design analysis",
        ),
        refusal_scope=(
            "do not mutate historical decisions in place",
            "do not take over lab queue authority or operational handoff ownership",
        ),
    ),
)


DEFAULT_INTELLIGENCE_CHARTER_ENTRIES: tuple[IntelligenceCharterEntry, ...] = (
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.PRIORITIZATION,
        owned_surface="Transparent multi-objective ranking that weighs evidence strength, reproducibility, assay feasibility, novelty, and execution burden.",
        required_modules=(
            "candidates/ranking.py",
            "judgment/policies.py",
            "judgment/paths.py",
        ),
        release_blocker="Intelligence cannot ship if candidate ordering collapses into opaque scores or policy-only prose.",
    ),
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.CONTRADICTION_HANDLING,
        owned_surface="Explicit contradiction, claim-support, freshness, and uncertainty posture that can refuse overconfident recommendations.",
        required_modules=(
            "contradictions.py",
            "claims/support.py",
            "refusal.py",
            "posture/evidence.py",
            "judgment/scenarios.py",
            "judgment/paths.py",
        ),
        release_blocker="Intelligence cannot ship if contradictory or stale evidence still produces confident progression output.",
    ),
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.REVIEW_REASONING,
        owned_surface="Review-board packets and skeptical challenge reports that survive scientific and software scrutiny.",
        required_modules=(
            "falsifiers.py",
            "query.py",
            "reviews/decision_briefs.py",
            "judgment/recommendations.py",
            "judgment/paths.py",
            "posture/skeptical.py",
            "reviews/benchmarks.py",
        ),
        release_blocker="Intelligence cannot ship if review consumers cannot see why a recommendation should be trusted or challenged.",
    ),
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
        owned_surface="Typed interpretation contracts that separate technical anomalies, biological signal, and pathway-overclaim risks.",
        required_modules=(
            "interpretation/runs.py",
            "interpretation/quantitative.py",
            "reviews/pathways.py",
        ),
        release_blocker="Intelligence cannot ship if interpretation helpers blur cautionary caveats into confident scientific claims.",
    ),
    IntelligenceCharterEntry(
        capability=IntelligenceCharterCapability.RECOMMENDATION,
        owned_surface="End-to-end decision paths that add analytical value beyond core workflow models and runtime delivery surfaces.",
        required_modules=(
            "candidates/ranking.py",
            "judgment/scenarios.py",
            "posture/skeptical.py",
        ),
        release_blocker="Intelligence cannot ship if downstream packages could recreate its outputs by stitching together core models and runtime wrappers alone.",
    ),
)


DEFAULT_INTELLIGENCE_MODULE_AUDIT: tuple[IntelligenceModuleAuditEntry, ...] = (
    IntelligenceModuleAuditEntry(
        module_path="__init__.py",
        classification=IntelligenceModuleClassification.THIN_ABSTRACTION,
        reason="The package root is an export surface that aggregates stable analytical entrypoints.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="claims/__init__.py",
        classification=IntelligenceModuleClassification.THIN_ABSTRACTION,
        reason="The claims package root groups claim-support validation owners without separate analytical logic.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="claims/support.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.CONTRADICTION_HANDLING,
            IntelligenceCharterCapability.REVIEW_REASONING,
        ),
        reason="Claim-support validation keeps unsupported claims invalid and leaves contradicting graph evidence explicit before downstream judgment or review packets are built.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="contradictions.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.CONTRADICTION_HANDLING,
            IntelligenceCharterCapability.REVIEW_REASONING,
        ),
        reason="Contradiction detection preserves direct disagreements while distinguishing corrected site-specific PTM residuals from real protein-versus-site conflicts.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="falsifiers.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.REVIEW_REASONING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Falsifier generation keeps claim challenge paths explicit by emitting distinct evidence requirements for protein, PTM, pathway, regulator, and biomarker claims.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="refusal.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.CONTRADICTION_HANDLING,
            IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
        ),
        reason="Claim refusal keeps strong analytical statements blocked when design validity, QC posture, peptide support, or PTM localization do not satisfy the minimum governed evidence boundary.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="query.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.REVIEW_REASONING,
            IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
        ),
        reason="Result-question answering keeps significance, rejection, peptide support, failed sample, and weakening answers deterministic and machine-readable by returning preserved IDs instead of prose alone.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="governance/charter.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.PRIORITIZATION,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="The machine-readable charter and module audit keep analytical ownership explicit and release-blocking.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="candidates/ranking.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.PRIORITIZATION,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Ranking logic and explainability live here instead of being recreated by downstream consumers.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="candidates/lifecycle.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.REVIEW_REASONING,),
        reason="Candidate lifecycle and risk summaries give review outputs analytical substance beyond transport formatting.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="judgment/policies.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.PRIORITIZATION,),
        reason="Policy lineage and factor validation make ranking reproducible instead of ad hoc.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="judgment/scenarios.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.CONTRADICTION_HANDLING,),
        reason="Scenario evaluators keep progression, redesign, synthesis, and scale-up judgment explicit instead of burying it inside review formatting.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="judgment/recommendations.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.CONTRADICTION_HANDLING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Recommendation refusal, escalation, and unresolved-question posture now live with the advisory decision contract they actually own.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="judgment/paths.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.REVIEW_REASONING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Decision paths turn scored evidence into explicit reviewable recommendations with unresolved questions intact.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="posture/evidence.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.CONTRADICTION_HANDLING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Freshness and contradiction posture make recommendation confidence defensible.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="posture/skeptical.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.REVIEW_REASONING,
            IntelligenceCharterCapability.RECOMMENDATION,
        ),
        reason="Skeptical review pressure proves recommendation quality against software and scientific objections.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="reviews/boards.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.REVIEW_REASONING,),
        reason="Board-facing review synthesis keeps escalation, unresolved questions, and review posture separate from candidate and pathway projections.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="reviews/candidates.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.REVIEW_REASONING,),
        reason="Candidate-facing review projections keep ranked evidence and candidate narratives out of generic review buckets.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="reviews/pathways.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(
            IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,
            IntelligenceCharterCapability.REVIEW_REASONING,
        ),
        reason="Pathway-facing review synthesis keeps cautious interpretation visible when review consumers need analytical summaries instead of raw signal tables.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="reviews/decision_briefs.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.REVIEW_REASONING,),
        reason="Review packet assembly now stays separate from scenario policy so review-facing evidence and recommendation artifacts have a clear owner.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="reviews/benchmarks.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.REVIEW_REASONING,),
        reason="Benchmark-backed review outputs keep release-facing workflow claims tied to checked-in datasets, owner surfaces, and explicit scientific limits.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="interpretation/runs.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,),
        reason="Run interpretation keeps QC posture and biological-readiness summaries typed instead of leaking into runtime or review transport layers.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="interpretation/quantitative.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,),
        reason="Quantitative interpretation keeps differential abundance and missingness caveats explicit instead of burying them in presentation helpers.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="interpretation/ptm.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,),
        reason="PTM interpretation keeps site-level caveats and motif context separate from broad analytical summaries.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="interpretation/contaminants.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,),
        reason="Contaminant interpretation keeps technical artifact semantics explicit instead of blending them into biological narrative.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="interpretation/contrasts.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,),
        reason="Contrast recommendation logic keeps study-design caveats explicit before downstream consumers build review or operational guidance.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="interpretation/pathways.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,),
        reason="Pathway and enrichment interpretation keep overclaim limits explicit instead of flattening them into generic report prose.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="interpretation/structures.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.INTERPRETATION_DISCIPLINE,),
        reason="Structure-oriented interpretation keeps low-confidence segment and protein-structure framing as a typed analytical surface.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="learning/adaptation.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.RECOMMENDATION,),
        reason="Outcome-aware follow-up pressure keeps later analytical posture explicit instead of turning learning into informal downstream lore.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="learning/refinement/convergence.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.RECOMMENDATION,),
        reason="Convergence logic keeps iterative design learning explicit instead of hiding it inside informal orchestration heuristics.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="learning/refinement/runner.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.RECOMMENDATION,),
        reason="Iterative design runner keeps future-oriented analytical loop behavior explicit under the learning band.",
    ),
    IntelligenceModuleAuditEntry(
        module_path="learning/refinement/stagnation.py",
        classification=IntelligenceModuleClassification.ANALYTICAL_VALUE,
        anchor_capabilities=(IntelligenceCharterCapability.RECOMMENDATION,),
        reason="Stagnation detection keeps iterative-design learning pressure explicit instead of flattening weak loops into progress theater.",
    ),
)


def list_intelligence_capabilities() -> tuple[IntelligenceCharterCapability, ...]:
    """Return the exact analytical capabilities intelligence is allowed to own."""
    return DEFAULT_INTELLIGENCE_CHARTER.capabilities


def list_intelligence_charter_entries() -> tuple[IntelligenceCharterEntry, ...]:
    """Return the exact capability charter entries intelligence must satisfy."""
    return DEFAULT_INTELLIGENCE_CHARTER_ENTRIES


def list_intelligence_analytical_bands() -> tuple[IntelligenceAnalyticalBand, ...]:
    """Return the stable analytical bands intelligence is organized around."""

    return tuple(entry.band for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP)


def list_intelligence_capability_map() -> tuple[IntelligenceCapabilityMapEntry, ...]:
    """Return the authoritative analytical-band capability map."""

    return DEFAULT_INTELLIGENCE_CAPABILITY_MAP


__all__ = [
    "DEFAULT_INTELLIGENCE_CHARTER",
    "DEFAULT_INTELLIGENCE_CHARTER_ENTRIES",
    "DEFAULT_INTELLIGENCE_CAPABILITY_MAP",
    "DEFAULT_INTELLIGENCE_MODULE_AUDIT",
    "IntelligenceAnalyticalBand",
    "IntelligenceCapabilityMapEntry",
    "IntelligenceCharterCapability",
    "IntelligenceCharterEntry",
    "IntelligenceModuleAuditEntry",
    "IntelligenceModuleClassification",
    "IntelligenceProductCharter",
    "list_intelligence_analytical_bands",
    "list_intelligence_capability_map",
    "list_intelligence_capabilities",
    "list_intelligence_charter_entries",
]
