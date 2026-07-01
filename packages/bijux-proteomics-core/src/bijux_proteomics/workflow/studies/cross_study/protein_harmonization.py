# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-study protein harmonization over owned study-result surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.ortholog_mapping import OrthologRecord
from bijux_proteomics.ptm.cards.evidence_cards import PtmEvidenceCard
from bijux_proteomics.workflow.studies.cross_study.protein_harmonization_matching import (
    _build_exact_accession_groups,
    _build_gene_symbol_candidates,
    _build_group_metadata,
    _build_harmonized_components,
    _component_sort_key,
    _group_candidate_indices,
    _GroupMetadata,
    _observation_sort_key,
    _OrthologResolution,
    _resolve_unique_ortholog_links,
)
from bijux_proteomics.workflow.studies.cross_study.protein_harmonization_rendering import (
    export_cross_study_protein_harmonization_tsv,
    export_cross_study_protein_unresolved_tsv,
    render_cross_study_protein_harmonization_tsv,
    render_cross_study_protein_unresolved_tsv,
)
from bijux_proteomics.workflow.studies.study_results import (
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


@dataclass(frozen=True)
class _ProteinHarmonizationContext:
    exact_group_members: dict[int, tuple[int, ...]]
    group_metadata: dict[int, _GroupMetadata]
    ortholog_resolution: _OrthologResolution
    component_group_ids: dict[int, set[int]]
    group_component_ids: dict[int, int]
    harmonized_component_ids: set[int]
    group_gene_candidates: dict[int, tuple[int, ...]]


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
        return _empty_harmonization_report(
            unsupported_studies=unsupported_studies,
            input_study_count=input_study_count,
        )

    context = _build_harmonization_context(observations, ortholog_records)
    (
        harmonized_entries,
        exact_accession_group_count,
        ortholog_linked_group_count,
    ) = _build_harmonized_entries(observations, context)
    unresolved_entries = _build_unresolved_entries(
        observations=observations,
        context=context,
        harmonized_entries=harmonized_entries,
    )
    summary = _build_harmonization_summary(
        observations=observations,
        unsupported_studies=unsupported_studies,
        input_study_count=input_study_count,
        harmonized_entries=harmonized_entries,
        unresolved_entries=unresolved_entries,
        exact_accession_group_count=exact_accession_group_count,
        ortholog_linked_group_count=ortholog_linked_group_count,
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


def _empty_harmonization_report(
    *,
    unsupported_studies: tuple[UnsupportedCrossStudyProteinStudy, ...],
    input_study_count: int | None,
) -> CrossStudyProteinHarmonizationReport:
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


def _build_harmonization_context(
    observations: tuple[CrossStudyProteinObservation, ...],
    ortholog_records: tuple[OrthologRecord, ...],
) -> _ProteinHarmonizationContext:
    exact_group_members, _ = _build_exact_accession_groups(observations)
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
        if _component_study_count(
            group_ids=group_ids,
            exact_group_members=exact_group_members,
            observations=observations,
        )
        >= 2
    }
    return _ProteinHarmonizationContext(
        exact_group_members=exact_group_members,
        group_metadata=group_metadata,
        ortholog_resolution=ortholog_resolution,
        component_group_ids=component_group_ids,
        group_component_ids=group_component_ids,
        harmonized_component_ids=harmonized_component_ids,
        group_gene_candidates=_build_gene_symbol_candidates(
            group_metadata=group_metadata,
            harmonized_component_ids=harmonized_component_ids,
            group_component_ids=group_component_ids,
        ),
    )


def _build_harmonized_entries(
    observations: tuple[CrossStudyProteinObservation, ...],
    context: _ProteinHarmonizationContext,
) -> tuple[list[CrossStudyProteinHarmonizedEntry], int, int]:
    harmonized_entries: list[CrossStudyProteinHarmonizedEntry] = []
    exact_accession_group_count = 0
    ortholog_linked_group_count = 0
    for component_index, component_id in enumerate(
        sorted(
            context.harmonized_component_ids,
            key=lambda item: _component_sort_key(
                context.component_group_ids[item],
                exact_group_members=context.exact_group_members,
                observations=observations,
            ),
        ),
        start=1,
    ):
        group_ids = context.component_group_ids[component_id]
        component_entries, exact_only = _component_harmonized_entries(
            component_index=component_index,
            group_ids=group_ids,
            observations=observations,
            context=context,
        )
        harmonized_entries.extend(component_entries)
        if exact_only:
            exact_accession_group_count += 1
        else:
            ortholog_linked_group_count += 1
    return harmonized_entries, exact_accession_group_count, ortholog_linked_group_count


def _component_harmonized_entries(
    *,
    component_index: int,
    group_ids: set[int],
    observations: tuple[CrossStudyProteinObservation, ...],
    context: _ProteinHarmonizationContext,
) -> tuple[list[CrossStudyProteinHarmonizedEntry], bool]:
    component_observation_indices = tuple(
        index
        for group_id in sorted(group_ids)
        for index in context.exact_group_members[group_id]
    )
    match_basis, note, exact_only = _component_match_basis_note(
        group_ids=group_ids,
        exact_group_members=context.exact_group_members,
        unique_links=context.ortholog_resolution.unique_links,
    )
    harmonized_id = f"harmonized_protein_{component_index:03d}"
    harmonized_study_count = len(
        {observations[index].study_id for index in component_observation_indices}
    )
    entries = [
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
        for observation in (
            observations[index]
            for index in sorted(
                component_observation_indices,
                key=lambda item: _observation_sort_key(observations[item]),
            )
        )
    ]
    return entries, exact_only


def _component_match_basis_note(
    *,
    group_ids: set[int],
    exact_group_members: dict[int, tuple[int, ...]],
    unique_links: tuple[tuple[int, int], ...],
) -> tuple[CrossStudyProteinMatchBasis, str, bool]:
    exact_only = len(group_ids) == 1
    if exact_only:
        return (
            CrossStudyProteinMatchBasis.EXACT_ACCESSION,
            "study observations share exact canonical protein accessions or aliases",
            True,
        )
    has_ortholog = any(
        tuple(sorted((left_group_id, right_group_id))) in unique_links
        for left_group_id in group_ids
        for right_group_id in group_ids
        if left_group_id < right_group_id
    )
    if has_ortholog and any(
        len(exact_group_members[group_id]) > 1 for group_id in group_ids
    ):
        return (
            CrossStudyProteinMatchBasis.EXACT_ACCESSION_AND_UNIQUE_ORTHOLOG,
            "study observations were linked through exact accession overlap within species and unique ortholog support across species",
            False,
        )
    return (
        CrossStudyProteinMatchBasis.UNIQUE_ORTHOLOG,
        "study observations were linked only through unique one-to-one ortholog support across species",
        False,
    )


def _build_unresolved_entries(
    *,
    observations: tuple[CrossStudyProteinObservation, ...],
    context: _ProteinHarmonizationContext,
    harmonized_entries: list[CrossStudyProteinHarmonizedEntry],
) -> list[CrossStudyProteinUnresolvedEntry]:
    harmonized_observation_ids = {entry.observation_id for entry in harmonized_entries}
    unresolved_entries: list[CrossStudyProteinUnresolvedEntry] = []
    for group_id, member_indices in sorted(
        context.exact_group_members.items(),
        key=lambda item: _component_sort_key(
            {item[0]},
            exact_group_members=context.exact_group_members,
            observations=observations,
        ),
    ):
        if context.group_component_ids[group_id] in context.harmonized_component_ids:
            continue
        reason, candidate_indices, note = _unresolved_group_reason(
            group_id=group_id,
            context=context,
        )
        candidate_observation_ids, candidate_study_ids = _candidate_identity_lists(
            candidate_indices=candidate_indices,
            observations=observations,
            harmonized_observation_ids=harmonized_observation_ids,
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
    return unresolved_entries


def _unresolved_group_reason(
    *,
    group_id: int,
    context: _ProteinHarmonizationContext,
) -> tuple[CrossStudyProteinUnresolvedReason, tuple[int, ...], str]:
    ambiguous_candidates = context.ortholog_resolution.ambiguous_candidates.get(
        group_id,
        (),
    )
    gene_symbol_candidates = tuple(
        candidate_group_id
        for candidate_group_id in context.group_gene_candidates.get(group_id, ())
        if candidate_group_id != group_id
    )
    if ambiguous_candidates:
        return (
            CrossStudyProteinUnresolvedReason.AMBIGUOUS_ORTHOLOG_MAPPING,
            _group_candidate_indices(
                ambiguous_candidates,
                exact_group_members=context.exact_group_members,
            ),
            "explicit ortholog records linked this protein observation to more than one cross-study candidate, so the mapping remains unresolved",
        )
    if gene_symbol_candidates:
        return (
            CrossStudyProteinUnresolvedReason.GENE_SYMBOL_ONLY_MATCH,
            _group_candidate_indices(
                gene_symbol_candidates,
                exact_group_members=context.exact_group_members,
            ),
            "cross-study candidates shared a gene symbol but did not share exact protein accessions or a unique ortholog relationship",
        )
    return (
        CrossStudyProteinUnresolvedReason.NO_CROSS_STUDY_MATCH,
        (),
        "no exact accession overlap or unique ortholog support linked this protein observation to another study",
    )


def _candidate_identity_lists(
    *,
    candidate_indices: tuple[int, ...],
    observations: tuple[CrossStudyProteinObservation, ...],
    harmonized_observation_ids: set[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (
        tuple(
            sorted(
                {
                    observations[index].observation_id
                    for index in candidate_indices
                    if observations[index].observation_id
                    not in harmonized_observation_ids
                }
            )
        ),
        tuple(
            sorted(
                {
                    observations[index].study_id
                    for index in candidate_indices
                    if observations[index].observation_id
                    not in harmonized_observation_ids
                }
            )
        ),
    )


def _build_harmonization_summary(
    *,
    observations: tuple[CrossStudyProteinObservation, ...],
    unsupported_studies: tuple[UnsupportedCrossStudyProteinStudy, ...],
    input_study_count: int | None,
    harmonized_entries: list[CrossStudyProteinHarmonizedEntry],
    unresolved_entries: list[CrossStudyProteinUnresolvedEntry],
    exact_accession_group_count: int,
    ortholog_linked_group_count: int,
) -> CrossStudyProteinHarmonizationSummary:
    return CrossStudyProteinHarmonizationSummary(
        input_study_count=_harmonization_input_study_count(
            observations=observations,
            unsupported_studies=unsupported_studies,
            input_study_count=input_study_count,
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


def _harmonization_input_study_count(
    *,
    observations: tuple[CrossStudyProteinObservation, ...],
    unsupported_studies: tuple[UnsupportedCrossStudyProteinStudy, ...],
    input_study_count: int | None,
) -> int:
    if input_study_count is not None:
        return input_study_count
    return len({entry.study_id for entry in observations}) + len(unsupported_studies)


def _component_study_count(
    *,
    group_ids: set[int],
    exact_group_members: dict[int, tuple[int, ...]],
    observations: tuple[CrossStudyProteinObservation, ...],
) -> int:
    return len(
        {
            observations[index].study_id
            for group_id in group_ids
            for index in exact_group_members[group_id]
        }
    )


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


def _sorted_nonempty(
    values: tuple[str, ...] | list[str] | tuple[object, ...],
) -> tuple[str, ...]:
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


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
