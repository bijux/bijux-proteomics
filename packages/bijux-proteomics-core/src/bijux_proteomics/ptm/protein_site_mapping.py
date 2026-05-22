# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM protein-site mapping and site-table review surfaces."""

from __future__ import annotations

from bijux_proteomics.chemistry import ModificationPosition, ModificationRegistryDocument
from bijux_proteomics.chemistry import parse_modified_peptide
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm.contracts import (
    PtmCoordinateValidationIssue,
    PtmCoordinateValidationReport,
    PtmEvidenceRecord,
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
        parsed = parse_modified_peptide(record.localized_peptide, registry=registry)
        shared_peptide = len(record.protein_refs) > 1
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
                            shared_peptide=shared_peptide,
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
                shared_peptide=any(mapping.shared_peptide for mapping in bucket),
            )
        )
    return tuple(entries)


def build_ptm_site_group_evidence(
    site_entries: tuple[PtmSiteEntry, ...],
) -> tuple[PtmSiteGroupEvidenceEntry, ...]:
    """Group PTM site evidence by candidate-position set when localization stays unresolved."""
    grouped: dict[tuple[str, str, tuple[int, ...]], list[PtmSiteEntry]] = {}
    for entry in site_entries:
        candidate_positions = (
            entry.candidate_positions
            if entry.candidate_positions
            else (entry.position,)
        )
        grouped.setdefault(
            (entry.protein_ref, entry.modification_name, candidate_positions),
            [],
        ).append(entry)

    group_entries: list[PtmSiteGroupEvidenceEntry] = []
    for (protein_ref, modification_name, candidate_positions), bucket in sorted(
        grouped.items()
    ):
        unresolved = len(candidate_positions) > 1 or any(
            entry.ambiguous for entry in bucket
        )
        positions_token = "|".join(str(position) for position in candidate_positions)
        note = (
            "site evidence remains unresolved across multiple candidate positions"
            if unresolved
            else "site evidence resolves to one protein position"
        )
        group_entries.append(
            PtmSiteGroupEvidenceEntry(
                group_key=f"{protein_ref}:{modification_name}:{positions_token}",
                protein_ref=protein_ref,
                modification_name=modification_name,
                candidate_positions=candidate_positions,
                site_keys=tuple(sorted(entry.site_key for entry in bucket)),
                spectrum_count=sum(entry.spectrum_count for entry in bucket),
                peptide_count=sum(entry.peptide_count for entry in bucket),
                sample_ids=tuple(
                    sorted(
                        {
                            sample_id
                            for entry in bucket
                            for sample_id in entry.sample_ids
                        }
                    )
                ),
                unresolved=unresolved,
                note=note,
            )
        )
    return tuple(group_entries)


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


def _find_occurrences(sequence: str, peptide_sequence: str) -> tuple[int, ...]:
    starts: list[int] = []
    offset = sequence.find(peptide_sequence)
    while offset != -1:
        starts.append(offset + 1)
        offset = sequence.find(peptide_sequence, offset + 1)
    return tuple(starts)
