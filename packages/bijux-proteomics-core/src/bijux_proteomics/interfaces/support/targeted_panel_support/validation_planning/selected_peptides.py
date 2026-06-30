# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Selected-peptide adaptation for validation planning entrypoints."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted.validation_planning import (
    ValidationPlanningSelectedPeptideInput,
)

from ..panel_design.selected_peptides import _load_targeted_panel_selected_peptides


def _load_validation_planning_selected_peptides(
    path: Path,
) -> tuple[ValidationPlanningSelectedPeptideInput, ...]:
    return tuple(
        ValidationPlanningSelectedPeptideInput(
            target_protein_ref=entry.target_protein_ref,
            target_protein_group_id=entry.target_protein_group_id,
            gene_symbol=entry.gene_symbol,
            peptide_sequence=entry.peptide_sequence,
            canonical_peptide=entry.canonical_peptide,
            rank=entry.rank,
            observed_in_discovery=entry.observed_in_discovery,
            observed_psm_count=entry.observed_psm_count,
            run_count=entry.run_count,
            detection_frequency=entry.detection_frequency,
            replicate_consistency=entry.replicate_consistency,
            primary_evidence_class=entry.primary_evidence_class,
            uniqueness_class=entry.uniqueness_class,
            uniqueness_score=entry.uniqueness_score,
            detectability_score=entry.detectability_score,
            detectability_tier=entry.detectability_tier,
            suitability_score=entry.suitability_score,
            liability_tier=entry.liability_tier,
            liability_codes=entry.liability_codes,
        )
        for entry in _load_targeted_panel_selected_peptides(path)
    )


__all__ = ("_load_validation_planning_selected_peptides",)
