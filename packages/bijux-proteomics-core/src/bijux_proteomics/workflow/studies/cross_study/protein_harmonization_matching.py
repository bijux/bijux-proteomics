# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Accession and ortholog matching for cross-study protein harmonization."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.ortholog_mapping import OrthologRecord
from bijux_proteomics.sequences.fasta import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.workflow.studies.cross_study.protein_harmonization import (
        CrossStudyProteinObservation,
    )


class _GroupMetadata(TypedDict):
    group_id: int
    member_indices: tuple[int, ...]
    tokens: set[str]
    normalized_gene_symbols: set[str]
    normalized_species: set[str]


class _OrthologResolution(JsonModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    unique_links: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    ambiguous_candidates: dict[int, tuple[int, ...]] = Field(default_factory=dict)


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
    "_GroupMetadata",
    "_OrthologResolution",
    "_build_exact_accession_groups",
    "_build_gene_symbol_candidates",
    "_build_group_metadata",
    "_build_harmonized_components",
    "_component_sort_key",
    "_group_candidate_indices",
    "_observation_sort_key",
    "_resolve_unique_ortholog_links",
]
