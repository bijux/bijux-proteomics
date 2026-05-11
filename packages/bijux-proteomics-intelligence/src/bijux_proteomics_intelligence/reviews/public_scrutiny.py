# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public scrutiny surfaces for flagship release and artifact-role review."""

from __future__ import annotations

from functools import lru_cache

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.reviews.external_review_kits import (
    WorkflowExternalReviewKit,
    build_workflow_external_review_kit_family,
)
from bijux_proteomics_intelligence.reviews.independent_reruns import (
    WorkflowIndependentRerunDossier,
    build_workflow_independent_rerun_dossier_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "PublicArtifactIndex",
    "PublicArtifactIndexEntry",
    "PublicArtifactRoleMatrix",
    "PublicArtifactRoleMatrixEntry",
    "build_public_artifact_index",
    "build_public_artifact_role_matrix",
]


_WORKFLOW_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)


class PublicArtifactIndexEntry(JsonModel):
    """One reviewer-facing artifact entry in the public scrutiny registry."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily | None = None
    owner_package: str = Field(..., min_length=1)
    artifact_kind: str = Field(..., min_length=1)
    locator: str = Field(..., min_length=1)
    audience: str = Field(..., min_length=1)
    question_answered: str = Field(..., min_length=1)
    decision_role: str = Field(..., min_length=1)
    stronger_neighbor: str | None = None
    weaker_neighbor: str | None = None
    coexistence_rationale: str = Field(..., min_length=1)
    why_open_this: str = Field(..., min_length=1)


class PublicArtifactIndex(JsonModel):
    """One public index across the strongest current release-facing artifacts."""

    model_config = ConfigDict(extra="forbid")

    index_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    artifact_budget: int = Field(..., ge=1)
    entries: tuple[PublicArtifactIndexEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PublicArtifactRoleMatrixEntry(JsonModel):
    """One role row describing why a public artifact still exists."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily | None = None
    artifact_kind: str = Field(..., min_length=1)
    audience: str = Field(..., min_length=1)
    decision_role: str = Field(..., min_length=1)
    question_answered: str = Field(..., min_length=1)
    stronger_neighbor: str | None = None
    weaker_neighbor: str | None = None
    coexistence_rationale: str = Field(..., min_length=1)


class PublicArtifactRoleMatrix(JsonModel):
    """One role matrix showing how adjacent public artifacts differ."""

    model_config = ConfigDict(extra="forbid")

    matrix_id: str = Field(..., min_length=1)
    doc_path: str = Field(..., min_length=1)
    rows: tuple[PublicArtifactRoleMatrixEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def _independent_rerun_dossiers() -> dict[
    KnowledgeWorkflowFamily, WorkflowIndependentRerunDossier
]:
    family = build_workflow_independent_rerun_dossier_family()
    return {dossier.workflow_family: dossier for dossier in family.dossiers}


@lru_cache(maxsize=1)
def _external_review_kits() -> dict[KnowledgeWorkflowFamily, WorkflowExternalReviewKit]:
    family = build_workflow_external_review_kit_family()
    return {kit.workflow_family: kit for kit in family.kits}


def _trust_page_path(workflow_family: KnowledgeWorkflowFamily) -> str:
    return f"docs/01-bijux-proteomics/foundation/why-trust-{workflow_family.value}.md"


def build_public_artifact_index() -> PublicArtifactIndex:
    """Build the public artifact registry for hostile review."""

    entries: list[PublicArtifactIndexEntry] = [
        PublicArtifactIndexEntry(
            entry_id="artifact-index:release-candidate",
            workflow_family=None,
            owner_package="bijux-proteomics-docs",
            artifact_kind="foundation-page",
            locator="docs/01-bijux-proteomics/foundation/flagship-release-candidate.md",
            audience="scientist",
            question_answered="Which workflow families can the repository defend today?",
            decision_role="repository-release-boundary",
            stronger_neighbor="artifact-index:hostile-review-kit",
            weaker_neighbor="artifact-index:elite-readiness-scorecard",
            coexistence_rationale="The release-candidate page names the bounded family set, while the hostile review kit is the harder challenge route and the scorecard is the narrower language ceiling.",
            why_open_this="This page names the current outsider-auditable families and the internal-support boundary in one place.",
        ),
        PublicArtifactIndexEntry(
            entry_id="artifact-index:elite-readiness-scorecard",
            workflow_family=None,
            owner_package="bijux-proteomics-docs",
            artifact_kind="foundation-page",
            locator="docs/01-bijux-proteomics/foundation/elite-readiness-scorecard.md",
            audience="maintainer",
            question_answered="How far may repository-wide language go today?",
            decision_role="repository-language-ceiling",
            stronger_neighbor="artifact-index:release-candidate",
            weaker_neighbor=None,
            coexistence_rationale="The scorecard is weaker than the release-candidate bundle because it summarizes a boundary rather than naming each family surface.",
            why_open_this="This page states how far public evidence currently authorizes stronger language.",
        ),
        PublicArtifactIndexEntry(
            entry_id="artifact-index:hostile-review-kit",
            workflow_family=None,
            owner_package="bijux-proteomics-docs",
            artifact_kind="foundation-page",
            locator="docs/01-bijux-proteomics/foundation/hostile-review-kit.md",
            audience="skeptical outsider",
            question_answered="What is the shortest whole-repository challenge route?",
            decision_role="repository-challenge-route",
            stronger_neighbor=None,
            weaker_neighbor="artifact-index:release-candidate",
            coexistence_rationale="The hostile review kit is the strongest whole-repository opening order because it routes directly from the root promise into the hardest challenge surfaces.",
            why_open_this="This page is the shortest repository-wide challenge order for a skeptical reviewer.",
        ),
        PublicArtifactIndexEntry(
            entry_id="artifact-index:why-not-ready",
            workflow_family=None,
            owner_package="bijux-proteomics-docs",
            artifact_kind="foundation-page",
            locator="docs/01-bijux-proteomics/foundation/why-this-repository-is-not-ready-yet.md",
            audience="reviewer",
            question_answered="Which blocked release bars still fail right now?",
            decision_role="repository-blocker-ledger",
            stronger_neighbor="artifact-index:what-makes-ready",
            weaker_neighbor="artifact-index:elite-readiness-scorecard",
            coexistence_rationale="This page names live blockers, while its paired next-step page turns those same categories into closing conditions instead of duplicating softer trust prose.",
            why_open_this="This page shows the live blocker categories that still prevent stronger release language.",
        ),
        PublicArtifactIndexEntry(
            entry_id="artifact-index:what-makes-ready",
            workflow_family=None,
            owner_package="bijux-proteomics-docs",
            artifact_kind="foundation-page",
            locator="docs/01-bijux-proteomics/foundation/what-would-make-this-repository-ready.md",
            audience="maintainer",
            question_answered="What concrete evidence would move the release boundary next?",
            decision_role="repository-closing-conditions",
            stronger_neighbor=None,
            weaker_neighbor="artifact-index:why-not-ready",
            coexistence_rationale="This page exists next to the blocker ledger because closing conditions are an action surface, not just a list of current failures.",
            why_open_this="This page turns blocked release bars into explicit closing conditions instead of roadmap theater.",
        ),
    ]
    for workflow_family in _WORKFLOW_FAMILIES:
        rerun_dossier = _independent_rerun_dossiers()[workflow_family]
        review_kit = _external_review_kits()[workflow_family]
        entries.extend(
            (
                PublicArtifactIndexEntry(
                    entry_id=f"artifact-index:{workflow_family.value}:trust-page",
                    workflow_family=workflow_family,
                    owner_package="bijux-proteomics-docs",
                    artifact_kind="workflow-trust-page",
                    locator=_trust_page_path(workflow_family),
                    audience="scientist",
                    question_answered=f"Why does {workflow_family.value} still earn bounded outsider-auditable language today?",
                    decision_role="workflow-justification",
                    stronger_neighbor=f"artifact-index:{workflow_family.value}:external-review-kit",
                    weaker_neighbor="artifact-index:release-candidate",
                    coexistence_rationale="The trust page narrows one workflow-family sentence, while the release-candidate page names the broader family set and the external review kit is the harder challenge lane.",
                    why_open_this="This page states the exact bounded sentence that the current workflow-family evidence can still carry.",
                ),
                PublicArtifactIndexEntry(
                    entry_id=f"artifact-index:{workflow_family.value}:independent-rerun",
                    workflow_family=workflow_family,
                    owner_package="bijux-proteomics-intelligence",
                    artifact_kind="independent-rerun-dossier",
                    locator=rerun_dossier.artifact_path,
                    audience="operator",
                    question_answered=f"Can {workflow_family.value} survive a second checked rerun challenge?",
                    decision_role="workflow-rerun-challenge",
                    stronger_neighbor=f"artifact-index:{workflow_family.value}:external-review-kit",
                    weaker_neighbor=f"artifact-index:{workflow_family.value}:trust-page",
                    coexistence_rationale="The rerun dossier exists because the trust page alone is too claim-oriented, while the external review kit is the stronger outsider path that packages the dossier with the key benchmark and recommendation files.",
                    why_open_this="This dossier explains how the workflow claim survives a paired rerun or cross-package challenge instead of one convenient flagship package.",
                ),
                PublicArtifactIndexEntry(
                    entry_id=f"artifact-index:{workflow_family.value}:external-review-kit",
                    workflow_family=workflow_family,
                    owner_package="bijux-proteomics-intelligence",
                    artifact_kind="external-review-kit",
                    locator=review_kit.artifact_path,
                    audience="skeptical outsider",
                    question_answered=f"What should an outsider open to challenge the {workflow_family.value} sentence?",
                    decision_role="workflow-outsider-challenge",
                    stronger_neighbor=None,
                    weaker_neighbor=f"artifact-index:{workflow_family.value}:independent-rerun",
                    coexistence_rationale="The external review kit remains the strongest family-level challenge artifact because it packages the rerun lane with the benchmark, recommendation, and consequence surfaces needed to reject the claim honestly.",
                    why_open_this="This kit is the shortest outsider route through the shipped files needed to challenge the current bounded claim.",
                ),
            )
        )
    return PublicArtifactIndex(
        index_id="flagship-public-artifact-index",
        artifact_path="artifacts/intelligence/public-scrutiny/flagship_public_artifact_index.json",
        artifact_budget=20,
        entries=tuple(entries),
        note=(
            "The index exists so a hostile reader can open the strongest current surfaces in a stable order instead of reverse-engineering the repository by package structure."
        ),
    )


def build_public_artifact_role_matrix() -> PublicArtifactRoleMatrix:
    """Build the role matrix that explains why each public artifact still exists."""

    index = build_public_artifact_index()
    rows = tuple(
        PublicArtifactRoleMatrixEntry(
            entry_id=entry.entry_id,
            workflow_family=entry.workflow_family,
            artifact_kind=entry.artifact_kind,
            audience=entry.audience,
            decision_role=entry.decision_role,
            question_answered=entry.question_answered,
            stronger_neighbor=entry.stronger_neighbor,
            weaker_neighbor=entry.weaker_neighbor,
            coexistence_rationale=entry.coexistence_rationale,
        )
        for entry in index.entries
    )
    return PublicArtifactRoleMatrix(
        matrix_id="public-artifact-role-matrix",
        doc_path="docs/01-bijux-proteomics/foundation/public-artifact-role-matrix.md",
        rows=rows,
        note=(
            "The role matrix exists so new public artifacts must justify a distinct decision role instead of piling up as adjacent trust-shaped noise."
        ),
    )
