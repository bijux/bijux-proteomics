# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Claim-grounding tables for flagship trust pages and outsider packets."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
)


class ClaimEvidenceKind(StrEnum):
    """Stable evidence-owner categories for grounded narrative claims."""

    BENCHMARK = "benchmark"
    CITATION = "citation"
    COMPARATOR = "comparator"
    GOVERNANCE = "governance"
    INTELLIGENCE = "intelligence"
    LAB = "lab"
    RUNTIME = "runtime"


class ClaimSupportState(StrEnum):
    """Whether the current evidence fully matches the shipped wording."""

    SUPPORTED = "supported"
    THINNER_THAN_WORDING = "thinner_than_wording"


class ScientificClaimSeverity(StrEnum):
    """Severity for grounded-but-still-thin narrative claims."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ClaimNarrativeSurface(StrEnum):
    """Named public narrative surfaces that carry workflow authority language."""

    TRUST_PAGE = "trust_page"
    AUTHORITY_BOUNDARY = "authority_boundary"
    OUTSIDER_PACKET = "outsider_packet"


class ClaimEvidenceRef(JsonModel):
    """One exact evidence owner for a shipped narrative sentence."""

    model_config = ConfigDict(extra="forbid")

    ref_id: str = Field(..., min_length=1)
    evidence_kind: ClaimEvidenceKind
    note: str = Field(..., min_length=1)


class WorkflowClaimCitationEntry(JsonModel):
    """One claim-bearing sentence mapped to exact evidence owners."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    surface: ClaimNarrativeSurface
    surface_locator: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    evidence_refs: tuple[ClaimEvidenceRef, ...] = Field(default_factory=tuple)
    support_state: ClaimSupportState
    note: str = Field(..., min_length=1)


class WorkflowClaimCitationTable(JsonModel):
    """Claim-bearing narrative sentences for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    trust_surface_path: str = Field(..., min_length=1)
    outsider_packet_id: str | None = None
    entries: tuple[WorkflowClaimCitationEntry, ...] = Field(default_factory=tuple)
    coverage_scope_note: str = Field(..., min_length=1)


class WorkflowUnsupportedClaimLedgerEntry(JsonModel):
    """One current sentence whose wording still outruns the public proof."""

    model_config = ConfigDict(extra="forbid")

    ledger_entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    claim_entry_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    scientific_severity: ScientificClaimSeverity
    why_still_thin: str = Field(..., min_length=1)
    strengthening_path: str = Field(..., min_length=1)


class WorkflowUnsupportedClaimLedger(JsonModel):
    """Workflow-family ledger of public wording that still needs stronger proof."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    ledger_id: str = Field(..., min_length=1)
    threshold_blocking_severities: tuple[ScientificClaimSeverity, ...] = Field(
        default_factory=tuple
    )
    entries: tuple[WorkflowUnsupportedClaimLedgerEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class _ClaimBlueprint(JsonModel):
    """Internal blueprint for one claim-bearing sentence."""

    model_config = ConfigDict(extra="forbid")

    claim_text: str = Field(..., min_length=1)
    evidence_refs: tuple[ClaimEvidenceRef, ...] = Field(default_factory=tuple)
    support_state: ClaimSupportState = ClaimSupportState.SUPPORTED
    note: str = Field(..., min_length=1)


def _ref(ref_id: str, evidence_kind: ClaimEvidenceKind, note: str) -> ClaimEvidenceRef:
    return ClaimEvidenceRef(ref_id=ref_id, evidence_kind=evidence_kind, note=note)


def _trust_page_path(workflow_family: KnowledgeWorkflowFamily) -> str:
    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
        return "docs/01-bijux-proteomics/foundation/why-multiplex-stops-at-internal-support.md"
    return f"docs/01-bijux-proteomics/foundation/why-trust-{workflow_family.value}.md"


def _outsider_packet_id(workflow_family: KnowledgeWorkflowFamily) -> str | None:
    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
        return None
    return f"outsider_review:{workflow_family.value}"


_DOC_CLAIMS: dict[KnowledgeWorkflowFamily, tuple[_ClaimBlueprint, ...]] = {
    KnowledgeWorkflowFamily.DDA: (
        _ClaimBlueprint(
            claim_text=(
                "It says the repository now ships two public DDA packages and one "
                "published cross-package report, so a skeptical reviewer can inspect "
                "whether the main DDA claims survive beyond one unusually convenient "
                "package."
            ),
            evidence_refs=(
                _ref(
                    "benchmark:dda_search_reproducibility",
                    ClaimEvidenceKind.BENCHMARK,
                    "The primary DDA benchmark anchors the first public package.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The companion DDA package publishes the cross-package generalization report.",
                ),
            ),
            note="The DDA trust page leads with paired public packages rather than one convenient benchmark lane.",
        ),
        _ClaimBlueprint(
            claim_text="`outsider_review:dda` is complete enough to audit end to end.",
            evidence_refs=(
                _ref(
                    "outsider_review:dda",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The outsider packet is the shipped end-to-end audit surface.",
                ),
                _ref(
                    "docs/01-bijux-proteomics/foundation/workflow-claim-limits.md",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The workflow authority matrix is the current release-facing authority declaration.",
                ),
            ),
            support_state=ClaimSupportState.THINNER_THAN_WORDING,
            note="The packet is strong, but the claim still depends on internal authority accounting instead of an independent rerun dossier.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the runtime package `dda-maxquant-pipeline-corpus` is real and "
                "currently `import_only`, not imaginary execution."
            ),
            evidence_refs=(
                _ref(
                    "dda-maxquant-pipeline-corpus",
                    ClaimEvidenceKind.RUNTIME,
                    "The flagship runtime lane declares the current DDA execution posture.",
                ),
                _ref(
                    "benchmark_runtime_truth:dda_import",
                    ClaimEvidenceKind.RUNTIME,
                    "The runtime truth surface preserves that the lane is import-backed rather than raw-executable.",
                ),
            ),
            note="The DDA runtime claim is grounded in the shipped runtime truth and package id.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the companion Comet-versus-Sage package ships a second engine "
                "pairing and a published family-transfer report at "
                "`packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
                "dda_cross_engine_review_package/cross_package_generalization.json`"
            ),
            evidence_refs=(
                _ref(
                    "benchmark_package:dda_cross_engine_review_package",
                    ClaimEvidenceKind.BENCHMARK,
                    "The companion package is the second public engine-pairing surface.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The published generalization report is the direct cross-package proof.",
                ),
            ),
            note="The DDA trust page must tie its family-transfer claim to the actual tracked generalization artifact.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "adapter-normalized DDA evidence preserves target-decoy semantics "
                "across the pinned fixture corpus"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:dda_search_reproducibility",
                    ClaimEvidenceKind.BENCHMARK,
                    "The benchmark is the primary empirical owner of this DDA claim.",
                ),
                _ref(
                    "citation:target_decoy_2007",
                    ClaimEvidenceKind.CITATION,
                    "The claim is bounded by the target-decoy literature anchor.",
                ),
            ),
            note="This is one of the two exact DDA benchmark-backed claims published for outsiders.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "review-ready DDA evidence retains reviewed-proteome grounding and "
                "explicit field-loss accounting"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:dda_search_reproducibility",
                    ClaimEvidenceKind.BENCHMARK,
                    "The flagship DDA package carries the current reviewed-proteome grounding proof.",
                ),
                _ref(
                    "citation:uniprot_2025",
                    ClaimEvidenceKind.CITATION,
                    "Reviewed-proteome grounding is tied to the UniProt scientific base.",
                ),
            ),
            note="The DDA trust page keeps the second exact claim tied to benchmark and literature owners.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the primary MaxQuant import and MSFragger comparator export are "
                "both shipped"
            ),
            evidence_refs=(
                _ref(
                    "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
                    ClaimEvidenceKind.BENCHMARK,
                    "The primary exported DDA result is checked in.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv",
                    ClaimEvidenceKind.COMPARATOR,
                    "The paired comparator export is checked in beside the primary lane.",
                ),
            ),
            note="This sentence matters because the DDA trust page promises inspectable paired engine evidence.",
        ),
        _ClaimBlueprint(
            claim_text="this is not live-engine rerun parity",
            evidence_refs=(
                _ref(
                    "outsider_review:dda",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The outsider packet keeps the DDA runtime posture explicitly import-backed.",
                ),
                _ref(
                    "benchmark_runtime_truth:dda_import",
                    ClaimEvidenceKind.RUNTIME,
                    "The runtime truth row keeps the lane out of raw-executable language.",
                ),
            ),
            note="The DDA trust page must keep the strongest missing proof stated directly.",
        ),
    ),
    KnowledgeWorkflowFamily.DIA: (
        _ClaimBlueprint(
            claim_text=(
                "The repository now ships two public DIA packages plus one "
                "published cross-package report, so a reviewer can inspect whether "
                "DIA trust survives beyond one library-conditioned package."
            ),
            evidence_refs=(
                _ref(
                    "benchmark:dia_library_extraction_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "The first DIA benchmark package is the primary public package anchor.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The companion DIA package publishes the current cross-package report.",
                ),
            ),
            note="The DIA trust page leads with paired public packages and the current family-transfer artifact.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "`outsider_review:dia` is complete enough to count as an "
                "outsider-auditable flagship family."
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:dia",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The outsider packet is the current public DIA audit packet.",
                ),
                _ref(
                    "docs/01-bijux-proteomics/foundation/workflow-claim-limits.md",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The workflow authority matrix publishes the bounded outsider authority call.",
                ),
            ),
            support_state=ClaimSupportState.THINNER_THAN_WORDING,
            note="The DIA outsider-auditable sentence still depends on internal authority gating rather than an independent external-review kit.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the runtime package `dia-diann-pipeline-corpus` is real and "
                "currently `raw_executable`."
            ),
            evidence_refs=(
                _ref(
                    "dia-diann-pipeline-corpus",
                    ClaimEvidenceKind.RUNTIME,
                    "The flagship DIA runtime lane is the named raw-executable package.",
                ),
                _ref(
                    "benchmark_runtime_truth:dia_import",
                    ClaimEvidenceKind.RUNTIME,
                    "The runtime truth surface preserves the actual DIA execution class.",
                ),
            ),
            note="The DIA runtime posture is a direct runtime proof claim, not a narrative flourish.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "DIA adapter normalization preserves library-conditioned transition "
                "semantics across the pinned export corpus"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:dia_library_extraction_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "The primary DIA benchmark package owns this exported-transition claim.",
                ),
                _ref(
                    "citation:swath_2012",
                    ClaimEvidenceKind.CITATION,
                    "The SWATH/DIA method paper is the core literature anchor.",
                ),
            ),
            note="The first exact DIA claim is intentionally bounded by library-conditioned transition semantics.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "DIA review surfaces keep capability limits explicit instead of "
                "implying vendor-pipeline parity"
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:dia",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The outsider packet carries the explicit capability-limit wording.",
                ),
                _ref(
                    "docs/01-bijux-proteomics/foundation/why-trust-dia.md",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The trust page repeats the same bounded-authority stance.",
                ),
            ),
            note="The second DIA exact claim is about explicit bounded language rather than raw vendor parity.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the DIA-NN and Spectronaut confrontation is visible instead of implied"
            ),
            evidence_refs=(
                _ref(
                    "comparator_confrontation:dia",
                    ClaimEvidenceKind.COMPARATOR,
                    "The comparator confrontation is the primary owner of this sentence.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv",
                    ClaimEvidenceKind.COMPARATOR,
                    "The tracked DIA comparator export keeps the confrontation inspectable.",
                ),
            ),
            note="DIA trust language is only defensible if the paired comparator files remain public.",
        ),
        _ClaimBlueprint(
            claim_text="vendor-library parity is not earned",
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:dia",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The evidence sufficiency rubric keeps DIA out of vendor-parity language.",
                ),
                _ref(
                    "workflow_knowledge_deficit:dia",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The deficit surface preserves the remaining DIA vendor/library gaps.",
                ),
            ),
            note="The trust page must keep the strongest DIA limit explicit.",
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: (
        _ClaimBlueprint(
            claim_text=(
                "What you can trust here is the repo's honesty around missingness, "
                "QC, and bounded cohort interpretation across two public LFQ "
                "packages plus one published cross-package report."
            ),
            evidence_refs=(
                _ref(
                    "benchmark:lfq_cohort_repeatability",
                    ClaimEvidenceKind.BENCHMARK,
                    "The primary LFQ public package anchors the first benchmark lane.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The companion sparse-contrast package provides the current family-transfer artifact.",
                ),
            ),
            note="The LFQ trust page is grounded in paired public packages and one generalization report.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the repository earns a bounded outsider-auditable LFQ claim, not "
                "broad cohort-transfer or decision-grade quant authority."
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:lfq",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The outsider packet is the public bounded-authority LFQ surface.",
                ),
                _ref(
                    "workflow_authority_matrix:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The workflow authority matrix keeps LFQ bounded rather than decision-grade.",
                ),
            ),
            support_state=ClaimSupportState.THINNER_THAN_WORDING,
            note="LFQ authority wording is still ahead of an independent rerun or outcome-bearing quant follow-up.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "LFQ review preserves study-design semantics, missingness "
                "visibility, and repeatable rollup behavior across the bundled "
                "cohort package"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:lfq_cohort_repeatability",
                    ClaimEvidenceKind.BENCHMARK,
                    "The flagship LFQ cohort package owns the primary repeatability claim.",
                ),
                _ref(
                    "citation:protein_inference_2012",
                    ClaimEvidenceKind.CITATION,
                    "Protein rollup caution remains tied to the literature base.",
                ),
            ),
            note="The first exact LFQ claim stays tied to the benchmarked cohort package.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "LFQ benchmark outputs can support review-grade abundance "
                "interpretation when QC and replicate caveats remain explicit"
            ),
            evidence_refs=(
                _ref(
                    "scientific_reading_pack:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The LFQ reading pack and rubric keep the claim at review grade rather than decision grade.",
                ),
                _ref(
                    "citation:uniprot_2025",
                    ClaimEvidenceKind.CITATION,
                    "Protein-meaning interpretation remains tied to the current reviewed-proteome base.",
                ),
            ),
            note="The second exact LFQ claim is explicitly QC- and replicate-bounded.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the runtime bundle now shows normalization, missingness, "
                "differential, and review outputs as one checked flagship run family"
            ),
            evidence_refs=(
                _ref(
                    "lfq-cohort-review-corpus",
                    ClaimEvidenceKind.RUNTIME,
                    "The LFQ runtime lane is the owner of the checked run bundle.",
                ),
                _ref(
                    "benchmark_runtime_truth:quant_review",
                    ClaimEvidenceKind.RUNTIME,
                    "The runtime truth surface preserves the current LFQ run bundle posture.",
                ),
            ),
            note="The LFQ runtime sentence needs explicit runtime owners because it claims one checked run family.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "comparator drift or missing external execution parity still "
                "materially limits this public workflow claim"
            ),
            evidence_refs=(
                _ref(
                    "comparator_confrontation:lfq",
                    ClaimEvidenceKind.COMPARATOR,
                    "The LFQ comparator confrontation explains why parity remains bounded.",
                ),
                _ref(
                    "workflow_knowledge_deficit:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The deficit surface keeps the missing parity proof visible.",
                ),
            ),
            note="The main LFQ limit stays tied to the comparator and deficit surfaces.",
        ),
        _ClaimBlueprint(
            claim_text="broad generalization beyond the two current cohort packages is not earned",
            evidence_refs=(
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The current generalization report is the positive limit boundary for LFQ transfer claims.",
                ),
                _ref(
                    "workflow_generalization:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The workflow generalization surface makes the current family-transfer scope explicit.",
                ),
            ),
            note="LFQ cannot overstate beyond the two current cohort packages.",
        ),
    ),
    KnowledgeWorkflowFamily.PTM: (
        _ClaimBlueprint(
            claim_text=(
                "The trustworthy part today is the repository's ambiguity "
                "discipline around localization, targetability, and follow-up "
                "burden across two public PTM packages plus one published "
                "cross-package report."
            ),
            evidence_refs=(
                _ref(
                    "benchmark:ptm_localization_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "The primary PTM benchmark package anchors the first public lane.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The ambiguity-stress package is the companion public transfer surface.",
                ),
            ),
            note="The PTM trust page is grounded in ambiguity pressure across paired public packages.",
        ),
        _ClaimBlueprint(
            claim_text="PTM is outsider-auditable in a bounded sense, not a decision-grade promotion story.",
            evidence_refs=(
                _ref(
                    "outsider_review:ptm",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The outsider packet is the public PTM bounded-authority surface.",
                ),
                _ref(
                    "workflow_authority_matrix:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The authority matrix blocks decision-grade promotion language for PTM.",
                ),
            ),
            support_state=ClaimSupportState.THINNER_THAN_WORDING,
            note="PTM outsider-auditable language still depends on internal bounded-authority gates instead of independent rerun and comparator breadth.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "PTM review preserves localization confidence, ambiguity, and "
                "PSI-MOD grounding across the pinned phospho-oriented package"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:ptm_localization_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "The flagship PTM package owns this localization-grounding claim.",
                ),
                _ref(
                    "citation:psi_mod_2008",
                    ClaimEvidenceKind.CITATION,
                    "PSI-MOD is the ontology anchor for the grounded PTM claim.",
                ),
            ),
            note="The first exact PTM claim stays tied to localization and ontology owners.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "PTM benchmark outputs separate localized evidence from broader "
                "occupancy or regulatory claims"
            ),
            evidence_refs=(
                _ref(
                    "citation:ascore_2006",
                    ClaimEvidenceKind.CITATION,
                    "Localization confidence and ambiguity are literature-backed boundaries.",
                ),
                _ref(
                    "scientific_reading_pack:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The PTM reading pack keeps occupancy and regulation limits explicit.",
                ),
            ),
            note="The second exact PTM claim is explicitly about separation, not promotion.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the runtime bundle now preserves localization, occupancy, motif, "
                "and lab-targeting outputs inside one checked PTM run family"
            ),
            evidence_refs=(
                _ref(
                    "ptm-localization-review-corpus",
                    ClaimEvidenceKind.RUNTIME,
                    "The PTM runtime lane owns the checked run-family claim.",
                ),
                _ref(
                    "benchmark_runtime_truth:ptm_review",
                    ClaimEvidenceKind.RUNTIME,
                    "The runtime truth surface preserves the PTM run bundle posture.",
                ),
            ),
            note="The PTM trust page claims one checked run family and therefore needs explicit runtime owners.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "occupancy and regulatory interpretation still remain narrower than "
                "localization evidence"
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The PTM sufficiency rubric keeps occupancy and regulation narrower than localization.",
                ),
                _ref(
                    "workflow_knowledge_deficit:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The PTM deficit surface records the broader occupancy and regulation gaps.",
                ),
            ),
            note="PTM trust must keep the main scope boundary explicit.",
        ),
        _ClaimBlueprint(
            claim_text="PTM follow-up remains exploratory",
            evidence_refs=(
                _ref(
                    "flagship_lab_packet:ptm",
                    ClaimEvidenceKind.LAB,
                    "The PTM lab packet posture is still exploratory-only.",
                ),
            ),
            note="The PTM lab consequence posture remains intentionally narrow.",
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        _ClaimBlueprint(
            claim_text=(
                "The trustworthy part today is the explicit QC, calibration, and "
                "interference limit surface across two public targeted packages plus "
                "one published cross-package report."
            ),
            evidence_refs=(
                _ref(
                    "benchmark:targeted_transition_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "The primary targeted benchmark package is the first public lane.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The companion targeted package owns the current family-transfer artifact.",
                ),
            ),
            note="The targeted trust page is grounded in paired public packages and the carryover transfer report.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "The repository earns a bounded outsider-auditable targeted "
                "workflow claim, not a vendor-parity or calibration-clean targeted authority."
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:targeted",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The outsider packet is the current public targeted audit surface.",
                ),
                _ref(
                    "workflow_authority_matrix:targeted",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The authority matrix keeps targeted out of vendor-parity language.",
                ),
            ),
            support_state=ClaimSupportState.THINNER_THAN_WORDING,
            note="Targeted outsider-auditable language still outruns Skyline-class comparator and independent rerun proof.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "targeted benchmark outputs preserve transition-level QC evidence "
                "and explicit protein-inference caution across the bundled "
                "chromatogram package"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:targeted_transition_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "The flagship targeted package owns the transition-level QC claim.",
                ),
                _ref(
                    "citation:protein_inference_2012",
                    ClaimEvidenceKind.CITATION,
                    "Protein-inference caution remains literature-backed.",
                ),
            ),
            note="The first exact targeted claim keeps QC and protein caution together.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "targeted review can support operator-facing QC interpretation "
                "without pretending to prove vendor-parity targeted biology"
            ),
            evidence_refs=(
                _ref(
                    "scientific_reading_pack:targeted",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The targeted reading pack and rubric keep the claim operator-facing rather than vendor-parity.",
                ),
                _ref(
                    "flagship_lab_packet:targeted",
                    ClaimEvidenceKind.LAB,
                    "The current lab packet posture keeps follow-up exploratory and bounded.",
                ),
            ),
            note="The second exact targeted claim is explicitly operator-facing and bounded.",
        ),
        _ClaimBlueprint(
            claim_text="the QC and follow-up packet boundaries are explicit",
            evidence_refs=(
                _ref(
                    "flagship_packet:targeted",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The targeted recommendation packet keeps QC downgrade boundaries public.",
                ),
                _ref(
                    "flagship_lab_packet:targeted",
                    ClaimEvidenceKind.LAB,
                    "The targeted lab packet exposes the follow-up boundary directly.",
                ),
            ),
            note="Targeted authority depends on explicit QC and handoff boundaries.",
        ),
        _ClaimBlueprint(
            claim_text="calibration-clean and vendor-parity targeted authority are not earned",
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:targeted",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The targeted sufficiency rubric blocks calibration-clean and vendor-parity authority.",
                ),
                _ref(
                    "comparator_confrontation:targeted",
                    ClaimEvidenceKind.COMPARATOR,
                    "The targeted comparator surface keeps the missing Skyline-class confrontation visible.",
                ),
            ),
            note="Targeted trust must keep the strongest missing comparator and calibration proof visible.",
        ),
        _ClaimBlueprint(
            claim_text="targeted follow-up remains exploratory",
            evidence_refs=(
                _ref(
                    "flagship_lab_packet:targeted",
                    ClaimEvidenceKind.LAB,
                    "The targeted lab packet still carries exploratory-only posture.",
                ),
            ),
            note="The targeted lab consequence posture remains intentionally narrow.",
        ),
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: (
        _ClaimBlueprint(
            claim_text="`multiplex` is not currently part of the outsider-auditable flagship family set.",
            evidence_refs=(
                _ref(
                    "workflow_authority_matrix:multiplex",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The workflow authority matrix places multiplex in the internal-support set.",
                ),
            ),
            note="The multiplex authority boundary opens with the current authority line rather than adjacent-family borrowing.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "It has a real public package, a raw-executable runtime lane, and "
                "explicit chemistry pressure, plus one companion stress package and "
                "one published cross-package report, but it still lacks a dedicated "
                "outsider decision brief, a requested-versus-observed outcome "
                "dossier, and an assay-worth-it ledger row."
            ),
            evidence_refs=(
                _ref(
                    "benchmark:multiplex_tmtpro_quantification",
                    ClaimEvidenceKind.BENCHMARK,
                    "The primary multiplex benchmark package is public and tracked.",
                ),
                _ref(
                    "benchmark_runtime_truth:multiplex_review",
                    ClaimEvidenceKind.RUNTIME,
                    "The runtime truth surface records the multiplex raw-executable lane.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The companion stress package owns the current cross-package report.",
                ),
            ),
            support_state=ClaimSupportState.THINNER_THAN_WORDING,
            note="The missing outsider-packet and lab-packet sentence is accurate, but the chemistry-pressure wording is still thinner than a dedicated public comparator and lab dossier would make it.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "explicit public chemistry pressure around channel balance, ratio "
                "compression, and missing-channel behavior"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:multiplex_tmtpro_quantification",
                    ClaimEvidenceKind.BENCHMARK,
                    "The public multiplex package owns the channel-balance and ratio-compression story.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The companion stress package keeps the missing-channel and transfer fragility visible.",
                ),
            ),
            note="Multiplex currently owns chemistry pressure through paired benchmark packages, not outsider review authority.",
        ),
        _ClaimBlueprint(
            claim_text="lab-consequential authority",
            evidence_refs=(
                _ref(
                    "workflow_authority_matrix:multiplex",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The authority matrix keeps multiplex out of lab-consequential language.",
                ),
            ),
            note="The multiplex boundary page lists lab-consequential authority among what remains unearned.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the current cross-package report labels that transfer "
                "`fragile_transfer`"
            ),
            evidence_refs=(
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The published cross-package report names the current transfer posture directly.",
                ),
            ),
            note="The multiplex boundary must cite the current fragile-transfer artifact directly.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Until outsider review and lab consequence surfaces exist, multiplex "
                "stays an internal-support family and should not be described as an "
                "outsider-auditable flagship family, even though it now has a second "
                "public package and one published family-transfer report."
            ),
            evidence_refs=(
                _ref(
                    "workflow_authority_matrix:multiplex",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The internal-support-only authority call is the release-facing boundary owner.",
                ),
                _ref(
                    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/cross_package_generalization.json",
                    ClaimEvidenceKind.BENCHMARK,
                    "The second package and published family-transfer report are the exact evidence named by the boundary sentence.",
                ),
            ),
            note="Multiplex keeps the strongest narrowing sentence explicit so adjacent-family authority cannot leak across.",
        ),
    ),
}


_PACKET_CLAIMS: dict[KnowledgeWorkflowFamily, tuple[_ClaimBlueprint, ...]] = {
    KnowledgeWorkflowFamily.DDA: (
        _ClaimBlueprint(
            claim_text=(
                "adapter-normalized DDA evidence preserves target-decoy semantics "
                "across the pinned fixture corpus"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:dda_search_reproducibility",
                    ClaimEvidenceKind.BENCHMARK,
                    "Primary DDA benchmark owner.",
                ),
                _ref(
                    "citation:target_decoy_2007",
                    ClaimEvidenceKind.CITATION,
                    "Target-decoy literature owner.",
                ),
            ),
            note="The DDA outsider packet repeats the first exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "review-ready DDA evidence retains reviewed-proteome grounding and "
                "explicit field-loss accounting"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:dda_search_reproducibility",
                    ClaimEvidenceKind.BENCHMARK,
                    "Primary DDA benchmark owner.",
                ),
                _ref(
                    "citation:uniprot_2025",
                    ClaimEvidenceKind.CITATION,
                    "Reviewed-proteome literature owner.",
                ),
            ),
            note="The DDA outsider packet repeats the second exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "comparator drift or missing external execution parity still "
                "materially limits this public workflow claim"
            ),
            evidence_refs=(
                _ref(
                    "comparator_confrontation:dda",
                    ClaimEvidenceKind.COMPARATOR,
                    "The DDA comparator confrontation keeps the main public limit explicit.",
                ),
                _ref(
                    "workflow_knowledge_deficit:dda",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The DDA deficit surface records the remaining parity gap.",
                ),
            ),
            note="This is the main repeated DDA limiting sentence across packet sections.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "add live-engine replay or stronger external DDA output comparison "
                "so claim trust does not stop at pinned export normalization"
            ),
            evidence_refs=(
                _ref(
                    "workflow_knowledge_deficit:dda",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The DDA deficit surface names the missing stronger replay and comparator path.",
                ),
                _ref(
                    "benchmark_runtime_truth:dda_import",
                    ClaimEvidenceKind.RUNTIME,
                    "The import-backed runtime posture explains why live replay is still a gap.",
                ),
            ),
            note="The DDA outsider packet states the next strongest proof upgrade rather than hiding it.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Applies to adapter-normalized DDA search outputs in the bundled "
                "fixture corpus, not arbitrary production exports."
            ),
            evidence_refs=(
                _ref(
                    "narrative:dda_evidence_claim",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The DDA narrative keeps the benchmark scope explicit.",
                ),
                _ref(
                    "benchmark:dda_search_reproducibility",
                    ClaimEvidenceKind.BENCHMARK,
                    "The benchmark is bounded to the bundled fixture corpus.",
                ),
            ),
            note="The packet keeps the DDA benchmark scope explicit.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Decision-grade DDA requires preserved target-decoy semantics, "
                "cross-engine accountability, and protein inference behavior that "
                "remains stable under contaminant and adapter pressure."
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:dda",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The DDA sufficiency rubric owns the decision-grade bar.",
                ),
                _ref(
                    "comparator_confrontation:dda",
                    ClaimEvidenceKind.COMPARATOR,
                    "Cross-engine accountability is tied to the public confrontation surface.",
                ),
            ),
            note="The packet states the current DDA decision-grade bar explicitly.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "The outsider packet exists to let a skeptical reviewer inspect the "
                "current flagship workflow posture from tracked files, runtime "
                "evidence, scientific reading, recommendation logic, planned assay "
                "boundaries, and shipped requested-versus-observed lab consequence "
                "without maintainer narration."
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:dda",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The DDA outsider packet is itself the public inspection bundle.",
                ),
                _ref(
                    "scientific_reading_pack:dda",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The scientific reading pack is one of the required evidence owners named by the note.",
                ),
                _ref(
                    "flagship_packet:dda",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The recommendation packet is one of the named packet owners.",
                ),
                _ref(
                    "flagship_lab_packet:dda",
                    ClaimEvidenceKind.LAB,
                    "The lab packet is the named consequence owner.",
                ),
            ),
            note="The packet note is itself a public contract about what outsiders can inspect without narration.",
        ),
    ),
    KnowledgeWorkflowFamily.DIA: (
        _ClaimBlueprint(
            claim_text=(
                "DIA adapter normalization preserves library-conditioned transition "
                "semantics across the pinned export corpus"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:dia_library_extraction_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "Primary DIA benchmark owner.",
                ),
                _ref(
                    "citation:swath_2012",
                    ClaimEvidenceKind.CITATION,
                    "DIA method literature owner.",
                ),
            ),
            note="The DIA outsider packet repeats the first exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "DIA review surfaces keep capability limits explicit instead of "
                "implying vendor-pipeline parity"
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:dia",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The DIA packet keeps capability limits public.",
                ),
                _ref(
                    "workflow_authority_matrix:dia",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The bounded DIA authority call is published in the matrix.",
                ),
            ),
            note="The DIA outsider packet repeats the second exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "expand DIA comparator pressure beyond checked-in reports so library "
                "and vendor drift can change release posture explicitly"
            ),
            evidence_refs=(
                _ref(
                    "workflow_knowledge_deficit:dia",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The DIA deficit surface records the remaining comparator and vendor drift gap.",
                ),
                _ref(
                    "comparator_confrontation:dia",
                    ClaimEvidenceKind.COMPARATOR,
                    "The current confrontation is the present comparator floor.",
                ),
            ),
            note="The DIA packet names the next public proof step instead of hiding it.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "DIA review claims stop at checked-in external-engine exports and "
                "explicit capability notes."
            ),
            evidence_refs=(
                _ref(
                    "benchmark_runtime_truth:dia_import",
                    ClaimEvidenceKind.RUNTIME,
                    "The DIA runtime truth and packet limits explain the export-bounded posture.",
                ),
                _ref(
                    "narrative:dia_limitation",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The DIA limitation narrative keeps the export-bounded scope explicit.",
                ),
            ),
            note="The DIA packet states that checked-in exports remain the current proof boundary.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Decision-grade DIA requires strong library-conditioned import, "
                "transition semantics, protein evidence, and biological-interpretation "
                "tiers with explicit comparator limits."
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:dia",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The DIA sufficiency rubric owns the decision-grade bar.",
                ),
                _ref(
                    "comparator_confrontation:dia",
                    ClaimEvidenceKind.COMPARATOR,
                    "Comparator limits remain a named part of the decision-grade threshold.",
                ),
            ),
            note="The DIA packet states the current decision-grade bar directly.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "the current reproduction story still depends on execution steps "
                "that remain outside the repository proof boundary"
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:dia",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The DIA outsider packet preserves this reproduction limit directly.",
                ),
                _ref(
                    "workflow_knowledge_deficit:dia",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The DIA deficit surface keeps the remaining reproduction gap visible.",
                ),
            ),
            note="The packet keeps the strongest non-comparator DIA limit explicit.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "The outsider packet exists to let a skeptical reviewer inspect the "
                "current flagship workflow posture from tracked files, runtime "
                "evidence, scientific reading, recommendation logic, planned assay "
                "boundaries, and shipped requested-versus-observed lab consequence "
                "without maintainer narration."
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:dia",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The DIA outsider packet is itself the public inspection bundle.",
                ),
                _ref(
                    "scientific_reading_pack:dia",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The scientific reading pack is one named evidence owner.",
                ),
                _ref(
                    "flagship_packet:dia",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The recommendation packet is one named evidence owner.",
                ),
                _ref(
                    "flagship_lab_packet:dia",
                    ClaimEvidenceKind.LAB,
                    "The lab packet is the named consequence owner.",
                ),
            ),
            note="The shared outsider-packet note is still a public contract for DIA inspection.",
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: (
        _ClaimBlueprint(
            claim_text=(
                "LFQ review preserves study-design semantics, missingness "
                "visibility, and repeatable rollup behavior across the bundled fixture"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:lfq_cohort_repeatability",
                    ClaimEvidenceKind.BENCHMARK,
                    "Primary LFQ benchmark owner.",
                ),
                _ref(
                    "citation:protein_inference_2012",
                    ClaimEvidenceKind.CITATION,
                    "LFQ rollup-caution literature owner.",
                ),
            ),
            note="The LFQ outsider packet repeats the first exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "LFQ benchmark outputs can support review-grade abundance "
                "interpretation when QC and replicate caveats remain explicit"
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The LFQ rubric owns the review-grade threshold.",
                ),
                _ref(
                    "benchmark:lfq_cohort_repeatability",
                    ClaimEvidenceKind.BENCHMARK,
                    "The primary LFQ benchmark is the empirical owner.",
                ),
            ),
            note="The LFQ outsider packet repeats the second exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "add stronger external quant comparator pressure so repeatability "
                "and effect-size claims are not inferred from fixture stability alone"
            ),
            evidence_refs=(
                _ref(
                    "workflow_knowledge_deficit:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The LFQ deficit surface records the missing stronger comparator path.",
                ),
                _ref(
                    "comparator_confrontation:lfq",
                    ClaimEvidenceKind.COMPARATOR,
                    "The current comparator confrontation is the present floor.",
                ),
            ),
            note="The LFQ packet states the next proof upgrade directly.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Decision-grade LFQ requires stable replicate structure, controlled "
                "missingness, batch-aware normalization, and comparator-bounded "
                "abundance claims."
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The LFQ sufficiency rubric owns the decision-grade bar.",
                ),
                _ref(
                    "scientific_reading_pack:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The reading pack preserves the missingness and batch boundary.",
                ),
            ),
            note="The LFQ packet states the current decision-grade bar directly.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Do not spend the assay if only one extra sample can be added to a "
                "fragile contrast."
            ),
            evidence_refs=(
                _ref(
                    "flagship_lab_packet:lfq",
                    ClaimEvidenceKind.LAB,
                    "The LFQ lab packet owns the current operational refusal boundary.",
                ),
            ),
            note="The LFQ packet ties assay refusal to a concrete operational boundary.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "The outsider packet exists to let a skeptical reviewer inspect the "
                "current flagship workflow posture from tracked files, runtime "
                "evidence, scientific reading, recommendation logic, planned assay "
                "boundaries, and shipped requested-versus-observed lab consequence "
                "without maintainer narration."
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:lfq",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The LFQ outsider packet is itself the public inspection bundle.",
                ),
                _ref(
                    "scientific_reading_pack:lfq",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The scientific reading pack is one named evidence owner.",
                ),
                _ref(
                    "flagship_packet:lfq",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The recommendation packet is one named evidence owner.",
                ),
                _ref(
                    "flagship_lab_packet:lfq",
                    ClaimEvidenceKind.LAB,
                    "The lab packet is the named consequence owner.",
                ),
            ),
            note="The shared outsider-packet note is still a public contract for LFQ inspection.",
        ),
    ),
    KnowledgeWorkflowFamily.PTM: (
        _ClaimBlueprint(
            claim_text=(
                "PTM review preserves localization confidence, ambiguity, and "
                "PSI-MOD grounding across the pinned phospho-oriented fixture"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:ptm_localization_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "Primary PTM benchmark owner.",
                ),
                _ref(
                    "citation:psi_mod_2008",
                    ClaimEvidenceKind.CITATION,
                    "PTM ontology owner.",
                ),
            ),
            note="The PTM outsider packet repeats the first exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "PTM benchmark outputs separate localized evidence from broader "
                "occupancy or regulatory claims"
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The PTM rubric keeps occupancy and regulation narrower than localization.",
                ),
                _ref(
                    "citation:ascore_2006",
                    ClaimEvidenceKind.CITATION,
                    "Localization-confidence literature owner.",
                ),
            ),
            note="The PTM outsider packet repeats the second exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "add stronger rescoring or external PTM comparator evidence so "
                "localization trust is not limited to imported tables"
            ),
            evidence_refs=(
                _ref(
                    "workflow_knowledge_deficit:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The PTM deficit surface records the missing rescoring and comparator breadth.",
                ),
                _ref(
                    "comparator_confrontation:ptm",
                    ClaimEvidenceKind.COMPARATOR,
                    "The PTM confrontation is the current comparator floor.",
                ),
            ),
            note="The PTM packet states the next stronger proof path directly.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Decision-grade PTM requires localization confidence, ambiguity "
                "propagation control, family-specific credibility, and "
                "literature-bounded site interpretation."
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The PTM sufficiency rubric owns the decision-grade bar.",
                ),
                _ref(
                    "scientific_reading_pack:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The PTM reading pack preserves the family-specific and site-interpretation boundaries.",
                ),
            ),
            note="The PTM packet states the current decision-grade bar directly.",
        ),
        _ClaimBlueprint(
            claim_text="operational burden remains too high for a justified recommendation",
            evidence_refs=(
                _ref(
                    "flagship_lab_packet:ptm",
                    ClaimEvidenceKind.LAB,
                    "The PTM lab packet owns the current operational burden refusal.",
                ),
            ),
            note="The PTM packet keeps the current lab burden limit explicit.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "The outsider packet exists to let a skeptical reviewer inspect the "
                "current flagship workflow posture from tracked files, runtime "
                "evidence, scientific reading, recommendation logic, planned assay "
                "boundaries, and shipped requested-versus-observed lab consequence "
                "without maintainer narration."
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:ptm",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The PTM outsider packet is itself the public inspection bundle.",
                ),
                _ref(
                    "scientific_reading_pack:ptm",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The scientific reading pack is one named evidence owner.",
                ),
                _ref(
                    "flagship_packet:ptm",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The recommendation packet is one named evidence owner.",
                ),
                _ref(
                    "flagship_lab_packet:ptm",
                    ClaimEvidenceKind.LAB,
                    "The lab packet is the named consequence owner.",
                ),
            ),
            note="The shared outsider-packet note is still a public contract for PTM inspection.",
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        _ClaimBlueprint(
            claim_text=(
                "Targeted benchmark outputs preserve transition-level QC evidence "
                "and explicit protein-inference caution across the bundled "
                "chromatogram fixture"
            ),
            evidence_refs=(
                _ref(
                    "benchmark:targeted_transition_consistency",
                    ClaimEvidenceKind.BENCHMARK,
                    "Primary targeted benchmark owner.",
                ),
                _ref(
                    "citation:protein_inference_2012",
                    ClaimEvidenceKind.CITATION,
                    "Targeted protein-caution literature owner.",
                ),
            ),
            note="The targeted outsider packet repeats the first exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Targeted review can support operator-facing QC interpretation "
                "without pretending to prove vendor-parity targeted biology"
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:targeted",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The targeted rubric owns the bounded operator-facing threshold.",
                ),
                _ref(
                    "flagship_lab_packet:targeted",
                    ClaimEvidenceKind.LAB,
                    "The targeted lab packet keeps the outcome posture exploratory.",
                ),
            ),
            note="The targeted outsider packet repeats the second exact public claim.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "build a raw-to-reviewed targeted comparator against Skyline-class "
                "chromatogram workflows so targeted support stops losing on "
                "calibration and interference realism"
            ),
            evidence_refs=(
                _ref(
                    "workflow_knowledge_deficit:targeted",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The targeted deficit surface records the missing Skyline-class confrontation.",
                ),
                _ref(
                    "comparator_confrontation:targeted",
                    ClaimEvidenceKind.COMPARATOR,
                    "The targeted confrontation is the current comparator floor.",
                ),
            ),
            note="The targeted packet states the next stronger proof path directly.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "Decision-grade targeted support requires chromatogram QC, "
                "calibration standards, heavy references, control coverage, honest "
                "handoff packets, and reconciled outcomes."
            ),
            evidence_refs=(
                _ref(
                    "workflow_evidence_sufficiency:targeted",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The targeted sufficiency rubric owns the decision-grade bar.",
                ),
                _ref(
                    "flagship_lab_packet:targeted",
                    ClaimEvidenceKind.LAB,
                    "The targeted lab packet owns the handoff and reconciled-outcome boundary.",
                ),
            ),
            note="The targeted packet states the current decision-grade bar directly.",
        ),
        _ClaimBlueprint(
            claim_text="operational burden remains too high for a justified recommendation",
            evidence_refs=(
                _ref(
                    "flagship_lab_packet:targeted",
                    ClaimEvidenceKind.LAB,
                    "The targeted lab packet owns the current operational burden refusal.",
                ),
            ),
            note="The targeted packet keeps the current lab burden limit explicit.",
        ),
        _ClaimBlueprint(
            claim_text=(
                "The outsider packet exists to let a skeptical reviewer inspect the "
                "current flagship workflow posture from tracked files, runtime "
                "evidence, scientific reading, recommendation logic, planned assay "
                "boundaries, and shipped requested-versus-observed lab consequence "
                "without maintainer narration."
            ),
            evidence_refs=(
                _ref(
                    "outsider_review:targeted",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The targeted outsider packet is itself the public inspection bundle.",
                ),
                _ref(
                    "scientific_reading_pack:targeted",
                    ClaimEvidenceKind.GOVERNANCE,
                    "The scientific reading pack is one named evidence owner.",
                ),
                _ref(
                    "flagship_packet:targeted",
                    ClaimEvidenceKind.INTELLIGENCE,
                    "The recommendation packet is one named evidence owner.",
                ),
                _ref(
                    "flagship_lab_packet:targeted",
                    ClaimEvidenceKind.LAB,
                    "The lab packet is the named consequence owner.",
                ),
            ),
            note="The shared outsider-packet note is still a public contract for targeted inspection.",
        ),
    ),
}


_UNSUPPORTED_CLAIM_BLUEPRINTS: dict[
    KnowledgeWorkflowFamily,
    tuple[tuple[str, ScientificClaimSeverity, str, str], ...],
] = {
    KnowledgeWorkflowFamily.DDA: (
        (
            "`outsider_review:dda` is complete enough to audit end to end.",
            ScientificClaimSeverity.LOW,
            "The packet is strong and internally consistent, but the repository still lacks an independent rerun dossier or external-review kit that would make the wording less governance-dependent.",
            "Ship the independent DDA rerun dossier and the DDA external-review kit together so outsider-auditable language depends less on internal proof accounting.",
        ),
    ),
    KnowledgeWorkflowFamily.DIA: (
        (
            "`outsider_review:dia` is complete enough to count as an outsider-auditable flagship family.",
            ScientificClaimSeverity.LOW,
            "The current sentence still leans on internal acceptance and authority gates while the independent rerun dossier, vendor-conditioned rerun proof, and external-review-kit proof remain thinner than the wording sounds.",
            "Ship the DIA independent rerun dossier and the DIA external-review kit so outsider-auditable wording depends less on internal release governance.",
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: (
        (
            "the repository earns a bounded outsider-auditable LFQ claim, not broad cohort-transfer or decision-grade quant authority.",
            ScientificClaimSeverity.LOW,
            "The wording is cautious, but the outsider-auditable part still rests on two public cohort packages without an observed outcome loop or independent rerun dossier.",
            "Add the LFQ observed follow-up outcome dossier plus the independent rerun kit so outsider-auditable wording depends on more than bounded internal proof surfaces.",
        ),
    ),
    KnowledgeWorkflowFamily.PTM: (
        (
            "PTM is outsider-auditable in a bounded sense, not a decision-grade promotion story.",
            ScientificClaimSeverity.LOW,
            "The sentence is bounded, but the outsider-auditable call still leans on internal authority accounting while wider PTM-family and comparator breadth remain thin.",
            "Ship the PTM independent rerun dossier and stronger external PTM confrontation so the outsider-auditable call rests on harder public proof.",
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        (
            "The repository earns a bounded outsider-auditable targeted workflow claim, not a vendor-parity or calibration-clean targeted authority.",
            ScientificClaimSeverity.LOW,
            "The bounded wording is honest, but the outsider-auditable part still outruns Skyline-class confrontation and independent rerun proof.",
            "Ship the targeted independent rerun dossier and Skyline-class external-review kit so the bounded outsider-auditable sentence depends less on internal gates.",
        ),
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: (
        (
            "It has a real public package, a raw-executable runtime lane, and explicit chemistry pressure, plus one companion stress package and one published cross-package report, but it still lacks a dedicated outsider decision brief, a requested-versus-observed outcome dossier, and an assay-worth-it ledger row.",
            ScientificClaimSeverity.LOW,
            "The narrowing is honest, but chemistry-pressure authority remains internal because the companion stress package fails the outsider boundary and no lab consequence packet closes the downstream gap.",
            "Ship a dedicated multiplex outsider decision brief and a dedicated multiplex lab consequence packet before promoting any stronger public chemistry-pressure language.",
        ),
    ),
}


def _entries_for_surface(
    workflow_family: KnowledgeWorkflowFamily,
    surface: ClaimNarrativeSurface,
    surface_locator: str,
    blueprints: tuple[_ClaimBlueprint, ...],
) -> tuple[WorkflowClaimCitationEntry, ...]:
    return tuple(
        WorkflowClaimCitationEntry(
            entry_id=(
                f"claim_grounding:{workflow_family.value}:{surface.value}:{index}"
            ),
            workflow_family=workflow_family,
            surface=surface,
            surface_locator=surface_locator,
            claim_text=blueprint.claim_text,
            evidence_refs=blueprint.evidence_refs,
            support_state=blueprint.support_state,
            note=blueprint.note,
        )
        for index, blueprint in enumerate(blueprints, start=1)
    )


def build_workflow_claim_citation_table(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowClaimCitationTable:
    """Build the claim-bearing sentence map for one workflow family."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    trust_surface = (
        ClaimNarrativeSurface.AUTHORITY_BOUNDARY
        if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX
        else ClaimNarrativeSurface.TRUST_PAGE
    )
    entries = [
        *_entries_for_surface(
            workflow_family,
            trust_surface,
            _trust_page_path(workflow_family),
            _DOC_CLAIMS[workflow_family],
        )
    ]
    outsider_packet_id = _outsider_packet_id(workflow_family)
    if outsider_packet_id is not None:
        entries.extend(
            _entries_for_surface(
                workflow_family,
                ClaimNarrativeSurface.OUTSIDER_PACKET,
                outsider_packet_id,
                _PACKET_CLAIMS[workflow_family],
            )
        )
    return WorkflowClaimCitationTable(
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        trust_surface_path=_trust_page_path(workflow_family),
        outsider_packet_id=outsider_packet_id,
        entries=tuple(entries),
        coverage_scope_note=(
            "This table covers the claim-bearing narrative sentences carried by the "
            "public trust page or authority-boundary page and, when present, the "
            "outsider packet narrative fields. It intentionally excludes artifact-link "
            "labels, section headers, and raw citation digest lines."
        ),
    )


def list_workflow_claim_citation_tables() -> tuple[WorkflowClaimCitationTable, ...]:
    """Return claim-grounding tables across all workflow families."""

    return tuple(
        build_workflow_claim_citation_table(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


def build_workflow_unsupported_claim_ledger(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowUnsupportedClaimLedger:
    """Build the unsupported-claim ledger for one workflow family."""

    table = build_workflow_claim_citation_table(workflow_family)
    entry_by_claim_text = {entry.claim_text: entry for entry in table.entries}
    entries = []
    for index, (claim_text, severity, why_thin, strengthening_path) in enumerate(
        _UNSUPPORTED_CLAIM_BLUEPRINTS[workflow_family],
        start=1,
    ):
        claim_entry = entry_by_claim_text[claim_text]
        entries.append(
            WorkflowUnsupportedClaimLedgerEntry(
                ledger_entry_id=f"unsupported_claim_ledger:{workflow_family.value}:{index}",
                workflow_family=workflow_family,
                claim_entry_id=claim_entry.entry_id,
                claim_text=claim_entry.claim_text,
                scientific_severity=severity,
                why_still_thin=why_thin,
                strengthening_path=strengthening_path,
            )
        )
    return WorkflowUnsupportedClaimLedger(
        workflow_family=workflow_family,
        ledger_id=f"unsupported_claim_ledger:{workflow_family.value}",
        threshold_blocking_severities=(
            ScientificClaimSeverity.MEDIUM,
            ScientificClaimSeverity.HIGH,
        ),
        entries=tuple(entries),
        note=(
            "This ledger lists only the currently shipped sentences whose wording is "
            "still somewhat stronger than the current public proof. The threshold is "
            "intentionally stricter than the low-severity entries listed here."
        ),
    )


def list_workflow_unsupported_claim_ledgers() -> tuple[
    WorkflowUnsupportedClaimLedger, ...
]:
    """Return unsupported-claim ledgers across all workflow families."""

    return tuple(
        build_workflow_unsupported_claim_ledger(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


__all__ = [
    "ClaimEvidenceKind",
    "ClaimEvidenceRef",
    "ClaimNarrativeSurface",
    "ClaimSupportState",
    "ScientificClaimSeverity",
    "WorkflowClaimCitationEntry",
    "WorkflowClaimCitationTable",
    "WorkflowUnsupportedClaimLedger",
    "WorkflowUnsupportedClaimLedgerEntry",
    "build_workflow_claim_citation_table",
    "build_workflow_unsupported_claim_ledger",
    "list_workflow_claim_citation_tables",
    "list_workflow_unsupported_claim_ledgers",
]
