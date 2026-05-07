# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Comparator paths and matrix surfaces for external proteomics-tool scrutiny."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


class ProteomicsComparatorTool(StrEnum):
    """Established external-tool surfaces compared against repo-owned behavior."""

    DIANN = "diann"
    MAXQUANT = "maxquant"
    MSFRAGGER = "msfragger"
    SKYLINE = "skyline"
    SPECTRONAUT = "spectronaut"


class ComparatorBehaviorStatus(StrEnum):
    """Exact posture for one named comparator behavior."""

    DOES_NOT_ATTEMPT = "does_not_attempt"
    MATCHES = "matches"
    PARTIAL = "partial"
    REFUSES = "refuses"


class ComparatorBehaviorClaim(JsonModel):
    """One explicit behavior claim for a comparator tool."""

    model_config = ConfigDict(extra="forbid")

    behavior_id: str = Field(..., min_length=1)
    status: ComparatorBehaviorStatus
    summary: str = Field(..., min_length=1)


class WorkflowComparatorPath(JsonModel):
    """One reproducible comparison path anchored to checked-in comparator artifacts."""

    model_config = ConfigDict(extra="forbid")

    comparator_path_id: str = Field(..., min_length=1)
    comparator_tool: ProteomicsComparatorTool
    benchmark_ids: tuple[str, ...] = Field(..., min_length=1)
    workflow_families: tuple[KnowledgeWorkflowFamily, ...] = Field(..., min_length=1)
    comparison_summary: str = Field(..., min_length=1)
    fixture_paths: tuple[str, ...] = Field(..., min_length=1)
    owned_surfaces: tuple[str, ...] = Field(..., min_length=1)
    comparison_behaviors: tuple[ComparatorBehaviorClaim, ...] = Field(..., min_length=1)
    non_goals: tuple[str, ...] = Field(..., min_length=1)

    @field_validator(
        "benchmark_ids",
        "fixture_paths",
        "owned_surfaces",
        "non_goals",
    )
    @classmethod
    def _forbid_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if not cleaned:
            raise ValueError("at least one non-blank value is required")
        return cleaned


class WorkflowComparatorToolStatus(JsonModel):
    """Exact match/partial/refusal posture for one tool within one workflow family."""

    model_config = ConfigDict(extra="forbid")

    comparator_tool: ProteomicsComparatorTool
    comparator_path_ids: tuple[str, ...] = Field(default_factory=tuple)
    matched_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    partial_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    refused_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    not_attempted_behaviors: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowComparatorMatrixEntry(JsonModel):
    """Workflow-family comparator matrix that names exact behavior posture."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    workflow_summary: str = Field(..., min_length=1)
    tool_statuses: tuple[WorkflowComparatorToolStatus, ...] = Field(
        default_factory=tuple
    )


class WorkflowComparatorMatrixReport(JsonModel):
    """Public comparator matrix across workflow families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowComparatorMatrixEntry, ...] = Field(default_factory=tuple)


DEFAULT_WORKFLOW_COMPARATOR_PATHS: tuple[WorkflowComparatorPath, ...] = (
    WorkflowComparatorPath(
        comparator_path_id="comparator_path:msfragger_imported_dda_review",
        comparator_tool=ProteomicsComparatorTool.MSFRAGGER,
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        workflow_families=(KnowledgeWorkflowFamily.DDA,),
        comparison_summary="MSFragger comparison path checks whether adapter-normalized DDA evidence and review-ready outputs preserve the same bounded import semantics as the pinned external-engine export.",
        fixture_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_results.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger.params",
        ),
        owned_surfaces=(
            "bijux-proteomics-core: identification.search_adapters",
            "bijux-proteomics-core: identification.review_ready_evidence_bundle",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        comparison_behaviors=(
            ComparatorBehaviorClaim(
                behavior_id="adapter_normalized_dda_import",
                status=ComparatorBehaviorStatus.MATCHES,
                summary="adapter-normalized DDA import preserves pinned MSFragger peptide and protein evidence semantics for review",
            ),
            ComparatorBehaviorClaim(
                behavior_id="target_decoy_scope_visibility",
                status=ComparatorBehaviorStatus.MATCHES,
                summary="target-decoy confidence posture remains explicit in review-ready outputs instead of being flattened away",
            ),
            ComparatorBehaviorClaim(
                behavior_id="live_engine_rerun_parity",
                status=ComparatorBehaviorStatus.DOES_NOT_ATTEMPT,
                summary="the repository does not rerun MSFragger or claim raw-spectrum scoring parity inside the benchmark path",
            ),
        ),
        non_goals=(
            "raw-spectrum scoring equivalence to live MSFragger execution",
            "engine-side calibration or search-space tuning parity outside the pinned export",
        ),
    ),
    WorkflowComparatorPath(
        comparator_path_id="comparator_path:spectronaut_dia_review_contracts",
        comparator_tool=ProteomicsComparatorTool.SPECTRONAUT,
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        workflow_families=(KnowledgeWorkflowFamily.DIA,),
        comparison_summary="Spectronaut-style comparison path tests whether checked-in DIA exports normalize into the same bounded extraction and review contracts owned by the repository.",
        fixture_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_pipeline_export.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_settings.txt",
        ),
        owned_surfaces=(
            "bijux-proteomics-core: identification.search_adapters",
            "bijux-proteomics-core: dia.capability_matrix",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        comparison_behaviors=(
            ComparatorBehaviorClaim(
                behavior_id="dia_report_normalization",
                status=ComparatorBehaviorStatus.MATCHES,
                summary="Spectronaut-style exports normalize into governed DIA review-ready evidence without dropping acquisition semantics",
            ),
            ComparatorBehaviorClaim(
                behavior_id="library_conditioned_capability_review",
                status=ComparatorBehaviorStatus.PARTIAL,
                summary="the repository can review library-conditioned extraction posture but does not claim full vendor library-building parity",
            ),
            ComparatorBehaviorClaim(
                behavior_id="vendor_execution_parity",
                status=ComparatorBehaviorStatus.DOES_NOT_ATTEMPT,
                summary="the benchmark path does not execute Spectronaut or claim chromatogram-level vendor parity",
            ),
        ),
        non_goals=(
            "full vendor-library construction parity",
            "live Spectronaut execution or chromatogram-level DIA tuning parity",
        ),
    ),
    WorkflowComparatorPath(
        comparator_path_id="comparator_path:maxquant_evidence_import_contracts",
        comparator_tool=ProteomicsComparatorTool.MAXQUANT,
        benchmark_ids=(
            "benchmark:dda_search_reproducibility",
            "benchmark:lfq_quantification_repeatability",
            "benchmark:ptm_site_localization_confidence",
        ),
        workflow_families=(
            KnowledgeWorkflowFamily.DDA,
            KnowledgeWorkflowFamily.LFQ,
            KnowledgeWorkflowFamily.PTM,
        ),
        comparison_summary="MaxQuant comparison path checks whether evidence import can feed protein inference, LFQ review, and PTM localization surfaces without claiming full MaxQuant workflow equivalence.",
        fixture_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_evidence.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_settings.txt",
        ),
        owned_surfaces=(
            "bijux-proteomics-core: identification.search_adapters",
            "bijux-proteomics-core: quantification.review",
            "bijux-proteomics-core: ptm.localization",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        comparison_behaviors=(
            ComparatorBehaviorClaim(
                behavior_id="evidence_import_visibility",
                status=ComparatorBehaviorStatus.MATCHES,
                summary="MaxQuant-style evidence imports retain peptide, protein, and modification evidence needed by downstream review contracts",
            ),
            ComparatorBehaviorClaim(
                behavior_id="lfq_and_ptm_downstream_contracts",
                status=ComparatorBehaviorStatus.PARTIAL,
                summary="LFQ and PTM downstream review contracts stay governed after import, but the repository does not claim full MaxQuant algorithmic parity",
            ),
            ComparatorBehaviorClaim(
                behavior_id="protein_inference_overclaim_refusal",
                status=ComparatorBehaviorStatus.REFUSES,
                summary="the repository refuses to treat imported MaxQuant evidence as automatic protein-certainty truth without explicit review caveats",
            ),
        ),
        non_goals=(
            "full Andromeda scoring parity and protein-group algorithm equivalence",
            "unqualified LFQ or PTM parity with live MaxQuant execution",
        ),
    ),
    WorkflowComparatorPath(
        comparator_path_id="comparator_path:diann_report_normalization_contracts",
        comparator_tool=ProteomicsComparatorTool.DIANN,
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        workflow_families=(KnowledgeWorkflowFamily.DIA,),
        comparison_summary="DIA-NN comparison path checks whether DIA report normalization and review outputs stay transparent about library assumptions and comparator limits.",
        fixture_paths=(
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv",
            "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_config.json",
        ),
        owned_surfaces=(
            "bijux-proteomics-core: identification.search_adapters",
            "bijux-proteomics-core: dia.capability_matrix",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        comparison_behaviors=(
            ComparatorBehaviorClaim(
                behavior_id="dia_report_import_and_normalization",
                status=ComparatorBehaviorStatus.MATCHES,
                summary="DIA-NN-style reports normalize into the same governed DIA evidence surface used for review-ready outputs",
            ),
            ComparatorBehaviorClaim(
                behavior_id="library_and_classifier_assumption_visibility",
                status=ComparatorBehaviorStatus.PARTIAL,
                summary="the repository makes library and classifier assumptions visible but does not reproduce DIA-NN classifier internals",
            ),
            ComparatorBehaviorClaim(
                behavior_id="live_diann_execution_parity",
                status=ComparatorBehaviorStatus.DOES_NOT_ATTEMPT,
                summary="the benchmark path does not execute DIA-NN or claim end-to-end runtime parity",
            ),
        ),
        non_goals=(
            "DIA-NN classifier internals or live runtime parity",
            "full spectral-library generation parity outside the pinned report snapshot",
        ),
    ),
)


def list_workflow_comparator_paths(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
    benchmark_id: str | None = None,
) -> tuple[WorkflowComparatorPath, ...]:
    """Return comparator paths filtered by workflow family and benchmark."""

    return tuple(
        path
        for path in DEFAULT_WORKFLOW_COMPARATOR_PATHS
        if (
            workflow_family is None or workflow_family in path.workflow_families
        )
        and (benchmark_id is None or benchmark_id in path.benchmark_ids)
    )


def get_workflow_comparator_path(
    comparator_path_id: str,
) -> WorkflowComparatorPath | None:
    """Return one comparator path by stable identifier."""

    return next(
        (
            path
            for path in DEFAULT_WORKFLOW_COMPARATOR_PATHS
            if path.comparator_path_id == comparator_path_id
        ),
        None,
    )


def _build_tool_status(
    workflow_family: KnowledgeWorkflowFamily,
    comparator_tool: ProteomicsComparatorTool,
) -> WorkflowComparatorToolStatus:
    relevant_paths = tuple(
        path
        for path in DEFAULT_WORKFLOW_COMPARATOR_PATHS
        if path.comparator_tool is comparator_tool
        and workflow_family in path.workflow_families
    )
    matched_behaviors = tuple(
        claim.summary
        for path in relevant_paths
        for claim in path.comparison_behaviors
        if claim.status is ComparatorBehaviorStatus.MATCHES
    )
    partial_behaviors = tuple(
        claim.summary
        for path in relevant_paths
        for claim in path.comparison_behaviors
        if claim.status is ComparatorBehaviorStatus.PARTIAL
    )
    refused_behaviors = tuple(
        claim.summary
        for path in relevant_paths
        for claim in path.comparison_behaviors
        if claim.status is ComparatorBehaviorStatus.REFUSES
    )
    not_attempted_behaviors = tuple(
        claim.summary
        for path in relevant_paths
        for claim in path.comparison_behaviors
        if claim.status is ComparatorBehaviorStatus.DOES_NOT_ATTEMPT
    )

    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX and comparator_tool is ProteomicsComparatorTool.MAXQUANT:
        not_attempted_behaviors = (
            "the repository does not yet offer a MaxQuant-style multiplex comparator path for vendor-specific TMT parity",
        )
    if workflow_family is KnowledgeWorkflowFamily.TARGETED and comparator_tool is ProteomicsComparatorTool.SKYLINE:
        refused_behaviors = (
            "the repository refuses to present targeted QC fixtures as Skyline-level chromatogram parity without a raw calibration comparator package",
        )
        not_attempted_behaviors = (
            "the repository does not yet offer a Skyline-style targeted comparator path",
        )
    if workflow_family is KnowledgeWorkflowFamily.TARGETED and comparator_tool is ProteomicsComparatorTool.MAXQUANT:
        not_attempted_behaviors = (
            "MaxQuant is not treated as a targeted chromatogram comparator surface for this workflow family",
        )
    return WorkflowComparatorToolStatus(
        comparator_tool=comparator_tool,
        comparator_path_ids=tuple(
            path.comparator_path_id for path in relevant_paths
        ),
        matched_behaviors=matched_behaviors,
        partial_behaviors=partial_behaviors,
        refused_behaviors=refused_behaviors,
        not_attempted_behaviors=not_attempted_behaviors,
    )


def build_workflow_comparator_matrix(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> WorkflowComparatorMatrixReport:
    """Build the workflow-family comparator matrix with exact behavior posture."""

    selected_families = (
        (workflow_family,)
        if workflow_family is not None
        else tuple(KnowledgeWorkflowFamily)
    )
    entries = tuple(
        WorkflowComparatorMatrixEntry(
            workflow_family=family,
            workflow_summary=(
                "Comparator posture names exactly which external-tool behaviors the repository matches, partially matches, refuses, or does not yet attempt for this workflow family."
            ),
            tool_statuses=tuple(
                status
                for status in (
                    _build_tool_status(family, tool)
                    for tool in ProteomicsComparatorTool
                )
                if status.comparator_path_ids
                or status.matched_behaviors
                or status.partial_behaviors
                or status.refused_behaviors
                or status.not_attempted_behaviors
            ),
        )
        for family in selected_families
    )
    return WorkflowComparatorMatrixReport(entries=entries)


__all__ = [
    "ComparatorBehaviorClaim",
    "ComparatorBehaviorStatus",
    "DEFAULT_WORKFLOW_COMPARATOR_PATHS",
    "ProteomicsComparatorTool",
    "WorkflowComparatorMatrixEntry",
    "WorkflowComparatorMatrixReport",
    "WorkflowComparatorPath",
    "WorkflowComparatorToolStatus",
    "build_workflow_comparator_matrix",
    "get_workflow_comparator_path",
    "list_workflow_comparator_paths",
]
