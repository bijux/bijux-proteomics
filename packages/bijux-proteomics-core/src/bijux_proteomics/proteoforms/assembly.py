# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Proteoform candidate assembly from peptide and PTM evidence constraints."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ProteoformCandidateAmbiguityClass(StrEnum):
    """Stable ambiguity outcomes for assembled proteoform candidates."""

    EXACT = "exact"
    AMBIGUOUS_SITE_SUPPORT = "ambiguous_site_support"
    INCOMPATIBLE_EVIDENCE = "incompatible_evidence"
    AMBIGUOUS_AND_INCOMPATIBLE = "ambiguous_and_incompatible"


class ProteoformPeptideEvidence(JsonModel):
    """One peptide-level proteoform constraint."""

    model_config = ConfigDict(extra="forbid")

    peptide_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    required_sites: tuple[str, ...] = Field(default_factory=tuple)
    excluded_sites: tuple[str, ...] = Field(default_factory=tuple)


class ProteoformPtmEvidence(JsonModel):
    """One PTM site assertion eligible for proteoform assembly."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    supporting_peptides: tuple[str, ...] = Field(default_factory=tuple)
    ambiguous: bool = False


class ProteoformCandidateEntry(JsonModel):
    """One assembled proteoform candidate constrained by compatible evidence."""

    model_config = ConfigDict(extra="forbid")

    proteoform_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    required_peptides: tuple[str, ...] = Field(default_factory=tuple)
    required_sites: tuple[str, ...] = Field(default_factory=tuple)
    excluded_by_evidence: tuple[str, ...] = Field(default_factory=tuple)
    ambiguity_class: ProteoformCandidateAmbiguityClass


@dataclass(frozen=True)
class _Constraint:
    label: str
    protein_id: str
    required_sites: frozenset[str]
    excluded_sites: frozenset[str]
    required_peptides: frozenset[str]
    ambiguous: bool


def assemble_proteoform_candidates(
    peptide_evidence: tuple[ProteoformPeptideEvidence, ...],
    ptm_evidence: tuple[ProteoformPtmEvidence, ...],
) -> tuple[ProteoformCandidateEntry, ...]:
    """Assemble maximal compatible proteoform candidates from peptide and PTM constraints."""

    constraints_by_protein: dict[str, list[_Constraint]] = {}
    peptide_ids: set[str] = set()
    site_ids: set[str] = set()
    for entry in peptide_evidence:
        if entry.peptide_id in peptide_ids:
            raise ValueError("proteoform assembly requires unique peptide_id rows")
        peptide_ids.add(entry.peptide_id)
        constraints_by_protein.setdefault(entry.protein_id, []).append(
            _Constraint(
                label=entry.peptide_id,
                protein_id=entry.protein_id,
                required_sites=frozenset(entry.required_sites),
                excluded_sites=frozenset(entry.excluded_sites),
                required_peptides=frozenset((entry.peptide_id,)),
                ambiguous=False,
            )
        )
    for entry in ptm_evidence:
        if entry.site_id in site_ids:
            raise ValueError("proteoform assembly requires unique site_id PTM rows")
        site_ids.add(entry.site_id)
        constraints_by_protein.setdefault(entry.protein_id, []).append(
            _Constraint(
                label=entry.site_id,
                protein_id=entry.protein_id,
                required_sites=frozenset((entry.site_id,)),
                excluded_sites=frozenset(),
                required_peptides=frozenset(entry.supporting_peptides),
                ambiguous=entry.ambiguous,
            )
        )

    assembled: list[ProteoformCandidateEntry] = []
    seen_candidate_keys: set[
        tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...], str]
    ] = set()
    for protein_id in sorted(constraints_by_protein):
        constraints = tuple(
            sorted(
                constraints_by_protein[protein_id],
                key=lambda entry: (
                    entry.label,
                    tuple(sorted(entry.required_sites)),
                    tuple(sorted(entry.excluded_sites)),
                ),
            )
        )
        maximal_subsets = _maximal_compatible_subsets(constraints)
        for subset in maximal_subsets:
            included = tuple(constraints[index] for index in subset)
            required_sites = tuple(
                sorted({site for entry in included for site in entry.required_sites})
            )
            required_peptides = tuple(
                sorted(
                    {peptide for entry in included for peptide in entry.required_peptides}
                )
            )
            excluded_by_evidence = tuple(sorted(_excluded_labels(subset, constraints)))
            ambiguity_class = _ambiguity_class(
                included=included,
                excluded_by_evidence=excluded_by_evidence,
            )
            candidate = ProteoformCandidateEntry(
                proteoform_id=_proteoform_id(
                    protein_id=protein_id,
                    required_sites=required_sites,
                    required_peptides=required_peptides,
                ),
                protein_id=protein_id,
                required_peptides=required_peptides,
                required_sites=required_sites,
                excluded_by_evidence=excluded_by_evidence,
                ambiguity_class=ambiguity_class,
            )
            key = (
                candidate.protein_id,
                candidate.required_peptides,
                candidate.required_sites,
                candidate.excluded_by_evidence,
                candidate.ambiguity_class.value,
            )
            if key in seen_candidate_keys:
                continue
            seen_candidate_keys.add(key)
            assembled.append(candidate)
    return tuple(
        sorted(
            assembled,
            key=lambda entry: (
                entry.protein_id,
                entry.proteoform_id,
            ),
        )
    )


def render_proteoform_candidate_tsv(
    entries: tuple[ProteoformCandidateEntry, ...],
) -> str:
    """Render proteoform candidates as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "proteoform_id",
            "protein_id",
            "required_peptides",
            "required_sites",
            "excluded_by_evidence",
            "ambiguity_class",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.proteoform_id,
                entry.protein_id,
                ";".join(entry.required_peptides),
                ";".join(entry.required_sites),
                ";".join(entry.excluded_by_evidence),
                entry.ambiguity_class.value,
            )
        )
    return buffer.getvalue()


def _maximal_compatible_subsets(
    constraints: tuple[_Constraint, ...],
) -> tuple[frozenset[int], ...]:
    if not constraints:
        return ()

    compatible_subsets: set[frozenset[int]] = set()

    def visit(
        index: int,
        selected: frozenset[int],
        required_sites: frozenset[str],
        excluded_sites: frozenset[str],
    ) -> None:
        if index == len(constraints):
            if selected:
                compatible_subsets.add(selected)
            return
        entry = constraints[index]
        visit(index + 1, selected, required_sites, excluded_sites)
        if entry.required_sites & excluded_sites:
            return
        if entry.excluded_sites & required_sites:
            return
        visit(
            index + 1,
            selected | frozenset((index,)),
            required_sites | entry.required_sites,
            excluded_sites | entry.excluded_sites,
        )

    visit(0, frozenset(), frozenset(), frozenset())
    return tuple(
        subset
        for subset in compatible_subsets
        if not any(subset < other for other in compatible_subsets)
    )


def _excluded_labels(
    selected: frozenset[int],
    constraints: tuple[_Constraint, ...],
) -> set[str]:
    included = tuple(constraints[index] for index in selected)
    required_sites = frozenset(
        site for entry in included for site in entry.required_sites
    )
    excluded_sites = frozenset(
        site for entry in included for site in entry.excluded_sites
    )
    excluded_labels: set[str] = set()
    for index, entry in enumerate(constraints):
        if index in selected:
            continue
        if entry.required_sites & excluded_sites or entry.excluded_sites & required_sites:
            excluded_labels.add(entry.label)
    return excluded_labels


def _ambiguity_class(
    *,
    included: tuple[_Constraint, ...],
    excluded_by_evidence: tuple[str, ...],
) -> ProteoformCandidateAmbiguityClass:
    has_ambiguous_support = any(entry.ambiguous for entry in included)
    has_incompatible_evidence = bool(excluded_by_evidence)
    if has_ambiguous_support and has_incompatible_evidence:
        return ProteoformCandidateAmbiguityClass.AMBIGUOUS_AND_INCOMPATIBLE
    if has_ambiguous_support:
        return ProteoformCandidateAmbiguityClass.AMBIGUOUS_SITE_SUPPORT
    if has_incompatible_evidence:
        return ProteoformCandidateAmbiguityClass.INCOMPATIBLE_EVIDENCE
    return ProteoformCandidateAmbiguityClass.EXACT


def _proteoform_id(
    *,
    protein_id: str,
    required_sites: tuple[str, ...],
    required_peptides: tuple[str, ...],
) -> str:
    site_token = "|".join(required_sites) if required_sites else "unmodified"
    peptide_token = "|".join(required_peptides) if required_peptides else "unspecified"
    return f"{protein_id}::sites={site_token}::peptides={peptide_token}"


__all__ = [
    "ProteoformCandidateAmbiguityClass",
    "ProteoformCandidateEntry",
    "ProteoformPeptideEvidence",
    "ProteoformPtmEvidence",
    "assemble_proteoform_candidates",
    "render_proteoform_candidate_tsv",
]
