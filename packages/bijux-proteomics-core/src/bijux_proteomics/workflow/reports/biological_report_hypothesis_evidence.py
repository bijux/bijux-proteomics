# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned evidence-link helpers for biological hypothesis candidates."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    PathwayActivityReport,
    RegulatorInferenceReport,
)
from bijux_proteomics.interpretation.pathway_activity import (
    PathwayConditionComparisonEntry,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCard,
)


def _graph_node_ids_from_cards(
    cards: tuple[ProteinMechanismCard, ...],
) -> tuple[str, ...]:
    node_ids: list[str] = []
    for card in cards:
        node_ids.extend((card.graph_subject_node_id, card.graph_claim_node_id))
    return tuple(sorted(set(node_ids)))


def _protein_hypothesis_opposing_evidence(
    card: ProteinMechanismCard,
) -> tuple[str, ...]:
    opposing = {
        *(reason.value for reason in card.downgrade_reasons),
        *(code.value for code in card.warning_codes),
    }
    return tuple(sorted(opposing))


def _pathway_hypothesis_supporting_protein_refs(
    pathway_activity_report: PathwayActivityReport,
    *,
    pathway_id: str,
    condition_a: str,
    condition_b: str,
    cards_by_ref: dict[str, ProteinMechanismCard],
) -> tuple[str, ...]:
    supporting_refs = {
        protein_ref
        for contribution in pathway_activity_report.member_contributions
        if contribution.pathway_id == pathway_id
        and contribution.observed
        and contribution.condition in {condition_a, condition_b}
        for protein_ref in contribution.observed_protein_refs
        if protein_ref in cards_by_ref
    }
    return tuple(sorted(supporting_refs))


def _pathway_hypothesis_opposing_evidence(
    pathway_activity_report: PathwayActivityReport,
    *,
    comparison: PathwayConditionComparisonEntry,
) -> tuple[str, ...]:
    unresolved_member_ids = {
        unresolved.member_id
        for unresolved in pathway_activity_report.unresolved_members
        if unresolved.pathway_id == comparison.pathway_id
    }
    opposing_evidence = {
        (
            "low_confidence_pathway_comparison"
            if comparison.comparison_confidence_status.value != "high"
            else ""
        ),
        *(
            f"unresolved pathway member {member_id}"
            for member_id in sorted(unresolved_member_ids)
        ),
    }
    return tuple(sorted(item for item in opposing_evidence if item))


def _regulator_hypothesis_opposing_evidence(
    regulator_inference_report: RegulatorInferenceReport,
    *,
    regulator: str,
) -> tuple[str, ...]:
    unresolved_targets = {
        entry.target_value
        for entry in regulator_inference_report.unresolved_targets
        if entry.regulator == regulator
    }
    return tuple(
        sorted(
            f"unresolved regulator target {target_value}"
            for target_value in unresolved_targets
        )
    )
