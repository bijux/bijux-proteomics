# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific-consequence triage for workflow-family contradiction pressure."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_dossiers import (
    build_workflow_contradiction_dossier,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
)


class ContradictionConsequenceLevel(StrEnum):
    """Scientific consequence class for contradiction triage."""

    RELEASE_BLOCKING = "release_blocking"
    CLAIM_NARROWING = "claim_narrowing"
    READING_SURFACE_DRIFT = "reading_surface_drift"


class WorkflowContradictionTriageEntry(JsonModel):
    """One contradiction ranked by scientific consequence."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    scientific_rank: int = Field(..., ge=1)
    consequence_level: ContradictionConsequenceLevel
    summary: str = Field(..., min_length=1)
    why_it_is_ranked_here: str = Field(..., min_length=1)
    next_action: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowContradictionTriageReport(JsonModel):
    """Public contradiction triage report for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    entries: tuple[WorkflowContradictionTriageEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


_TRIAGE_BLUEPRINTS: dict[
    KnowledgeWorkflowFamily,
    tuple[
        tuple[
            ContradictionConsequenceLevel,
            str,
            str,
            str,
            tuple[str, ...],
        ],
        ...,
    ],
] = {
    KnowledgeWorkflowFamily.DDA: (
        (
            ContradictionConsequenceLevel.RELEASE_BLOCKING,
            "Cross-engine DDA drift still makes protein-facing promotion unsafe beyond the bounded benchmark story.",
            "This contradiction sits at the top because it directly changes what DDA release language can safely say today.",
            "Promote the paired DDA transfer loss into a dedicated literature-backed claim row and keep protein-facing trust downgraded until live replay or stronger cross-engine proof lands.",
            ("contradiction_dossier:dda:1", "comparator_confrontation:dda"),
        ),
        (
            ContradictionConsequenceLevel.CLAIM_NARROWING,
            "The current DDA literature matrix is still thinner than the concrete paired-package transfer failure it is supposed to explain.",
            "This is second because it does not invalidate the benchmark itself, but it leaves the reading pack less scientifically explanatory than the public evidence now deserves.",
            "Add one DDA matrix row and bibliography tag that directly names the cross-engine protein-rollup loss mode.",
            ("contradiction_dossier:dda:1", "literature_matrix:dda:1"),
        ),
    ),
    KnowledgeWorkflowFamily.DIA: (
        (
            ContradictionConsequenceLevel.RELEASE_BLOCKING,
            "DIA transition-grade confidence still conflicts with wider vendor- and library-parity expectations outsiders may assume.",
            "This stays first because it directly determines how far DIA release language may go before it overclaims beyond the current library-conditioned proof surface.",
            "Keep DIA bounded to library-conditioned review until broader vendor-conditioned confrontation and rerun proof exist.",
            ("contradiction_dossier:dia:1", "comparator_confrontation:dia"),
        ),
        (
            ContradictionConsequenceLevel.CLAIM_NARROWING,
            "The current DIA reading surface explains library scope better than it explains broader chromatography drift and vendor-conditioned fragility.",
            "This is second because it narrows interpretation quality rather than outright invalidating the current bounded DIA claim.",
            "Add a second DIA literature-backed confrontation or perturbation lane that names chromatography drift as explicitly as library scope.",
            ("contradiction_dossier:dia:1", "literature_matrix:dia:2"),
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: (
        (
            ContradictionConsequenceLevel.RELEASE_BLOCKING,
            "LFQ review-grade abundance confidence still conflicts with the harder cohort and missingness behavior named by the literature.",
            "This ranks first because it directly limits whether repeatable LFQ summaries can be promoted beyond bounded review-grade language.",
            "Keep LFQ decision-grade wording blocked until harsher cohort pressure and observed outcome closure both exist.",
            ("contradiction_dossier:lfq:1", "literature_matrix:lfq:1"),
        ),
        (
            ContradictionConsequenceLevel.CLAIM_NARROWING,
            "The current LFQ confrontation surface still under-pressures the broader cohort drift described by the literature base.",
            "This ranks second because it narrows current interpretation quality instead of invalidating the benchmarked cohort packages themselves.",
            "Add one LFQ confrontation or failure dossier that brings broader cohort drift directly into the shipped proof set.",
            ("contradiction_dossier:lfq:1", "comparator_confrontation:lfq"),
        ),
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: (
        (
            ContradictionConsequenceLevel.RELEASE_BLOCKING,
            "Multiplex has a paired public benchmark surface, but the companion stress result defeats outsider authority and no dedicated lab consequence packet closes the downstream gap.",
            "This ranks first because it decides the authority boundary outright: multiplex stays internal support until its companion-package failure and missing consequence closure are resolved.",
            "Keep multiplex internal support only until companion pressure passes and dedicated outsider review and lab consequence packets exist.",
            (
                "contradiction_dossier:multiplex:1",
                "workflow_authority_matrix:multiplex",
            ),
        ),
        (
            ContradictionConsequenceLevel.CLAIM_NARROWING,
            "The literature keeps harsher multiplex chemistry burden in play than the current public package pair and confrontation surfaces can yet prove.",
            "This ranks second because it explains why even the internal-support chemistry story must stay explicitly bounded.",
            "Add a chemistry-heavier multiplex package and external confrontation path before widening any chemistry-facing narrative.",
            ("contradiction_dossier:multiplex:1", "literature_matrix:multiplex:1"),
        ),
    ),
    KnowledgeWorkflowFamily.PTM: (
        (
            ContradictionConsequenceLevel.RELEASE_BLOCKING,
            "PTM localization confidence still conflicts with the temptation to read occupancy or regulation into a narrower phospho-oriented evidence surface.",
            "This is first because it directly determines whether PTM language can stay at localization review or drifts into mechanistic overclaim.",
            "Keep PTM release language bounded to localization and ambiguity until broader family-specific comparator pressure exists.",
            ("contradiction_dossier:ptm:1", "literature_matrix:ptm:2"),
        ),
        (
            ContradictionConsequenceLevel.CLAIM_NARROWING,
            "The current PTM confrontation and literature coverage still under-explain how broader PTM-family ambiguity would change the reading surface.",
            "This ranks second because it narrows the explanatory quality of the PTM scientific reading pack more than the validity of the current localized benchmark claim.",
            "Add one broader PTM family benchmark or confrontation lane and tie it directly into the PTM contradiction dossier.",
            ("contradiction_dossier:ptm:1", "comparator_confrontation:ptm"),
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        (
            ContradictionConsequenceLevel.RELEASE_BLOCKING,
            "Targeted operator-facing confidence still conflicts with missing Skyline-class comparator and calibration realism.",
            "This ranks first because it directly controls whether targeted language can remain bounded operator-facing review or drifts into vendor-parity storytelling.",
            "Keep targeted language out of calibration-clean and vendor-parity authority until the missing confrontation lands.",
            ("contradiction_dossier:targeted:1", "comparator_confrontation:targeted"),
        ),
        (
            ContradictionConsequenceLevel.CLAIM_NARROWING,
            "The current targeted reading surface still explains protein-rollup caution better than it explains calibration burden and chromatogram realism.",
            "This ranks second because it narrows current interpretation quality instead of invalidating the bounded targeted QC claim itself.",
            "Add one targeted literature-backed calibration row and one stronger comparator lane so the reading pack covers calibration realism explicitly.",
            ("contradiction_dossier:targeted:1", "literature_matrix:targeted:2"),
        ),
    ),
}


def build_workflow_contradiction_triage_report(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowContradictionTriageReport:
    """Build the contradiction triage report for one workflow family."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    contradiction_dossier = build_workflow_contradiction_dossier(workflow_family)
    entries = tuple(
        WorkflowContradictionTriageEntry(
            entry_id=f"contradiction_triage:{workflow_family.value}:{index}",
            workflow_family=workflow_family,
            scientific_rank=index,
            consequence_level=consequence_level,
            summary=summary,
            why_it_is_ranked_here=why_it_is_ranked_here,
            next_action=next_action,
            evidence_refs=(
                *evidence_refs,
                contradiction_dossier.scenarios[0].scenario_id,
            ),
        )
        for index, (
            consequence_level,
            summary,
            why_it_is_ranked_here,
            next_action,
            evidence_refs,
        ) in enumerate(_TRIAGE_BLUEPRINTS[workflow_family], start=1)
    )
    return WorkflowContradictionTriageReport(
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        entries=entries,
        note=(
            "This triage report ranks contradictions by scientific consequence so "
            "the first item is the one most likely to change release language, "
            "claim scope, or public reading quality."
        ),
    )


def list_workflow_contradiction_triage_reports() -> tuple[
    WorkflowContradictionTriageReport, ...
]:
    """Return contradiction triage reports across workflow families."""

    return tuple(
        build_workflow_contradiction_triage_report(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


__all__ = [
    "ContradictionConsequenceLevel",
    "WorkflowContradictionTriageEntry",
    "WorkflowContradictionTriageReport",
    "build_workflow_contradiction_triage_report",
    "list_workflow_contradiction_triage_reports",
]
