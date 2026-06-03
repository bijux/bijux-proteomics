# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM localization scoring and probability review surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import (
    AppliedModification,
    FragmentIonSeries,
    ModificationLocalizationCandidate,
    ModificationPosition,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    build_modification_localization_advisory,
    build_modified_peptide,
    calculate_fragment_ions,
    parse_modified_peptide,
)
from bijux_proteomics.ptm.contracts import PtmEvidenceRecord
from bijux_proteomics_foundation import JsonModel


class PtmLocalizationProbabilitySource(StrEnum):
    """How one PTM localization probability was obtained."""

    REPORTED_PROBABILITY = "reported_probability"
    NORMALIZED_SCORE = "normalized_score"


class PtmLocalizationConfidenceTier(StrEnum):
    """Confidence tier for one localized PTM assignment."""

    HIGH_CONFIDENCE = "high_confidence"
    SUPPORTED = "supported"
    AMBIGUOUS = "ambiguous"
    REFUSED = "refused"


class PtmLocalizationScoringEntry(JsonModel):
    """One PTM localization-scoring entry for one localized modification."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    peptide_site_index: int = Field(..., ge=1)
    candidate_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    ambiguity_group: str = Field(..., min_length=1)
    localization_score: float = Field(..., ge=0.0)
    localization_probability: float = Field(..., ge=0.0, le=1.0)
    probability_source: PtmLocalizationProbabilitySource
    localization_tier: PtmLocalizationConfidenceTier
    site_determining_ions: tuple[str, ...] = Field(default_factory=tuple)
    supported_site_determining_ions: tuple[str, ...] = Field(default_factory=tuple)
    ambiguous: bool
    multi_phosphorylated: bool
    note: str = Field(..., min_length=1)


class PtmLocalizationScoringReport(JsonModel):
    """Stable PTM localization-scoring report."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PtmLocalizationScoringEntry, ...] = Field(default_factory=tuple)
    ambiguous_entry_count: int = Field(..., ge=0)
    confident_entry_count: int = Field(..., ge=0)
    high_confidence_entry_count: int = Field(..., ge=0)
    supported_entry_count: int = Field(..., ge=0)
    refused_entry_count: int = Field(..., ge=0)
    multi_phosphorylated_entry_count: int = Field(..., ge=0)
    fragment_supported_entry_count: int = Field(..., ge=0)


def build_ptm_localization_scoring_report(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None,
    registry: ModificationRegistryDocument | None = None,
) -> PtmLocalizationScoringReport:
    """Score localized PTM sites and derive explicit localization probabilities."""

    entries: list[PtmLocalizationScoringEntry] = []
    for record in records:
        parsed = parse_modified_peptide(record.localized_peptide, registry=registry)
        advisory = build_modification_localization_advisory(parsed, registry=registry)
        phospho_count = sum(
            1
            for modification in parsed.modifications
            if modification.name == "Phospho"
            and modification.site is ModificationPosition.ANYWHERE
        )
        same_name_counts = {
            modification.name: sum(
                1
                for candidate_modification in parsed.modifications
                if candidate_modification.name == modification.name
                and candidate_modification.site is ModificationPosition.ANYWHERE
            )
            for modification in parsed.modifications
        }

        for index, (modification, candidate) in enumerate(
            zip(parsed.modifications, advisory.candidates, strict=False)
        ):
            if (
                modification.site is not ModificationPosition.ANYWHERE
                or modification.site_index is None
            ):
                continue

            candidate_site_indices = _filter_candidate_site_indices(
                parsed,
                modification_index=index,
                candidate_site_indices=_candidate_site_indices(
                    record=record,
                    modification=modification,
                    candidate=candidate,
                    same_name_count=same_name_counts.get(modification.name, 1),
                ),
                registry=registry,
            )
            site_determining_ions = _site_determining_ions(
                parsed,
                modification_index=index,
                candidate_site_indices=candidate_site_indices,
                registry=registry,
            )
            supported_site_determining_ions = (
                tuple(
                    ion
                    for ion in site_determining_ions
                    if ion
                    in set(fragment_ion_support_by_spectrum.get(record.spectrum_id, ()))
                )
                if fragment_ion_support_by_spectrum is not None
                else ()
            )
            probability, source = normalize_ptm_localization_probability(
                localization_score=record.localization_score,
                reported_probability=getattr(record, "localization_probability", None),
                ambiguous=len(candidate_site_indices) > 1,
                site_determining_ion_count=len(site_determining_ions),
                supported_site_determining_ion_count=len(
                    supported_site_determining_ions
                ),
            )
            ambiguity_group = _build_ambiguity_group(
                modification_name=modification.name,
                candidate_site_indices=candidate_site_indices,
            )
            tier = _determine_localization_tier(
                localization_probability=probability,
                probability_source=source,
                candidate_site_indices=candidate_site_indices,
                supported_site_determining_ion_count=len(
                    supported_site_determining_ions
                ),
            )
            ambiguous = tier is PtmLocalizationConfidenceTier.AMBIGUOUS
            note = _localization_tier_note(
                tier=tier,
                probability_source=source,
                supported_site_determining_ion_count=len(
                    supported_site_determining_ions
                ),
            )
            entries.append(
                PtmLocalizationScoringEntry(
                    spectrum_id=record.spectrum_id,
                    sample_id=record.sample_id,
                    localized_peptide=record.localized_peptide,
                    canonical_peptide=record.canonical_peptide,
                    modification_name=modification.name,
                    peptide_site_index=modification.site_index,
                    candidate_site_indices=candidate_site_indices,
                    ambiguity_group=ambiguity_group,
                    localization_score=record.localization_score,
                    localization_probability=probability,
                    probability_source=source,
                    localization_tier=tier,
                    site_determining_ions=site_determining_ions,
                    supported_site_determining_ions=supported_site_determining_ions,
                    ambiguous=ambiguous,
                    multi_phosphorylated=phospho_count > 1,
                    note=note,
                )
            )
    sorted_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.spectrum_id,
                entry.peptide_site_index,
                entry.modification_name,
            ),
        )
    )
    return PtmLocalizationScoringReport(
        entries=sorted_entries,
        ambiguous_entry_count=sum(1 for entry in sorted_entries if entry.ambiguous),
        confident_entry_count=sum(
            1
            for entry in sorted_entries
            if entry.localization_tier
            in {
                PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                PtmLocalizationConfidenceTier.SUPPORTED,
            }
        ),
        high_confidence_entry_count=sum(
            1
            for entry in sorted_entries
            if entry.localization_tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE
        ),
        supported_entry_count=sum(
            1
            for entry in sorted_entries
            if entry.localization_tier is PtmLocalizationConfidenceTier.SUPPORTED
        ),
        refused_entry_count=sum(
            1
            for entry in sorted_entries
            if entry.localization_tier is PtmLocalizationConfidenceTier.REFUSED
        ),
        multi_phosphorylated_entry_count=sum(
            1 for entry in sorted_entries if entry.multi_phosphorylated
        ),
        fragment_supported_entry_count=sum(
            1 for entry in sorted_entries if entry.supported_site_determining_ions
        ),
    )


def normalize_ptm_localization_probability(
    *,
    localization_score: float,
    reported_probability: float | None = None,
    ambiguous: bool,
    site_determining_ion_count: int,
    supported_site_determining_ion_count: int,
) -> tuple[float, PtmLocalizationProbabilitySource]:
    """Normalize one PTM localization score into an explicit probability."""

    if reported_probability is not None:
        probability = reported_probability
        source = PtmLocalizationProbabilitySource.REPORTED_PROBABILITY
    else:
        probability = (
            localization_score
            if localization_score <= 1.0
            else localization_score / (localization_score + 1.0)
        )
        source = PtmLocalizationProbabilitySource.NORMALIZED_SCORE

    if ambiguous and site_determining_ion_count == 0:
        probability = min(probability, 0.5)
    if (
        ambiguous
        and supported_site_determining_ion_count == 0
        and site_determining_ion_count > 0
    ):
        probability = min(probability, 0.75)
    return round(probability, 4), source


def _determine_localization_tier(
    *,
    localization_probability: float,
    probability_source: PtmLocalizationProbabilitySource,
    candidate_site_indices: tuple[int, ...],
    supported_site_determining_ion_count: int,
) -> PtmLocalizationConfidenceTier:
    has_reported_high_probability = (
        probability_source is PtmLocalizationProbabilitySource.REPORTED_PROBABILITY
        and localization_probability >= 0.95
    )
    has_supported_site_evidence = supported_site_determining_ion_count > 0
    unresolved_ambiguity = (
        len(candidate_site_indices) > 1
        and not has_reported_high_probability
        and not has_supported_site_evidence
    )
    if localization_probability >= 0.95 and (
        has_reported_high_probability or has_supported_site_evidence
    ):
        return PtmLocalizationConfidenceTier.HIGH_CONFIDENCE
    if unresolved_ambiguity:
        return PtmLocalizationConfidenceTier.AMBIGUOUS
    if localization_probability >= 0.75 or has_supported_site_evidence:
        return PtmLocalizationConfidenceTier.SUPPORTED
    return PtmLocalizationConfidenceTier.REFUSED


def _build_ambiguity_group(
    *,
    modification_name: str,
    candidate_site_indices: tuple[int, ...],
) -> str:
    if not candidate_site_indices:
        return f"{modification_name}:unassigned"
    return f"{modification_name}:" + "|".join(
        str(site_index) for site_index in candidate_site_indices
    )


def _localization_tier_note(
    *,
    tier: PtmLocalizationConfidenceTier,
    probability_source: PtmLocalizationProbabilitySource,
    supported_site_determining_ion_count: int,
) -> str:
    if tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE:
        if probability_source is PtmLocalizationProbabilitySource.REPORTED_PROBABILITY:
            return "high-confidence localization is supported by imported localization probability"
        return "high-confidence localization is supported by site-determining fragment ions"
    if tier is PtmLocalizationConfidenceTier.SUPPORTED:
        return (
            "localization is reviewable but remains short of high-confidence evidence"
        )
    if tier is PtmLocalizationConfidenceTier.AMBIGUOUS:
        if supported_site_determining_ion_count == 0:
            return (
                "localization remains unresolved across multiple candidate phosphosites"
            )
        return "localization has partial support but remains unresolved across candidate phosphosites"
    return "localization evidence remains too weak for site-level interpretation"


def render_ptm_localization_scoring_summary_tsv(
    report: PtmLocalizationScoringReport,
) -> str:
    """Render compact PTM localization-scoring summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entry_count",
            "ambiguous_entry_count",
            "confident_entry_count",
            "high_confidence_entry_count",
            "supported_entry_count",
            "refused_entry_count",
            "multi_phosphorylated_entry_count",
            "fragment_supported_entry_count",
        ]
    )
    writer.writerow(
        [
            len(report.entries),
            report.ambiguous_entry_count,
            report.confident_entry_count,
            report.high_confidence_entry_count,
            report.supported_entry_count,
            report.refused_entry_count,
            report.multi_phosphorylated_entry_count,
            report.fragment_supported_entry_count,
        ]
    )
    return buffer.getvalue()


def render_ptm_localization_scoring_entry_tsv(
    report: PtmLocalizationScoringReport,
) -> str:
    """Render PTM localization-scoring entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "spectrum_id",
            "sample_id",
            "localized_peptide",
            "canonical_peptide",
            "modification_name",
            "peptide_site_index",
            "candidate_site_indices",
            "ambiguity_group",
            "localization_score",
            "localization_probability",
            "probability_source",
            "localization_tier",
            "ambiguous",
            "multi_phosphorylated",
            "site_determining_ions",
            "supported_site_determining_ions",
            "note",
        ]
    )
    for entry in report.entries:
        writer.writerow(
            [
                entry.spectrum_id,
                entry.sample_id or "",
                entry.localized_peptide,
                entry.canonical_peptide,
                entry.modification_name,
                entry.peptide_site_index,
                ";".join(str(site) for site in entry.candidate_site_indices),
                entry.ambiguity_group,
                entry.localization_score,
                entry.localization_probability,
                entry.probability_source.value,
                entry.localization_tier.value,
                str(entry.ambiguous).lower(),
                str(entry.multi_phosphorylated).lower(),
                ";".join(entry.site_determining_ions),
                ";".join(entry.supported_site_determining_ions),
                entry.note,
            ]
        )
    return buffer.getvalue()


def _candidate_site_indices(
    *,
    record: PtmEvidenceRecord,
    modification: AppliedModification,
    candidate: ModificationLocalizationCandidate,
    same_name_count: int,
) -> tuple[int, ...]:
    for site_candidate in record.site_candidates:
        if (
            site_candidate.modification_name == modification.name
            and site_candidate.peptide_site_index == modification.site_index
        ):
            return site_candidate.candidate_site_indices or (modification.site_index,)
    if (
        same_name_count == 1
        and record.candidate_site_indices
        and modification.site_index in record.candidate_site_indices
    ):
        return record.candidate_site_indices
    if candidate.candidate_site_indices:
        return candidate.candidate_site_indices
    return (modification.site_index,) if modification.site_index is not None else ()


def _site_determining_ions(
    parsed: ParsedModifiedPeptide,
    *,
    modification_index: int,
    candidate_site_indices: tuple[int, ...],
    registry: ModificationRegistryDocument | None = None,
) -> tuple[str, ...]:
    modification = parsed.modifications[modification_index]
    if modification.site_index is None:
        return ()
    alternative_sites = _alternative_site_indices(
        parsed,
        modification_index=modification_index,
        candidate_site_indices=candidate_site_indices,
    )
    if not alternative_sites:
        return ()
    assigned_ions = _fragment_ion_mz_map(parsed, registry=registry)
    differing_by_alternative: list[set[str]] = []
    for site_index in alternative_sites:
        alternative = _localized_variant(
            parsed,
            modification_index=modification_index,
            new_site_index=site_index,
            registry=registry,
        )
        alternative_ions = _fragment_ion_mz_map(alternative, registry=registry)
        differing = {
            ion_label
            for ion_label, mz in assigned_ions.items()
            if ion_label in alternative_ions
            and abs(mz - alternative_ions[ion_label]) > 1e-9
        }
        differing_by_alternative.append(differing)
    if not differing_by_alternative:
        return ()
    return tuple(sorted(set.intersection(*differing_by_alternative)))


def _filter_candidate_site_indices(
    parsed: ParsedModifiedPeptide,
    *,
    modification_index: int,
    candidate_site_indices: tuple[int, ...],
    registry: ModificationRegistryDocument | None = None,
) -> tuple[int, ...]:
    valid_site_indices: list[int] = []
    for site_index in candidate_site_indices:
        try:
            _localized_variant(
                parsed,
                modification_index=modification_index,
                new_site_index=site_index,
                registry=registry,
            )
        except ValueError:
            continue
        valid_site_indices.append(site_index)
    return tuple(valid_site_indices)


def _alternative_site_indices(
    parsed: ParsedModifiedPeptide,
    *,
    modification_index: int,
    candidate_site_indices: tuple[int, ...],
) -> tuple[int, ...]:
    modification = parsed.modifications[modification_index]
    occupied_same_name = {
        candidate_modification.site_index
        for index, candidate_modification in enumerate(parsed.modifications)
        if index != modification_index
        and candidate_modification.name == modification.name
        and candidate_modification.site is ModificationPosition.ANYWHERE
        and candidate_modification.site_index is not None
    }
    return tuple(
        site_index
        for site_index in candidate_site_indices
        if site_index != modification.site_index
        and site_index not in occupied_same_name
    )


def _localized_variant(
    parsed: ParsedModifiedPeptide,
    *,
    modification_index: int,
    new_site_index: int,
    registry: ModificationRegistryDocument | None = None,
) -> ParsedModifiedPeptide:
    assignments = tuple(
        _assignment_for_modification(
            modification,
            override_site_index=new_site_index if index == modification_index else None,
        )
        for index, modification in enumerate(parsed.modifications)
    )
    return build_modified_peptide(
        parsed.sequence,
        assignments=assignments,
        registry=registry,
        at_protein_n_term=parsed.at_protein_n_term,
        at_protein_c_term=parsed.at_protein_c_term,
    )


def _assignment_for_modification(
    modification: AppliedModification,
    *,
    override_site_index: int | None = None,
) -> str:
    if modification.site is ModificationPosition.ANYWHERE:
        site = (
            override_site_index
            if override_site_index is not None
            else modification.site_index
        )
        if site is None:
            raise ValueError("residue-local modification is missing a site index")
        return f"{modification.name}@{site}"
    if modification.site is ModificationPosition.PEPTIDE_N_TERM:
        return f"{modification.name}@n-term"
    if modification.site is ModificationPosition.PROTEIN_N_TERM:
        return f"{modification.name}@protein-n-term"
    if modification.site is ModificationPosition.PEPTIDE_C_TERM:
        return f"{modification.name}@c-term"
    if modification.site is ModificationPosition.PROTEIN_C_TERM:
        return f"{modification.name}@protein-c-term"
    raise ValueError(f"unsupported modification site {modification.site!r}")


def _fragment_ion_mz_map(
    peptide: ParsedModifiedPeptide,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> dict[str, float]:
    ions = calculate_fragment_ions(
        peptide,
        registry=registry,
        series=(FragmentIonSeries.B, FragmentIonSeries.Y),
        charges=(1,),
        include_neutral_losses=False,
    )
    return {
        _ion_label(ion.series, ion.ordinal, ion.charge): ion.mz_monoisotopic
        for ion in ions
    }


def _ion_label(series: FragmentIonSeries, ordinal: int, charge: int) -> str:
    if charge == 1:
        return f"{series.value}{ordinal}"
    return f"{series.value}{ordinal}^{charge}"
