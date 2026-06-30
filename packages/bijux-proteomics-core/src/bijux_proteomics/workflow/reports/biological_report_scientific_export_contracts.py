# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contracts for scientific artifact exports in biological reports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BiologicalScientificExportNames:
    """Artifact names emitted for core scientific report outputs."""

    summary_name: str
    differential_name: str
    protein_card_summary_name: str
    protein_card_name: str
    protein_mechanism_card_summary_name: str
    protein_mechanism_card_name: str
    evidence_graph_nodes_name: str
    evidence_graph_edges_name: str
    experiment_confidence_summary_name: str
    experiment_confidence_components_name: str
    section_confidence_name: str
    evidence_aware_ranking_name: str | None
    claim_validation_summary_name: str | None
    supported_claim_name: str | None
    rejected_claim_name: str | None
    biological_hypothesis_summary_name: str | None
    biological_hypothesis_name: str | None
    rejected_hypothesis_candidate_name: str | None
    foreground_background_summary_name: str
    foreground_background_entry_name: str
    foreground_background_issue_name: str
    regulator_inference_summary_name: str | None
    regulator_inference_name: str | None
    regulator_unresolved_name: str | None
    regulator_rejected_name: str | None
    annotation_summary_name: str
    annotation_name: str
    annotation_unmapped_name: str


__all__ = ["BiologicalScientificExportNames"]
