# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Assay-target matching support for biomarker stability analysis."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.result_import import TargetedResultImportReport
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationPanelAssayInput,
)


@dataclass(frozen=True)
class _ImportedTargetDescriptor:
    target_id: str
    peptide_sequence: str
    precursor_charge: int | None
    protein_refs: tuple[str, ...]


def _build_imported_target_descriptors(
    import_report: TargetedResultImportReport,
) -> tuple[_ImportedTargetDescriptor, ...]:
    grouped: dict[str, list[tuple[str, int | None, str | None]]] = {}
    for observation in import_report.observations:
        grouped.setdefault(observation.precursor_id, []).append(
            (
                observation.peptide_sequence,
                observation.precursor_charge,
                observation.protein_ref,
            )
        )
    descriptors: list[_ImportedTargetDescriptor] = []
    for target_id, rows in sorted(grouped.items()):
        peptide_sequence = rows[0][0]
        precursor_charge = rows[0][1]
        protein_refs = tuple(sorted({row[2] for row in rows if row[2]}))
        descriptors.append(
            _ImportedTargetDescriptor(
                target_id=target_id,
                peptide_sequence=peptide_sequence,
                precursor_charge=precursor_charge,
                protein_refs=protein_refs,
            )
        )
    return tuple(descriptors)


def _match_assay_target_ids(
    assay: TargetedValidationPanelAssayInput,
    descriptors: tuple[_ImportedTargetDescriptor, ...],
) -> tuple[str, ...]:
    peptide_matches = [
        descriptor
        for descriptor in descriptors
        if descriptor.peptide_sequence == assay.canonical_peptide
        and descriptor.precursor_charge == assay.precursor_charge
    ]
    if not peptide_matches:
        return ()
    protein_matches = [
        descriptor
        for descriptor in peptide_matches
        if assay.target_protein_ref in descriptor.protein_refs
    ]
    if protein_matches:
        return tuple(sorted(descriptor.target_id for descriptor in protein_matches))
    if assay.uniqueness_class is PeptideUniquenessClass.UNIQUE:
        return ()
    return tuple(sorted(descriptor.target_id for descriptor in peptide_matches))


def _compute_assay_agreement_score(
    assay_values_by_sample: dict[str, dict[str, float]],
    *,
    disagreement_delta_threshold: float,
) -> float:
    spreads = [
        max(values.values()) - min(values.values())
        for values in assay_values_by_sample.values()
        if len(values) >= 2
    ]
    if not spreads:
        return 1.0 if assay_values_by_sample else 0.0
    return max(0.0, min(1.0, 1.0 - (mean(spreads) / disagreement_delta_threshold)))


__all__ = [
    "_ImportedTargetDescriptor",
    "_build_imported_target_descriptors",
    "_compute_assay_agreement_score",
    "_match_assay_target_ids",
]
