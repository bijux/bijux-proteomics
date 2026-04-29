# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""PTM site, localization, and occupancy contracts."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import (
    ModificationPosition,
    ModificationRegistryDocument,
    build_modification_localization_advisory,
    parse_modified_peptide,
)
from bijux_proteomics.identification import (
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    parse_target_decoy_label,
)
from bijux_proteomics.quantification import Ms1FeatureRecord
from bijux_proteomics_foundation import JsonModel


class PtmLocalizationColumnMapping(JsonModel):
    """Mapping from engine columns to normalized PTM evidence."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    charge: str = Field(..., min_length=1)
    score: str = Field(..., min_length=1)
    protein_refs: str = Field(..., min_length=1)
    localization_score: str = Field(..., min_length=1)
    q_value: str | None = None
    sample_id: str | None = None
    candidate_sites: str | None = None
    decoy_label: str | None = None
    protein_separator: str = ";"
    site_separator: str = ";"


class PtmValidationIssue(JsonModel):
    """One PTM parsing or mapping validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=2)


class RejectedPtmEvidenceRow(JsonModel):
    """One rejected PTM evidence row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[PtmValidationIssue, ...] = Field(default_factory=tuple)


class PtmEvidenceRecord(JsonModel):
    """One normalized PTM evidence record from search-style output."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
    localization_score: float = Field(..., ge=0.0)
    candidate_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)


class PtmEvidenceParseReport(JsonModel):
    """Stable parse report for PTM localization evidence."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PtmEvidenceRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPtmEvidenceRow, ...] = Field(default_factory=tuple)
    column_mapping: PtmLocalizationColumnMapping


class PtmProteinSiteMapping(JsonModel):
    """One peptide-localized PTM mapped onto a protein site."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    protein_ref: str = Field(..., min_length=1)
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    peptide_site_index: int = Field(..., ge=1)
    protein_position: int = Field(..., ge=1)
    localization_score: float = Field(..., ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
    candidate_protein_positions: tuple[int, ...] = Field(default_factory=tuple)
    ambiguous: bool = False


class PtmCoordinateValidationIssue(JsonModel):
    """One PTM coordinate validation issue over peptide and protein mappings."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    site_key: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PtmCoordinateValidationReport(JsonModel):
    """Validation result for PTM peptide/protein coordinate consistency."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    issues: tuple[PtmCoordinateValidationIssue, ...] = Field(default_factory=tuple)


class PtmSiteEntry(JsonModel):
    """One aggregated PTM site row."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    position: int = Field(..., ge=1)
    modification_name: str = Field(..., min_length=1)
    localization_score: float = Field(..., ge=0.0)
    best_q_value: float | None = Field(default=None, ge=0.0)
    spectrum_count: int = Field(..., ge=1)
    peptide_count: int = Field(..., ge=1)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    ambiguous: bool = False


class PtmSiteAmbiguityEntry(JsonModel):
    """One PTM site ambiguity record."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    reason: str = Field(..., min_length=1)


class PtmSiteCoverageEntry(JsonModel):
    """Site-level coverage summary."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    spectrum_count: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    spectra: tuple[str, ...] = Field(default_factory=tuple)
    peptides: tuple[str, ...] = Field(default_factory=tuple)


class PtmSiteFdrEntry(JsonModel):
    """One PTM site with cumulative FDR state."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    localization_score: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    fdr: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)
    accepted: bool
    target_decoy_label: TargetDecoyLabel


class PtmSiteFdrReport(JsonModel):
    """Stable site-level PTM FDR report."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0)
    entries: tuple[PtmSiteFdrEntry, ...] = Field(default_factory=tuple)


class PtmOccupancyEntry(JsonModel):
    """One site occupancy estimate for one sample."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    modified_intensity: float = Field(..., ge=0.0)
    unmodified_intensity: float = Field(..., ge=0.0)
    occupancy_fraction: float | None = Field(default=None, ge=0.0, le=1.0)


class PtmEnrichmentInput(JsonModel):
    """Stable site list and background list for PTM enrichment workflows."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    site_ids: tuple[str, ...] = Field(default_factory=tuple)
    background_ids: tuple[str, ...] = Field(default_factory=tuple)


class PtmMotifWindow(JsonModel):
    """One motif window around a PTM site."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    window: str = Field(..., min_length=1)
    center_index: int = Field(..., ge=1)
    flank_size: int = Field(..., ge=0)


def _parse_protein_refs(raw_value: str, separator: str) -> tuple[str, ...]:
    refs = tuple(token.strip() for token in raw_value.split(separator) if token.strip())
    return tuple(dict.fromkeys(refs))


def _row_issue(code: str, message: str, row_number: int) -> PtmValidationIssue:
    return PtmValidationIssue(code=code, message=message, row_number=row_number)


def _localization_candidates_from_field(value: str, separator: str) -> tuple[int, ...]:
    if not value.strip():
        return ()
    indices: list[int] = []
    for token in value.split(separator):
        normalized = token.strip()
        if not normalized:
            continue
        indices.append(int(normalized))
    return tuple(dict.fromkeys(indices))


def _find_occurrences(sequence: str, peptide_sequence: str) -> tuple[int, ...]:
    starts: list[int] = []
    offset = sequence.find(peptide_sequence)
    while offset != -1:
        starts.append(offset + 1)
        offset = sequence.find(peptide_sequence, offset + 1)
    return tuple(starts)


def parse_ptm_localization_tsv(
    path: Path,
    *,
    mapping: PtmLocalizationColumnMapping | None = None,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
    registry: ModificationRegistryDocument | None = None,
) -> PtmEvidenceParseReport:
    """Parse one PTM localization table into normalized evidence records."""
    active_mapping = mapping or PtmLocalizationColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        protein_refs="proteins",
        localization_score="localization_score",
        q_value="q_value",
        sample_id="sample_id",
        candidate_sites="candidate_sites",
        decoy_label="decoy_label",
    )
    active_decoy_policy = decoy_policy or TargetDecoyLabelPolicy()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("PTM evidence TSV must include a header row")
        required = (
            active_mapping.spectrum_id,
            active_mapping.peptide,
            active_mapping.charge,
            active_mapping.score,
            active_mapping.protein_refs,
            active_mapping.localization_score,
        )
        for required_column in required:
            if required_column not in reader.fieldnames:
                raise ValueError(
                    f"missing required PTM evidence column {required_column!r}"
                )

        accepted: list[PtmEvidenceRecord] = []
        rejected: list[RejectedPtmEvidenceRow] = []
        for row_number, row in enumerate(reader, start=2):
            raw_fields = {
                str(key): str(value or "")
                for key, value in row.items()
                if key is not None
            }
            issues: list[PtmValidationIssue] = []
            spectrum_id = raw_fields.get(active_mapping.spectrum_id, "").strip()
            peptide = raw_fields.get(active_mapping.peptide, "").strip()
            if not spectrum_id:
                issues.append(
                    _row_issue(
                        "missing_spectrum_id", "missing spectrum identifier", row_number
                    )
                )
            if not peptide:
                issues.append(
                    _row_issue(
                        "missing_peptide", "missing localized peptide", row_number
                    )
                )
            try:
                charge = int(raw_fields.get(active_mapping.charge, "").strip())
                if charge < 1:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue("invalid_charge", "invalid charge value", row_number)
                )
                charge = 0
            try:
                score = float(raw_fields.get(active_mapping.score, "").strip())
            except ValueError:
                issues.append(
                    _row_issue("invalid_score", "invalid score value", row_number)
                )
                score = 0.0
            try:
                localization_score = float(
                    raw_fields.get(active_mapping.localization_score, "").strip()
                )
                if localization_score < 0:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_localization_score",
                        "invalid localization score",
                        row_number,
                    )
                )
                localization_score = 0.0

            q_value: float | None = None
            if active_mapping.q_value:
                q_token = raw_fields.get(active_mapping.q_value, "").strip()
                if q_token:
                    try:
                        q_value = float(q_token)
                        if q_value < 0:
                            raise ValueError
                    except ValueError:
                        issues.append(
                            _row_issue("invalid_q_value", "invalid q-value", row_number)
                        )

            protein_refs = _parse_protein_refs(
                raw_fields.get(active_mapping.protein_refs, ""),
                active_mapping.protein_separator,
            )
            if not protein_refs:
                issues.append(
                    _row_issue(
                        "missing_protein_refs", "missing protein references", row_number
                    )
                )

            try:
                parsed = parse_modified_peptide(peptide, registry=registry)
            except ValueError as exc:
                issues.append(
                    _row_issue("invalid_modified_peptide", str(exc), row_number)
                )
                parsed = None

            candidate_sites: tuple[int, ...] = ()
            if active_mapping.candidate_sites:
                candidate_token = raw_fields.get(active_mapping.candidate_sites, "")
                try:
                    candidate_sites = _localization_candidates_from_field(
                        candidate_token,
                        active_mapping.site_separator,
                    )
                except ValueError:
                    issues.append(
                        _row_issue(
                            "invalid_candidate_sites",
                            "candidate sites must be integers",
                            row_number,
                        )
                    )

            modification_names: tuple[str, ...] = ()
            if parsed is not None:
                modification_names = tuple(
                    dict.fromkeys(
                        modification.name
                        for modification in parsed.modifications
                        if modification.site is ModificationPosition.ANYWHERE
                    )
                )
                if not modification_names:
                    issues.append(
                        _row_issue(
                            "missing_internal_modification",
                            "PTM evidence requires at least one residue-localized modification",
                            row_number,
                        )
                    )
                if not candidate_sites:
                    advisory = build_modification_localization_advisory(
                        parsed, registry=registry
                    )
                    for candidate in advisory.candidates:
                        if candidate.assigned_site_index is not None:
                            candidate_sites = candidate.candidate_site_indices
                            break

            if issues or parsed is None:
                rejected.append(
                    RejectedPtmEvidenceRow(
                        row_number=row_number,
                        raw_fields=raw_fields,
                        issues=tuple(issues),
                    )
                )
                continue

            accepted.append(
                PtmEvidenceRecord(
                    spectrum_id=spectrum_id,
                    sample_id=raw_fields.get(active_mapping.sample_id, "").strip()
                    or None
                    if active_mapping.sample_id
                    else None,
                    localized_peptide=peptide,
                    canonical_peptide=parsed.canonical_notation,
                    sequence=parsed.sequence,
                    charge=charge,
                    score=score,
                    q_value=q_value,
                    protein_refs=protein_refs,
                    target_decoy_label=parse_target_decoy_label(
                        protein_refs=protein_refs,
                        explicit_label=raw_fields.get(active_mapping.decoy_label)
                        if active_mapping.decoy_label
                        else None,
                        policy=active_decoy_policy,
                    ),
                    localization_score=localization_score,
                    candidate_site_indices=candidate_sites,
                    modification_names=modification_names,
                )
            )

    accepted = sorted(
        accepted,
        key=lambda record: (
            record.sample_id or "",
            record.spectrum_id,
            -record.localization_score,
            record.canonical_peptide,
        ),
    )
    return PtmEvidenceParseReport(
        total_rows=len(accepted) + len(rejected),
        accepted_records=tuple(accepted),
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
    )


def map_ptm_evidence_to_protein_sites(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    protein_sequences: dict[str, str],
    registry: ModificationRegistryDocument | None = None,
) -> tuple[PtmProteinSiteMapping, ...]:
    """Map residue-localized modified peptides onto protein coordinates."""
    mappings: list[PtmProteinSiteMapping] = []
    for record in records:
        parsed = parse_modified_peptide(record.localized_peptide, registry=registry)
        for protein_ref in record.protein_refs:
            sequence = protein_sequences.get(protein_ref)
            if sequence is None:
                continue
            starts = _find_occurrences(sequence, parsed.sequence)
            if not starts:
                continue
            for modification in parsed.modifications:
                if (
                    modification.site is not ModificationPosition.ANYWHERE
                    or modification.site_index is None
                ):
                    continue
                for start in starts:
                    protein_position = start + modification.site_index - 1
                    candidate_positions = tuple(
                        start + site_index - 1
                        for site_index in record.candidate_site_indices
                    ) or (protein_position,)
                    mappings.append(
                        PtmProteinSiteMapping(
                            spectrum_id=record.spectrum_id,
                            sample_id=record.sample_id,
                            protein_ref=protein_ref,
                            localized_peptide=record.localized_peptide,
                            canonical_peptide=record.canonical_peptide,
                            sequence=record.sequence,
                            modification_name=modification.name,
                            residue=sequence[protein_position - 1],
                            peptide_site_index=modification.site_index,
                            protein_position=protein_position,
                            localization_score=record.localization_score,
                            q_value=record.q_value,
                            target_decoy_label=record.target_decoy_label,
                            candidate_protein_positions=candidate_positions,
                            ambiguous=(len(candidate_positions) > 1 or len(starts) > 1),
                        )
                    )
    return tuple(
        sorted(
            mappings,
            key=lambda mapping: (
                mapping.protein_ref,
                mapping.protein_position,
                -mapping.localization_score,
                mapping.spectrum_id,
            ),
        )
    )


def build_ptm_site_table(
    mappings: tuple[PtmProteinSiteMapping, ...],
) -> tuple[PtmSiteEntry, ...]:
    """Aggregate peptide-level PTM mappings into site-level entries."""
    grouped: dict[tuple[str, int, str], list[PtmProteinSiteMapping]] = {}
    for mapping in mappings:
        grouped.setdefault(
            (mapping.protein_ref, mapping.protein_position, mapping.modification_name),
            [],
        ).append(mapping)

    entries: list[PtmSiteEntry] = []
    for (protein_ref, protein_position, modification_name), bucket in sorted(
        grouped.items()
    ):
        best_score = max(mapping.localization_score for mapping in bucket)
        q_values = [
            mapping.q_value for mapping in bucket if mapping.q_value is not None
        ]
        residue = bucket[0].residue
        site_key = f"{protein_ref}:{residue}{protein_position}:{modification_name}"
        entries.append(
            PtmSiteEntry(
                site_key=site_key,
                protein_ref=protein_ref,
                residue=residue,
                position=protein_position,
                modification_name=modification_name,
                localization_score=best_score,
                best_q_value=min(q_values) if q_values else None,
                spectrum_count=len({mapping.spectrum_id for mapping in bucket}),
                peptide_count=len({mapping.canonical_peptide for mapping in bucket}),
                localized_peptides=tuple(
                    sorted({mapping.localized_peptide for mapping in bucket})
                ),
                sample_ids=tuple(
                    sorted(
                        {mapping.sample_id for mapping in bucket if mapping.sample_id}
                    )
                ),
                target_decoy_label=max(
                    (mapping.target_decoy_label for mapping in bucket),
                    key=lambda label: (
                        3
                        if label is TargetDecoyLabel.DECOY
                        else 2
                        if label is TargetDecoyLabel.MIXED
                        else 1
                        if label is TargetDecoyLabel.TARGET
                        else 0
                    ),
                ),
                candidate_positions=tuple(
                    sorted(
                        {
                            position
                            for mapping in bucket
                            for position in mapping.candidate_protein_positions
                        }
                    )
                ),
                ambiguous=any(mapping.ambiguous for mapping in bucket),
            )
        )
    return tuple(entries)


def build_ptm_site_ambiguity_report(
    site_entries: tuple[PtmSiteEntry, ...],
) -> tuple[PtmSiteAmbiguityEntry, ...]:
    """Report ambiguous PTM site assignments."""
    return tuple(
        PtmSiteAmbiguityEntry(
            site_key=entry.site_key,
            protein_ref=entry.protein_ref,
            modification_name=entry.modification_name,
            candidate_positions=entry.candidate_positions,
            localized_peptides=entry.localized_peptides,
            reason="multiple candidate protein positions for the localized modification"
            if len(entry.candidate_positions) > 1
            else "localized peptide mapped to multiple candidate occurrences",
        )
        for entry in site_entries
        if entry.ambiguous
    )


def build_ptm_site_coverage_report(
    mappings: tuple[PtmProteinSiteMapping, ...],
) -> tuple[PtmSiteCoverageEntry, ...]:
    """Build site-level spectrum and peptide coverage summaries."""
    grouped: dict[str, list[PtmProteinSiteMapping]] = {}
    for mapping in mappings:
        site_key = f"{mapping.protein_ref}:{mapping.residue}{mapping.protein_position}:{mapping.modification_name}"
        grouped.setdefault(site_key, []).append(mapping)
    return tuple(
        PtmSiteCoverageEntry(
            site_key=site_key,
            spectrum_count=len({mapping.spectrum_id for mapping in bucket}),
            peptide_count=len({mapping.canonical_peptide for mapping in bucket}),
            sample_count=len(
                {mapping.sample_id for mapping in bucket if mapping.sample_id}
            ),
            spectra=tuple(sorted({mapping.spectrum_id for mapping in bucket})),
            peptides=tuple(sorted({mapping.localized_peptide for mapping in bucket})),
        )
        for site_key, bucket in sorted(grouped.items())
    )


def validate_ptm_site_coordinates(
    mappings: tuple[PtmProteinSiteMapping, ...],
    *,
    protein_sequences: dict[str, str],
) -> PtmCoordinateValidationReport:
    """Validate that peptide-localized PTM coordinates agree with protein mappings."""
    issues: list[PtmCoordinateValidationIssue] = []
    for mapping in mappings:
        sequence = protein_sequences.get(mapping.protein_ref)
        site_key = (
            f"{mapping.protein_ref}:{mapping.residue}{mapping.protein_position}:{mapping.modification_name}"
        )
        if sequence is None:
            issues.append(
                PtmCoordinateValidationIssue(
                    spectrum_id=mapping.spectrum_id,
                    protein_ref=mapping.protein_ref,
                    site_key=site_key,
                    code="missing_protein_sequence",
                    message="protein sequence is required for PTM coordinate validation",
                )
            )
            continue
        if mapping.peptide_site_index > len(mapping.sequence):
            issues.append(
                PtmCoordinateValidationIssue(
                    spectrum_id=mapping.spectrum_id,
                    protein_ref=mapping.protein_ref,
                    site_key=site_key,
                    code="peptide_site_out_of_range",
                    message="peptide-localized site index exceeds the peptide sequence length",
                )
            )
            continue
        if mapping.protein_position > len(sequence):
            issues.append(
                PtmCoordinateValidationIssue(
                    spectrum_id=mapping.spectrum_id,
                    protein_ref=mapping.protein_ref,
                    site_key=site_key,
                    code="protein_position_out_of_range",
                    message="mapped protein position exceeds the protein sequence length",
                )
            )
            continue
        peptide_residue = mapping.sequence[mapping.peptide_site_index - 1]
        protein_residue = sequence[mapping.protein_position - 1]
        if peptide_residue != mapping.residue or protein_residue != mapping.residue:
            issues.append(
                PtmCoordinateValidationIssue(
                    spectrum_id=mapping.spectrum_id,
                    protein_ref=mapping.protein_ref,
                    site_key=site_key,
                    code="residue_mismatch",
                    message="peptide, mapping, and protein residues do not agree at the localized site",
                )
            )
        for candidate_position in mapping.candidate_protein_positions:
            if candidate_position < 1 or candidate_position > len(sequence):
                issues.append(
                    PtmCoordinateValidationIssue(
                        spectrum_id=mapping.spectrum_id,
                        protein_ref=mapping.protein_ref,
                        site_key=site_key,
                        code="candidate_position_out_of_range",
                        message="candidate protein position falls outside the protein sequence",
                    )
                )
    return PtmCoordinateValidationReport(
        valid=not issues,
        issues=tuple(issues),
    )


def build_ptm_site_fdr(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    threshold: float = 0.01,
) -> PtmSiteFdrReport:
    """Compute a simple target-decoy FDR over PTM sites."""
    ranked = sorted(
        site_entries,
        key=lambda entry: (
            -entry.localization_score,
            entry.best_q_value if entry.best_q_value is not None else float("inf"),
            entry.site_key,
        ),
    )
    interim: list[PtmSiteFdrEntry] = []
    target_count = 0
    decoy_count = 0
    for rank, entry in enumerate(ranked, start=1):
        if entry.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_count += 1
        else:
            target_count += 1
        fdr = decoy_count / max(target_count, 1)
        interim.append(
            PtmSiteFdrEntry(
                site_key=entry.site_key,
                localization_score=entry.localization_score,
                q_value=0.0,
                fdr=fdr,
                rank=rank,
                accepted=False,
                target_decoy_label=entry.target_decoy_label,
            )
        )
    running = 1.0
    finalized: list[PtmSiteFdrEntry] = []
    for fdr_entry in reversed(interim):
        running = min(running, fdr_entry.fdr)
        q_value = running
        finalized.append(
            fdr_entry.model_copy(
                update={
                    "q_value": q_value,
                    "accepted": q_value <= threshold,
                }
            )
        )
    return PtmSiteFdrReport(threshold=threshold, entries=tuple(reversed(finalized)))


def estimate_ptm_site_occupancy(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    feature_records: tuple[Ms1FeatureRecord, ...],
) -> tuple[PtmOccupancyEntry, ...]:
    """Estimate sample-level occupancy from modified and unmodified peptide intensities."""
    feature_by_sample: dict[str, list[Ms1FeatureRecord]] = {}
    for record in feature_records:
        feature_by_sample.setdefault(record.sample_id, []).append(record)

    occupancy_entries: list[PtmOccupancyEntry] = []
    for entry in site_entries:
        if not entry.sample_ids:
            continue
        for sample_id in entry.sample_ids:
            numerator = 0.0
            denominator_unmodified = 0.0
            sample_records = feature_by_sample.get(sample_id, [])
            localized_peptides = set(entry.localized_peptides)
            stripped_sequences = {
                parse_modified_peptide(peptide).sequence
                for peptide in entry.localized_peptides
            }
            for record in sample_records:
                if (
                    entry.protein_ref not in record.protein_refs
                    or record.intensity is None
                ):
                    continue
                if record.canonical_peptide in localized_peptides:
                    numerator += record.intensity
                elif record.canonical_peptide in stripped_sequences:
                    denominator_unmodified += record.intensity
            total = numerator + denominator_unmodified
            occupancy_entries.append(
                PtmOccupancyEntry(
                    site_key=entry.site_key,
                    sample_id=sample_id,
                    modified_intensity=numerator,
                    unmodified_intensity=denominator_unmodified,
                    occupancy_fraction=(numerator / total) if total > 0 else None,
                )
            )
    return tuple(
        sorted(occupancy_entries, key=lambda entry: (entry.site_key, entry.sample_id))
    )


def build_ptm_enrichment_input(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    modification_name: str = "Phospho",
) -> PtmEnrichmentInput:
    """Build foreground and background site lists for PTM enrichment."""
    site_ids = tuple(
        entry.site_key
        for entry in site_entries
        if entry.modification_name == modification_name
        and entry.target_decoy_label is not TargetDecoyLabel.DECOY
    )
    background: list[str] = []
    for protein_ref, sequence in sorted(protein_sequences.items()):
        for index, residue in enumerate(sequence, start=1):
            if residue in {"S", "T", "Y"}:
                background.append(f"{protein_ref}:{residue}{index}")
    return PtmEnrichmentInput(
        modification_name=modification_name,
        site_ids=tuple(site_ids),
        background_ids=tuple(background),
    )


def build_ptm_motif_windows(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    flank_size: int = 7,
) -> tuple[PtmMotifWindow, ...]:
    """Extract +/- N residue motif windows around PTM sites."""
    windows: list[PtmMotifWindow] = []
    for entry in site_entries:
        sequence = protein_sequences.get(entry.protein_ref)
        if sequence is None:
            continue
        start = max(1, entry.position - flank_size)
        end = min(len(sequence), entry.position + flank_size)
        window = sequence[start - 1 : end]
        windows.append(
            PtmMotifWindow(
                site_key=entry.site_key,
                protein_ref=entry.protein_ref,
                window=window,
                center_index=entry.position - start + 1,
                flank_size=flank_size,
            )
        )
    return tuple(windows)
