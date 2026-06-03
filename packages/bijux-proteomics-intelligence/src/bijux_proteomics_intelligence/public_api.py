"""Machine-readable intelligence root public API contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntelligenceRootApiBudget:
    """Budget for the durable intelligence root surface."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class IntelligenceRootApiEntry:
    """One stable intelligence root export."""

    export_name: str
    owner_module: str
    classification: str
    rationale: str


INTELLIGENCE_ROOT_API_BUDGET = IntelligenceRootApiBudget(
    max_public_symbols=14,
    max_init_lines=36,
)


def _entries(
    *,
    export_names: tuple[str, ...],
    owner_module: str,
    classification: str,
    rationale: str,
) -> tuple[IntelligenceRootApiEntry, ...]:
    return tuple(
        IntelligenceRootApiEntry(
            export_name=name,
            owner_module=owner_module
            if "." in owner_module
            else f"bijux_proteomics_intelligence.{owner_module}",
            classification=classification,
            rationale=rationale,
        )
        for name in export_names
    )


def list_intelligence_root_api_entries() -> tuple[IntelligenceRootApiEntry, ...]:
    """Return the curated public root API for the intelligence package.

    Inputs:
    This function takes no runtime arguments and returns the in-module
    intelligence root export ledger.

    Outputs:
    Returns the full tuple of ``IntelligenceRootApiEntry`` records that define
    the supported intelligence package root exports.

    Failure Modes:
    This function does not raise governed public exceptions under normal
    package import conditions.

    Scientific Caveats:
    The ledger records package-level review ownership and export policy only; it
    does not score evidence, judge claims, or validate one scientific report.
    """

    return (
        _entries(
            export_names=("belief_audit",),
            owner_module="bijux_proteomics_intelligence.belief_audit",
            classification="root_owner_surface",
            rationale="belief-audit review stays public as a package-level challenge surface over assembled scientific evidence",
        )
        + _entries(
            export_names=("candidates",),
            owner_module="bijux_proteomics_intelligence.candidates",
            classification="owner_family_namespace",
            rationale="candidate ranking and selection stay public under one stable intelligence owner family",
        )
        + _entries(
            export_names=("claims",),
            owner_module="bijux_proteomics_intelligence.claims",
            classification="root_owner_surface",
            rationale="claim-support evaluation remains a stable package-level intelligence surface for downstream review work",
        )
        + _entries(
            export_names=("contradictions",),
            owner_module="bijux_proteomics_intelligence.contradictions",
            classification="root_owner_surface",
            rationale="claim contradiction detection stays public as a direct review surface over assembled evidence",
        )
        + _entries(
            export_names=("falsifiers",),
            owner_module="bijux_proteomics_intelligence.falsifiers",
            classification="root_owner_surface",
            rationale="falsifier generation remains a stable intelligence entrypoint for skeptical follow-up design",
        )
        + _entries(
            export_names=("governance",),
            owner_module="bijux_proteomics_intelligence.governance",
            classification="supporting_owner_namespace",
            rationale="governance remains a first-class intelligence owner family that downstream callers need to discover directly from the package root",
        )
        + _entries(
            export_names=("interpretation",),
            owner_module="bijux_proteomics_intelligence.interpretation",
            classification="supporting_owner_namespace",
            rationale="interpretation remains a first-class intelligence owner family that downstream callers need to discover directly from the package root",
        )
        + _entries(
            export_names=("judgment",),
            owner_module="bijux_proteomics_intelligence.judgment",
            classification="owner_family_namespace",
            rationale="judgment-path and recommendation logic stays public under one stable intelligence owner family",
        )
        + _entries(
            export_names=("learning",),
            owner_module="bijux_proteomics_intelligence.learning",
            classification="owner_family_namespace",
            rationale="learning and adaptation logic stays grouped under one public intelligence owner family",
        )
        + _entries(
            export_names=("next_steps",),
            owner_module="bijux_proteomics_intelligence.next_steps",
            classification="root_owner_surface",
            rationale="next-step recommendation remains a stable package-level handoff from evidence review into action planning",
        )
        + _entries(
            export_names=("posture",),
            owner_module="bijux_proteomics_intelligence.posture",
            classification="owner_family_namespace",
            rationale="evidence-posture review remains public under one stable intelligence owner family",
        )
        + _entries(
            export_names=("query",),
            owner_module="bijux_proteomics_intelligence.query",
            classification="root_owner_surface",
            rationale="result interrogation stays public as a first-class intelligence-facing question surface",
        )
        + _entries(
            export_names=("refusal",),
            owner_module="bijux_proteomics_intelligence.refusal",
            classification="root_owner_surface",
            rationale="refusal of unsupported claims remains a stable package-level scientific safety surface",
        )
        + _entries(
            export_names=("reviews",),
            owner_module="bijux_proteomics_intelligence.reviews",
            classification="owner_family_namespace",
            rationale="review-board helper families stay public under one stable intelligence owner namespace",
        )
    )


__all__ = [
    "INTELLIGENCE_ROOT_API_BUDGET",
    "IntelligenceRootApiBudget",
    "IntelligenceRootApiEntry",
    "list_intelligence_root_api_entries",
]
