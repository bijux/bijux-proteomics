# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-study protein harmonization over owned study-result surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation.ortholog_mapping import OrthologRecord
from bijux_proteomics.ptm.cards.evidence_cards import PtmEvidenceCard
from bijux_proteomics.sequences.fasta import canonicalize_protein_reference
from bijux_proteomics.workflow.studies.study_result import (
    ProteomicsStudyKind,
    ProteomicsStudyResult,
)
from bijux_proteomics_foundation import JsonModel


class CrossStudyProteinObservationSourceKind(StrEnum):
    """Durable study-surface kinds that can contribute protein identities."""

    PROTEIN_EVIDENCE_CARD = "protein_evidence_card"
    LABEL_BASED_DIFFERENTIAL_ROW = "label_based_differential_row"
    PTM_PARENT_PROTEIN = "ptm_parent_protein"


class CrossStudyProteinMatchBasis(StrEnum):
    """Stable reasons that a harmonized protein group was considered linkable."""

    EXACT_ACCESSION = "exact_accession"
    UNIQUE_ORTHOLOG = "unique_ortholog"
    EXACT_ACCESSION_AND_UNIQUE_ORTHOLOG = "exact_accession_and_unique_ortholog"


class CrossStudyProteinUnresolvedReason(StrEnum):
    """Stable unresolved reasons preserved on cross-study protein identities."""

    NO_CROSS_STUDY_MATCH = "no_cross_study_match"
    GENE_SYMBOL_ONLY_MATCH = "gene_symbol_only_match"
    AMBIGUOUS_ORTHOLOG_MAPPING = "ambiguous_ortholog_mapping"


class CrossStudyProteinStudyInput(JsonModel):
    """One study-level input packet for protein harmonization."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    study_result: ProteomicsStudyResult
    study_label: str | None = None
    species: str | None = None


class CrossStudyProteinObservation(JsonModel):
    """One protein identity observation extracted from one study result."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    species: str | None = None
    source_kind: CrossStudyProteinObservationSourceKind
    source_surface: str = Field(..., min_length=1)
    source_entity_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    accession_aliases: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbol: str | None = None
    note: str = Field(..., min_length=1)


class _GroupMetadata(TypedDict):
    group_id: int
    member_indices: tuple[int, ...]
    tokens: set[str]
    normalized_gene_symbols: set[str]
    normalized_species: set[str]


class UnsupportedCrossStudyProteinStudy(JsonModel):
    """One study input that could not yield any protein-harmonization observations."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    reason: str = Field(..., min_length=1)


class CrossStudyProteinExtractionSummary(JsonModel):
    """Summary over protein observations extracted from study results."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    supported_study_count: int = Field(..., ge=0)
    unsupported_study_count: int = Field(..., ge=0)
    observation_count: int = Field(..., ge=0)
    protein_card_observation_count: int = Field(..., ge=0)
    label_based_observation_count: int = Field(..., ge=0)
    ptm_parent_protein_count: int = Field(..., ge=0)


class CrossStudyProteinExtractionReport(JsonModel):
    """Owned extraction report over cross-study protein observations."""

    model_config = ConfigDict(extra="forbid")

    observations: tuple[CrossStudyProteinObservation, ...] = Field(
        default_factory=tuple
    )
    unsupported_studies: tuple[UnsupportedCrossStudyProteinStudy, ...] = Field(
        default_factory=tuple
    )
    summary: CrossStudyProteinExtractionSummary
    note: str = Field(..., min_length=1)


class CrossStudyProteinHarmonizedEntry(JsonModel):
    """One study membership inside one harmonized cross-study protein group."""

    model_config = ConfigDict(extra="forbid")

    harmonized_id: str = Field(..., min_length=1)
    observation_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    species: str | None = None
    source_kind: CrossStudyProteinObservationSourceKind
    source_surface: str = Field(..., min_length=1)
    source_entity_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    accession_aliases: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbol: str | None = None
    match_basis: CrossStudyProteinMatchBasis
    harmonized_study_count: int = Field(..., ge=2)
    note: str = Field(..., min_length=1)


class CrossStudyProteinUnresolvedEntry(JsonModel):
    """One protein observation that could not be harmonized honestly."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    species: str | None = None
    source_kind: CrossStudyProteinObservationSourceKind
    source_surface: str = Field(..., min_length=1)
    source_entity_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    accession_aliases: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbol: str | None = None
    reason: CrossStudyProteinUnresolvedReason
    candidate_observation_ids: tuple[str, ...] = Field(default_factory=tuple)
    candidate_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class CrossStudyProteinHarmonizationSummary(JsonModel):
    """Summary over one cross-study protein harmonization pass."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    supported_study_count: int = Field(..., ge=0)
    unsupported_study_count: int = Field(..., ge=0)
    observation_count: int = Field(..., ge=0)
    harmonized_group_count: int = Field(..., ge=0)
    harmonized_membership_count: int = Field(..., ge=0)
    unresolved_entry_count: int = Field(..., ge=0)
    exact_accession_group_count: int = Field(..., ge=0)
    ortholog_linked_group_count: int = Field(..., ge=0)
    ambiguous_ortholog_entry_count: int = Field(..., ge=0)
    gene_symbol_only_unresolved_count: int = Field(..., ge=0)


class CrossStudyProteinHarmonizationReport(JsonModel):
    """Owned report over protein identity harmonization across study results."""

    model_config = ConfigDict(extra="forbid")

    extracted_observations: tuple[CrossStudyProteinObservation, ...] = Field(
        default_factory=tuple
    )
    unsupported_studies: tuple[UnsupportedCrossStudyProteinStudy, ...] = Field(
        default_factory=tuple
    )
    harmonized_entries: tuple[CrossStudyProteinHarmonizedEntry, ...] = Field(
        default_factory=tuple
    )
    unresolved_entries: tuple[CrossStudyProteinUnresolvedEntry, ...] = Field(
        default_factory=tuple
    )
    summary: CrossStudyProteinHarmonizationSummary
    note: str = Field(..., min_length=1)


def extract_cross_study_protein_observations(
    studies: tuple[CrossStudyProteinStudyInput, ...],
) -> CrossStudyProteinExtractionReport:
    """Extract study-comparable protein identities from owned study-result surfaces."""

    observations: list[CrossStudyProteinObservation] = []
    unsupported: list[UnsupportedCrossStudyProteinStudy] = []
    for study in studies:
        extracted = _extract_study_observations(study)
        if extracted:
            observations.extend(extracted)
            continue
        unsupported.append(
            UnsupportedCrossStudyProteinStudy(
                study_id=study.study_id,
                study_label=study.study_label,
                study_kind=study.study_result.study_kind,
                reason=(
                    "study result does not expose a governed protein identity surface "
                    "that can participate in cross-study harmonization"
                ),
            )
        )

    summary = CrossStudyProteinExtractionSummary(
        input_study_count=len(studies),
        supported_study_count=len({entry.study_id for entry in observations}),
        unsupported_study_count=len(unsupported),
        observation_count=len(observations),
        protein_card_observation_count=sum(
            entry.source_kind
            is CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD
            for entry in observations
        ),
        label_based_observation_count=sum(
            entry.source_kind
            is CrossStudyProteinObservationSourceKind.LABEL_BASED_DIFFERENTIAL_ROW
            for entry in observations
        ),
        ptm_parent_protein_count=sum(
            entry.source_kind
            is CrossStudyProteinObservationSourceKind.PTM_PARENT_PROTEIN
            for entry in observations
        ),
    )
    return CrossStudyProteinExtractionReport(
        observations=tuple(observations),
        unsupported_studies=tuple(unsupported),
        summary=summary,
        note=(
            "cross-study protein extraction preserves protein evidence cards, labeled "
            "protein differential rows, and PTM parent-protein identities on one "
            "comparable observation surface"
        ),
    )


def build_cross_study_protein_harmonization_report(
    studies: tuple[CrossStudyProteinStudyInput, ...],
    *,
    ortholog_records: tuple[OrthologRecord, ...] = (),
) -> CrossStudyProteinHarmonizationReport:
    """Harmonize protein identities across study-result surfaces without guessing."""

    extraction = extract_cross_study_protein_observations(studies)
    return build_cross_study_protein_harmonization_report_from_observations(
        extraction.observations,
        ortholog_records=ortholog_records,
        unsupported_studies=extraction.unsupported_studies,
        input_study_count=extraction.summary.input_study_count,
    )


def build_cross_study_protein_harmonization_report_from_observations(
    observations: tuple[CrossStudyProteinObservation, ...],
    *,
    ortholog_records: tuple[OrthologRecord, ...] = (),
    unsupported_studies: tuple[UnsupportedCrossStudyProteinStudy, ...] = (),
    input_study_count: int | None = None,
) -> CrossStudyProteinHarmonizationReport:
    """Harmonize extracted cross-study protein observations."""

    if not observations:
        return CrossStudyProteinHarmonizationReport(
            extracted_observations=(),
            unsupported_studies=unsupported_studies,
            harmonized_entries=(),
            unresolved_entries=(),
            summary=CrossStudyProteinHarmonizationSummary(
                input_study_count=0 if input_study_count is None else input_study_count,
                supported_study_count=0,
                unsupported_study_count=len(unsupported_studies),
                observation_count=0,
                harmonized_group_count=0,
                harmonized_membership_count=0,
                unresolved_entry_count=0,
                exact_accession_group_count=0,
                ortholog_linked_group_count=0,
                ambiguous_ortholog_entry_count=0,
                gene_symbol_only_unresolved_count=0,
            ),
            note=(
                "cross-study protein harmonization did not receive any supported "
                "protein observations"
            ),
        )

    exact_group_members, observation_group_ids = _build_exact_accession_groups(
        observations
    )
    group_metadata = {
        group_id: _build_group_metadata(group_id, member_indices, observations)
        for group_id, member_indices in exact_group_members.items()
    }
    ortholog_resolution = _resolve_unique_ortholog_links(
        group_metadata=group_metadata,
        ortholog_records=ortholog_records,
    )
    component_group_ids = _build_harmonized_components(
        exact_group_members=exact_group_members,
        ortholog_links=ortholog_resolution.unique_links,
    )
    group_component_ids = {
        group_id: component_id
        for component_id, group_ids in component_group_ids.items()
        for group_id in group_ids
    }
    harmonized_component_ids = {
        component_id
        for component_id, group_ids in component_group_ids.items()
        if len(
            {
                observations[index].study_id
                for group_id in group_ids
                for index in exact_group_members[group_id]
            }
        )
        >= 2
    }
    group_gene_candidates = _build_gene_symbol_candidates(
        group_metadata=group_metadata,
        harmonized_component_ids=harmonized_component_ids,
        group_component_ids=group_component_ids,
    )

    harmonized_entries: list[CrossStudyProteinHarmonizedEntry] = []
    unresolved_entries: list[CrossStudyProteinUnresolvedEntry] = []
    exact_accession_group_count = 0
    ortholog_linked_group_count = 0

    for component_index, component_id in enumerate(
        sorted(
            harmonized_component_ids,
            key=lambda item: _component_sort_key(
                component_group_ids[item],
                exact_group_members=exact_group_members,
                observations=observations,
            ),
        ),
        start=1,
    ):
        group_ids = component_group_ids[component_id]
        component_observation_indices = tuple(
            index
            for group_id in sorted(group_ids)
            for index in exact_group_members[group_id]
        )
        exact_only = len(group_ids) == 1
        has_ortholog = any(
            tuple(sorted((left_group_id, right_group_id)))
            in ortholog_resolution.unique_links
            for left_group_id in group_ids
            for right_group_id in group_ids
            if left_group_id < right_group_id
        )
        if exact_only:
            exact_accession_group_count += 1
            match_basis = CrossStudyProteinMatchBasis.EXACT_ACCESSION
            note = (
                "study observations share exact canonical protein accessions or aliases"
            )
        elif has_ortholog and any(
            len(exact_group_members[group_id]) > 1 for group_id in group_ids
        ):
            ortholog_linked_group_count += 1
            match_basis = (
                CrossStudyProteinMatchBasis.EXACT_ACCESSION_AND_UNIQUE_ORTHOLOG
            )
            note = (
                "study observations were linked through exact accession overlap within "
                "species and unique ortholog support across species"
            )
        else:
            ortholog_linked_group_count += 1
            match_basis = CrossStudyProteinMatchBasis.UNIQUE_ORTHOLOG
            note = (
                "study observations were linked only through unique one-to-one "
                "ortholog support across species"
            )
        harmonized_id = f"harmonized_protein_{component_index:03d}"
        harmonized_study_count = len(
            {observations[index].study_id for index in component_observation_indices}
        )
        for observation_index in sorted(
            component_observation_indices,
            key=lambda item: _observation_sort_key(observations[item]),
        ):
            observation = observations[observation_index]
            harmonized_entries.append(
                CrossStudyProteinHarmonizedEntry(
                    harmonized_id=harmonized_id,
                    observation_id=observation.observation_id,
                    study_id=observation.study_id,
                    study_label=observation.study_label,
                    study_kind=observation.study_kind,
                    species=observation.species,
                    source_kind=observation.source_kind,
                    source_surface=observation.source_surface,
                    source_entity_id=observation.source_entity_id,
                    representative_protein_ref=observation.representative_protein_ref,
                    protein_refs=observation.protein_refs,
                    accession_aliases=observation.accession_aliases,
                    gene_symbol=observation.gene_symbol,
                    match_basis=match_basis,
                    harmonized_study_count=harmonized_study_count,
                    note=note,
                )
            )

    harmonized_observation_ids = {entry.observation_id for entry in harmonized_entries}
    for group_id, member_indices in sorted(
        exact_group_members.items(),
        key=lambda item: _component_sort_key(
            {item[0]},
            exact_group_members=exact_group_members,
            observations=observations,
        ),
    ):
        if group_component_ids[group_id] in harmonized_component_ids:
            continue
        ambiguous_ortholog_candidates = ortholog_resolution.ambiguous_candidates.get(
            group_id, ()
        )
        gene_symbol_candidates = tuple(
            candidate_group_id
            for candidate_group_id in group_gene_candidates.get(group_id, ())
            if candidate_group_id != group_id
        )
        if ambiguous_ortholog_candidates:
            candidate_indices = _group_candidate_indices(
                ambiguous_ortholog_candidates,
                exact_group_members=exact_group_members,
            )
            reason = CrossStudyProteinUnresolvedReason.AMBIGUOUS_ORTHOLOG_MAPPING
            note = (
                "explicit ortholog records linked this protein observation to more than "
                "one cross-study candidate, so the mapping remains unresolved"
            )
        elif gene_symbol_candidates:
            candidate_indices = _group_candidate_indices(
                gene_symbol_candidates,
                exact_group_members=exact_group_members,
            )
            reason = CrossStudyProteinUnresolvedReason.GENE_SYMBOL_ONLY_MATCH
            note = (
                "cross-study candidates shared a gene symbol but did not share exact "
                "protein accessions or a unique ortholog relationship"
            )
        else:
            candidate_indices = ()
            reason = CrossStudyProteinUnresolvedReason.NO_CROSS_STUDY_MATCH
            note = (
                "no exact accession overlap or unique ortholog support linked this "
                "protein observation to another study"
            )
        candidate_observation_ids = tuple(
            sorted(
                {
                    observations[index].observation_id
                    for index in candidate_indices
                    if observations[index].observation_id
                    not in harmonized_observation_ids
                }
            )
        )
        candidate_study_ids = tuple(
            sorted(
                {
                    observations[index].study_id
                    for index in candidate_indices
                    if observations[index].observation_id
                    not in harmonized_observation_ids
                }
            )
        )
        for observation_index in sorted(
            member_indices,
            key=lambda item: _observation_sort_key(observations[item]),
        ):
            observation = observations[observation_index]
            unresolved_entries.append(
                CrossStudyProteinUnresolvedEntry(
                    observation_id=observation.observation_id,
                    study_id=observation.study_id,
                    study_label=observation.study_label,
                    study_kind=observation.study_kind,
                    species=observation.species,
                    source_kind=observation.source_kind,
                    source_surface=observation.source_surface,
                    source_entity_id=observation.source_entity_id,
                    representative_protein_ref=observation.representative_protein_ref,
                    protein_refs=observation.protein_refs,
                    accession_aliases=observation.accession_aliases,
                    gene_symbol=observation.gene_symbol,
                    reason=reason,
                    candidate_observation_ids=candidate_observation_ids,
                    candidate_study_ids=candidate_study_ids,
                    note=note,
                )
            )

    summary = CrossStudyProteinHarmonizationSummary(
        input_study_count=(
            len({entry.study_id for entry in observations}) + len(unsupported_studies)
            if input_study_count is None
            else input_study_count
        ),
        supported_study_count=len({entry.study_id for entry in observations}),
        unsupported_study_count=len(unsupported_studies),
        observation_count=len(observations),
        harmonized_group_count=len(
            {entry.harmonized_id for entry in harmonized_entries}
        ),
        harmonized_membership_count=len(harmonized_entries),
        unresolved_entry_count=len(unresolved_entries),
        exact_accession_group_count=exact_accession_group_count,
        ortholog_linked_group_count=ortholog_linked_group_count,
        ambiguous_ortholog_entry_count=sum(
            entry.reason is CrossStudyProteinUnresolvedReason.AMBIGUOUS_ORTHOLOG_MAPPING
            for entry in unresolved_entries
        ),
        gene_symbol_only_unresolved_count=sum(
            entry.reason is CrossStudyProteinUnresolvedReason.GENE_SYMBOL_ONLY_MATCH
            for entry in unresolved_entries
        ),
    )
    return CrossStudyProteinHarmonizationReport(
        extracted_observations=observations,
        unsupported_studies=unsupported_studies,
        harmonized_entries=tuple(harmonized_entries),
        unresolved_entries=tuple(unresolved_entries),
        summary=summary,
        note=(
            "cross-study protein harmonization links study observations only through "
            "exact accession overlap or unique ortholog support, while preserving "
            "gene-symbol-only and one-to-many mappings as unresolved"
        ),
    )


def render_cross_study_protein_harmonization_tsv(
    report: CrossStudyProteinHarmonizationReport,
) -> str:
    """Render harmonized cross-study protein memberships as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "harmonized_id",
            "observation_id",
            "study_id",
            "study_label",
            "study_kind",
            "species",
            "source_kind",
            "source_surface",
            "source_entity_id",
            "representative_protein_ref",
            "protein_refs",
            "accession_aliases",
            "gene_symbol",
            "match_basis",
            "harmonized_study_count",
            "note",
        ]
    )
    for entry in report.harmonized_entries:
        writer.writerow(
            [
                entry.harmonized_id,
                entry.observation_id,
                entry.study_id,
                "" if entry.study_label is None else entry.study_label,
                entry.study_kind.value,
                "" if entry.species is None else entry.species,
                entry.source_kind.value,
                entry.source_surface,
                entry.source_entity_id,
                entry.representative_protein_ref,
                ";".join(entry.protein_refs),
                ";".join(entry.accession_aliases),
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.match_basis.value,
                entry.harmonized_study_count,
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_protein_unresolved_tsv(
    report: CrossStudyProteinHarmonizationReport,
) -> str:
    """Render unresolved cross-study protein identities as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "observation_id",
            "study_id",
            "study_label",
            "study_kind",
            "species",
            "source_kind",
            "source_surface",
            "source_entity_id",
            "representative_protein_ref",
            "protein_refs",
            "accession_aliases",
            "gene_symbol",
            "reason",
            "candidate_observation_ids",
            "candidate_study_ids",
            "note",
        ]
    )
    for entry in report.unresolved_entries:
        writer.writerow(
            [
                entry.observation_id,
                entry.study_id,
                "" if entry.study_label is None else entry.study_label,
                entry.study_kind.value,
                "" if entry.species is None else entry.species,
                entry.source_kind.value,
                entry.source_surface,
                entry.source_entity_id,
                entry.representative_protein_ref,
                ";".join(entry.protein_refs),
                ";".join(entry.accession_aliases),
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.reason.value,
                ";".join(entry.candidate_observation_ids),
                ";".join(entry.candidate_study_ids),
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_cross_study_protein_harmonization_tsv(
    report: CrossStudyProteinHarmonizationReport,
    path: Path,
) -> None:
    """Write harmonized cross-study protein memberships to a TSV artifact."""

    write_output_table_tsv(path, render_cross_study_protein_harmonization_tsv(report))


def export_cross_study_protein_unresolved_tsv(
    report: CrossStudyProteinHarmonizationReport,
    path: Path,
) -> None:
    """Write unresolved cross-study protein identities to a TSV artifact."""

    write_output_table_tsv(path, render_cross_study_protein_unresolved_tsv(report))


def _extract_study_observations(
    study: CrossStudyProteinStudyInput,
) -> tuple[CrossStudyProteinObservation, ...]:
    if study.study_result.biological_report is not None:
        return _extract_biological_report_observations(study)
    if study.study_result.label_based_report is not None:
        return _extract_label_based_observations(study)
    if (
        study.study_result.ptm_report is not None
        and study.study_result.ptm_report.evidence_cards is not None
    ):
        return _extract_ptm_parent_protein_observations(study)
    return ()


def _extract_biological_report_observations(
    study: CrossStudyProteinStudyInput,
) -> tuple[CrossStudyProteinObservation, ...]:
    report = study.study_result.biological_report
    if report is None:
        raise RuntimeError(
            "cross-study harmonization requires a biological report for biological observations"
        )
    observations: list[CrossStudyProteinObservation] = []
    for card in report.protein_cards.cards:
        protein_refs = _sorted_nonempty(
            (
                card.representative_protein_ref,
                *card.protein_refs,
            )
        )
        accession_aliases = _sorted_nonempty(card.annotation.accession_aliases)
        observation_id = f"{study.study_id}:{card.card_id}"
        observations.append(
            CrossStudyProteinObservation(
                observation_id=observation_id,
                study_id=study.study_id,
                study_label=study.study_label,
                study_kind=study.study_result.study_kind,
                species=study.species or card.annotation.organism,
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id=card.card_id,
                representative_protein_ref=card.representative_protein_ref,
                protein_refs=protein_refs,
                accession_aliases=accession_aliases,
                gene_symbol=card.annotation.gene_symbol,
                note=(
                    "protein evidence card preserves representative protein reference, "
                    "protein refs, accession aliases, and annotation context"
                ),
            )
        )
    return tuple(observations)


def _extract_label_based_observations(
    study: CrossStudyProteinStudyInput,
) -> tuple[CrossStudyProteinObservation, ...]:
    report = study.study_result.label_based_report
    if report is None:
        raise RuntimeError(
            "cross-study harmonization requires a label-based report for label-based observations"
        )
    observations: list[CrossStudyProteinObservation] = []
    for row in report.differential_analysis_report.normalized_matrix.rows:
        protein_refs = _sorted_nonempty(row.protein_refs)
        representative_protein_ref = protein_refs[0] if protein_refs else row.entity_id
        observation_id = f"{study.study_id}:{row.entity_id}"
        observations.append(
            CrossStudyProteinObservation(
                observation_id=observation_id,
                study_id=study.study_id,
                study_label=study.study_label,
                study_kind=study.study_result.study_kind,
                species=study.species,
                source_kind=(
                    CrossStudyProteinObservationSourceKind.LABEL_BASED_DIFFERENTIAL_ROW
                ),
                source_surface="label_based_normalized_matrix",
                source_entity_id=row.entity_id,
                representative_protein_ref=representative_protein_ref,
                protein_refs=protein_refs,
                accession_aliases=(),
                gene_symbol=None,
                note=(
                    "label-based differential rows preserve protein references but do "
                    "not claim gene-symbol identity without an external annotation surface"
                ),
            )
        )
    return tuple(observations)


def _extract_ptm_parent_protein_observations(
    study: CrossStudyProteinStudyInput,
) -> tuple[CrossStudyProteinObservation, ...]:
    report = study.study_result.ptm_report
    if report is None:
        raise RuntimeError(
            "cross-study harmonization requires a PTM report for PTM parent-protein observations"
        )
    evidence_cards = report.evidence_cards
    if evidence_cards is None:
        raise RuntimeError(
            "cross-study harmonization requires PTM evidence cards when a PTM report is present"
        )
    grouped_cards: dict[str, list[PtmEvidenceCard]] = {}
    for card in evidence_cards.cards:
        grouped_cards.setdefault(card.protein_ref, []).append(card)

    observations: list[CrossStudyProteinObservation] = []
    for protein_ref, cards in sorted(grouped_cards.items()):
        protein_refs = _sorted_nonempty(
            (
                protein_ref,
                *(
                    observed_ref
                    for card in cards
                    for observation in card.peptide_evidence
                    for observed_ref in observation.protein_refs
                ),
            )
        )
        observation_id = f"{study.study_id}:ptm-parent:{protein_ref}"
        observations.append(
            CrossStudyProteinObservation(
                observation_id=observation_id,
                study_id=study.study_id,
                study_label=study.study_label,
                study_kind=study.study_result.study_kind,
                species=study.species,
                source_kind=CrossStudyProteinObservationSourceKind.PTM_PARENT_PROTEIN,
                source_surface="ptm_evidence_cards",
                source_entity_id=f"ptm-parent:{protein_ref}",
                representative_protein_ref=protein_ref,
                protein_refs=protein_refs,
                accession_aliases=(),
                gene_symbol=None,
                note=(
                    "ptm evidence cards were aggregated onto one parent-protein "
                    "observation so protein-level cross-study harmonization remains explicit"
                ),
            )
        )
    return tuple(observations)


def _build_exact_accession_groups(
    observations: tuple[CrossStudyProteinObservation, ...],
) -> tuple[dict[int, tuple[int, ...]], dict[int, int]]:
    parents = list(range(len(observations)))
    token_to_indices: dict[str, list[int]] = {}
    for index, observation in enumerate(observations):
        for token in _identity_tokens(observation):
            token_to_indices.setdefault(token, []).append(index)
    for indices in token_to_indices.values():
        anchor = indices[0]
        for index in indices[1:]:
            _union(parents, anchor, index)

    grouped_members: dict[int, list[int]] = {}
    for index in range(len(observations)):
        grouped_members.setdefault(_find(parents, index), []).append(index)
    group_members = {
        group_id: tuple(sorted(member_indices))
        for group_id, member_indices in sorted(grouped_members.items())
    }
    observation_group_ids = {
        index: group_id
        for group_id, indices in group_members.items()
        for index in indices
    }
    return group_members, observation_group_ids


def _build_group_metadata(
    group_id: int,
    member_indices: tuple[int, ...],
    observations: tuple[CrossStudyProteinObservation, ...],
) -> _GroupMetadata:
    tokens = {
        token
        for index in member_indices
        for token in _identity_tokens(observations[index])
    }
    normalized_gene_symbols = {
        normalized
        for index in member_indices
        if (normalized := _normalize_gene_symbol(observations[index].gene_symbol))
        is not None
    }
    normalized_species = {
        normalized
        for index in member_indices
        if (normalized := _normalize_species(observations[index].species)) is not None
    }
    return {
        "group_id": group_id,
        "member_indices": member_indices,
        "tokens": tokens,
        "normalized_gene_symbols": normalized_gene_symbols,
        "normalized_species": normalized_species,
    }


class _OrthologResolution(JsonModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    unique_links: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    ambiguous_candidates: dict[int, tuple[int, ...]] = Field(default_factory=dict)


def _resolve_unique_ortholog_links(
    *,
    group_metadata: dict[int, _GroupMetadata],
    ortholog_records: tuple[OrthologRecord, ...],
) -> _OrthologResolution:
    if not ortholog_records:
        return _OrthologResolution(unique_links=(), ambiguous_candidates={})

    source_pair_matches: dict[tuple[int, str], set[int]] = {}
    target_pair_matches: dict[tuple[int, str], set[int]] = {}
    for record in ortholog_records:
        source_species = _normalize_species(record.source_species)
        target_species = _normalize_species(record.target_species)
        if source_species is None or target_species is None:
            continue
        source_ref = _canonical_token(record.source_protein_ref)
        target_ref = _canonical_token(record.target_protein_ref)
        if source_ref is None or target_ref is None:
            continue

        source_group_ids = tuple(
            group_id
            for group_id, metadata in group_metadata.items()
            if source_ref in metadata["tokens"]
            and source_species in metadata["normalized_species"]
        )
        target_group_ids = tuple(
            group_id
            for group_id, metadata in group_metadata.items()
            if target_ref in metadata["tokens"]
            and target_species in metadata["normalized_species"]
        )
        if not source_group_ids or not target_group_ids:
            continue
        for source_group_id in source_group_ids:
            source_pair_matches.setdefault(
                (source_group_id, target_species), set()
            ).update(target_group_ids)
        for target_group_id in target_group_ids:
            target_pair_matches.setdefault(
                (target_group_id, source_species), set()
            ).update(source_group_ids)

    unique_links: set[tuple[int, int]] = set()
    ambiguous_candidates: dict[int, set[int]] = {}
    for (
        source_group_id,
        _target_species,
    ), target_group_id_set in source_pair_matches.items():
        for target_group_id in target_group_id_set:
            source_species_candidates = group_metadata[source_group_id][
                "normalized_species"
            ]
            if not source_species_candidates:
                continue
            source_species = sorted(source_species_candidates)[0]
            reverse_sources = target_pair_matches.get(
                (target_group_id, source_species), set()
            )
            if len(target_group_id_set) == 1 and len(reverse_sources) == 1:
                ordered_link = (
                    (source_group_id, target_group_id)
                    if source_group_id <= target_group_id
                    else (target_group_id, source_group_id)
                )
                unique_links.add(ordered_link)
                continue
            ambiguous_candidates.setdefault(source_group_id, set()).add(target_group_id)
            ambiguous_candidates.setdefault(target_group_id, set()).add(source_group_id)

    return _OrthologResolution(
        unique_links=tuple(sorted(unique_links)),
        ambiguous_candidates={
            group_id: tuple(sorted(candidate_group_ids))
            for group_id, candidate_group_ids in sorted(ambiguous_candidates.items())
        },
    )


def _build_harmonized_components(
    *,
    exact_group_members: dict[int, tuple[int, ...]],
    ortholog_links: tuple[tuple[int, int], ...],
) -> dict[int, set[int]]:
    group_ids = tuple(sorted(exact_group_members))
    group_index = {group_id: index for index, group_id in enumerate(group_ids)}
    parents = list(range(len(group_ids)))
    for left_group_id, right_group_id in ortholog_links:
        _union(parents, group_index[left_group_id], group_index[right_group_id])
    components: dict[int, set[int]] = {}
    for group_id in group_ids:
        root = _find(parents, group_index[group_id])
        components.setdefault(root, set()).add(group_id)
    return components


def _build_gene_symbol_candidates(
    *,
    group_metadata: dict[int, _GroupMetadata],
    harmonized_component_ids: set[int],
    group_component_ids: dict[int, int],
) -> dict[int, tuple[int, ...]]:
    symbol_to_groups: dict[str, set[int]] = {}
    for group_id, metadata in group_metadata.items():
        for symbol in metadata["normalized_gene_symbols"]:
            symbol_to_groups.setdefault(symbol, set()).add(group_id)

    candidates: dict[int, set[int]] = {}
    for group_ids in symbol_to_groups.values():
        if len(group_ids) < 2:
            continue
        for group_id in group_ids:
            if group_component_ids[group_id] in harmonized_component_ids:
                continue
            candidates.setdefault(group_id, set()).update(group_ids - {group_id})
    return {
        group_id: tuple(sorted(candidate_group_ids))
        for group_id, candidate_group_ids in sorted(candidates.items())
    }


def _component_sort_key(
    group_ids: set[int],
    *,
    exact_group_members: dict[int, tuple[int, ...]],
    observations: tuple[CrossStudyProteinObservation, ...],
) -> tuple[str, ...]:
    first_observation = observations[
        min(index for group_id in group_ids for index in exact_group_members[group_id])
    ]
    return (
        first_observation.study_id,
        first_observation.representative_protein_ref,
        first_observation.source_entity_id,
    )


def _observation_sort_key(
    observation: CrossStudyProteinObservation,
) -> tuple[str, str, str]:
    return (
        observation.study_id,
        observation.representative_protein_ref,
        observation.source_entity_id,
    )


def _group_candidate_indices(
    candidate_group_ids: tuple[int, ...],
    *,
    exact_group_members: dict[int, tuple[int, ...]],
) -> tuple[int, ...]:
    return tuple(
        sorted(
            index
            for group_id in candidate_group_ids
            for index in exact_group_members[group_id]
        )
    )


def _identity_tokens(observation: CrossStudyProteinObservation) -> tuple[str, ...]:
    tokens: set[str] = set()
    for raw_token in (
        observation.representative_protein_ref,
        *observation.protein_refs,
        *observation.accession_aliases,
    ):
        canonical_token = _canonical_token(raw_token)
        if canonical_token is not None:
            tokens.add(canonical_token)
    return tuple(sorted(tokens))


def _canonical_token(value: str | None) -> str | None:
    if value is None:
        return None
    token = value.strip()
    if not token:
        return None
    return canonicalize_protein_reference(token)


def _normalize_species(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _normalize_gene_symbol(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized or None


def _sorted_nonempty(
    values: tuple[str, ...] | list[str] | tuple[object, ...],
) -> tuple[str, ...]:
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


def _find(parents: list[int], index: int) -> int:
    while parents[index] != index:
        parents[index] = parents[parents[index]]
        index = parents[index]
    return index


def _union(parents: list[int], left: int, right: int) -> None:
    left_root = _find(parents, left)
    right_root = _find(parents, right)
    if left_root != right_root:
        parents[right_root] = left_root


__all__ = [
    "CrossStudyProteinExtractionReport",
    "CrossStudyProteinExtractionSummary",
    "CrossStudyProteinHarmonizationReport",
    "CrossStudyProteinHarmonizationSummary",
    "CrossStudyProteinHarmonizedEntry",
    "CrossStudyProteinMatchBasis",
    "CrossStudyProteinObservation",
    "CrossStudyProteinObservationSourceKind",
    "CrossStudyProteinStudyInput",
    "CrossStudyProteinUnresolvedEntry",
    "CrossStudyProteinUnresolvedReason",
    "UnsupportedCrossStudyProteinStudy",
    "build_cross_study_protein_harmonization_report",
    "build_cross_study_protein_harmonization_report_from_observations",
    "export_cross_study_protein_harmonization_tsv",
    "export_cross_study_protein_unresolved_tsv",
    "extract_cross_study_protein_observations",
    "render_cross_study_protein_harmonization_tsv",
    "render_cross_study_protein_unresolved_tsv",
]
