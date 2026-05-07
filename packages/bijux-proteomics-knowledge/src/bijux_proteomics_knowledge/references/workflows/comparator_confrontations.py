# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public comparator confrontations for flagship workflow benchmark families."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    ProteomicsComparatorTool,
    list_workflow_comparator_paths,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
)


class ComparatorConfrontationOutcome(StrEnum):
    """Outcome of one scientific comparison axis."""

    ALIGNED = "aligned"
    REPO_STRICTER = "repo_stricter"
    REPO_WEAKER = "repo_weaker"
    BLOCKED = "blocked"


class ComparatorConfrontationFinding(JsonModel):
    """One explicit scientific difference against an established workflow."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(..., min_length=1)
    axis: str = Field(..., min_length=1)
    outcome: ComparatorConfrontationOutcome
    repository_position: str = Field(..., min_length=1)
    comparator_position: str = Field(..., min_length=1)
    scientific_difference: str = Field(..., min_length=1)
    consequence_for_review: str = Field(..., min_length=1)


class WorkflowComparatorConfrontation(JsonModel):
    """One workflow-family comparator confrontation on a flagship benchmark."""

    model_config = ConfigDict(extra="forbid")

    confrontation_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    comparator_tool: ProteomicsComparatorTool
    findings: tuple[ComparatorConfrontationFinding, ...] = Field(
        default_factory=tuple
    )
    overall_conclusion: str = Field(..., min_length=1)
    artifact_refs: tuple[str, ...] = Field(default_factory=tuple)
    next_escalation: str = Field(..., min_length=1)


class WorkflowComparatorConfrontationReport(JsonModel):
    """Comparator confrontations across workflow families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowComparatorConfrontation, ...] = Field(default_factory=tuple)


def _build_dda_confrontation() -> WorkflowComparatorConfrontation:
    manifest = get_benchmark_manifest_for_family(KnowledgeWorkflowFamily.DDA)
    comparator_paths = list_workflow_comparator_paths(
        workflow_family=KnowledgeWorkflowFamily.DDA
    )
    return WorkflowComparatorConfrontation(
        confrontation_id="comparator_confrontation:dda",
        workflow_family=KnowledgeWorkflowFamily.DDA,
        benchmark_id=manifest.benchmark_id,
        comparator_tool=ProteomicsComparatorTool.MSFRAGGER,
        findings=(
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:dda:peptide_evidence",
                axis="peptide-level evidence",
                outcome=ComparatorConfrontationOutcome.ALIGNED,
                repository_position="The repository preserves the pinned peptide evidence and keeps adapter-normalized PSM semantics visible in the review surface.",
                comparator_position="The established DDA workflow produces the pinned peptide evidence snapshot that the repository normalizes and reviews.",
                scientific_difference="There is no current peptide-evidence disagreement inside the pinned export boundary.",
                consequence_for_review="Peptide-facing review can stay benchmark-backed as long as the conversation remains inside the pinned export family.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:dda:protein_evidence",
                axis="protein-level evidence",
                outcome=ComparatorConfrontationOutcome.REPO_STRICTER,
                repository_position="The repository keeps reviewed-proteome grounding and protein-inference caveats explicit before any protein-facing claim leaves review status.",
                comparator_position="The external DDA workflow provides the protein evidence snapshot, but it does not itself carry the repository's downgrade logic around downstream claim scope.",
                scientific_difference="The repository is stricter about not letting imported protein evidence harden into unqualified certainty.",
                consequence_for_review="Protein-level interpretation stays more conservative than a naive import of the comparator output.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:dda:calibration",
                axis="calibration and live-engine parity",
                outcome=ComparatorConfrontationOutcome.REPO_WEAKER,
                repository_position="The repository only normalizes and reviews the checked-in comparator export and does not rerun the external engine.",
                comparator_position="The established DDA workflow owns the live search execution, engine calibration, and raw-spectrum scoring behavior.",
                scientific_difference="The repository cannot currently prove live-engine calibration parity or raw-spectrum scoring equivalence.",
                consequence_for_review="Current DDA authority stays bounded to imported evidence review, not end-to-end DDA engine parity.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:dda:downstream_review",
                axis="downstream review behavior",
                outcome=ComparatorConfrontationOutcome.REPO_STRICTER,
                repository_position="The repository carries field-loss accounting and target-decoy caution into the review-facing packet.",
                comparator_position="The external workflow produces the search result, but its review posture is not represented as a governed downgrade chain in this repository.",
                scientific_difference="The repository is stronger at keeping downgrade logic and provenance visible once the external result becomes review material.",
                consequence_for_review="Review packets better expose why strong-looking DDA evidence can still remain bounded.",
            ),
        ),
        overall_conclusion=(
            "The repository now ships a real DDA public package with paired comparator evidence: peptide import semantics, target-decoy visibility, and protein-rollup drift are public, but live-engine calibration parity still belongs to the comparator."
        ),
        artifact_refs=tuple(path.comparator_path_id for path in comparator_paths),
        next_escalation=(
            "Add live-engine DDA rerun parity or a stronger multi-run public comparison so the current public package no longer stops at imported-result confrontation."
        ),
    )


def _build_dia_confrontation() -> WorkflowComparatorConfrontation:
    manifest = get_benchmark_manifest_for_family(KnowledgeWorkflowFamily.DIA)
    comparator_paths = list_workflow_comparator_paths(
        workflow_family=KnowledgeWorkflowFamily.DIA
    )
    return WorkflowComparatorConfrontation(
        confrontation_id="comparator_confrontation:dia",
        workflow_family=KnowledgeWorkflowFamily.DIA,
        benchmark_id=manifest.benchmark_id,
        comparator_tool=ProteomicsComparatorTool.SPECTRONAUT,
        findings=(
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:dia:peptide_evidence",
                axis="peptide and transition evidence",
                outcome=ComparatorConfrontationOutcome.ALIGNED,
                repository_position="The repository normalizes the pinned DIA export into the same governed transition and peptide-facing evidence surface it uses for review.",
                comparator_position="The established DIA workflow produces the pinned transition-rich export that the repository ingests.",
                scientific_difference="Within the imported report boundary, transition semantics remain aligned enough for governed review.",
                consequence_for_review="Peptide- and transition-facing review can remain benchmark-backed under the current pinned export package.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:dia:protein_evidence",
                axis="protein-level evidence",
                outcome=ComparatorConfrontationOutcome.REPO_STRICTER,
                repository_position="The repository refuses to let library-conditioned evidence imply open-ended protein certainty or absence claims.",
                comparator_position="The established DIA workflow can present stronger-looking protein summaries even when the underlying evidence remains library-conditioned.",
                scientific_difference="The repository keeps a tighter boundary between transition evidence and protein-level interpretation.",
                consequence_for_review="Protein-facing DIA conclusions stay more conservative and more explicit about library scope.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:dia:quant_summaries",
                axis="quant summaries",
                outcome=ComparatorConfrontationOutcome.ALIGNED,
                repository_position="The repository preserves the imported quant summary structure and keeps library-conditioned assumptions visible in review.",
                comparator_position="The established DIA workflow emits the quant summary snapshot that the repository imports and interprets.",
                scientific_difference="There is no current quant-summary disagreement inside the pinned export family, but the repo remains bounded to import-shaped proof.",
                consequence_for_review="Quant summaries can be compared and reviewed without pretending the repository has reproduced vendor internals.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:dia:missingness_behavior",
                axis="missingness and absent-expected-peptide behavior",
                outcome=ComparatorConfrontationOutcome.REPO_WEAKER,
                repository_position="The repository can expose missing expected peptides and library gaps in review, but it does not yet pressure them through a harder public runtime package.",
                comparator_position="The established DIA workflow owns the original classifier and extraction behavior that generated the missingness posture.",
                scientific_difference="The repository still lacks a stronger confrontation on how absent expected peptides and vendor extraction choices alter downstream trust.",
                consequence_for_review="DIA review remains honest about missingness limits, but not yet fully cross-checked at the execution layer.",
            ),
        ),
        overall_conclusion=(
            "The repository can confront an established DIA workflow on imported evidence and review semantics, but still loses on execution-level and missingness realism beyond the pinned report boundary."
        ),
        artifact_refs=tuple(path.comparator_path_id for path in comparator_paths),
        next_escalation=(
            "Add a harder public DIA package and a live external confrontation so missing expected peptides, library gaps, and vendor execution choices move from advisory caveats into real public comparison pressure."
        ),
    )


def _build_lfq_confrontation() -> WorkflowComparatorConfrontation:
    manifest = get_benchmark_manifest_for_family(KnowledgeWorkflowFamily.LFQ)
    comparator_paths = list_workflow_comparator_paths(
        workflow_family=KnowledgeWorkflowFamily.LFQ
    )
    return WorkflowComparatorConfrontation(
        confrontation_id="comparator_confrontation:lfq",
        workflow_family=KnowledgeWorkflowFamily.LFQ,
        benchmark_id=manifest.benchmark_id,
        comparator_tool=ProteomicsComparatorTool.MAXQUANT,
        findings=(
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:lfq:normalization",
                axis="normalization behavior",
                outcome=ComparatorConfrontationOutcome.ALIGNED,
                repository_position="The repository preserves the imported LFQ summary structure and keeps normalization posture review-visible.",
                comparator_position="The established LFQ workflow emits the evidence table that anchors the imported normalization and abundance review.",
                scientific_difference="There is no current normalization disagreement inside the imported evidence boundary.",
                consequence_for_review="Review-grade LFQ normalization claims can stay aligned while the benchmark remains import-shaped.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:lfq:differential",
                axis="differential interpretation",
                outcome=ComparatorConfrontationOutcome.REPO_STRICTER,
                repository_position="The repository keeps study-design scope, missingness, and batch posture visible before a differential result becomes stronger biology.",
                comparator_position="The external LFQ workflow can present differential summaries without the same governed downgrade chain around contrast scope.",
                scientific_difference="The repository is stricter about not letting tidy differential outputs outrun the benchmarked contrast and replicate structure.",
                consequence_for_review="LFQ differential packets stay more conservative about what abundance biology has actually been earned.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:lfq:evidence_loss",
                axis="evidence-loss behavior",
                outcome=ComparatorConfrontationOutcome.REPO_WEAKER,
                repository_position="The repository can explain evidence-loss and missingness pressure, but still lacks a flagship public cohort package that makes those losses hurt more realistically.",
                comparator_position="The established LFQ workflow owns the original evidence table and broader algorithmic handling that generated the imported abundance summary.",
                scientific_difference="The repository still lacks a harder public comparison on how evidence loss and cohort heterogeneity change the final abundance claim.",
                consequence_for_review="LFQ trust remains bounded to imported-review semantics rather than broader cohort-grade quant parity.",
            ),
        ),
        overall_conclusion=(
            "The repository can confront an established LFQ workflow on imported normalization and bounded differential review, but it still loses on harder public-cohort evidence-loss realism."
        ),
        artifact_refs=tuple(path.comparator_path_id for path in comparator_paths),
        next_escalation=(
            "Move LFQ comparison onto a flagship public cohort package so missingness, batch drift, and evidence-loss pressure become public comparator substance instead of tidy imported review."
        ),
    )


def _build_multiplex_confrontation() -> WorkflowComparatorConfrontation:
    manifest = get_benchmark_manifest_for_family(KnowledgeWorkflowFamily.MULTIPLEX)
    comparator_paths = list_workflow_comparator_paths(
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX
    )
    return WorkflowComparatorConfrontation(
        confrontation_id="comparator_confrontation:multiplex",
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX,
        benchmark_id=manifest.benchmark_id,
        comparator_tool=ProteomicsComparatorTool.MAXQUANT,
        findings=(
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:multiplex:channel_level",
                axis="channel-level evidence",
                outcome=ComparatorConfrontationOutcome.BLOCKED,
                repository_position="The repository keeps reporter-channel semantics and chemistry caveats explicit, but it does not yet have a real external multiplex comparator path.",
                comparator_position="An established multiplex workflow would own the vendor-grade channel extraction and chemistry-specific behavior that the repository still lacks.",
                scientific_difference="There is no real shipped external multiplex confrontation yet; channel-level parity remains explicitly blocked.",
                consequence_for_review="Any multiplex comparison claim must stay honest about being blocked rather than partially satisfied.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:multiplex:protein_level",
                axis="protein-level evidence",
                outcome=ComparatorConfrontationOutcome.REPO_STRICTER,
                repository_position="The repository keeps channel chemistry, reference dependence, and ratio-compression warnings attached to any protein-facing summary.",
                comparator_position="An established multiplex workflow can still emit strong protein summaries even when the reporter chemistry burden remains hard to see from the final table alone.",
                scientific_difference="The repository is stronger at stopping channel-level caveats from disappearing during protein rollup.",
                consequence_for_review="Protein-facing multiplex conclusions remain visibly coupled to channel-level fragility.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:multiplex:ratio_compression_and_interference",
                axis="ratio compression and interference",
                outcome=ComparatorConfrontationOutcome.REPO_WEAKER,
                repository_position="The repository names ratio-compression and interference risk, but it does not yet confront them on a harder external comparator package.",
                comparator_position="A real external multiplex workflow would pressure the chemistry burden with vendor-grade outputs and interference-heavy public data.",
                scientific_difference="The repository still lacks a public external confrontation on the chemistry burden that most threatens multiplex trust.",
                consequence_for_review="Multiplex authority remains review-grade and blocked from stronger chemistry claims until the external confrontation exists.",
            ),
        ),
        overall_conclusion=(
            "The repository is stronger at keeping multiplex chemistry caveats visible, but the actual external multiplex confrontation is still blocked and that missing comparison remains a major weakness."
        ),
        artifact_refs=tuple(path.comparator_path_id for path in comparator_paths),
        next_escalation=(
            "Add a real public multiplex comparator path with channel-heavy outputs so the blocked channel-level confrontation becomes a shipped comparison instead of a declared absence."
        ),
    )


def _build_ptm_confrontation() -> WorkflowComparatorConfrontation:
    manifest = get_benchmark_manifest_for_family(KnowledgeWorkflowFamily.PTM)
    comparator_paths = list_workflow_comparator_paths(
        workflow_family=KnowledgeWorkflowFamily.PTM
    )
    return WorkflowComparatorConfrontation(
        confrontation_id="comparator_confrontation:ptm",
        workflow_family=KnowledgeWorkflowFamily.PTM,
        benchmark_id=manifest.benchmark_id,
        comparator_tool=ProteomicsComparatorTool.MAXQUANT,
        findings=(
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:ptm:localization_agreement",
                axis="localization agreement",
                outcome=ComparatorConfrontationOutcome.ALIGNED,
                repository_position="The repository preserves localized versus ambiguous site evidence in the imported PTM review surface.",
                comparator_position="The established PTM workflow provides the imported localization-rich evidence table that the repository normalizes and reviews.",
                scientific_difference="Within the imported evidence boundary, the localization ladder remains aligned enough for governed PTM review.",
                consequence_for_review="Site-localization review can stay benchmark-backed while the conversation remains inside the pinned imported evidence family.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:ptm:ambiguity_divergence",
                axis="ambiguity divergence",
                outcome=ComparatorConfrontationOutcome.REPO_STRICTER,
                repository_position="The repository insists that ambiguous site groups stay visible and refuses to let them harden into a clean mechanistic site claim.",
                comparator_position="The external PTM workflow can still look stronger at a glance because the ambiguity burden is easier to miss once a site table is already emitted.",
                scientific_difference="The repository is stricter about carrying ambiguity pressure into the final PTM interpretation.",
                consequence_for_review="PTM packets better show why a site list is not automatically a mechanism claim.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:ptm:downstream_consequence",
                axis="downstream consequence differences",
                outcome=ComparatorConfrontationOutcome.REPO_WEAKER,
                repository_position="The repository can explain why PTM evidence stays bounded, but it still lacks a harder public comparator package that pressures broader PTM family diversity and downstream consequence realism.",
                comparator_position="The external PTM workflow owns the original algorithmic behavior that generated the imported site evidence and the broader family-specific burden the repository still lacks.",
                scientific_difference="The repository remains weaker on broader PTM comparator realism beyond the tidy imported phospho-oriented evidence package.",
                consequence_for_review="PTM authority remains strong on explicit ambiguity handling but still narrow on public comparator breadth.",
            ),
        ),
        overall_conclusion=(
            "The repository holds the line well on PTM ambiguity honesty, but it still relies on a narrow imported comparator family and therefore remains weaker on broader downstream PTM consequence realism."
        ),
        artifact_refs=tuple(path.comparator_path_id for path in comparator_paths),
        next_escalation=(
            "Add a harder flagship PTM package with broader family burden and external rescoring pressure so the PTM confrontation stops depending on one tidy imported evidence family."
        ),
    )


def _build_targeted_confrontation() -> WorkflowComparatorConfrontation:
    manifest = get_benchmark_manifest_for_family(KnowledgeWorkflowFamily.TARGETED)
    comparator_paths = list_workflow_comparator_paths(
        workflow_family=KnowledgeWorkflowFamily.TARGETED
    )
    return WorkflowComparatorConfrontation(
        confrontation_id="comparator_confrontation:targeted",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        benchmark_id=manifest.benchmark_id,
        comparator_tool=ProteomicsComparatorTool.SKYLINE,
        findings=(
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:targeted:calibration",
                axis="calibration behavior",
                outcome=ComparatorConfrontationOutcome.REPO_WEAKER,
                repository_position="The repository can state calibration burden and block overconfident follow-up, but it does not yet confront real calibration curves or calibrant drift against a Skyline-class comparator package.",
                comparator_position="The established targeted workflow owns the calibration-facing chromatogram and quantitative behavior the repository still lacks.",
                scientific_difference="The external targeted workflow clearly beats the repository on real calibration realism today.",
                consequence_for_review="Targeted decision-grade support remains blocked until calibration evidence becomes comparator-facing public substance.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:targeted:transition_handling",
                axis="transition handling",
                outcome=ComparatorConfrontationOutcome.REPO_STRICTER,
                repository_position="The repository is stronger at refusing to flatten transition-level caveats into automatic protein certainty or clean handoff optimism.",
                comparator_position="The external targeted workflow offers the deeper transition execution surface, but that does not automatically mean it carries the repository's refusal logic into the final operator narrative.",
                scientific_difference="The repository is stricter about keeping transition-level caution attached to the final follow-up recommendation.",
                consequence_for_review="Transition-facing review remains more honest even though the underlying comparator package is scientifically richer.",
            ),
            ComparatorConfrontationFinding(
                finding_id="comparator_confrontation:targeted:interference_conclusions",
                axis="interference conclusions",
                outcome=ComparatorConfrontationOutcome.REPO_WEAKER,
                repository_position="The repository names interference burden and blocks overclaiming, but it still has no public raw comparator bundle that proves it can read interference as well as the established targeted workflow.",
                comparator_position="The established targeted workflow owns the chromatogram-heavy interference evidence and vendor-shaped execution burden that the repository does not yet reproduce.",
                scientific_difference="The external targeted workflow still wins on interference realism, even though the repository is more explicit about the consequence of failure.",
                consequence_for_review="Targeted support remains advisory because interference conclusions are not yet backed by a real public comparator bundle.",
            ),
        ),
        overall_conclusion=(
            "The repository is better at refusing overconfident targeted storytelling, but the established targeted workflow still clearly beats it on calibration and interference realism."
        ),
        artifact_refs=tuple(path.comparator_path_id for path in comparator_paths),
        next_escalation=(
            "Build the promised Skyline-class raw comparator package so calibration curves, transition behavior, and interference conclusions are confronted on real public artifacts rather than only described."
        ),
    )


_SUPPORTED_BUILDERS = {
    KnowledgeWorkflowFamily.DDA: _build_dda_confrontation,
    KnowledgeWorkflowFamily.DIA: _build_dia_confrontation,
    KnowledgeWorkflowFamily.LFQ: _build_lfq_confrontation,
    KnowledgeWorkflowFamily.MULTIPLEX: _build_multiplex_confrontation,
    KnowledgeWorkflowFamily.PTM: _build_ptm_confrontation,
    KnowledgeWorkflowFamily.TARGETED: _build_targeted_confrontation,
}


def build_workflow_comparator_confrontation(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowComparatorConfrontation:
    """Build the comparator confrontation for one supported workflow family."""

    return _SUPPORTED_BUILDERS[workflow_family]()


def build_workflow_comparator_confrontation_report(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> WorkflowComparatorConfrontationReport:
    """Build comparator confrontations across supported workflow families."""

    families = (
        (workflow_family,)
        if workflow_family is not None
        else tuple(_SUPPORTED_BUILDERS)
    )
    return WorkflowComparatorConfrontationReport(
        entries=tuple(
            build_workflow_comparator_confrontation(family) for family in families
        )
    )


__all__ = [
    "ComparatorConfrontationFinding",
    "ComparatorConfrontationOutcome",
    "WorkflowComparatorConfrontation",
    "WorkflowComparatorConfrontationReport",
    "build_workflow_comparator_confrontation",
    "build_workflow_comparator_confrontation_report",
]
