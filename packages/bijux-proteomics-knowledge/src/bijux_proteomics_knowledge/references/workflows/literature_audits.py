# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Literature freshness, bibliography, and gap audits for workflow families."""

from __future__ import annotations

from enum import StrEnum
import re

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.grounding.citations import CitationRecord
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_dossiers import (
    build_workflow_contradiction_dossier,
)
from bijux_proteomics_knowledge.references.workflows.knowledge_deficits import (
    build_workflow_knowledge_deficit_report,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
    get_citation_record,
    get_workflow_reference_briefing_for_family,
)


class LiteratureFreshnessState(StrEnum):
    """Curated freshness status for one workflow-family citation."""

    CURRENT = "current"
    CURATED_BUT_AGING = "curated_but_aging"
    SUMMARY_OUTDATED = "summary_outdated"


class GapDirection(StrEnum):
    """Whether the benchmark or the surrounding literature is ahead."""

    BENCHMARK_OUTRUNS_LITERATURE = "benchmark_outruns_literature"
    LITERATURE_OUTRUNS_BENCHMARK = "literature_outruns_benchmark"
    COMPARATOR_OUTRUNS_LITERATURE = "comparator_outruns_literature"
    LITERATURE_OUTRUNS_COMPARATOR = "literature_outruns_comparator"


class WorkflowLiteratureFreshnessEntry(JsonModel):
    """One citation-level freshness row for a workflow-family summary."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    citation_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    publication_year: int = Field(..., ge=1900, le=2100)
    last_checked_on: str = Field(..., min_length=1)
    resolves_in_curated_audit: bool
    materially_newer_citation_ids: tuple[str, ...] = Field(default_factory=tuple)
    family_summary_outdated: bool
    freshness_state: LiteratureFreshnessState
    note: str = Field(..., min_length=1)


class WorkflowLiteratureFreshnessAudit(JsonModel):
    """Workflow-family literature freshness audit."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowLiteratureFreshnessEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowBibliographyEntry(JsonModel):
    """One machine-readable bibliography row for a workflow family."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    publication_year: int = Field(..., ge=1900, le=2100)
    doi: str | None = None
    stable_url: str | None = None
    relevance_tags: tuple[str, ...] = Field(default_factory=tuple)
    contradiction_tags: tuple[str, ...] = Field(default_factory=tuple)
    freshness_state: LiteratureFreshnessState


class WorkflowBibliographyExport(JsonModel):
    """Machine-readable bibliography export for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    export_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowBibliographyEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowLiteratureGapEntry(JsonModel):
    """One gap between workflow-family evidence planes and the literature base."""

    model_config = ConfigDict(extra="forbid")

    gap_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    direction: GapDirection
    summary: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)
    strengthening_path: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkLiteratureGapMatrix(JsonModel):
    """Cross-family benchmark-versus-literature gap matrix."""

    model_config = ConfigDict(extra="forbid")

    matrix_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowLiteratureGapEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ComparatorLiteratureGapMatrix(JsonModel):
    """Cross-family comparator-versus-literature gap matrix."""

    model_config = ConfigDict(extra="forbid")

    matrix_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowLiteratureGapEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")

_NEWER_CITATION_IDS: dict[str, tuple[str, ...]] = {
    "citation:target_decoy_2007": (),
    "citation:protein_inference_2012": (),
    "citation:swath_2012": (),
    "citation:psi_ms_cv_2012": (),
    "citation:ascore_2006": (),
    "citation:psi_mod_2008": (),
    "citation:tmtpro_2020": (),
    "citation:uniprot_2025": (),
}

_BENCHMARK_GAP_BLUEPRINTS: dict[
    KnowledgeWorkflowFamily,
    tuple[tuple[GapDirection, str, str, str, tuple[str, ...]], ...],
] = {
    KnowledgeWorkflowFamily.DDA: (
        (
            GapDirection.BENCHMARK_OUTRUNS_LITERATURE,
            "The paired DDA engine-transfer package now shows family-transfer drift more concretely than the current literature matrix explains.",
            "Outsiders can see the transfer failure in tracked files faster than they can see why the literature base predicts that failure.",
            "Add one DDA matrix row that explains cross-engine protein-rollup instability directly against the paired DDA generalization package.",
            (
                "benchmark_package:dda_cross_engine_review_package",
                "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.DIA: (
        (
            GapDirection.LITERATURE_OUTRUNS_BENCHMARK,
            "The DIA literature base names library and transition limits, but the current benchmark set still under-tests broader vendor-conditioned chromatography drift.",
            "The literature already warns about a wider DIA failure surface than the shipped public packages currently pressure.",
            "Add a second DIA literature-backed benchmark or perturbation lane that makes chromatography and vendor drift as visible as library scope is today.",
            (
                "benchmark:dia_library_extraction_consistency",
                "benchmark_package:dia_matrix_shift_review_package",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: (
        (
            GapDirection.LITERATURE_OUTRUNS_BENCHMARK,
            "LFQ literature keeps missing-not-at-random behavior and harsher cohort heterogeneity active, but the shipped public packages still stop short of those outer cohort cases.",
            "The current public packages are stronger than before, but the literature still describes more painful cohort behavior than the benchmark family currently carries.",
            "Add one LFQ package or perturbation that pushes missing-not-at-random pressure and broader cohort heterogeneity directly into the public benchmark family.",
            (
                "benchmark:lfq_cohort_repeatability",
                "benchmark_package:lfq_sparse_contrast_review_package",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: (
        (
            GapDirection.LITERATURE_OUTRUNS_BENCHMARK,
            "Multiplex literature treats carrier overload and chemistry distortion as first-order, but the current public multiplex pair still lacks a stronger external chemistry confrontation.",
            "The literature says chemistry pressure should bite harder than the current public package pair can yet prove.",
            "Add a chemistry-heavier public multiplex package and literature row that directly grounds the current fragile-transfer boundary.",
            (
                "benchmark:multiplex_tmtpro_quantification",
                "benchmark_package:multiplex_channel_stress_review_package",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.PTM: (
        (
            GapDirection.LITERATURE_OUTRUNS_BENCHMARK,
            "PTM literature keeps broader family coverage and ambiguity burden alive beyond the current phospho-oriented public package pair.",
            "The current PTM public packages are inspectable, but the literature still describes a wider PTM family landscape than the shipped packages carry.",
            "Add a second PTM family package or literature row that grounds non-phospho ambiguity pressure and family-specific transfer limits directly.",
            (
                "benchmark:ptm_localization_consistency",
                "benchmark_package:ptm_ambiguity_stress_review_package",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        (
            GapDirection.LITERATURE_OUTRUNS_BENCHMARK,
            "Targeted literature keeps calibration burden and Skyline-class chromatogram practice more explicit than the current public package pair can yet prove.",
            "The current targeted packages show honest QC and carryover limits, but the literature still outruns the shipped calibration and comparator realism.",
            "Add a stronger targeted calibration package and literature row that ties the current bounded-authority language directly to Skyline-class confrontation and control burden.",
            (
                "benchmark:targeted_transition_consistency",
                "benchmark_package:targeted_carryover_review_package",
            ),
        ),
    ),
}

_COMPARATOR_GAP_BLUEPRINTS: dict[
    KnowledgeWorkflowFamily,
    tuple[tuple[GapDirection, str, str, str, tuple[str, ...]], ...],
] = {
    KnowledgeWorkflowFamily.DDA: (
        (
            GapDirection.COMPARATOR_OUTRUNS_LITERATURE,
            "The paired DDA comparator files show protein-rollup drift more concretely than the current literature rows name it.",
            "A reviewer can learn about the current DDA loss mode from the comparator confrontation faster than from the literature matrix.",
            "Add one DDA literature row that names the currently observed cross-engine protein-rollup loss directly.",
            ("comparator_confrontation:dda", "literature_matrix:dda:1"),
        ),
    ),
    KnowledgeWorkflowFamily.DIA: (
        (
            GapDirection.LITERATURE_OUTRUNS_COMPARATOR,
            "DIA literature names wider vendor and library gaps than the current checked-in confrontation can yet pressure.",
            "Comparator pressure exists, but the literature still describes a broader DIA failure surface than the confrontation reaches.",
            "Add one broader DIA comparator lane or literature-linked failure dossier that covers vendor-conditioned drift beyond the current confrontation.",
            ("comparator_confrontation:dia", "literature_matrix:dia:1"),
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: (
        (
            GapDirection.LITERATURE_OUTRUNS_COMPARATOR,
            "LFQ literature keeps batch drift and cohort heterogeneity more active than the current confrontation surface does.",
            "The current LFQ confrontation is valuable, but it still does not pressure the harder cohort-wide failure modes named in the literature.",
            "Add one stronger LFQ confrontation or failure dossier that pushes batch-aware and cohort-shaped drift as hard as the literature base expects.",
            ("comparator_confrontation:lfq", "literature_matrix:lfq:1"),
        ),
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: (
        (
            GapDirection.LITERATURE_OUTRUNS_COMPARATOR,
            "Multiplex literature keeps chemistry burden central while the current family still lacks a dedicated external multiplex comparator path.",
            "Without a dedicated external comparator, the literature remains ahead of the confrontation surface for multiplex.",
            "Ship the missing multiplex comparator path or keep the internal-support boundary until chemistry-facing confrontation exists.",
            ("comparator_confrontation:multiplex", "literature_matrix:multiplex:1"),
        ),
    ),
    KnowledgeWorkflowFamily.PTM: (
        (
            GapDirection.LITERATURE_OUTRUNS_COMPARATOR,
            "PTM literature describes broader ambiguity and family-specific limits than the current confrontation surface pressures.",
            "The current PTM confrontation is useful, but it still under-pressures the literature-backed breadth of PTM ambiguity cases.",
            "Add one broader PTM comparator lane that covers non-phospho or harsher ambiguity pressure directly.",
            ("comparator_confrontation:ptm", "literature_matrix:ptm:1"),
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        (
            GapDirection.LITERATURE_OUTRUNS_COMPARATOR,
            "Targeted literature keeps calibration and chromatogram realism more explicit than the current confrontation surface can yet prove.",
            "The current targeted confrontation remains weaker than the literature-backed Skyline-class burden the family is compared against.",
            "Add the stronger targeted comparator lane so calibration and chromatogram realism stop living mainly in literature and deficit language.",
            ("comparator_confrontation:targeted", "literature_matrix:targeted:1"),
        ),
    ),
}


def _latest_checked_on(*traces: tuple[str, ...]) -> str:
    dates = [match for trace in traces for match in _DATE_RE.findall(" ".join(trace))]
    return max(dates) if dates else "unknown"


def _entry_state(
    *,
    citation: CitationRecord,
    summary_outdated: bool,
) -> LiteratureFreshnessState:
    if summary_outdated:
        return LiteratureFreshnessState.SUMMARY_OUTDATED
    if citation.publication_year <= 2012:
        return LiteratureFreshnessState.CURATED_BUT_AGING
    return LiteratureFreshnessState.CURRENT


def build_workflow_literature_freshness_audit(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowLiteratureFreshnessAudit:
    """Build the citation freshness audit for one workflow family."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    briefing = get_workflow_reference_briefing_for_family(workflow_family)
    deficit_report = build_workflow_knowledge_deficit_report(workflow_family)
    summary_outdated = bool(deficit_report.literature_gaps)
    citation_ids = sorted(
        {
            citation_id
            for group in briefing.literature_groups
            for citation_id in group.citation_ids
        }
    )
    groups_by_citation = {
        citation_id: tuple(
            group for group in briefing.literature_groups if citation_id in group.citation_ids
        )
        for citation_id in citation_ids
    }
    entries = []
    for index, citation_id in enumerate(citation_ids, start=1):
        citation = get_citation_record(citation_id)
        groups = groups_by_citation[citation_id]
        last_checked_on = _latest_checked_on(
            citation.retrieval_trace,
            *(group.retrieval_trace for group in groups),
        )
        entries.append(
            WorkflowLiteratureFreshnessEntry(
                entry_id=f"literature_freshness:{workflow_family.value}:{index}",
                workflow_family=workflow_family,
                citation_id=citation.citation_id,
                title=citation.title,
                publication_year=citation.publication_year,
                last_checked_on=last_checked_on,
                resolves_in_curated_audit=bool(citation.doi or citation.url),
                materially_newer_citation_ids=_NEWER_CITATION_IDS[citation.citation_id],
                family_summary_outdated=summary_outdated,
                freshness_state=_entry_state(
                    citation=citation,
                    summary_outdated=summary_outdated,
                ),
                note=(
                    "Freshness reflects the current curated registry audit state and "
                    "the workflow-family literature summary posture, not a claim of "
                    "live external citation crawling during runtime."
                ),
            )
        )
    return WorkflowLiteratureFreshnessAudit(
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        entries=tuple(entries),
        note=(
            "The freshness audit keeps workflow-family literature posture honest by "
            "showing when each citation was last rechecked in the curated registry "
            "and whether the current family summary is already aging beyond the "
            "shipped literature surface."
        ),
    )


def list_workflow_literature_freshness_audits() -> (
    tuple[WorkflowLiteratureFreshnessAudit, ...]
):
    """Return freshness audits across workflow families."""

    return tuple(
        build_workflow_literature_freshness_audit(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


def build_workflow_bibliography_export(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowBibliographyExport:
    """Build the machine-readable workflow-family bibliography export."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    briefing = get_workflow_reference_briefing_for_family(workflow_family)
    freshness_audit = build_workflow_literature_freshness_audit(workflow_family)
    freshness_by_citation = {entry.citation_id: entry for entry in freshness_audit.entries}
    contradiction_dossier = build_workflow_contradiction_dossier(workflow_family)
    contradiction_groups = {
        group.group_id
        for group in briefing.literature_groups
        if any(group.group_id.split(":")[-1] in scenario.tension_title for scenario in contradiction_dossier.scenarios)
    }
    citation_ids = sorted(
        {
            citation_id
            for group in briefing.literature_groups
            for citation_id in group.citation_ids
        }
    )
    entries = []
    for citation_id in citation_ids:
        citation = get_citation_record(citation_id)
        groups = tuple(
            group for group in briefing.literature_groups if citation_id in group.citation_ids
        )
        contradiction_tags = tuple(
            f"focus:{group.focus_area.value}"
            for group in groups
            if group.group_id in contradiction_groups
        )
        relevance_tags = tuple(
            sorted(
                {
                    f"workflow:{workflow_family.value}",
                    *(f"focus:{group.focus_area.value}" for group in groups),
                }
            )
        )
        entries.append(
            WorkflowBibliographyEntry(
                citation_id=citation.citation_id,
                title=citation.title,
                publication_year=citation.publication_year,
                doi=citation.doi,
                stable_url=citation.url,
                relevance_tags=relevance_tags,
                contradiction_tags=contradiction_tags,
                freshness_state=freshness_by_citation[citation_id].freshness_state,
            )
        )
    return WorkflowBibliographyExport(
        export_id=f"workflow_bibliography:{workflow_family.value}",
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        entries=tuple(entries),
        note=(
            "This export is the machine-readable bibliography surface for the "
            "workflow family and is intended to be serialized directly without "
            "needing repository-specific prose."
        ),
    )


def list_workflow_bibliography_exports() -> tuple[WorkflowBibliographyExport, ...]:
    """Return bibliography exports across workflow families."""

    return tuple(
        build_workflow_bibliography_export(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


def _build_gap_entries(
    blueprints: dict[
        KnowledgeWorkflowFamily,
        tuple[tuple[GapDirection, str, str, str, tuple[str, ...]], ...],
    ],
    *,
    prefix: str,
) -> tuple[WorkflowLiteratureGapEntry, ...]:
    entries = []
    for workflow_family in KnowledgeWorkflowFamily:
        for index, (
            direction,
            summary,
            why_it_matters,
            strengthening_path,
            evidence_refs,
        ) in enumerate(blueprints[workflow_family], start=1):
            entries.append(
                WorkflowLiteratureGapEntry(
                    gap_id=f"{prefix}:{workflow_family.value}:{index}",
                    workflow_family=workflow_family,
                    direction=direction,
                    summary=summary,
                    why_it_matters=why_it_matters,
                    strengthening_path=strengthening_path,
                    evidence_refs=evidence_refs,
                )
            )
    return tuple(entries)


def build_benchmark_literature_gap_matrix() -> BenchmarkLiteratureGapMatrix:
    """Build the cross-family benchmark-versus-literature gap matrix."""

    return BenchmarkLiteratureGapMatrix(
        matrix_id="benchmark_literature_gap_matrix",
        entries=_build_gap_entries(
            _BENCHMARK_GAP_BLUEPRINTS,
            prefix="benchmark_literature_gap",
        ),
        note=(
            "This cross-family matrix records where shipped public benchmark "
            "packages are already more concrete than the curated literature "
            "surface, and where the literature still describes failure modes the "
            "benchmark family has not yet brought into shipped public proof."
        ),
    )


def build_comparator_literature_gap_matrix() -> ComparatorLiteratureGapMatrix:
    """Build the cross-family comparator-versus-literature gap matrix."""

    return ComparatorLiteratureGapMatrix(
        matrix_id="comparator_literature_gap_matrix",
        entries=_build_gap_entries(
            _COMPARATOR_GAP_BLUEPRINTS,
            prefix="comparator_literature_gap",
        ),
        note=(
            "This matrix records where published confrontations already expose a "
            "scientific weakness more concretely than the literature matrix does, "
            "and where the literature still names comparator pressure that the "
            "shipped confrontation surface has not yet earned."
        ),
    )


__all__ = [
    "BenchmarkLiteratureGapMatrix",
    "ComparatorLiteratureGapMatrix",
    "GapDirection",
    "LiteratureFreshnessState",
    "WorkflowBibliographyEntry",
    "WorkflowBibliographyExport",
    "WorkflowLiteratureFreshnessAudit",
    "WorkflowLiteratureFreshnessEntry",
    "WorkflowLiteratureGapEntry",
    "build_benchmark_literature_gap_matrix",
    "build_comparator_literature_gap_matrix",
    "build_workflow_bibliography_export",
    "build_workflow_literature_freshness_audit",
    "list_workflow_bibliography_exports",
    "list_workflow_literature_freshness_audits",
]
