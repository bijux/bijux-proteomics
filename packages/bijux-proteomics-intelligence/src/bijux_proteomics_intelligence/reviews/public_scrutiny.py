# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public scrutiny surfaces for flagship release and trust review."""

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
from bijux_proteomics_intelligence.reviews.outsider_packets import (
    FlagshipOutsiderReviewPacket,
    build_flagship_outsider_review_packet_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.claim_grounding import (
    WorkflowUnsupportedClaimLedger,
    build_workflow_unsupported_claim_ledger,
)

__all__ = [
    "PublicArtifactIndex",
    "PublicArtifactIndexEntry",
    "TrustBreakPage",
    "TrustBreakPageEntry",
    "TrustNextPage",
    "TrustNextPageEntry",
    "build_public_artifact_index",
    "build_trust_break_page",
    "build_trust_next_page",
]


_WORKFLOW_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)


class PublicArtifactIndexEntry(JsonModel):
    """One reviewer-facing artifact entry in the flagship scrutiny index."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily | None = None
    owner_package: str = Field(..., min_length=1)
    artifact_kind: str = Field(..., min_length=1)
    locator: str = Field(..., min_length=1)
    why_open_this: str = Field(..., min_length=1)


class PublicArtifactIndex(JsonModel):
    """One public index across the strongest current flagship review surfaces."""

    model_config = ConfigDict(extra="forbid")

    index_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[PublicArtifactIndexEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class TrustBreakPageEntry(JsonModel):
    """One condition that would weaken today's strongest trust surface."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily | None = None
    break_condition: str = Field(..., min_length=1)
    affected_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    why_it_matters: str = Field(..., min_length=1)


class TrustBreakPage(JsonModel):
    """One page explaining how today's bounded trust could fail tomorrow."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(..., min_length=1)
    doc_path: str = Field(..., min_length=1)
    entries: tuple[TrustBreakPageEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class TrustNextPageEntry(JsonModel):
    """One strengthening path that would earn more trust next."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily | None = None
    current_claim: str = Field(..., min_length=1)
    why_still_thin: str = Field(..., min_length=1)
    strengthening_path: str = Field(..., min_length=1)


class TrustNextPage(JsonModel):
    """One page explaining what would earn stronger trust next."""

    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(..., min_length=1)
    doc_path: str = Field(..., min_length=1)
    entries: tuple[TrustNextPageEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def _outsider_packets() -> dict[KnowledgeWorkflowFamily, FlagshipOutsiderReviewPacket]:
    family = build_flagship_outsider_review_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


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


def _ledger(workflow_family: KnowledgeWorkflowFamily) -> WorkflowUnsupportedClaimLedger:
    return build_workflow_unsupported_claim_ledger(workflow_family)


def build_public_artifact_index() -> PublicArtifactIndex:
    """Build the flagship public artifact index for hostile review."""

    entries: list[PublicArtifactIndexEntry] = [
        PublicArtifactIndexEntry(
            entry_id="artifact-index:release-candidate",
            workflow_family=None,
            owner_package="bijux-proteomics-docs",
            artifact_kind="foundation-page",
            locator="docs/01-bijux-proteomics/foundation/flagship-release-candidate.md",
            why_open_this="This page names the current outsider-auditable families and the internal-support boundary in one place.",
        ),
        PublicArtifactIndexEntry(
            entry_id="artifact-index:elite-readiness-scorecard",
            workflow_family=None,
            owner_package="bijux-proteomics-docs",
            artifact_kind="foundation-page",
            locator="docs/01-bijux-proteomics/foundation/elite-readiness-scorecard.md",
            why_open_this="This page states how far public evidence currently authorizes stronger language.",
        ),
    ]
    for workflow_family in _WORKFLOW_FAMILIES:
        packet = _outsider_packets()[workflow_family]
        rerun_dossier = _independent_rerun_dossiers()[workflow_family]
        review_kit = _external_review_kits()[workflow_family]
        entries.extend(
            (
                PublicArtifactIndexEntry(
                    entry_id=f"artifact-index:{workflow_family.value}:outsider-packet",
                    workflow_family=workflow_family,
                    owner_package="bijux-proteomics-intelligence",
                    artifact_kind="outsider-packet",
                    locator=packet.packet_id,
                    why_open_this="This is the shortest owner-facing packet that ties benchmark, comparator, recommendation, and consequence surfaces together.",
                ),
                PublicArtifactIndexEntry(
                    entry_id=f"artifact-index:{workflow_family.value}:independent-rerun",
                    workflow_family=workflow_family,
                    owner_package="bijux-proteomics-intelligence",
                    artifact_kind="independent-rerun-dossier",
                    locator=rerun_dossier.artifact_path,
                    why_open_this="This dossier explains how the workflow claim survives a paired rerun or cross-package challenge instead of one convenient flagship package.",
                ),
                PublicArtifactIndexEntry(
                    entry_id=f"artifact-index:{workflow_family.value}:external-review-kit",
                    workflow_family=workflow_family,
                    owner_package="bijux-proteomics-intelligence",
                    artifact_kind="external-review-kit",
                    locator=review_kit.artifact_path,
                    why_open_this="This kit is the shortest outsider route through the shipped files needed to challenge the current bounded claim.",
                ),
            )
        )
    return PublicArtifactIndex(
        index_id="flagship-public-artifact-index",
        artifact_path="artifacts/intelligence/public-scrutiny/flagship_public_artifact_index.json",
        entries=tuple(entries),
        note=(
            "The index exists so a hostile reader can open the strongest current surfaces in a stable order instead of reverse-engineering the repository by package structure."
        ),
    )


def build_trust_break_page() -> TrustBreakPage:
    """Build the page describing what would weaken current flagship trust tomorrow."""

    entries: list[TrustBreakPageEntry] = [
        TrustBreakPageEntry(
            entry_id="trust-break:repository",
            workflow_family=None,
            break_condition=(
                "If the repository stops shipping one coherent artifact index, release-candidate page, and review-kit path, current bounded trust becomes maintainer-memory dependent again."
            ),
            affected_surfaces=(
                "docs/01-bijux-proteomics/foundation/flagship-release-candidate.md",
                "docs/01-bijux-proteomics/foundation/elite-readiness-scorecard.md",
                "artifacts/intelligence/public-scrutiny/flagship_public_artifact_index.json",
            ),
            why_it_matters=(
                "The proof boundary is already narrow. If the navigation layer drifts, the remaining trust becomes harder to audit than it is to claim."
            ),
        )
    ]
    for workflow_family in _WORKFLOW_FAMILIES:
        packet = _outsider_packets()[workflow_family]
        rerun_dossier = _independent_rerun_dossiers()[workflow_family]
        review_kit = _external_review_kits()[workflow_family]
        entries.append(
            TrustBreakPageEntry(
                entry_id=f"trust-break:{workflow_family.value}",
                workflow_family=workflow_family,
                break_condition=(
                    f"If {workflow_family.value} loses either its companion rerun dossier or its outsider review kit, the current bounded outsider-auditable sentence becomes too governance-dependent again."
                ),
                affected_surfaces=(
                    packet.packet_id,
                    rerun_dossier.dossier_id,
                    review_kit.kit_id,
                ),
                why_it_matters=(
                    "The current trust boundary depends on more than one flagship package. Lose the paired challenge path and the sentence falls back toward one-package optimism."
                ),
            )
        )
    return TrustBreakPage(
        page_id="what-breaks-elite-trust",
        doc_path="docs/01-bijux-proteomics/foundation/what-breaks-elite-trust.md",
        entries=tuple(entries),
        note=(
            "The page is intentionally about fragile current trust, not imaginary future prestige."
        ),
    )


def build_trust_next_page() -> TrustNextPage:
    """Build the page describing what would earn stronger trust next."""

    entries: list[TrustNextPageEntry] = []
    for workflow_family in _WORKFLOW_FAMILIES:
        ledger_entry = _ledger(workflow_family).entries[0]
        entries.append(
            TrustNextPageEntry(
                entry_id=f"trust-next:{workflow_family.value}",
                workflow_family=workflow_family,
                current_claim=ledger_entry.claim_text,
                why_still_thin=ledger_entry.why_still_thin,
                strengthening_path=ledger_entry.strengthening_path,
            )
        )
    entries.append(
        TrustNextPageEntry(
            entry_id="trust-next:repository",
            workflow_family=None,
            current_claim=(
                "The repository may talk about bounded outsider-auditable workflow families, but not about repository-wide elite or reliable scientific authority."
            ),
            why_still_thin=(
                "Multiple workflow families are bounded and real, but the strongest current trust still depends on advisory comparator posture, narrow rerun surfaces, and benchmark-simulated consequence loops."
            ),
            strengthening_path=(
                "Earn more than one stronger supported comparator and consequence loop first, then let the README and release pages move only after repository truth stops blocking the language."
            ),
        )
    )
    return TrustNextPage(
        page_id="what-earns-elite-trust-next",
        doc_path="docs/01-bijux-proteomics/foundation/what-earns-elite-trust-next.md",
        entries=tuple(entries),
        note=(
            "The page names the next hard proof moves instead of generic improvement wishes."
        ),
    )
