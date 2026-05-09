# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow-family contradiction dossiers for flagship benchmark reading."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    build_benchmark_comparator_failure_report,
)
from bijux_proteomics_knowledge.references.workflows.literature_matrices import (
    WorkflowLiteratureMatrix,
    build_workflow_literature_matrix,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
)


class WorkflowContradictionScenario(JsonModel):
    """One disagreement scenario that limits current trust for a workflow family."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    tension_title: str = Field(..., min_length=1)
    literature_position: str = Field(..., min_length=1)
    benchmark_position: str = Field(..., min_length=1)
    comparator_position: str = Field(..., min_length=1)
    current_repo_trust_position: str = Field(..., min_length=1)
    recommended_hold_reason: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    recommended_hold: bool = True


class WorkflowContradictionDossier(JsonModel):
    """Public contradiction dossier for one flagship benchmark workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    scenarios: tuple[WorkflowContradictionScenario, ...] = Field(default_factory=tuple)
    trust_posture: str = Field(..., min_length=1)


class _ScenarioBlueprint(JsonModel):
    """Internal blueprint for workflow contradiction scenarios."""

    model_config = ConfigDict(extra="forbid")

    tension_title: str = Field(..., min_length=1)
    literature_position: str = Field(..., min_length=1)
    benchmark_position: str = Field(..., min_length=1)
    current_repo_trust_position: str = Field(..., min_length=1)
    recommended_hold_reason: str = Field(..., min_length=1)
    matrix_entry_ids: tuple[str, ...] = Field(default_factory=tuple)


_SCENARIO_BLUEPRINTS: dict[KnowledgeWorkflowFamily, tuple[_ScenarioBlueprint, ...]] = {
    KnowledgeWorkflowFamily.DDA: (
        _ScenarioBlueprint(
            tension_title="confidence semantics survive only while decoy posture remains visible",
            literature_position="Target-decoy and protein-inference references treat confidence framing as inseparable from explicit error-model visibility.",
            benchmark_position="The pinned DDA export is strong enough to review normalization and proteome grounding, but still not strong enough to prove live-engine parity.",
            current_repo_trust_position="Trust the adapter-normalized decision brief only for bounded confidence semantics and reviewed-proteome grounding.",
            recommended_hold_reason="Broader identification trust stays blocked until the benchmark stops depending on one pinned external export family.",
            matrix_entry_ids=("literature_matrix:dda:1", "literature_matrix:dda:2"),
        ),
    ),
    KnowledgeWorkflowFamily.DIA: (
        _ScenarioBlueprint(
            tension_title="clean import does not resolve library and transition uncertainty",
            literature_position="DIA method grounding treats library scope and transition semantics as active scientific limits, not just import metadata.",
            benchmark_position="The benchmark package demonstrates library-conditioned extraction consistency, but still does not prove broader protein-level absence or vendor-parity conclusions.",
            current_repo_trust_position="Trust the current DIA surface for bounded transition and review behavior, not for general biological certainty.",
            recommended_hold_reason="Biological promotion must stay downgraded while library coverage and absent-expected-peptide pressure remain benchmark-shaped rather than public-package hard.",
            matrix_entry_ids=("literature_matrix:dia:1", "literature_matrix:dia:2"),
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: (
        _ScenarioBlueprint(
            tension_title="repeatable tables still disagree with decision-grade abundance trust",
            literature_position="Quantification grounding keeps missingness, batch posture, and contrast scope active even when numeric summaries look stable.",
            benchmark_position="The LFQ fixture preserves study design and repeatability, but it is still too tidy to authorize stronger cohort-style abundance claims.",
            current_repo_trust_position="Trust the current LFQ surface for review-grade abundance interpretation inside the benchmarked contrast only.",
            recommended_hold_reason="Decision-grade abundance claims stay blocked until missingness and cohort heterogeneity are pressured on a harder public package.",
            matrix_entry_ids=("literature_matrix:lfq:1", "literature_matrix:lfq:2"),
        ),
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: (
        _ScenarioBlueprint(
            tension_title="reporter-channel stability still conflicts with missing external chemistry confrontation",
            literature_position="Multiplex chemistry references treat interference, compression, and channel imbalance as first-order interpretation limits.",
            benchmark_position="The bundled multiplex fixture keeps channel semantics explicit, but it does not yet carry the harshest chemistry burden seen in real public TMT data.",
            current_repo_trust_position="Trust the current multiplex surface only for review-grade channel interpretation with explicit chemistry caveats.",
            recommended_hold_reason="Stronger multiplex claims stay blocked until a public chemistry-heavy package and an external comparator path both exist.",
            matrix_entry_ids=("literature_matrix:multiplex:1", "literature_matrix:multiplex:2"),
        ),
    ),
    KnowledgeWorkflowFamily.PTM: (
        _ScenarioBlueprint(
            tension_title="localized evidence still disagrees with mechanistic storytelling",
            literature_position="PTM grounding and localization references keep site confidence separate from occupancy, regulation, and pathway mechanism.",
            benchmark_position="The benchmark package can preserve localization ladders and ambiguity, but it is too narrow and tidy to justify broad regulatory claims.",
            current_repo_trust_position="Trust the current PTM surface for localized evidence review and explicit ambiguity, not for mechanism promotion.",
            recommended_hold_reason="Mechanistic PTM claims stay blocked until the benchmark package and comparator pressure cover broader PTM family and ambiguity burden.",
            matrix_entry_ids=("literature_matrix:ptm:1", "literature_matrix:ptm:2"),
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        _ScenarioBlueprint(
            tension_title="transition-facing QC still outruns calibration and comparator proof",
            literature_position="Targeted references keep transition evidence, control burden, and protein rollup caution attached to any operator-facing conclusion.",
            benchmark_position="The current targeted package keeps QC and follow-up honesty visible, but it still lacks public calibration burden and Skyline-class confrontation.",
            current_repo_trust_position="Trust the current targeted surface for operator-facing QC interpretation only, not for decision-grade targeted biology.",
            recommended_hold_reason="Decision-facing targeted support stays blocked until calibration, interference, and comparator pressure are materially harder.",
            matrix_entry_ids=("literature_matrix:targeted:1", "literature_matrix:targeted:2"),
        ),
    ),
}


def _comparator_position_for_family(workflow_family: KnowledgeWorkflowFamily) -> str:
    report = build_benchmark_comparator_failure_report(workflow_family=workflow_family)
    if not report.entries:
        return "No comparator contradiction is currently recorded for this workflow family."
    entry = report.entries[0]
    return f"{entry.failure_summary} Blocking reasons: {'; '.join(entry.blocking_reasons)}."


def _scenarios_for_family(
    workflow_family: KnowledgeWorkflowFamily,
    matrix: WorkflowLiteratureMatrix,
) -> tuple[WorkflowContradictionScenario, ...]:
    comparator_position = _comparator_position_for_family(workflow_family)
    matrix_entry_ids = {entry.entry_id for entry in matrix.entries}
    scenarios = []
    for index, blueprint in enumerate(_SCENARIO_BLUEPRINTS[workflow_family], start=1):
        scenarios.append(
            WorkflowContradictionScenario(
                scenario_id=f"contradiction_dossier:{workflow_family.value}:{index}",
                workflow_family=workflow_family,
                tension_title=blueprint.tension_title,
                literature_position=blueprint.literature_position,
                benchmark_position=blueprint.benchmark_position,
                comparator_position=comparator_position,
                current_repo_trust_position=blueprint.current_repo_trust_position,
                recommended_hold_reason=blueprint.recommended_hold_reason,
                evidence_refs=(
                    get_benchmark_manifest_for_family(workflow_family).benchmark_id,
                    *tuple(entry_id for entry_id in blueprint.matrix_entry_ids if entry_id in matrix_entry_ids),
                ),
            )
        )
    return tuple(scenarios)


def build_workflow_contradiction_dossier(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowContradictionDossier:
    """Build the contradiction dossier for one workflow family."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    matrix = build_workflow_literature_matrix(workflow_family)
    scenarios = _scenarios_for_family(workflow_family, matrix)
    return WorkflowContradictionDossier(
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        scenarios=scenarios,
        trust_posture=(
            "The repository currently trusts only the bounded benchmark story that still survives literature pressure, benchmark limits, and comparator weakness together."
        ),
    )


def list_workflow_contradiction_dossiers() -> tuple[WorkflowContradictionDossier, ...]:
    """Return contradiction dossiers across all workflow families."""

    return tuple(
        build_workflow_contradiction_dossier(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


__all__ = [
    "WorkflowContradictionDossier",
    "WorkflowContradictionScenario",
    "build_workflow_contradiction_dossier",
    "list_workflow_contradiction_dossiers",
]
