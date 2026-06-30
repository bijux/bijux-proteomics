# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Multi-study biological comparison over governed study-result surfaces."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation import (
    OrthologRecord,
    PathwayEnrichmentCorrectionPolicy,
)
from bijux_proteomics.workflow.studies.cross_study_effect_comparison import (
    CrossStudyEffectComparisonStatus,
    CrossStudyProteinEffectComparisonEntry,
    CrossStudyProteinEffectComparisonReport,
    CrossStudyProteinStudyInput,
    build_cross_study_effect_comparison_report,
    render_cross_study_conflicting_hit_tsv,
    render_cross_study_replicated_hit_tsv,
)
from bijux_proteomics.workflow.studies.cross_study_pathway_comparison import (
    CrossStudyPathwayComparisonEntry,
    CrossStudyPathwayComparisonReport,
    CrossStudyPathwayComparisonStatus,
    build_cross_study_pathway_comparison_report,
    render_cross_study_shared_pathway_signal_tsv,
    render_cross_study_study_specific_pathway_tsv,
)
from bijux_proteomics.workflow.studies.cross_study_protein_harmonization import (
    CrossStudyProteinHarmonizationReport,
    CrossStudyProteinHarmonizedEntry,
    CrossStudyProteinUnresolvedEntry,
    build_cross_study_protein_harmonization_report,
    render_cross_study_protein_harmonization_tsv,
    render_cross_study_protein_unresolved_tsv,
)
from bijux_proteomics.workflow.result_types import (
    BiologyResult,
    RejectedEvidenceEntry,
    ResultWarningEntry,
    artifact_name_map,
    build_rejected_evidence_entry,
    build_result_warning,
)
from bijux_proteomics_foundation import JsonModel


class MultiStudyComparisonSummary(JsonModel):
    """Summary over one governed multi-study biological comparison."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    harmonization_supported_study_count: int = Field(..., ge=0)
    effect_supported_study_count: int = Field(..., ge=0)
    pathway_supported_study_count: int = Field(..., ge=0)
    harmonized_protein_group_count: int = Field(..., ge=0)
    harmonized_protein_membership_count: int = Field(..., ge=0)
    unresolved_protein_entry_count: int = Field(..., ge=0)
    ambiguous_ortholog_unresolved_count: int = Field(..., ge=0)
    shared_effect_count: int = Field(..., ge=0)
    conflicting_effect_count: int = Field(..., ge=0)
    shared_pathway_count: int = Field(..., ge=0)
    study_specific_pathway_count: int = Field(..., ge=0)


class MultiStudyComparisonArtifactPaths(JsonModel):
    """Stable artifact names exposed by the multi-study comparison workflow."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = "multi_study_comparison_summary.tsv"
    harmonized_proteins_tsv: str = "multi_study_harmonized_proteins.tsv"
    unresolved_proteins_tsv: str = "multi_study_unresolved_proteins.tsv"
    shared_effects_tsv: str = "multi_study_shared_effects.tsv"
    conflicting_effects_tsv: str = "multi_study_conflicting_effects.tsv"
    shared_pathways_tsv: str = "multi_study_shared_pathways.tsv"
    study_specific_pathways_tsv: str = "multi_study_study_specific_pathways.tsv"


class MultiStudyComparisonManifest(JsonModel):
    """Manifest for stable multi-study comparison artifact names."""

    model_config = ConfigDict(extra="forbid")

    artifacts: MultiStudyComparisonArtifactPaths = Field(
        default_factory=MultiStudyComparisonArtifactPaths
    )


class MultiStudyComparisonReport(BiologyResult):
    """Owned report over harmonized biological signals across multiple studies."""

    model_config = ConfigDict(extra="forbid")

    manifest: MultiStudyComparisonManifest = Field(
        default_factory=MultiStudyComparisonManifest
    )
    harmonization_report: CrossStudyProteinHarmonizationReport
    effect_comparison_report: CrossStudyProteinEffectComparisonReport
    pathway_comparison_report: CrossStudyPathwayComparisonReport
    harmonized_proteins: tuple[CrossStudyProteinHarmonizedEntry, ...] = Field(
        default_factory=tuple
    )
    unresolved_proteins: tuple[CrossStudyProteinUnresolvedEntry, ...] = Field(
        default_factory=tuple
    )
    shared_effects: tuple[CrossStudyProteinEffectComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    conflicting_effects: tuple[CrossStudyProteinEffectComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    shared_pathways: tuple[CrossStudyPathwayComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    study_specific_pathways: tuple[CrossStudyPathwayComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    summary: MultiStudyComparisonSummary
    note: str = Field(..., min_length=1)


def compare_studies(
    results: tuple[CrossStudyProteinStudyInput, ...],
    *,
    ortholog_records: tuple[OrthologRecord, ...] = (),
    enrichment_policy: PathwayEnrichmentCorrectionPolicy | None = None,
    minimum_absolute_activity_score_delta: float = 0.25,
    significance_threshold: float = 0.05,
    low_robustness_threshold: float = 0.5,
) -> MultiStudyComparisonReport:
    """Compare multiple governed study results without collapsing ambiguity."""

    harmonization_report = build_cross_study_protein_harmonization_report(
        results,
        ortholog_records=ortholog_records,
    )
    effect_comparison_report = build_cross_study_effect_comparison_report(
        results,
        ortholog_records=ortholog_records,
        significance_threshold=significance_threshold,
        low_robustness_threshold=low_robustness_threshold,
    )
    pathway_comparison_report = build_cross_study_pathway_comparison_report(
        results,
        enrichment_policy=enrichment_policy,
        minimum_absolute_activity_score_delta=minimum_absolute_activity_score_delta,
    )

    shared_effects = tuple(
        entry
        for entry in effect_comparison_report.comparisons
        if entry.comparison_status is CrossStudyEffectComparisonStatus.REPLICATED_HIT
    )
    conflicting_effects = tuple(
        entry
        for entry in effect_comparison_report.comparisons
        if entry.comparison_status is CrossStudyEffectComparisonStatus.CONFLICTING_HIT
    )
    shared_pathways = tuple(
        entry
        for entry in pathway_comparison_report.comparisons
        if entry.comparison_status is CrossStudyPathwayComparisonStatus.SHARED_SIGNAL
    )
    study_specific_pathways = tuple(
        entry
        for entry in pathway_comparison_report.comparisons
        if entry.comparison_status
        is CrossStudyPathwayComparisonStatus.STUDY_SPECIFIC_SIGNAL
    )
    manifest = MultiStudyComparisonManifest()
    summary = MultiStudyComparisonSummary(
        input_study_count=len(results),
        harmonization_supported_study_count=harmonization_report.summary.supported_study_count,
        effect_supported_study_count=effect_comparison_report.summary.supported_study_count,
        pathway_supported_study_count=pathway_comparison_report.summary.supported_study_count,
        harmonized_protein_group_count=harmonization_report.summary.harmonized_group_count,
        harmonized_protein_membership_count=harmonization_report.summary.harmonized_membership_count,
        unresolved_protein_entry_count=harmonization_report.summary.unresolved_entry_count,
        ambiguous_ortholog_unresolved_count=(
            harmonization_report.summary.ambiguous_ortholog_entry_count
        ),
        shared_effect_count=len(shared_effects),
        conflicting_effect_count=len(conflicting_effects),
        shared_pathway_count=len(shared_pathways),
        study_specific_pathway_count=len(study_specific_pathways),
    )

    return MultiStudyComparisonReport(
        manifest=manifest,
        harmonization_report=harmonization_report,
        effect_comparison_report=effect_comparison_report,
        pathway_comparison_report=pathway_comparison_report,
        harmonized_proteins=harmonization_report.harmonized_entries,
        unresolved_proteins=harmonization_report.unresolved_entries,
        shared_effects=shared_effects,
        conflicting_effects=conflicting_effects,
        shared_pathways=shared_pathways,
        study_specific_pathways=study_specific_pathways,
        artifacts=artifact_name_map(manifest.artifacts),
        warnings=_build_multi_study_warnings(summary, manifest),
        rejected_evidence=_build_multi_study_rejected_evidence(
            harmonization_report.unresolved_entries,
            manifest,
        ),
        summary=summary,
        note=(
            "multi-study comparison composes governed cross-study protein "
            "harmonization, effect comparison, and pathway comparison so shared "
            "signals stay explicit while ambiguous ortholog mappings remain unresolved"
        ),
    )


def render_multi_study_comparison_summary_tsv(
    report: MultiStudyComparisonReport,
) -> str:
    """Render one-row multi-study comparison summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "input_study_count",
            "harmonization_supported_study_count",
            "effect_supported_study_count",
            "pathway_supported_study_count",
            "harmonized_protein_group_count",
            "harmonized_protein_membership_count",
            "unresolved_protein_entry_count",
            "ambiguous_ortholog_unresolved_count",
            "shared_effect_count",
            "conflicting_effect_count",
            "shared_pathway_count",
            "study_specific_pathway_count",
        ]
    )
    writer.writerow(
        [
            report.summary.input_study_count,
            report.summary.harmonization_supported_study_count,
            report.summary.effect_supported_study_count,
            report.summary.pathway_supported_study_count,
            report.summary.harmonized_protein_group_count,
            report.summary.harmonized_protein_membership_count,
            report.summary.unresolved_protein_entry_count,
            report.summary.ambiguous_ortholog_unresolved_count,
            report.summary.shared_effect_count,
            report.summary.conflicting_effect_count,
            report.summary.shared_pathway_count,
            report.summary.study_specific_pathway_count,
        ]
    )
    return buffer.getvalue()


def render_multi_study_harmonized_proteins_tsv(
    report: MultiStudyComparisonReport,
) -> str:
    """Render harmonized proteins as TSV."""

    return render_cross_study_protein_harmonization_tsv(report.harmonization_report)


def render_multi_study_unresolved_proteins_tsv(
    report: MultiStudyComparisonReport,
) -> str:
    """Render unresolved proteins as TSV."""

    return render_cross_study_protein_unresolved_tsv(report.harmonization_report)


def render_multi_study_shared_effects_tsv(report: MultiStudyComparisonReport) -> str:
    """Render shared cross-study protein effects as TSV."""

    return render_cross_study_replicated_hit_tsv(report.effect_comparison_report)


def render_multi_study_conflicting_effects_tsv(
    report: MultiStudyComparisonReport,
) -> str:
    """Render conflicting cross-study protein effects as TSV."""

    return render_cross_study_conflicting_hit_tsv(report.effect_comparison_report)


def render_multi_study_shared_pathways_tsv(report: MultiStudyComparisonReport) -> str:
    """Render shared pathways as TSV."""

    return render_cross_study_shared_pathway_signal_tsv(
        report.pathway_comparison_report
    )


def render_multi_study_study_specific_pathways_tsv(
    report: MultiStudyComparisonReport,
) -> str:
    """Render study-specific pathways as TSV."""

    return render_cross_study_study_specific_pathway_tsv(
        report.pathway_comparison_report
    )


def _build_multi_study_warnings(
    summary: MultiStudyComparisonSummary,
    manifest: MultiStudyComparisonManifest,
) -> tuple[ResultWarningEntry, ...]:
    warnings = []
    if summary.conflicting_effect_count:
        warnings.append(
            build_result_warning(
                warning_id="multi-study:conflicting-effects",
                warning_code="conflicting_effects_present",
                source_surface="multi_study",
                message=(
                    f"{summary.conflicting_effect_count} harmonized protein effects "
                    "disagree across studies"
                ),
                related_artifact=manifest.artifacts.conflicting_effects_tsv,
            )
        )
    if summary.ambiguous_ortholog_unresolved_count:
        warnings.append(
            build_result_warning(
                warning_id="multi-study:ambiguous-orthologs",
                warning_code="ambiguous_ortholog_unresolved",
                source_surface="multi_study",
                message=(
                    f"{summary.ambiguous_ortholog_unresolved_count} protein observations "
                    "remain unresolved because ortholog mapping is ambiguous"
                ),
                related_artifact=manifest.artifacts.unresolved_proteins_tsv,
            )
        )
    return tuple(warnings)


def _build_multi_study_rejected_evidence(
    unresolved_proteins: tuple[CrossStudyProteinUnresolvedEntry, ...],
    manifest: MultiStudyComparisonManifest,
) -> tuple[RejectedEvidenceEntry, ...]:
    return tuple(
        build_rejected_evidence_entry(
            evidence_id=f"multi_study:{entry.observation_id}",
            source_surface="multi_study",
            reason_code=entry.reason.value,
            message=entry.note,
            related_artifact=manifest.artifacts.unresolved_proteins_tsv,
            entity_id=entry.source_entity_id,
        )
        for entry in unresolved_proteins
    )


__all__ = [
    "MultiStudyComparisonArtifactPaths",
    "MultiStudyComparisonManifest",
    "MultiStudyComparisonReport",
    "MultiStudyComparisonSummary",
    "compare_studies",
    "render_multi_study_comparison_summary_tsv",
    "render_multi_study_conflicting_effects_tsv",
    "render_multi_study_harmonized_proteins_tsv",
    "render_multi_study_shared_effects_tsv",
    "render_multi_study_shared_pathways_tsv",
    "render_multi_study_study_specific_pathways_tsv",
    "render_multi_study_unresolved_proteins_tsv",
]
