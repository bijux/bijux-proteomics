# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow-family literature matrices tied to flagship benchmark packages."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
    get_citation_record,
    get_literature_group,
)


class WorkflowLiteratureMatrixEntry(JsonModel):
    """One literature-backed claim row for a flagship workflow benchmark."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    literature_group_id: str = Field(..., min_length=1)
    claim_theme: str = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(default_factory=tuple)
    citation_titles: tuple[str, ...] = Field(default_factory=tuple)
    benchmark_ids: tuple[str, ...] = Field(default_factory=tuple)
    context_ids: tuple[str, ...] = Field(default_factory=tuple)
    supported_claims: tuple[str, ...] = Field(default_factory=tuple)
    bounded_claims: tuple[str, ...] = Field(default_factory=tuple)
    carry_forward_caveats: tuple[str, ...] = Field(default_factory=tuple)
    reviewer_questions: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowLiteratureMatrix(JsonModel):
    """Curated literature matrix for one flagship workflow benchmark family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_id: str = Field(..., min_length=1)
    benchmark_title: str = Field(..., min_length=1)
    entries: tuple[WorkflowLiteratureMatrixEntry, ...] = Field(default_factory=tuple)
    coverage_note: str = Field(..., min_length=1)


class _MatrixBlueprint(JsonModel):
    """Internal blueprint for one matrix row."""

    model_config = ConfigDict(extra="forbid")

    literature_group_id: str = Field(..., min_length=1)
    claim_theme: str = Field(..., min_length=1)
    supported_claims: tuple[str, ...] = Field(default_factory=tuple)
    bounded_claims: tuple[str, ...] = Field(default_factory=tuple)
    carry_forward_caveats: tuple[str, ...] = Field(default_factory=tuple)
    reviewer_questions: tuple[str, ...] = Field(default_factory=tuple)


_MATRIX_BLUEPRINTS: dict[KnowledgeWorkflowFamily, tuple[_MatrixBlueprint, ...]] = {
    KnowledgeWorkflowFamily.DDA: (
        _MatrixBlueprint(
            literature_group_id="literature:fdr_scope",
            claim_theme="target-decoy scope and confidence survivability",
            supported_claims=(
                "The flagship DDA benchmark can support peptide-facing confidence review only when target-decoy evidence remains visible after adapter normalization.",
            ),
            bounded_claims=(
                "A stable protein list is not enough to claim trustworthy identification if target-decoy posture becomes opaque.",
            ),
            carry_forward_caveats=(
                "The benchmark still relies on a pinned external export instead of a live engine rerun inside the repository.",
            ),
            reviewer_questions=(
                "Does the artifact bundle still make decoy visibility auditable after normalization and rollup?",
            ),
        ),
        _MatrixBlueprint(
            literature_group_id="literature:enzyme_panel_comparability",
            claim_theme="reviewed-proteome grounding and protease-bounded interpretation",
            supported_claims=(
                "The flagship DDA benchmark can support reviewed-proteome mapping and explicit enzyme-bounded interpretation.",
            ),
            bounded_claims=(
                "The benchmark cannot authorize broad multi-protease or cohort-scale protein inference trust.",
            ),
            carry_forward_caveats=(
                "The checked-in fixture is cleaner and more uniform than a mixed-engine production search bundle.",
            ),
            reviewer_questions=(
                "Do the reviewed-proteome mappings stay explicit enough that downstream biology still knows what was actually identified?",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.DIA: (
        _MatrixBlueprint(
            literature_group_id="literature:dia_library_scope",
            claim_theme="library-conditioned transition semantics",
            supported_claims=(
                "The flagship DIA benchmark can support library-conditioned transition and extraction review when the linked library scope remains visible.",
            ),
            bounded_claims=(
                "The benchmark cannot authorize open-ended protein absence or broad vendor-parity claims outside the pinned library-conditioned export family.",
            ),
            carry_forward_caveats=(
                "The benchmark remains bounded by library completeness and does not yet confront production-scale chromatography drift.",
            ),
            reviewer_questions=(
                "Is the final review still explicit about what the library made visible and what it could never observe?",
            ),
        ),
        _MatrixBlueprint(
            literature_group_id="literature:qc_signal_quality",
            claim_theme="quality-control pressure on biological interpretation",
            supported_claims=(
                "The flagship DIA benchmark can support review-grade interpretation only while absent expected peptides, ion-mobility scope, and transition quality stay explicit together.",
            ),
            bounded_claims=(
                "A numerically clean import is not enough to call the downstream biological story trustworthy.",
            ),
            carry_forward_caveats=(
                "The current benchmark package still reads from pinned exports rather than a fully reproduced external DIA engine run inside this repository.",
            ),
            reviewer_questions=(
                "Can an outsider see where transition quality pressure still downgrades the biological takeaway?",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.LFQ: (
        _MatrixBlueprint(
            literature_group_id="literature:quantification_rollup",
            claim_theme="missingness-aware abundance interpretation",
            supported_claims=(
                "The flagship LFQ benchmark can support review-grade abundance interpretation when missingness and rollup scope remain first-class in the output.",
            ),
            bounded_claims=(
                "Stable protein summaries do not by themselves authorize decision-grade abundance biology when missingness may still be informative.",
            ),
            carry_forward_caveats=(
                "The current fixture does not yet express the severe missing-not-at-random behavior expected from a flagship public cohort package.",
            ),
            reviewer_questions=(
                "Would a skeptical reader still see how missingness changes the meaning of the abundance claim?",
            ),
        ),
        _MatrixBlueprint(
            literature_group_id="literature:study_design_contrast_limits",
            claim_theme="contrast scope and cohort transfer limits",
            supported_claims=(
                "The flagship LFQ benchmark can support one documented study-design contrast with explicit replicate and batch framing.",
            ),
            bounded_claims=(
                "The benchmark cannot authorize broad cohort-transferable conclusions beyond the documented contrast and replicate structure.",
            ),
            carry_forward_caveats=(
                "The current benchmark still reflects a tidy study shape rather than a public cohort with harder heterogeneity.",
            ),
            reviewer_questions=(
                "Can a reader tell exactly which abundance contrast was benchmarked and which broader cohort claims remain out of scope?",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: (
        _MatrixBlueprint(
            literature_group_id="literature:multiplex_interference_limits",
            claim_theme="reporter-channel chemistry and interference limits",
            supported_claims=(
                "The flagship multiplex benchmark can support review-grade channel interpretation when reporter interference and balance caveats stay attached to the result.",
            ),
            bounded_claims=(
                "Reporter stability in this benchmark does not authorize label-free-style biological certainty.",
            ),
            carry_forward_caveats=(
                "The current package still lacks the strongest public carrier overload and interference burden expected from a flagship external dataset.",
            ),
            reviewer_questions=(
                "Do the tracked outputs still show the chemistry burden that makes reporter ratios fragile?",
            ),
        ),
        _MatrixBlueprint(
            literature_group_id="literature:quantification_rollup",
            claim_theme="rollup caution under channel-specific evidence",
            supported_claims=(
                "The flagship multiplex benchmark can support protein-facing review only when peptide- and channel-level caveats remain visible in the rollup.",
            ),
            bounded_claims=(
                "A clean multiplex summary should not erase channel dropouts, ratio compression, or reference dependence.",
            ),
            carry_forward_caveats=(
                "The benchmark package currently lacks an external multiplex comparator path, so channel-level interpretation still stops short of outsider-grade trust.",
            ),
            reviewer_questions=(
                "Is the protein summary still anchored to the channel behavior that made it credible in the first place?",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.PTM: (
        _MatrixBlueprint(
            literature_group_id="literature:ptm_localization",
            claim_theme="site-localization confidence versus ambiguity",
            supported_claims=(
                "The flagship PTM benchmark can support site-localization review when the localization ladder stays visible and ambiguity is not flattened into a clean site call.",
            ),
            bounded_claims=(
                "The benchmark cannot authorize confident site-level biology when ambiguous and localized evidence are collapsed together.",
            ),
            carry_forward_caveats=(
                "The current benchmark emphasizes phosphorylation-style localization and does not yet cover a broader flagship PTM family landscape.",
            ),
            reviewer_questions=(
                "Can a reviewer still see which site claims stayed ambiguous even when the output looks tidy?",
            ),
        ),
        _MatrixBlueprint(
            literature_group_id="literature:ptm_regulation_limits",
            claim_theme="occupancy and regulation boundary",
            supported_claims=(
                "The flagship PTM benchmark can support bounded interpretation about localized evidence and cautionary occupancy framing.",
            ),
            bounded_claims=(
                "The benchmark cannot authorize mechanistic or pathway-level regulation claims on the basis of localization alone.",
            ),
            carry_forward_caveats=(
                "The present package remains too tidy to justify broad regulatory storytelling even when localization confidence appears strong.",
            ),
            reviewer_questions=(
                "Does the reading surface still prevent localized evidence from silently turning into a mechanistic claim?",
            ),
        ),
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        _MatrixBlueprint(
            literature_group_id="literature:targeted_rollup_caution",
            claim_theme="transition-first evidence and protein rollup caution",
            supported_claims=(
                "The flagship targeted benchmark can support operator-facing transition QC interpretation when transition evidence stays connected to any protein-facing summary.",
            ),
            bounded_claims=(
                "A clean targeted summary does not authorize protein certainty when chromatogram-specific caveats disappear.",
            ),
            carry_forward_caveats=(
                "The current targeted benchmark still lacks the real calibration and interference burden expected from a public flagship targeted dataset.",
            ),
            reviewer_questions=(
                "Would a lab reader still know which transition-level failures made the higher-level claim unsafe?",
            ),
        ),
        _MatrixBlueprint(
            literature_group_id="literature:qc_signal_quality",
            claim_theme="quality-control burden on operator-facing trust",
            supported_claims=(
                "The flagship targeted benchmark can support advisory QC interpretation while control coverage, carryover visibility, and handoff honesty remain explicit.",
            ),
            bounded_claims=(
                "The benchmark cannot authorize vendor-parity targeted biology or direct outcome certainty on the current fixture package alone.",
            ),
            carry_forward_caveats=(
                "The comparator path is still missing, so targeted support remains structurally weaker than a Skyline-class confrontation would require.",
            ),
            reviewer_questions=(
                "Can the current packet tell an operator why a follow-up still should not be trusted as decision-grade?",
            ),
        ),
    ),
}

def build_workflow_literature_matrix(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowLiteratureMatrix:
    """Build the curated literature matrix for one workflow family."""

    manifest = get_benchmark_manifest_for_family(workflow_family)
    entries = []
    for index, blueprint in enumerate(_MATRIX_BLUEPRINTS[workflow_family], start=1):
        group = get_literature_group(blueprint.literature_group_id)
        citations = tuple(get_citation_record(citation_id) for citation_id in group.citation_ids)
        entries.append(
            WorkflowLiteratureMatrixEntry(
                entry_id=f"literature_matrix:{workflow_family.value}:{index}",
                workflow_family=workflow_family,
                literature_group_id=group.group_id,
                claim_theme=blueprint.claim_theme,
                citation_ids=group.citation_ids,
                citation_titles=tuple(citation.title for citation in citations),
                benchmark_ids=group.benchmark_ids,
                context_ids=group.context_ids,
                supported_claims=blueprint.supported_claims,
                bounded_claims=blueprint.bounded_claims,
                carry_forward_caveats=blueprint.carry_forward_caveats,
                reviewer_questions=blueprint.reviewer_questions,
            )
        )
    coverage_note = (
        "This matrix ties the flagship benchmark to exact paper-backed themes, and every bounded claim remains visible alongside the support claim instead of being pushed into a separate caveat bucket."
    )
    return WorkflowLiteratureMatrix(
        workflow_family=workflow_family,
        benchmark_id=manifest.benchmark_id,
        benchmark_title=manifest.title,
        entries=tuple(entries),
        coverage_note=coverage_note,
    )


def list_workflow_literature_matrices() -> tuple[WorkflowLiteratureMatrix, ...]:
    """Return curated literature matrices across all workflow families."""

    return tuple(
        build_workflow_literature_matrix(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


__all__ = [
    "WorkflowLiteratureMatrix",
    "WorkflowLiteratureMatrixEntry",
    "build_workflow_literature_matrix",
    "list_workflow_literature_matrices",
]
