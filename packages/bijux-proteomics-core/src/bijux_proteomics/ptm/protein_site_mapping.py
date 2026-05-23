# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM protein-site mapping and site-table review surfaces."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.chemistry import ModificationPosition, ModificationRegistryDocument
from bijux_proteomics.chemistry import parse_modified_peptide
from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.ptm.contracts import (
    PtmCoordinateValidationIssue,
    PtmCoordinateValidationReport,
    PtmEvidenceRecord,
    PtmEvidenceSiteCandidate,
    PtmProteinSiteMapping,
    PtmSiteAmbiguityEntry,
    PtmSiteCoverageEntry,
    PtmSiteEntry,
    PtmSiteGroupEvidenceEntry,
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
        shared_peptide = len(record.protein_refs) > 1
        site_candidates = _site_candidates_for_record(record, registry=registry)
        for protein_ref in record.protein_refs:
            sequence = protein_sequences.get(protein_ref)
            if sequence is None:
                continue
            starts = _find_occurrences(sequence, record.sequence)
            if not starts:
                continue
            for site_candidate in site_candidates:
                for start in starts:
                    protein_position = start + site_candidate.peptide_site_index - 1
                    candidate_positions = tuple(
                        start + site_index - 1
                        for site_index in site_candidate.candidate_site_indices
                    ) or (protein_position,)
                    mappings.append(
                        PtmProteinSiteMapping(
                            spectrum_id=record.spectrum_id,
                            sample_id=record.sample_id,
                            protein_ref=protein_ref,
                            localized_peptide=record.localized_peptide,
                            canonical_peptide=record.canonical_peptide,
                            sequence=record.sequence,
                            modification_name=site_candidate.modification_name,
                            residue=sequence[protein_position - 1],
                            peptide_site_index=site_candidate.peptide_site_index,
                            protein_position=protein_position,
                            localization_score=record.localization_score,
                            q_value=record.q_value,
                            target_decoy_label=record.target_decoy_label,
                            candidate_protein_positions=candidate_positions,
                            ambiguous=(len(candidate_positions) > 1 or len(starts) > 1),
                            shared_peptide=shared_peptide,
                            provenance=record.provenance,
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


def _site_candidates_for_record(
    record: PtmEvidenceRecord,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> tuple[PtmEvidenceSiteCandidate, ...]:
    if record.site_candidates:
        return record.site_candidates
    parsed = parse_modified_peptide(record.localized_peptide, registry=registry)
    site_candidates: list[PtmEvidenceSiteCandidate] = []
    for modification in parsed.modifications:
        if (
            modification.site is not ModificationPosition.ANYWHERE
            or modification.site_index is None
        ):
            continue
        site_candidates.append(
            PtmEvidenceSiteCandidate(
                modification_name=modification.name,
                controlled_id=modification.controlled_id,
                residue=parsed.sequence[modification.site_index - 1],
                peptide_site_index=modification.site_index,
                candidate_site_indices=record.candidate_site_indices
                or (modification.site_index,),
                site_kind=modification.site,
            )
        )
    return tuple(site_candidates)


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
                shared_peptide=any(mapping.shared_peptide for mapping in bucket),
                provenance=ImportedEvidenceProvenance.combine(
                    tuple(mapping.provenance for mapping in bucket),
                    original_identifiers={
                        "site_key": site_key,
                        "protein_ref": protein_ref,
                        "spectrum_ids": ";".join(
                            sorted({mapping.spectrum_id for mapping in bucket})
                        ),
                    },
                ),
            )
        )
    return tuple(entries)


def build_ptm_site_group_evidence(
    site_entries: tuple[PtmSiteEntry, ...],
) -> tuple[PtmSiteGroupEvidenceEntry, ...]:
    """Group PTM site evidence by candidate-position set when localization stays unresolved."""
    from bijux_proteomics.ptm.ambiguity_handling import (
        build_ptm_site_group_evidence as _build_ptm_site_group_evidence,
    )

    return _build_ptm_site_group_evidence(site_entries)


def build_ptm_site_ambiguity_report(
    site_entries: tuple[PtmSiteEntry, ...],
) -> tuple[PtmSiteAmbiguityEntry, ...]:
    """Report ambiguous PTM site assignments."""
    entries: list[PtmSiteAmbiguityEntry] = []
    for entry in site_entries:
        if not entry.ambiguous:
            continue
        if entry.shared_peptide:
            reason = "localized peptide is shared across multiple protein references"
        elif len(entry.candidate_positions) > 1:
            reason = "multiple candidate protein positions for the localized modification"
        else:
            reason = "localized peptide mapped to multiple candidate occurrences"
        entries.append(
            PtmSiteAmbiguityEntry(
                site_key=entry.site_key,
                protein_ref=entry.protein_ref,
                modification_name=entry.modification_name,
                candidate_positions=entry.candidate_positions,
                localized_peptides=entry.localized_peptides,
                reason=reason,
                shared_peptide=entry.shared_peptide,
            )
        )
    return tuple(entries)


def build_ptm_site_coverage_report(
    mappings: tuple[PtmProteinSiteMapping, ...],
) -> tuple[PtmSiteCoverageEntry, ...]:
    """Build site-level spectrum and peptide coverage summaries."""
    grouped: dict[str, list[PtmProteinSiteMapping]] = {}
    for mapping in mappings:
        site_key = (
            f"{mapping.protein_ref}:{mapping.residue}{mapping.protein_position}:"
            f"{mapping.modification_name}"
        )
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
            f"{mapping.protein_ref}:{mapping.residue}{mapping.protein_position}:"
            f"{mapping.modification_name}"
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
    return PtmCoordinateValidationReport(valid=not issues, issues=tuple(issues))


def render_ptm_protein_site_mapping_tsv(
    mappings: tuple[PtmProteinSiteMapping, ...],
) -> str:
    """Render peptide-level PTM protein-site mappings as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "spectrum_id",
            "sample_id",
            "protein_ref",
            "localized_peptide",
            "canonical_peptide",
            "modification_name",
            "residue",
            "peptide_site_index",
            "protein_position",
            "localization_score",
            "q_value",
            "candidate_protein_positions",
            "ambiguous",
            "shared_peptide",
            "target_decoy_label",
        ]
    )
    for mapping in sort_rows_by_fields(
        mappings,
        "protein_ref",
        "protein_position",
        "spectrum_id",
    ):
        writer.writerow(
            [
                mapping.spectrum_id,
                mapping.sample_id or "",
                mapping.protein_ref,
                mapping.localized_peptide,
                mapping.canonical_peptide,
                mapping.modification_name,
                mapping.residue,
                mapping.peptide_site_index,
                mapping.protein_position,
                mapping.localization_score,
                mapping.q_value if mapping.q_value is not None else "",
                ";".join(
                    str(position) for position in sorted(mapping.candidate_protein_positions)
                ),
                str(mapping.ambiguous).lower(),
                str(mapping.shared_peptide).lower(),
                mapping.target_decoy_label.value,
            ]
        )
    return buffer.getvalue()


def render_ptm_site_table_tsv(site_entries: tuple[PtmSiteEntry, ...]) -> str:
    """Render aggregated PTM site entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "localization_score",
            "best_q_value",
            "spectrum_count",
            "peptide_count",
            "sample_ids",
            "candidate_positions",
            "ambiguous",
            "shared_peptide",
            "target_decoy_label",
            *ImportedEvidenceProvenance.tsv_header(),
        ]
    )
    for entry in sort_rows_by_fields(site_entries, "site_key"):
        writer.writerow(
            [
                entry.site_key,
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                entry.localization_score,
                entry.best_q_value if entry.best_q_value is not None else "",
                entry.spectrum_count,
                entry.peptide_count,
                ";".join(sort_strings(entry.sample_ids)),
                ";".join(str(position) for position in sorted(entry.candidate_positions)),
                str(entry.ambiguous).lower(),
                str(entry.shared_peptide).lower(),
                entry.target_decoy_label.value,
                *entry.provenance.to_tsv_row(),
            ]
        )
    return buffer.getvalue()


def render_ptm_site_ambiguity_tsv(
    ambiguity_entries: tuple[PtmSiteAmbiguityEntry, ...],
) -> str:
    """Render PTM site ambiguity rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "site_key",
            "protein_ref",
            "modification_name",
            "candidate_positions",
            "localized_peptides",
            "shared_peptide",
            "reason",
        ]
    )
    for entry in sort_rows_by_fields(ambiguity_entries, "site_key"):
        writer.writerow(
            [
                entry.site_key,
                entry.protein_ref,
                entry.modification_name,
                ";".join(str(position) for position in sorted(entry.candidate_positions)),
                ";".join(sort_strings(entry.localized_peptides)),
                str(entry.shared_peptide).lower(),
                entry.reason,
            ]
        )
    return buffer.getvalue()


def render_ptm_site_coverage_tsv(coverage_entries: tuple[PtmSiteCoverageEntry, ...]) -> str:
    """Render PTM site coverage rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "site_key",
            "spectrum_count",
            "peptide_count",
            "sample_count",
            "spectra",
            "peptides",
        ]
    )
    for entry in sort_rows_by_fields(coverage_entries, "site_key"):
        writer.writerow(
            [
                entry.site_key,
                entry.spectrum_count,
                entry.peptide_count,
                entry.sample_count,
                ";".join(sort_strings(entry.spectra)),
                ";".join(sort_strings(entry.peptides)),
            ]
        )
    return buffer.getvalue()


def render_ptm_coordinate_validation_tsv(
    report: PtmCoordinateValidationReport,
) -> str:
    """Render PTM coordinate validation issues as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(["spectrum_id", "protein_ref", "site_key", "code", "message"])
    for issue in sort_rows_by_fields(
        report.issues,
        "spectrum_id",
        "protein_ref",
        "site_key",
        "code",
    ):
        writer.writerow(
            [
                issue.spectrum_id,
                issue.protein_ref,
                issue.site_key,
                issue.code,
                issue.message,
            ]
        )
    return buffer.getvalue()


def _find_occurrences(sequence: str, peptide_sequence: str) -> tuple[int, ...]:
    starts: list[int] = []
    offset = sequence.find(peptide_sequence)
    while offset != -1:
        starts.append(offset + 1)
        offset = sequence.find(peptide_sequence, offset + 1)
    return tuple(starts)
