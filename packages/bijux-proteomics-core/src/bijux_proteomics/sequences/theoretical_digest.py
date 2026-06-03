# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned theoretical digest builder for peptide search-space exports."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.chemistry import (
    IsotopicLabelingPolicy,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    StaticModification,
    VariableModification,
    VariableModificationEnumerationEntry,
    VariableModificationEnumerationReport,
    build_modification_registry,
    calculate_monoisotopic_peptide_mass,
    enumerate_variable_modifications,
)
from bijux_proteomics.sequences.digestion import (
    DigestedPeptide,
    DigestPolicy,
    PeptideDigestionMode,
    ProteaseRule,
    build_digest_policy,
    digest_protein_records,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel, hash_payload


class TheoreticalDigestModificationPolicy(JsonModel):
    """Stable modification settings for one theoretical digest search space."""

    model_config = ConfigDict(extra="forbid")

    static_modification_names: tuple[str, ...] = Field(default_factory=tuple)
    variable_modification_names: tuple[str, ...] = Field(default_factory=tuple)
    allow_isotopic_labels: bool = False
    allowed_label_families: tuple[str, ...] = Field(default_factory=tuple)
    max_variable_variants_per_peptide: int = Field(..., ge=1)
    registry_content_hash: str | None = None


class TheoreticalDigestPeptideEntry(JsonModel):
    """One unique candidate peptide in the theoretical digest search space."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    stripped_sequence: str = Field(..., min_length=1)
    sequence_length: int = Field(..., ge=1)
    neutral_mass: float = Field(..., gt=0.0)
    modification_count: int = Field(..., ge=0)
    occurrence_count: int = Field(..., ge=0)
    protein_accession_count: int = Field(..., ge=0)
    min_missed_cleavages: int = Field(..., ge=0)
    max_missed_cleavages: int = Field(..., ge=0)
    source_context_count: int = Field(..., ge=0)
    truncated_source_context_count: int = Field(..., ge=0)
    max_candidate_site_count: int = Field(..., ge=0)
    terminal_contexts: tuple[str, ...] = Field(default_factory=tuple)


class TheoreticalDigestProteinMappingEntry(JsonModel):
    """One candidate peptide-to-protein coordinate mapping."""

    model_config = ConfigDict(extra="forbid")

    canonical_notation: str = Field(..., min_length=1)
    stripped_sequence: str = Field(..., min_length=1)
    source_accession: str = Field(..., min_length=1)
    source_identifier: str = Field(..., min_length=1)
    source_protein_family: str = Field(..., min_length=1)
    source_isoform: int | None = Field(default=None, ge=1)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)
    matched_sequence: str = Field(..., min_length=1)
    missed_cleavages: int = Field(..., ge=0)
    protease: str = Field(..., min_length=1)
    digestion_mode: PeptideDigestionMode
    cleavage_type: str = Field(..., min_length=1)
    at_protein_n_term: bool = False
    at_protein_c_term: bool = False


class TheoreticalDigestSummary(JsonModel):
    """One stable summary row for a theoretical digest build."""

    model_config = ConfigDict(extra="forbid")

    input_record_count: int = Field(..., ge=0)
    peptide_occurrence_count: int = Field(..., ge=0)
    unique_stripped_sequence_count: int = Field(..., ge=0)
    output_candidate_peptide_count: int = Field(..., ge=0)
    output_mapping_count: int = Field(..., ge=0)
    shared_candidate_peptide_count: int = Field(..., ge=0)
    truncated_source_context_count: int = Field(..., ge=0)
    total_candidate_site_count: int = Field(..., ge=0)
    total_generated_variant_count: int = Field(..., ge=0)
    coordinate_map_valid: bool = False


class TheoreticalDigestBundle(JsonModel):
    """Durable theoretical digest bundle with candidates, mappings, and summary."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    digest_policy: DigestPolicy
    modification_policy: TheoreticalDigestModificationPolicy
    search_space_hash: str = Field(..., min_length=64, max_length=64)
    summary: TheoreticalDigestSummary
    digest_peptides: tuple[TheoreticalDigestPeptideEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_to_protein: tuple[TheoreticalDigestProteinMappingEntry, ...] = Field(
        default_factory=tuple
    )


class _TheoreticalDigestAggregate(TypedDict):
    canonical_notation: str
    stripped_sequence: str
    sequence_length: int
    neutral_mass: float
    modification_count: int
    occurrence_count: int
    protein_accessions: set[str]
    min_missed_cleavages: int | None
    max_missed_cleavages: int | None
    source_contexts: set[tuple[str, bool, bool]]
    truncated_source_context_count: int
    max_candidate_site_count: int
    terminal_contexts: set[str]


def build_theoretical_digest_bundle(
    records: tuple[object, ...],
    *,
    protease: ProteaseRule | str,
    missed_cleavages: int,
    digestion_mode: PeptideDigestionMode,
    min_length: int = 1,
    max_length: int | None = None,
    min_mass: float | None = None,
    max_mass: float | None = None,
    static_modifications: tuple[StaticModification, ...] = (),
    variable_modifications: tuple[VariableModification, ...] = (),
    registry: ModificationRegistryDocument | None = None,
    labeling_policy: IsotopicLabelingPolicy | None = None,
    max_variable_variants_per_peptide: int = 128,
) -> TheoreticalDigestBundle:
    """Build a full theoretical digest search-space bundle from protein records."""
    effective_registry = _effective_search_space_registry(
        static_modifications=static_modifications,
        variable_modifications=variable_modifications,
        registry=registry,
    )
    digested = digest_protein_records(
        records,
        protease=protease,
        missed_cleavages=missed_cleavages,
        mode=digestion_mode,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )
    digest_policy = build_digest_policy(
        protease=protease,
        digestion_mode=digestion_mode,
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )
    modification_policy = TheoreticalDigestModificationPolicy(
        static_modification_names=tuple(
            sorted(definition.name for definition in static_modifications)
        ),
        variable_modification_names=tuple(
            sorted(definition.name for definition in variable_modifications)
        ),
        allow_isotopic_labels=(
            False if labeling_policy is None else labeling_policy.allow_isotopic_labels
        ),
        allowed_label_families=(
            () if labeling_policy is None else labeling_policy.allowed_label_families
        ),
        max_variable_variants_per_peptide=max_variable_variants_per_peptide,
        registry_content_hash=(
            None
            if effective_registry is None
            or effective_registry.document_schema.content_hash is None
            else effective_registry.document_schema.content_hash
        ),
    )
    search_space_hash = hash_payload(
        {
            "digest_policy": digest_policy.to_dict(),
            "modification_policy": modification_policy.to_dict(),
        }
    )
    record_sequences = _record_sequence_lookup(records)
    grouped_occurrences: dict[tuple[str, bool, bool], list[DigestedPeptide]] = (
        defaultdict(list)
    )
    for peptide in digested:
        context_key = (
            peptide.sequence,
            peptide.start == 1,
            peptide.end == len(record_sequences[peptide.source_identifier]),
        )
        grouped_occurrences[context_key].append(peptide)

    peptide_aggregates: dict[str, _TheoreticalDigestAggregate] = {}
    mapping_entries: list[TheoreticalDigestProteinMappingEntry] = []
    total_candidate_site_count = 0
    total_generated_variant_count = 0
    truncated_source_context_count = 0

    for context_key in sorted(grouped_occurrences):
        sequence, at_protein_n_term, at_protein_c_term = context_key
        occurrences = grouped_occurrences[context_key]
        parsed = ParsedModifiedPeptide(
            sequence=sequence,
            modifications=(),
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
            canonical_notation=sequence,
        )
        enumeration = _enumerate_theoretical_variants(
            parsed,
            variable_modifications=variable_modifications,
            registry=effective_registry,
            labeling_policy=labeling_policy,
            max_variable_variants_per_peptide=max_variable_variants_per_peptide,
        )
        total_candidate_site_count += enumeration.candidate_site_count
        total_generated_variant_count += enumeration.generated_variant_count
        if enumeration.truncated:
            truncated_source_context_count += 1
        terminal_context = _terminal_context_label(
            at_protein_n_term=at_protein_n_term,
            at_protein_c_term=at_protein_c_term,
        )

        for variant in enumeration.variants:
            parsed_variant = ParsedModifiedPeptide(
                sequence=sequence,
                modifications=variant.modifications,
                at_protein_n_term=at_protein_n_term,
                at_protein_c_term=at_protein_c_term,
                canonical_notation=variant.canonical_notation,
            )
            neutral_mass = calculate_monoisotopic_peptide_mass(
                parsed_variant,
                static_modifications=static_modifications,
                registry=effective_registry,
            )
            aggregate = peptide_aggregates.setdefault(
                variant.canonical_notation,
                {
                    "canonical_notation": variant.canonical_notation,
                    "stripped_sequence": sequence,
                    "sequence_length": len(sequence),
                    "neutral_mass": neutral_mass,
                    "modification_count": variant.modification_count,
                    "occurrence_count": 0,
                    "protein_accessions": set(),
                    "min_missed_cleavages": None,
                    "max_missed_cleavages": None,
                    "source_contexts": set(),
                    "truncated_source_context_count": 0,
                    "max_candidate_site_count": 0,
                    "terminal_contexts": set(),
                },
            )
            aggregate["occurrence_count"] += len(occurrences)
            aggregate["protein_accessions"].update(
                occurrence.source_accession for occurrence in occurrences
            )
            aggregate["source_contexts"].add(context_key)
            aggregate["terminal_contexts"].add(terminal_context)
            aggregate["max_candidate_site_count"] = max(
                aggregate["max_candidate_site_count"],
                enumeration.candidate_site_count,
            )
            if enumeration.truncated:
                aggregate["truncated_source_context_count"] += 1
            for occurrence in occurrences:
                aggregate["min_missed_cleavages"] = _bounded_min(
                    aggregate["min_missed_cleavages"],
                    occurrence.missed_cleavages,
                )
                aggregate["max_missed_cleavages"] = _bounded_max(
                    aggregate["max_missed_cleavages"],
                    occurrence.missed_cleavages,
                )
                matched_sequence = _coordinate_matched_sequence(
                    occurrence,
                    record_sequences=record_sequences,
                )
                mapping_entries.append(
                    TheoreticalDigestProteinMappingEntry(
                        canonical_notation=variant.canonical_notation,
                        stripped_sequence=sequence,
                        source_accession=occurrence.source_accession,
                        source_identifier=occurrence.source_identifier,
                        source_protein_family=occurrence.source_protein_family,
                        source_isoform=occurrence.source_isoform,
                        start=occurrence.start,
                        end=occurrence.end,
                        matched_sequence=matched_sequence,
                        missed_cleavages=occurrence.missed_cleavages,
                        protease=occurrence.protease,
                        digestion_mode=occurrence.digestion_mode,
                        cleavage_type=occurrence.cleavage_type,
                        at_protein_n_term=at_protein_n_term,
                        at_protein_c_term=at_protein_c_term,
                    )
                )

    digest_peptides = tuple(
        TheoreticalDigestPeptideEntry(
            canonical_notation=aggregate["canonical_notation"],
            stripped_sequence=aggregate["stripped_sequence"],
            sequence_length=aggregate["sequence_length"],
            neutral_mass=aggregate["neutral_mass"],
            modification_count=aggregate["modification_count"],
            occurrence_count=aggregate["occurrence_count"],
            protein_accession_count=len(aggregate["protein_accessions"]),
            min_missed_cleavages=aggregate["min_missed_cleavages"] or 0,
            max_missed_cleavages=aggregate["max_missed_cleavages"] or 0,
            source_context_count=len(aggregate["source_contexts"]),
            truncated_source_context_count=aggregate["truncated_source_context_count"],
            max_candidate_site_count=aggregate["max_candidate_site_count"],
            terminal_contexts=tuple(sorted(aggregate["terminal_contexts"])),
        )
        for _key, aggregate in sorted(peptide_aggregates.items())
    )
    ordered_mappings = tuple(
        sorted(
            mapping_entries,
            key=lambda entry: (
                entry.canonical_notation,
                entry.source_accession,
                entry.start,
                entry.end,
                entry.source_identifier,
            ),
        )
    )
    summary = TheoreticalDigestSummary(
        input_record_count=len(records),
        peptide_occurrence_count=len(digested),
        unique_stripped_sequence_count=len({peptide.sequence for peptide in digested}),
        output_candidate_peptide_count=len(digest_peptides),
        output_mapping_count=len(ordered_mappings),
        shared_candidate_peptide_count=sum(
            1 for peptide in digest_peptides if peptide.protein_accession_count > 1
        ),
        truncated_source_context_count=truncated_source_context_count,
        total_candidate_site_count=total_candidate_site_count,
        total_generated_variant_count=total_generated_variant_count,
        coordinate_map_valid=True,
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="theoretical_peptide_digest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    bundle = TheoreticalDigestBundle(
        document_schema=schema,
        digest_policy=digest_policy,
        modification_policy=modification_policy,
        search_space_hash=search_space_hash,
        summary=summary,
        digest_peptides=digest_peptides,
        peptide_to_protein=ordered_mappings,
    )
    payload = bundle.to_dict()
    return bundle.model_copy(
        update={"document_schema": bundle.document_schema.with_content_hash(payload)}
    )


def write_theoretical_digest_bundle(
    bundle: TheoreticalDigestBundle,
    out_dir: Path,
) -> tuple[Path, Path, Path]:
    """Write the governed theoretical digest TSV bundle to one directory."""
    out_dir.mkdir(parents=True, exist_ok=True)
    peptides_path = out_dir / "digest_peptides.tsv"
    mappings_path = out_dir / "peptide_to_protein.tsv"
    summary_path = out_dir / "digest_summary.tsv"
    write_output_table_tsv(
        peptides_path, render_theoretical_digest_peptides_tsv(bundle)
    )
    write_output_table_tsv(
        mappings_path, render_theoretical_digest_mappings_tsv(bundle)
    )
    write_output_table_tsv(summary_path, render_theoretical_digest_summary_tsv(bundle))
    return peptides_path, mappings_path, summary_path


def export_theoretical_digest_bundle(
    bundle: TheoreticalDigestBundle,
    out_dir: Path,
) -> tuple[Path, Path, Path]:
    """Compatibility wrapper for the legacy theoretical digest bundle export name."""

    return write_theoretical_digest_bundle(bundle, out_dir)


def render_theoretical_digest_peptides_tsv(bundle: TheoreticalDigestBundle) -> str:
    """Render stable candidate-peptide TSV output."""
    lines = [
        "\t".join(
            [
                "canonical_notation",
                "stripped_sequence",
                "sequence_length",
                "neutral_mass",
                "modification_count",
                "occurrence_count",
                "protein_accession_count",
                "min_missed_cleavages",
                "max_missed_cleavages",
                "source_context_count",
                "truncated_source_context_count",
                "max_candidate_site_count",
                "terminal_contexts",
            ]
        )
    ]
    for peptide in bundle.digest_peptides:
        lines.append(
            "\t".join(
                [
                    peptide.canonical_notation,
                    peptide.stripped_sequence,
                    str(peptide.sequence_length),
                    f"{peptide.neutral_mass:.5f}",
                    str(peptide.modification_count),
                    str(peptide.occurrence_count),
                    str(peptide.protein_accession_count),
                    str(peptide.min_missed_cleavages),
                    str(peptide.max_missed_cleavages),
                    str(peptide.source_context_count),
                    str(peptide.truncated_source_context_count),
                    str(peptide.max_candidate_site_count),
                    ";".join(peptide.terminal_contexts),
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_theoretical_digest_mappings_tsv(bundle: TheoreticalDigestBundle) -> str:
    """Render stable peptide-to-protein coordinate TSV output."""
    lines = [
        "\t".join(
            [
                "canonical_notation",
                "stripped_sequence",
                "source_accession",
                "source_identifier",
                "source_protein_family",
                "source_isoform",
                "start",
                "end",
                "matched_sequence",
                "missed_cleavages",
                "protease",
                "digestion_mode",
                "cleavage_type",
                "at_protein_n_term",
                "at_protein_c_term",
            ]
        )
    ]
    for mapping in bundle.peptide_to_protein:
        lines.append(
            "\t".join(
                [
                    mapping.canonical_notation,
                    mapping.stripped_sequence,
                    mapping.source_accession,
                    mapping.source_identifier,
                    mapping.source_protein_family,
                    ""
                    if mapping.source_isoform is None
                    else str(mapping.source_isoform),
                    str(mapping.start),
                    str(mapping.end),
                    mapping.matched_sequence,
                    str(mapping.missed_cleavages),
                    mapping.protease,
                    mapping.digestion_mode.value,
                    mapping.cleavage_type,
                    "true" if mapping.at_protein_n_term else "false",
                    "true" if mapping.at_protein_c_term else "false",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_theoretical_digest_summary_tsv(bundle: TheoreticalDigestBundle) -> str:
    """Render stable one-row summary TSV output."""
    summary = bundle.summary
    policy = bundle.digest_policy
    modification_policy = bundle.modification_policy
    lines = [
        "\t".join(
            [
                "input_record_count",
                "peptide_occurrence_count",
                "unique_stripped_sequence_count",
                "output_candidate_peptide_count",
                "output_mapping_count",
                "shared_candidate_peptide_count",
                "truncated_source_context_count",
                "total_candidate_site_count",
                "total_generated_variant_count",
                "coordinate_map_valid",
                "protease",
                "digestion_mode",
                "missed_cleavages",
                "min_length",
                "max_length",
                "min_mass",
                "max_mass",
                "static_modification_names",
                "variable_modification_names",
                "allow_isotopic_labels",
                "allowed_label_families",
                "max_variable_variants_per_peptide",
                "registry_content_hash",
                "search_space_hash",
            ]
        ),
        "\t".join(
            [
                str(summary.input_record_count),
                str(summary.peptide_occurrence_count),
                str(summary.unique_stripped_sequence_count),
                str(summary.output_candidate_peptide_count),
                str(summary.output_mapping_count),
                str(summary.shared_candidate_peptide_count),
                str(summary.truncated_source_context_count),
                str(summary.total_candidate_site_count),
                str(summary.total_generated_variant_count),
                "true" if summary.coordinate_map_valid else "false",
                policy.protease,
                policy.digestion_mode.value,
                str(policy.missed_cleavages),
                "" if policy.min_length is None else str(policy.min_length),
                "" if policy.max_length is None else str(policy.max_length),
                "" if policy.min_mass is None else str(policy.min_mass),
                "" if policy.max_mass is None else str(policy.max_mass),
                ";".join(modification_policy.static_modification_names),
                ";".join(modification_policy.variable_modification_names),
                "true" if modification_policy.allow_isotopic_labels else "false",
                ";".join(modification_policy.allowed_label_families),
                str(modification_policy.max_variable_variants_per_peptide),
                modification_policy.registry_content_hash or "",
                bundle.search_space_hash,
            ]
        ),
    ]
    return "\n".join(lines) + "\n"


def _record_sequence_lookup(records: tuple[object, ...]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for record in records:
        identifier = getattr(record, "source_identifier", None) or getattr(
            record, "identifier", None
        )
        residues = getattr(record, "residues", None)
        if identifier is None or residues is None:
            raise TypeError(
                "theoretical digest builder expects records with identifier and residues"
            )
        lookup[str(identifier)] = str(residues).strip().upper()
    return lookup


def _effective_search_space_registry(
    *,
    static_modifications: tuple[StaticModification, ...],
    variable_modifications: tuple[VariableModification, ...],
    registry: ModificationRegistryDocument | None,
) -> ModificationRegistryDocument | None:
    if registry is None and not static_modifications and not variable_modifications:
        return None
    if registry is None:
        return build_modification_registry(
            static_modifications=tuple(static_modifications),
            variable_modifications=tuple(variable_modifications),
        )
    return build_modification_registry(
        static_modifications=_unique_static_definitions(
            (*registry.static_modifications, *static_modifications)
        ),
        variable_modifications=_unique_variable_definitions(
            (*registry.variable_modifications, *variable_modifications)
        ),
    )


def _enumerate_theoretical_variants(
    peptide: ParsedModifiedPeptide,
    *,
    variable_modifications: tuple[VariableModification, ...],
    registry: ModificationRegistryDocument | None,
    labeling_policy: IsotopicLabelingPolicy | None,
    max_variable_variants_per_peptide: int,
) -> VariableModificationEnumerationReport:
    if variable_modifications:
        return enumerate_variable_modifications(
            peptide,
            variable_modifications=variable_modifications,
            registry=registry,
            labeling_policy=labeling_policy,
            max_variants=max_variable_variants_per_peptide,
        )
    return VariableModificationEnumerationReport(
        sequence=peptide.sequence,
        at_protein_n_term=peptide.at_protein_n_term,
        at_protein_c_term=peptide.at_protein_c_term,
        base_modification_count=len(peptide.modifications),
        candidate_site_count=0,
        generated_variant_count=1,
        max_variants=max_variable_variants_per_peptide,
        truncated=False,
        variants=(
            VariableModificationEnumerationEntry(
                canonical_notation=peptide.canonical_notation,
                modification_count=len(peptide.modifications),
                modifications=peptide.modifications,
            ),
        ),
    )


def _coordinate_matched_sequence(
    occurrence: DigestedPeptide,
    *,
    record_sequences: dict[str, str],
) -> str:
    protein_sequence = record_sequences[occurrence.source_identifier]
    matched = protein_sequence[occurrence.start - 1 : occurrence.end]
    if matched != occurrence.sequence:
        raise ValueError(
            "digested peptide coordinates do not map back to the source protein sequence"
        )
    return matched


def _terminal_context_label(
    *,
    at_protein_n_term: bool,
    at_protein_c_term: bool,
) -> str:
    if at_protein_n_term and at_protein_c_term:
        return "protein_both_terms"
    if at_protein_n_term:
        return "protein_n_term"
    if at_protein_c_term:
        return "protein_c_term"
    return "internal"


def _bounded_min(current: int | None, candidate: int) -> int:
    return candidate if current is None else min(current, candidate)


def _bounded_max(current: int | None, candidate: int) -> int:
    return candidate if current is None else max(current, candidate)


def _unique_static_definitions(
    definitions: tuple[StaticModification, ...],
) -> tuple[StaticModification, ...]:
    unique: list[StaticModification] = []
    signatures: set[tuple[object, ...]] = set()
    for definition in definitions:
        signature = _definition_signature(definition)
        if signature in signatures:
            continue
        signatures.add(signature)
        unique.append(definition)
    return tuple(unique)


def _unique_variable_definitions(
    definitions: tuple[VariableModification, ...],
) -> tuple[VariableModification, ...]:
    unique: list[VariableModification] = []
    signatures: set[tuple[object, ...]] = set()
    for definition in definitions:
        signature = _definition_signature(definition)
        if signature in signatures:
            continue
        signatures.add(signature)
        unique.append(definition)
    return tuple(unique)


def _definition_signature(
    definition: StaticModification | VariableModification,
) -> tuple[object, ...]:
    return (
        definition.name,
        definition.controlled_id,
        definition.position,
        definition.residues,
        definition.mass_delta_monoisotopic,
        definition.mass_delta_average,
        definition.isotopic_label_family,
        tuple(
            (
                neutral_loss.name,
                neutral_loss.monoisotopic_mass,
                neutral_loss.average_mass,
            )
            for neutral_loss in definition.neutral_losses
        ),
        getattr(definition, "max_occurrences", None),
    )


__all__ = [
    "TheoreticalDigestBundle",
    "TheoreticalDigestModificationPolicy",
    "TheoreticalDigestPeptideEntry",
    "TheoreticalDigestProteinMappingEntry",
    "TheoreticalDigestSummary",
    "build_theoretical_digest_bundle",
    "export_theoretical_digest_bundle",
    "write_theoretical_digest_bundle",
    "render_theoretical_digest_mappings_tsv",
    "render_theoretical_digest_peptides_tsv",
    "render_theoretical_digest_summary_tsv",
]
