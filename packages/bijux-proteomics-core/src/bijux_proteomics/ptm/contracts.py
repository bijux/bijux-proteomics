# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""PTM site, localization, and occupancy contracts."""

from __future__ import annotations

import csv
from enum import StrEnum
from importlib import import_module
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import (
    ModificationPosition,
    ModificationRegistryDocument,
    build_modification_localization_advisory,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    PTMSite as CanonicalPtmSite,
    RejectedEvidence as CanonicalRejectedEvidence,
)
from bijux_proteomics.identification import (
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    parse_target_decoy_label,
)
from bijux_proteomics.ptm.peptide_parser import parse_ptm_peptide
from bijux_proteomics.quantification import Ms1FeatureRecord
from bijux_proteomics._scientific_tables import (
    ScientificTableValidationIssue,
    build_ptm_evidence_schema,
    validate_scientific_table,
)
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
    localization_probability: str | None = None
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

    def to_domain_record(self) -> CanonicalRejectedEvidence:
        """Expose one rejected PTM evidence row as canonical rejected evidence."""

        return CanonicalRejectedEvidence(
            record_kind="ptm_evidence",
            rejection_reason="; ".join(issue.message for issue in self.issues)
            or "rejected ptm evidence row",
            row_number=self.row_number,
            raw_fields=self.raw_fields,
            metadata={
                "source_contract": "ptm.rejected_evidence_row",
                "issue_codes": ";".join(issue.code for issue in self.issues),
            },
        )


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
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
    localization_score: float = Field(..., ge=0.0)
    candidate_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)
    site_candidates: tuple["PtmEvidenceSiteCandidate", ...] = Field(default_factory=tuple)
    provenance: ImportedEvidenceProvenance


class PtmEvidenceSiteCandidate(JsonModel):
    """One localized PTM site candidate preserved inside one evidence row."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    controlled_id: str | None = None
    residue: str = Field(..., min_length=1, max_length=1)
    peptide_site_index: int = Field(..., ge=1)
    candidate_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    site_kind: ModificationPosition


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
    shared_peptide: bool = False
    provenance: ImportedEvidenceProvenance


class PtmUnmappedPeptideEntry(JsonModel):
    """One localized PTM peptide site that could not be placed onto protein coordinates."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    modification_name: str = Field(..., min_length=1)
    residue: str = Field(..., min_length=1, max_length=1)
    peptide_site_index: int = Field(..., ge=1)
    candidate_site_indices: tuple[int, ...] = Field(default_factory=tuple)
    reason_code: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)
    provenance: ImportedEvidenceProvenance


class PtmProteinSiteMappingReport(JsonModel):
    """Stable PTM protein-site mapping report with explicit ambiguity and miss ledgers."""

    model_config = ConfigDict(extra="forbid")

    mappings: tuple[PtmProteinSiteMapping, ...] = Field(default_factory=tuple)
    exact_mappings: tuple[PtmProteinSiteMapping, ...] = Field(default_factory=tuple)
    ambiguous_mappings: tuple[PtmProteinSiteMapping, ...] = Field(default_factory=tuple)
    unmapped_peptides: tuple[PtmUnmappedPeptideEntry, ...] = Field(default_factory=tuple)


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
    shared_peptide: bool = False
    provenance: ImportedEvidenceProvenance

    def to_domain_record(self) -> CanonicalPtmSite:
        """Convert one PTM site row into the canonical domain site record."""

        return CanonicalPtmSite(
            site_key=self.site_key,
            protein_ref=self.protein_ref,
            residue=self.residue,
            position=self.position,
            modification_name=self.modification_name,
            localized_peptides=self.localized_peptides,
            sample_ids=self.sample_ids,
            localization_score=self.localization_score,
            q_value=self.best_q_value,
            ambiguous=self.ambiguous,
            candidate_positions=self.candidate_positions,
            metadata={
                "source_contract": "ptm.site_entry",
                "spectrum_count": str(self.spectrum_count),
                "peptide_count": str(self.peptide_count),
                "shared_peptide": str(self.shared_peptide).lower(),
                "target_decoy_state": self.target_decoy_label.value,
                **self.provenance.to_metadata_fields(),
            },
        )

_SITE_GROUPS_MODULE = import_module("bijux_proteomics.ptm.sites.site_groups")
PtmSiteGroupEvidenceEntry = _SITE_GROUPS_MODULE.PtmSiteGroupEvidenceEntry


class PtmSiteAmbiguityEntry(JsonModel):
    """One PTM site ambiguity record."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    modification_name: str = Field(..., min_length=1)
    candidate_positions: tuple[int, ...] = Field(default_factory=tuple)
    localized_peptides: tuple[str, ...] = Field(default_factory=tuple)
    reason: str = Field(..., min_length=1)
    shared_peptide: bool = False


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


class PtmOccupancyUncertainty(StrEnum):
    """Uncertainty states for PTM occupancy estimates."""

    NONE = "none"
    MISSING_COUNTERPART = "missing_counterpart"
    AMBIGUOUS_SITE = "ambiguous_site"


class PtmOccupancyConfidenceTier(StrEnum):
    """Confidence tier for one PTM occupancy proxy estimate."""

    HIGH_CONFIDENCE = "high_confidence"
    MISSING_UNMODIFIED_EVIDENCE = "missing_unmodified_evidence"
    MISSING_MODIFIED_EVIDENCE = "missing_modified_evidence"
    AMBIGUOUS_SITE = "ambiguous_site"


class PtmOccupancyEntry(JsonModel):
    """One site occupancy estimate for one sample."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    modified_intensity: float = Field(..., ge=0.0)
    unmodified_intensity: float = Field(..., ge=0.0)
    occupancy_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_tier: PtmOccupancyConfidenceTier = (
        PtmOccupancyConfidenceTier.HIGH_CONFIDENCE
    )
    uncertainty: PtmOccupancyUncertainty = PtmOccupancyUncertainty.NONE
    modified_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unmodified_peptides: tuple[str, ...] = Field(default_factory=tuple)
    modified_feature_count: int = Field(default=0, ge=0)
    unmodified_feature_count: int = Field(default=0, ge=0)
    note: str = Field(..., min_length=1)


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


class PtmMotifBackgroundEntry(JsonModel):
    """Foreground/background residue counts for PTM motif interpretation."""

    model_config = ConfigDict(extra="forbid")

    residue: str = Field(..., min_length=1, max_length=1)
    foreground_site_count: int = Field(..., ge=0)
    background_site_count: int = Field(..., ge=0)


class PtmMotifBackgroundReport(JsonModel):
    """Residue background report for one PTM modification class."""

    model_config = ConfigDict(extra="forbid")

    modification_name: str = Field(..., min_length=1)
    background_mode: str = Field(..., min_length=1)
    total_foreground_sites: int = Field(..., ge=0)
    total_background_sites: int = Field(..., ge=0)
    entries: tuple[PtmMotifBackgroundEntry, ...] = Field(default_factory=tuple)


def _parse_protein_refs(raw_value: str, separator: str) -> tuple[str, ...]:
    refs = tuple(token.strip() for token in raw_value.split(separator) if token.strip())
    return tuple(dict.fromkeys(refs))


def _row_issue(code: str, message: str, row_number: int) -> PtmValidationIssue:
    return PtmValidationIssue(code=code, message=message, row_number=row_number)


def _ptm_issues_from_scientific_issues(
    issues: tuple[ScientificTableValidationIssue, ...],
) -> tuple[PtmValidationIssue, ...]:
    translated: list[PtmValidationIssue] = []
    for issue in issues:
        if issue.code == "missing_value":
            if issue.column == "spectrum_id":
                translated.append(
                    _row_issue(
                        "missing_spectrum_id",
                        "missing spectrum identifier",
                        issue.row_number,
                    )
                )
                continue
            if issue.column == "peptide":
                translated.append(
                    _row_issue(
                        "missing_peptide",
                        "missing localized peptide",
                        issue.row_number,
                    )
                )
                continue
            if issue.column == "protein_refs":
                translated.append(
                    _row_issue(
                        "missing_protein_refs",
                        "missing protein references",
                        issue.row_number,
                    )
                )
                continue
        if issue.code == "wrong_type":
            if issue.column == "charge":
                translated.append(
                    _row_issue("invalid_charge", "invalid charge value", issue.row_number)
                )
                continue
            if issue.column == "score":
                translated.append(
                    _row_issue("invalid_score", "invalid score value", issue.row_number)
                )
                continue
        translated.append(_row_issue(issue.code, issue.message, issue.row_number))
    return tuple(translated)


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


def _site_candidate_indices(
    *,
    site_index: int,
    candidate_site_indices: tuple[int, ...],
    advisory_candidate_indices: tuple[int, ...],
    same_name_count: int,
) -> tuple[int, ...]:
    if (
        same_name_count == 1
        and candidate_site_indices
        and site_index in candidate_site_indices
    ):
        return candidate_site_indices
    if advisory_candidate_indices:
        return advisory_candidate_indices
    return (site_index,)


def _build_ptm_evidence_site_candidates(
    *,
    parsed_sites: tuple,
    parsed_modifications: tuple,
    advisory_candidates: tuple,
    candidate_site_indices: tuple[int, ...],
) -> tuple[PtmEvidenceSiteCandidate, ...]:
    same_name_counts: dict[str, int] = {}
    for site in parsed_sites:
        if site.site_kind is ModificationPosition.ANYWHERE:
            same_name_counts[site.modification_name] = (
                same_name_counts.get(site.modification_name, 0) + 1
            )
    site_candidates: list[PtmEvidenceSiteCandidate] = []
    for site, modification, advisory in zip(
        parsed_sites,
        parsed_modifications,
        advisory_candidates,
        strict=False,
    ):
        if site.site_kind is not ModificationPosition.ANYWHERE:
            continue
        site_candidates.append(
            PtmEvidenceSiteCandidate(
                modification_name=site.modification_name,
                controlled_id=site.controlled_id,
                residue=site.residue,
                peptide_site_index=site.peptide_position,
                candidate_site_indices=_site_candidate_indices(
                    site_index=site.peptide_position,
                    candidate_site_indices=candidate_site_indices,
                    advisory_candidate_indices=advisory.candidate_site_indices,
                    same_name_count=same_name_counts.get(site.modification_name, 1),
                ),
                site_kind=site.site_kind,
            )
        )
    return tuple(site_candidates)


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
        localization_probability="localization_probability",
        q_value="q_value",
        sample_id="sample_id",
        candidate_sites="candidate_sites",
        decoy_label="decoy_label",
    )
    active_decoy_policy = decoy_policy or TargetDecoyLabelPolicy()
    validation_report = validate_scientific_table(
        path,
        schema=build_ptm_evidence_schema(active_mapping),
    )
    accepted: list[PtmEvidenceRecord] = []
    rejected: list[RejectedPtmEvidenceRow] = [
        RejectedPtmEvidenceRow(
            row_number=row.row_number,
            raw_fields=row.raw_values,
            issues=_ptm_issues_from_scientific_issues(row.issues),
        )
        for row in validation_report.rejected_rows
    ]
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows_by_number = {
            row_number: {
                str(key): str(value or "")
                for key, value in row.items()
                if key is not None
            }
            for row_number, row in enumerate(reader, start=2)
        }
        for accepted_row in validation_report.accepted_rows:
            row_number = accepted_row.row_number
            raw_fields = rows_by_number.get(row_number, {})
            issues: list[PtmValidationIssue] = []
            spectrum_id = raw_fields.get(active_mapping.spectrum_id, "").strip()
            peptide = raw_fields.get(active_mapping.peptide, "").strip()
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

            localization_probability: float | None = None
            if active_mapping.localization_probability:
                probability_token = raw_fields.get(
                    active_mapping.localization_probability,
                    "",
                ).strip()
                if probability_token:
                    try:
                        localization_probability = float(probability_token)
                        if (
                            localization_probability < 0.0
                            or localization_probability > 1.0
                        ):
                            raise ValueError
                    except ValueError:
                        issues.append(
                            _row_issue(
                                "invalid_localization_probability",
                                "invalid localization probability",
                                row_number,
                            )
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
                parsed = parse_ptm_peptide(peptide, registry=registry)
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
            site_candidates: tuple[PtmEvidenceSiteCandidate, ...] = ()
            if parsed is not None:
                parsed_peptide = parse_modified_peptide(
                    parsed.canonical_peptide,
                    registry=registry,
                )
                advisory = build_modification_localization_advisory(
                    parsed_peptide,
                    registry=registry,
                )
                site_candidates = _build_ptm_evidence_site_candidates(
                    parsed_sites=parsed.sites,
                    parsed_modifications=parsed_peptide.modifications,
                    advisory_candidates=advisory.candidates,
                    candidate_site_indices=candidate_sites,
                )
                modification_names = tuple(
                    site.modification_name for site in site_candidates
                )
                if not site_candidates:
                    issues.append(
                        _row_issue(
                            "missing_internal_modification",
                            "PTM evidence requires at least one residue-localized modification",
                            row_number,
                        )
                    )
                candidate_sites = tuple(
                    sorted(
                        {
                            site_index
                            for site_candidate in site_candidates
                            for site_index in site_candidate.candidate_site_indices
                        }
                    )
                )

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
                    canonical_peptide=parsed.canonical_peptide,
                    sequence=parsed.sequence,
                    charge=charge,
                    score=score,
                    q_value=q_value,
                    localization_probability=localization_probability,
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
                    site_candidates=site_candidates,
                    provenance=ImportedEvidenceProvenance.from_single_row(
                        source_engine="ptm-localization",
                        source_file=str(path),
                        source_row_number=row_number,
                        original_identifiers={
                            "spectrum_id": spectrum_id,
                            "localized_peptide": peptide,
                            "sample_id": raw_fields.get(active_mapping.sample_id, "").strip(),
                        },
                    ),
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


def render_ptm_evidence_site_candidate_tsv(report: PtmEvidenceParseReport) -> str:
    """Render one PTM evidence parser candidate-site ledger as TSV."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "spectrum_id",
            "localized_peptide",
            "canonical_peptide",
            "protein_refs",
            "modification_name",
            "controlled_id",
            "residue",
            "peptide_site_index",
            "candidate_site_indices",
            "site_kind",
        ]
    )
    for record in report.accepted_records:
        for site in record.site_candidates:
            writer.writerow(
                [
                    record.sample_id or "",
                    record.spectrum_id,
                    record.localized_peptide,
                    record.canonical_peptide,
                    ";".join(record.protein_refs),
                    site.modification_name,
                    site.controlled_id or "",
                    site.residue,
                    site.peptide_site_index,
                    ";".join(
                        str(site_index) for site_index in site.candidate_site_indices
                    ),
                    site.site_kind.value,
                ]
            )
    return buffer.getvalue()


def map_ptm_evidence_to_protein_sites(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    protein_sequences: dict[str, str],
    registry: ModificationRegistryDocument | None = None,
) -> tuple[PtmProteinSiteMapping, ...]:
    """Map residue-localized modified peptides onto protein coordinates."""
    from bijux_proteomics.ptm.protein_site_mapping import (
        map_ptm_evidence_to_protein_sites as _map_ptm_evidence_to_protein_sites,
    )

    return _map_ptm_evidence_to_protein_sites(
        records,
        protein_sequences=protein_sequences,
        registry=registry,
    )


def build_ptm_protein_site_mapping_report(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    protein_sequences: dict[str, str],
    registry: ModificationRegistryDocument | None = None,
) -> PtmProteinSiteMappingReport:
    """Classify PTM protein-site mappings into exact, ambiguous, and unmapped ledgers."""
    from bijux_proteomics.ptm.protein_site_mapping import (
        build_ptm_protein_site_mapping_report as _build_ptm_protein_site_mapping_report,
    )

    return _build_ptm_protein_site_mapping_report(
        records,
        protein_sequences=protein_sequences,
        registry=registry,
    )


def build_ptm_site_table(
    mappings: tuple[PtmProteinSiteMapping, ...],
) -> tuple[PtmSiteEntry, ...]:
    """Aggregate peptide-level PTM mappings into site-level entries."""
    from bijux_proteomics.ptm.protein_site_mapping import (
        build_ptm_site_table as _build_ptm_site_table,
    )

    return _build_ptm_site_table(mappings)


build_ptm_site_group_evidence = _SITE_GROUPS_MODULE.build_ptm_site_group_evidence


def build_ptm_site_ambiguity_report(
    site_entries: tuple[PtmSiteEntry, ...],
) -> tuple[PtmSiteAmbiguityEntry, ...]:
    """Report ambiguous PTM site assignments."""
    from bijux_proteomics.ptm.protein_site_mapping import (
        build_ptm_site_ambiguity_report as _build_ptm_site_ambiguity_report,
    )

    return _build_ptm_site_ambiguity_report(site_entries)


def build_ptm_site_coverage_report(
    mappings: tuple[PtmProteinSiteMapping, ...],
) -> tuple[PtmSiteCoverageEntry, ...]:
    """Build site-level spectrum and peptide coverage summaries."""
    from bijux_proteomics.ptm.protein_site_mapping import (
        build_ptm_site_coverage_report as _build_ptm_site_coverage_report,
    )

    return _build_ptm_site_coverage_report(mappings)


def validate_ptm_site_coordinates(
    mappings: tuple[PtmProteinSiteMapping, ...],
    *,
    protein_sequences: dict[str, str],
) -> PtmCoordinateValidationReport:
    """Validate that peptide-localized PTM coordinates agree with protein mappings."""
    from bijux_proteomics.ptm.protein_site_mapping import (
        validate_ptm_site_coordinates as _validate_ptm_site_coordinates,
    )

    return _validate_ptm_site_coordinates(
        mappings,
        protein_sequences=protein_sequences,
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
    from bijux_proteomics.ptm.occupancy_estimation import (
        build_ptm_site_occupancy_report as _build_ptm_site_occupancy_report,
    )

    return _build_ptm_site_occupancy_report(
        site_entries,
        feature_records=feature_records,
    ).entries


def build_ptm_enrichment_input(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    modification_name: str = "Phospho",
) -> PtmEnrichmentInput:
    """Build foreground and background site lists for PTM enrichment."""
    from bijux_proteomics.ptm.motif_analysis import (
        build_ptm_enrichment_input as _implementation,
    )

    return _implementation(
        site_entries,
        protein_sequences=protein_sequences,
        modification_name=modification_name,
    )


def build_ptm_motif_background_report(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    modification_name: str = "Phospho",
    background_mode: str = "whole_proteome_background",
) -> PtmMotifBackgroundReport:
    """Build a residue background report for PTM motif interpretation."""
    from bijux_proteomics.ptm.motif_analysis import (
        build_ptm_motif_background_report as _implementation,
    )

    return _implementation(
        site_entries,
        protein_sequences=protein_sequences,
        modification_name=modification_name,
        background_mode=background_mode,
    )


def build_ptm_motif_windows(
    site_entries: tuple[PtmSiteEntry, ...],
    *,
    protein_sequences: dict[str, str],
    flank_size: int = 7,
) -> tuple[PtmMotifWindow, ...]:
    """Extract +/- N residue motif windows around PTM sites."""
    from bijux_proteomics.ptm.motif_analysis import (
        build_ptm_motif_windows as _implementation,
    )

    return _implementation(
        site_entries,
        protein_sequences=protein_sequences,
        flank_size=flank_size,
    )
