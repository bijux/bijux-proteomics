# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Search-result and peptide-spectrum match contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry import canonicalize_modified_peptide
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class TargetDecoyLabel(StrEnum):
    """Normalized target/decoy state for one evidence record."""

    TARGET = "target"
    DECOY = "decoy"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PsmSortField(StrEnum):
    """Supported stable PSM sorting policies."""

    SPECTRUM = "spectrum"
    SCORE = "score"
    Q_VALUE = "q_value"
    PEPTIDE = "peptide"


class SearchResultColumnMapping(JsonModel):
    """User-supplied mapping from engine columns to the stable PSM contract."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    charge: str = Field(..., min_length=1)
    score: str = Field(..., min_length=1)
    protein_refs: str | None = None
    q_value: str | None = None
    decoy_label: str | None = None
    protein_separator: str = ";"


class TargetDecoyLabelPolicy(JsonModel):
    """Policy for inferring target-decoy labels from search-result fields."""

    model_config = ConfigDict(extra="forbid")

    protein_prefix: str | None = "DECOY_"
    protein_suffix: str | None = None
    explicit_decoy_values: tuple[str, ...] = ("decoy", "true", "1")
    explicit_target_values: tuple[str, ...] = ("target", "false", "0")

    @field_validator("explicit_decoy_values", "explicit_target_values", mode="before")
    @classmethod
    def _normalize_values(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            values: tuple[str, ...] = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("decoy label values must be iterable")
            values = tuple(str(token) for token in value)
        return tuple(token.strip().lower() for token in values if token.strip())


class PsmRecord(JsonModel):
    """Stable peptide-spectrum match record."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN

    @field_validator("spectrum_id", "peptide", "canonical_peptide", mode="before")
    @classmethod
    def _strip_required_text(cls, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("field must not be blank")
        return text

    @field_validator("protein_refs", mode="before")
    @classmethod
    def _normalize_protein_refs(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            refs = [value]
        else:
            if not isinstance(value, Iterable):
                raise ValueError("protein references must be iterable")
            refs = [str(token) for token in value]
        normalized = tuple(token.strip() for token in refs if token.strip())
        return tuple(dict.fromkeys(normalized))


class SearchResultValidationIssue(JsonModel):
    """One validation issue while parsing or normalizing search results."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)


class RejectedPsmRow(JsonModel):
    """One rejected raw PSM row plus stable issue details."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[SearchResultValidationIssue, ...] = Field(default_factory=tuple)


class PsmParseReport(JsonModel):
    """Result of parsing one generic PSM TSV file."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPsmRow, ...] = Field(default_factory=tuple)
    column_mapping: SearchResultColumnMapping


class PeptideEvidenceEntry(JsonModel):
    """Rolled-up peptide-level evidence across PSMs."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    psm_count: int = Field(..., ge=1)
    spectrum_count: int = Field(..., ge=1)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN


class ProteinEvidenceEntry(JsonModel):
    """Rolled-up protein-level evidence across peptides and PSMs."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=1)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN


class FdrPolicy(JsonModel):
    """Stable policy for basic target-decoy FDR evaluation."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(
        default="higher_better", pattern="^(higher_better|lower_better)$"
    )
    threshold: float | None = Field(default=None, ge=0.0)
    decoy_policy: TargetDecoyLabelPolicy = Field(default_factory=TargetDecoyLabelPolicy)


class FdrAnnotatedPsm(JsonModel):
    """PSM record plus cumulative target-decoy FDR state."""

    model_config = ConfigDict(extra="forbid")

    psm: PsmRecord
    rank: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool = True


class NormalizedScoreEntry(JsonModel):
    """One PSM score normalized onto an orientation-stable rank scale."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    raw_score: float
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel


class CalibrationPlotBin(JsonModel):
    """One score-calibration bin over normalized target-decoy evidence."""

    model_config = ConfigDict(extra="forbid")

    bin_lower: float = Field(..., ge=0.0, le=1.0)
    bin_upper: float = Field(..., ge=0.0, le=1.0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)
    unknown_count: int = Field(..., ge=0)
    decoy_fraction: float = Field(..., ge=0.0)


class CalibrationPlotData(JsonModel):
    """Plot-ready calibration data for one scored target-decoy ranking."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    total_psms: int = Field(..., ge=0)
    bins: tuple[CalibrationPlotBin, ...] = Field(default_factory=tuple)


class FdrAuditEntry(JsonModel):
    """One sorted FDR-audit row with cumulative derivation state."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    raw_score: float
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    target_decoy_label: TargetDecoyLabel
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class FdrAuditTrail(JsonModel):
    """Stable audit payload for one target-decoy FDR calculation."""

    model_config = ConfigDict(extra="forbid")

    policy: FdrPolicy
    entries: tuple[FdrAuditEntry, ...] = Field(default_factory=tuple)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


class FdrEvidenceLevel(StrEnum):
    """Supported evidence levels for level-specific FDR reporting."""

    PSM = "psm"
    PEPTIDE = "peptide"
    PROTEIN = "protein"


class FdrLevelEntry(JsonModel):
    """One FDR-annotated entity at the PSM, peptide, or protein level."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: FdrEvidenceLevel
    entity_id: str = Field(..., min_length=1)
    score: float
    q_value: float = Field(..., ge=0.0)
    fdr: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)
    accepted: bool
    target_decoy_label: TargetDecoyLabel
    member_count: int = Field(..., ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class LevelSpecificFdrReport(JsonModel):
    """Stable report over PSM-, peptide-, and protein-level FDR surfaces."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    threshold: float | None = Field(default=None, ge=0.0)
    psm_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)
    peptide_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)
    protein_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)


class GroupedFdrBucket(JsonModel):
    """One grouped-FDR bucket with its own ranked entries."""

    model_config = ConfigDict(extra="forbid")

    group_key: str = Field(..., min_length=1)
    entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)


class GroupedFdrReport(JsonModel):
    """Stable grouped-FDR report across multiple evidence buckets."""

    model_config = ConfigDict(extra="forbid")

    group_by: str = Field(..., pattern="^(charge_state|modification_state)$")
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    threshold: float | None = Field(default=None, ge=0.0)
    groups: tuple[GroupedFdrBucket, ...] = Field(default_factory=tuple)


class ProteinGroupEntry(JsonModel):
    """One indistinguishable protein group from shared peptide evidence."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class ParsimonyProteinEntry(JsonModel):
    """One protein selected by the greedy parsimony inference policy."""

    model_config = ConfigDict(extra="forbid")

    selection_rank: int = Field(..., ge=1)
    protein_ref: str = Field(..., min_length=1)
    source_group_id: str = Field(..., min_length=1)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)
    newly_explained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class RazorPeptideAssignment(JsonModel):
    """One peptide-to-protein assignment under a razor policy."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    candidate_proteins: tuple[str, ...] = Field(default_factory=tuple)
    assigned_protein: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)


class ProteinCoverageEntry(JsonModel):
    """Sequence-aware protein coverage summary from identified peptides."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    residue_count: int = Field(..., ge=1)
    covered_residue_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    covered_ranges: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)


class DatabasePeptideUniqueness(StrEnum):
    """Uniqueness classification across a provided protein database."""

    UNIQUE = "unique"
    SHARED = "shared"
    MISSING = "missing"


class DatabasePeptideUniquenessEntry(JsonModel):
    """One peptide uniqueness entry over a provided database."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    uniqueness: DatabasePeptideUniqueness


class PickedProteinFdrEntry(JsonModel):
    """One picked target-decoy protein entry with FDR state."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    partner_ref: str | None = None
    score: float
    q_value: float = Field(..., ge=0.0)
    fdr: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)
    accepted: bool
    target_decoy_label: TargetDecoyLabel
    supporting_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ConfidenceLabel(StrEnum):
    """Stable confidence labels over q-valued evidence."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REJECTED = "rejected"
    DECOY = "decoy"


class ConfidenceAssignment(JsonModel):
    """Confidence label plus its explanation."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0)
    label: ConfidenceLabel
    explanation: str = Field(..., min_length=1)


class PsmSummaryReport(JsonModel):
    """Compact search-result summary over normalized PSM records."""

    model_config = ConfigDict(extra="forbid")

    total_psms: int = Field(..., ge=0)
    target_psms: int = Field(..., ge=0)
    decoy_psms: int = Field(..., ge=0)
    mixed_psms: int = Field(..., ge=0)
    unknown_psms: int = Field(..., ge=0)
    counts_by_charge: dict[str, int] = Field(default_factory=dict)
    counts_by_score_bin: dict[str, int] = Field(default_factory=dict)


class PeptideSummaryReport(JsonModel):
    """Compact peptide-level summary derived from PSM records."""

    model_config = ConfigDict(extra="forbid")

    total_peptides: int = Field(..., ge=0)
    modified_peptides: int = Field(..., ge=0)
    unique_peptides: int = Field(..., ge=0)
    shared_peptides: int = Field(..., ge=0)
    decoy_peptides: int = Field(..., ge=0)


class ProteinSummaryEntry(JsonModel):
    """One protein summary row with optional sequence coverage."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)


class ProteinSummaryReport(JsonModel):
    """Compact protein-level summary over evidence rollups."""

    model_config = ConfigDict(extra="forbid")

    total_proteins: int = Field(..., ge=0)
    target_proteins: int = Field(..., ge=0)
    decoy_proteins: int = Field(..., ge=0)
    protein_groups: tuple[ProteinSummaryEntry, ...] = Field(default_factory=tuple)


class SearchResultProvenanceManifest(JsonModel):
    """Stable manifest for one search-result parsing and filtering operation."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    source_path: str | None = None
    source_sha256: str | None = None
    total_rows: int = Field(..., ge=0)
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    column_mapping: SearchResultColumnMapping
    decoy_policy: TargetDecoyLabelPolicy
    fdr_policy: FdrPolicy | None = None


def _parse_protein_refs(raw_value: str | None, separator: str) -> tuple[str, ...]:
    if raw_value in (None, ""):
        return ()
    text = raw_value.strip() if raw_value is not None else ""
    refs = tuple(token.strip() for token in text.split(separator) if token.strip())
    return tuple(dict.fromkeys(refs))


def _rank_label(label: TargetDecoyLabel) -> int:
    if label is TargetDecoyLabel.DECOY:
        return 3
    if label is TargetDecoyLabel.MIXED:
        return 2
    if label is TargetDecoyLabel.TARGET:
        return 1
    return 0


def _combine_labels(labels: tuple[TargetDecoyLabel, ...]) -> TargetDecoyLabel:
    active = tuple(label for label in labels if label is not TargetDecoyLabel.UNKNOWN)
    if not active:
        return TargetDecoyLabel.UNKNOWN
    if all(label is TargetDecoyLabel.DECOY for label in active):
        return TargetDecoyLabel.DECOY
    if all(label is TargetDecoyLabel.TARGET for label in active):
        return TargetDecoyLabel.TARGET
    if any(label is TargetDecoyLabel.MIXED for label in active):
        return TargetDecoyLabel.MIXED
    return TargetDecoyLabel.MIXED


def parse_target_decoy_label(
    *,
    protein_refs: tuple[str, ...] = (),
    explicit_label: str | None = None,
    policy: TargetDecoyLabelPolicy | None = None,
) -> TargetDecoyLabel:
    """Parse target-decoy state from explicit and protein-reference signals."""
    active_policy = policy or TargetDecoyLabelPolicy()
    if explicit_label is not None and explicit_label.strip():
        normalized = explicit_label.strip().lower()
        if normalized in active_policy.explicit_decoy_values:
            return TargetDecoyLabel.DECOY
        if normalized in active_policy.explicit_target_values:
            return TargetDecoyLabel.TARGET

    if not protein_refs:
        return TargetDecoyLabel.UNKNOWN

    prefix = active_policy.protein_prefix or ""
    suffix = active_policy.protein_suffix or ""
    labels: list[TargetDecoyLabel] = []
    for protein_ref in protein_refs:
        is_prefix = bool(prefix) and protein_ref.startswith(prefix)
        is_suffix = bool(suffix) and protein_ref.endswith(suffix)
        labels.append(
            TargetDecoyLabel.DECOY
            if is_prefix or is_suffix
            else TargetDecoyLabel.TARGET
        )
    return _combine_labels(tuple(labels))


def _row_issue(code: str, message: str, row_number: int) -> SearchResultValidationIssue:
    return SearchResultValidationIssue(
        code=code, message=message, row_number=row_number
    )


def _parse_psm_row(
    row: dict[str, str],
    *,
    row_number: int,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy,
) -> PsmRecord:
    issues: list[SearchResultValidationIssue] = []

    spectrum_id = row.get(mapping.spectrum_id, "").strip()
    if not spectrum_id:
        issues.append(
            _row_issue("missing_spectrum_id", "missing spectrum identifier", row_number)
        )

    peptide = row.get(mapping.peptide, "").strip()
    if not peptide:
        issues.append(
            _row_issue("missing_peptide", "missing peptide sequence", row_number)
        )

    try:
        charge = int(row.get(mapping.charge, "").strip())
        if charge < 1:
            raise ValueError
    except ValueError:
        issues.append(_row_issue("invalid_charge", "invalid charge value", row_number))
        charge = 0

    try:
        score = float(row.get(mapping.score, "").strip())
    except ValueError:
        issues.append(_row_issue("invalid_score", "invalid score value", row_number))
        score = 0.0

    q_value: float | None = None
    if mapping.q_value:
        q_token = row.get(mapping.q_value, "").strip()
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
        row.get(mapping.protein_refs) if mapping.protein_refs else None,
        mapping.protein_separator,
    )
    explicit_label = row.get(mapping.decoy_label) if mapping.decoy_label else None

    canonical_peptide = peptide
    if peptide:
        try:
            canonical_peptide = canonicalize_modified_peptide(peptide)
        except ValueError as exc:
            issues.append(_row_issue("invalid_peptide_notation", str(exc), row_number))

    if issues:
        raise ValueError(
            RejectedPsmRow(
                row_number=row_number, raw_fields=row, issues=tuple(issues)
            ).to_stable_json()
        )

    return PsmRecord(
        spectrum_id=spectrum_id,
        peptide=peptide,
        canonical_peptide=canonical_peptide,
        charge=charge,
        score=score,
        q_value=q_value,
        protein_refs=protein_refs,
        target_decoy_label=parse_target_decoy_label(
            protein_refs=protein_refs,
            explicit_label=explicit_label,
            policy=decoy_policy,
        ),
    )


def parse_psm_tsv(
    path: Path,
    *,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> PsmParseReport:
    """Parse a generic peptide-spectrum match TSV into stable records."""
    active_policy = decoy_policy or TargetDecoyLabelPolicy()
    accepted_records: list[PsmRecord] = []
    rejected_rows: list[RejectedPsmRow] = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("PSM TSV must include a header row")
        for required_column in (
            mapping.spectrum_id,
            mapping.peptide,
            mapping.charge,
            mapping.score,
        ):
            if required_column not in reader.fieldnames:
                raise ValueError(f"missing required PSM column {required_column!r}")

        for index, row in enumerate(reader, start=2):
            normalized_row = {
                str(key): str(value) for key, value in row.items() if key is not None
            }
            try:
                accepted_records.append(
                    _parse_psm_row(
                        normalized_row,
                        row_number=index,
                        mapping=mapping,
                        decoy_policy=active_policy,
                    )
                )
            except ValueError as exc:
                rejected_rows.append(RejectedPsmRow.model_validate_json(str(exc)))

    return PsmParseReport(
        total_rows=len(accepted_records) + len(rejected_rows),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=mapping,
    )


def normalize_psm_records(records: tuple[PsmRecord, ...]) -> tuple[PsmRecord, ...]:
    """Return a stable normalized PSM ordering for downstream exports."""
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.spectrum_id,
                record.q_value if record.q_value is not None else float("inf"),
                -record.score,
                record.canonical_peptide,
                record.charge,
            ),
        )
    )


def export_psm_jsonl(records: tuple[PsmRecord, ...], path: Path) -> None:
    """Write normalized PSM records as stable JSONL."""
    normalized = normalize_psm_records(records)
    with path.open("w", encoding="utf-8") as handle:
        for record in normalized:
            handle.write(
                json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def export_psm_tsv(records: tuple[PsmRecord, ...], path: Path) -> None:
    """Write normalized PSM records as a stable TSV table."""
    normalized = normalize_psm_records(records)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "spectrum_id",
                "peptide",
                "canonical_peptide",
                "charge",
                "score",
                "q_value",
                "protein_refs",
                "target_decoy_label",
            ]
        )
        for record in normalized:
            writer.writerow(
                [
                    record.spectrum_id,
                    record.peptide,
                    record.canonical_peptide,
                    record.charge,
                    record.score,
                    "" if record.q_value is None else record.q_value,
                    ";".join(record.protein_refs),
                    record.target_decoy_label.value,
                ]
            )


def sort_psm_records(
    records: tuple[PsmRecord, ...],
    *,
    by: PsmSortField = PsmSortField.SPECTRUM,
) -> tuple[PsmRecord, ...]:
    """Sort PSMs by one stable policy."""
    if by is PsmSortField.SPECTRUM:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.spectrum_id,
                    -record.score,
                    record.canonical_peptide,
                ),
            )
        )
    if by is PsmSortField.SCORE:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    -record.score,
                    record.spectrum_id,
                    record.canonical_peptide,
                ),
            )
        )
    if by is PsmSortField.Q_VALUE:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.q_value if record.q_value is not None else float("inf"),
                    record.spectrum_id,
                    -record.score,
                    record.canonical_peptide,
                ),
            )
        )
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.canonical_peptide,
                record.spectrum_id,
                -record.score,
            ),
        )
    )


def select_best_psm_per_spectrum(
    records: tuple[PsmRecord, ...],
) -> tuple[PsmRecord, ...]:
    """Select one best PSM per spectrum with stable tie-breaking."""
    best_by_spectrum: dict[str, PsmRecord] = {}
    for record in records:
        current = best_by_spectrum.get(record.spectrum_id)
        if current is None:
            best_by_spectrum[record.spectrum_id] = record
            continue
        replacement_key = (
            record.score,
            -(record.q_value if record.q_value is not None else float("inf")),
            -_rank_label(record.target_decoy_label),
            record.canonical_peptide,
        )
        current_key = (
            current.score,
            -(current.q_value if current.q_value is not None else float("inf")),
            -_rank_label(current.target_decoy_label),
            current.canonical_peptide,
        )
        if replacement_key > current_key:
            best_by_spectrum[record.spectrum_id] = record
    return tuple(best_by_spectrum[key] for key in sorted(best_by_spectrum))


def rollup_peptide_evidence(
    records: tuple[PsmRecord, ...],
) -> tuple[PeptideEvidenceEntry, ...]:
    """Roll up multiple PSMs into peptide-level evidence rows."""
    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        grouped[record.canonical_peptide].append(record)

    rollups: list[PeptideEvidenceEntry] = []
    for canonical_peptide in sorted(grouped):
        group = grouped[canonical_peptide]
        best = max(
            group,
            key=lambda record: (
                record.score,
                -(record.q_value if record.q_value is not None else float("inf")),
                record.peptide,
            ),
        )
        protein_refs = tuple(
            sorted(
                {protein_ref for record in group for protein_ref in record.protein_refs}
            )
        )
        charge_states = tuple(sorted({record.charge for record in group}))
        spectra = {record.spectrum_id for record in group}
        q_values = [record.q_value for record in group if record.q_value is not None]
        rollups.append(
            PeptideEvidenceEntry(
                peptide=best.peptide,
                canonical_peptide=canonical_peptide,
                psm_count=len(group),
                spectrum_count=len(spectra),
                best_score=best.score,
                best_q_value=min(q_values) if q_values else None,
                charge_states=charge_states,
                protein_refs=protein_refs,
                target_decoy_label=_combine_labels(
                    tuple(record.target_decoy_label for record in group)
                ),
            )
        )
    return tuple(rollups)


def rollup_protein_evidence(
    records: tuple[PsmRecord, ...],
) -> tuple[ProteinEvidenceEntry, ...]:
    """Roll up PSMs and peptides into protein-level evidence rows."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_to_peptides: dict[str, list[PeptideEvidenceEntry]] = defaultdict(list)
    protein_to_spectra: dict[str, set[str]] = defaultdict(set)

    record_by_peptide: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        record_by_peptide[record.canonical_peptide].append(record)

    for peptide_rollup in peptide_rollups:
        for protein_ref in peptide_rollup.protein_refs:
            protein_to_peptides[protein_ref].append(peptide_rollup)
            for record in record_by_peptide[peptide_rollup.canonical_peptide]:
                if protein_ref in record.protein_refs:
                    protein_to_spectra[protein_ref].add(record.spectrum_id)

    rollups: list[ProteinEvidenceEntry] = []
    for protein_ref in sorted(protein_to_peptides):
        peptides = protein_to_peptides[protein_ref]
        peptide_names = tuple(sorted(peptide.canonical_peptide for peptide in peptides))
        unique_peptide_count = sum(
            1 for peptide in peptides if len(peptide.protein_refs) == 1
        )
        shared_peptide_count = sum(
            1 for peptide in peptides if len(peptide.protein_refs) > 1
        )
        q_values = [
            peptide.best_q_value
            for peptide in peptides
            if peptide.best_q_value is not None
        ]
        rollups.append(
            ProteinEvidenceEntry(
                protein_ref=protein_ref,
                peptide_count=len(peptides),
                unique_peptide_count=unique_peptide_count,
                shared_peptide_count=shared_peptide_count,
                best_score=max(peptide.best_score for peptide in peptides),
                best_q_value=min(q_values) if q_values else None,
                peptides=peptide_names,
                spectrum_count=len(protein_to_spectra[protein_ref]),
                target_decoy_label=parse_target_decoy_label(
                    protein_refs=(protein_ref,),
                ),
            )
        )
    return tuple(rollups)


def calculate_basic_target_decoy_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> tuple[FdrAnnotatedPsm, ...]:
    """Annotate PSMs with cumulative target-decoy FDR and monotonic q-values."""
    if score_orientation not in {"higher_better", "lower_better"}:
        raise ValueError("score_orientation must be 'higher_better' or 'lower_better'")

    sorted_records = tuple(
        sorted(
            records,
            key=(
                (
                    lambda record: (
                        -record.score,
                        record.spectrum_id,
                        record.canonical_peptide,
                    )
                )
                if score_orientation == "higher_better"
                else (
                    lambda record: (
                        record.score,
                        record.spectrum_id,
                        record.canonical_peptide,
                    )
                )
            ),
        )
    )
    annotated: list[FdrAnnotatedPsm] = []
    cumulative_targets = 0
    cumulative_decoys = 0
    for rank, record in enumerate(sorted_records, start=1):
        if record.target_decoy_label is TargetDecoyLabel.DECOY:
            cumulative_decoys += 1
        else:
            cumulative_targets += 1
        fdr = min(cumulative_decoys / max(cumulative_targets, 1), 1.0)
        annotated.append(
            FdrAnnotatedPsm(
                psm=record,
                rank=rank,
                cumulative_targets=cumulative_targets,
                cumulative_decoys=cumulative_decoys,
                fdr=fdr,
                q_value=fdr,
                accepted=threshold is None or fdr <= threshold,
            )
        )

    running_min = float("inf")
    revised: list[FdrAnnotatedPsm] = []
    for entry in reversed(annotated):
        running_min = min(running_min, entry.fdr)
        revised.append(
            entry.model_copy(
                update={
                    "q_value": running_min,
                    "accepted": threshold is None or running_min <= threshold,
                }
            )
        )
    return tuple(reversed(revised))


def normalize_psm_score_orientation(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
) -> tuple[NormalizedScoreEntry, ...]:
    """Normalize scores onto a stable best-to-worst rank scale."""
    if score_orientation not in {"higher_better", "lower_better"}:
        raise ValueError("score_orientation must be 'higher_better' or 'lower_better'")

    sorted_records = tuple(
        sorted(
            records,
            key=(
                (
                    lambda record: (
                        -record.score,
                        record.spectrum_id,
                        record.canonical_peptide,
                        record.charge,
                    )
                )
                if score_orientation == "higher_better"
                else (
                    lambda record: (
                        record.score,
                        record.spectrum_id,
                        record.canonical_peptide,
                        record.charge,
                    )
                )
            ),
        )
    )
    if not sorted_records:
        return ()

    denominator = max(len(sorted_records) - 1, 1)
    normalized_entries: list[NormalizedScoreEntry] = []
    for rank, record in enumerate(sorted_records, start=1):
        normalized_score = (
            1.0 if len(sorted_records) == 1 else 1.0 - ((rank - 1) / denominator)
        )
        normalized_entries.append(
            NormalizedScoreEntry(
                spectrum_id=record.spectrum_id,
                canonical_peptide=record.canonical_peptide,
                raw_score=record.score,
                normalized_score=normalized_score,
                rank=rank,
                target_decoy_label=record.target_decoy_label,
            )
        )
    return tuple(normalized_entries)


def build_calibration_plot_data(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
) -> CalibrationPlotData:
    """Build plot-ready score calibration bins over target-decoy evidence."""
    if bin_count < 1:
        raise ValueError("bin_count must be at least 1")

    normalized_entries = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    bins: list[CalibrationPlotBin] = []
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        if index == bin_count - 1:
            bucket = tuple(
                entry
                for entry in normalized_entries
                if lower <= entry.normalized_score <= upper
            )
        else:
            bucket = tuple(
                entry
                for entry in normalized_entries
                if lower <= entry.normalized_score < upper
            )
        target_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.TARGET
        )
        decoy_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.DECOY
        )
        mixed_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.MIXED
        )
        unknown_count = sum(
            1
            for entry in bucket
            if entry.target_decoy_label is TargetDecoyLabel.UNKNOWN
        )
        denominator = target_count + decoy_count
        bins.append(
            CalibrationPlotBin(
                bin_lower=lower,
                bin_upper=upper,
                target_count=target_count,
                decoy_count=decoy_count,
                mixed_count=mixed_count,
                unknown_count=unknown_count,
                decoy_fraction=decoy_count / denominator if denominator else 0.0,
            )
        )
    return CalibrationPlotData(
        score_orientation=score_orientation,
        total_psms=len(records),
        bins=tuple(bins),
    )


def compute_fdr_reproducibility_hash(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> str:
    """Compute a stable digest over the sorted FDR derivation inputs."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    payload = {
        "score_orientation": score_orientation,
        "threshold": threshold,
        "entries": [
            {
                "rank": entry.rank,
                "spectrum_id": entry.psm.spectrum_id,
                "canonical_peptide": entry.psm.canonical_peptide,
                "charge": entry.psm.charge,
                "score": entry.psm.score,
                "target_decoy_label": entry.psm.target_decoy_label.value,
                "cumulative_targets": entry.cumulative_targets,
                "cumulative_decoys": entry.cumulative_decoys,
                "fdr": entry.fdr,
                "q_value": entry.q_value,
                "accepted": entry.accepted,
            }
            for entry in annotated
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_fdr_audit_trail(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> FdrAuditTrail:
    """Build a stable audit trail for one target-decoy FDR calculation."""
    policy = FdrPolicy(score_orientation=score_orientation, threshold=threshold)
    normalized_entries = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    score_index = {
        (entry.spectrum_id, entry.canonical_peptide, entry.rank): entry
        for entry in normalized_entries
    }
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    audit_entries: list[FdrAuditEntry] = []
    for entry in annotated:
        normalized_entry = score_index.get(
            (entry.psm.spectrum_id, entry.psm.canonical_peptide, entry.rank)
        )
        audit_entries.append(
            FdrAuditEntry(
                rank=entry.rank,
                spectrum_id=entry.psm.spectrum_id,
                canonical_peptide=entry.psm.canonical_peptide,
                raw_score=entry.psm.score,
                normalized_score=normalized_entry.normalized_score
                if normalized_entry is not None
                else 0.0,
                target_decoy_label=entry.psm.target_decoy_label,
                cumulative_targets=entry.cumulative_targets,
                cumulative_decoys=entry.cumulative_decoys,
                fdr=entry.fdr,
                q_value=entry.q_value,
                accepted=entry.accepted,
            )
        )
    return FdrAuditTrail(
        policy=policy,
        entries=tuple(audit_entries),
        reproducibility_hash=compute_fdr_reproducibility_hash(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        ),
    )


def apply_q_values(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
) -> tuple[PsmRecord, ...]:
    """Return PSM records with q-values filled from target-decoy FDR."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        score_orientation=score_orientation,
    )
    return tuple(
        entry.psm.model_copy(update={"q_value": entry.q_value}) for entry in annotated
    )


def filter_psms_by_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float,
    score_orientation: str = "higher_better",
) -> tuple[PsmRecord, ...]:
    """Filter PSMs to those that pass the requested q-value threshold."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    return tuple(
        entry.psm.model_copy(update={"q_value": entry.q_value})
        for entry in annotated
        if entry.accepted
    )


def build_psm_summary_report(
    records: tuple[PsmRecord, ...],
    *,
    score_bin_size: float = 10.0,
) -> PsmSummaryReport:
    """Build a compact summary report over normalized PSM records."""
    counts_by_charge: dict[str, int] = defaultdict(int)
    counts_by_score_bin: dict[str, int] = defaultdict(int)
    target_psms = 0
    decoy_psms = 0
    mixed_psms = 0
    unknown_psms = 0
    for record in records:
        counts_by_charge[str(record.charge)] += 1
        lower = int(record.score // score_bin_size) * int(score_bin_size)
        upper = lower + int(score_bin_size)
        counts_by_score_bin[f"{lower}-{upper}"] += 1
        if record.target_decoy_label is TargetDecoyLabel.TARGET:
            target_psms += 1
        elif record.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_psms += 1
        elif record.target_decoy_label is TargetDecoyLabel.MIXED:
            mixed_psms += 1
        else:
            unknown_psms += 1
    return PsmSummaryReport(
        total_psms=len(records),
        target_psms=target_psms,
        decoy_psms=decoy_psms,
        mixed_psms=mixed_psms,
        unknown_psms=unknown_psms,
        counts_by_charge=dict(sorted(counts_by_charge.items())),
        counts_by_score_bin=dict(sorted(counts_by_score_bin.items())),
    )


def build_peptide_summary_report(
    records: tuple[PsmRecord, ...],
) -> PeptideSummaryReport:
    """Build a compact peptide-level summary report."""
    peptide_rollups = rollup_peptide_evidence(records)
    return PeptideSummaryReport(
        total_peptides=len(peptide_rollups),
        modified_peptides=sum(
            1 for peptide in peptide_rollups if "[" in peptide.canonical_peptide
        ),
        unique_peptides=sum(
            1 for peptide in peptide_rollups if len(peptide.protein_refs) == 1
        ),
        shared_peptides=sum(
            1 for peptide in peptide_rollups if len(peptide.protein_refs) > 1
        ),
        decoy_peptides=sum(
            1
            for peptide in peptide_rollups
            if peptide.target_decoy_label is TargetDecoyLabel.DECOY
        ),
    )


def build_protein_summary_report(
    records: tuple[PsmRecord, ...],
    *,
    protein_lengths: dict[str, int] | None = None,
) -> ProteinSummaryReport:
    """Build a compact protein-level summary report with optional coverage."""
    rollups = rollup_protein_evidence(records)
    summary_entries: list[ProteinSummaryEntry] = []
    target_proteins = 0
    decoy_proteins = 0
    for rollup in rollups:
        coverage_fraction: float | None = None
        if protein_lengths and protein_lengths.get(rollup.protein_ref):
            covered_residues = {
                residue_index
                for peptide in rollup.peptides
                for residue_index in range(1, len(peptide) + 1)
            }
            coverage_fraction = min(
                len(covered_residues) / protein_lengths[rollup.protein_ref],
                1.0,
            )
        summary_entries.append(
            ProteinSummaryEntry(
                protein_ref=rollup.protein_ref,
                peptide_count=rollup.peptide_count,
                unique_peptide_count=rollup.unique_peptide_count,
                shared_peptide_count=rollup.shared_peptide_count,
                coverage_fraction=coverage_fraction,
            )
        )
        if rollup.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_proteins += 1
        else:
            target_proteins += 1
    return ProteinSummaryReport(
        total_proteins=len(summary_entries),
        target_proteins=target_proteins,
        decoy_proteins=decoy_proteins,
        protein_groups=tuple(summary_entries),
    )


def _entity_fdr_entries(
    entities: tuple[tuple[str, float, TargetDecoyLabel, int, tuple[str, ...]], ...],
    *,
    evidence_level: FdrEvidenceLevel,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> tuple[FdrLevelEntry, ...]:
    pseudo_records = tuple(
        PsmRecord(
            spectrum_id=entity_id,
            peptide=entity_id,
            canonical_peptide=entity_id,
            charge=1,
            score=score,
            protein_refs=protein_refs,
            target_decoy_label=label,
        )
        for entity_id, score, label, _member_count, protein_refs in entities
    )
    annotated = calculate_basic_target_decoy_fdr(
        pseudo_records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    entity_index = {
        entity_id: (member_count, protein_refs)
        for entity_id, _score, _label, member_count, protein_refs in entities
    }
    return tuple(
        FdrLevelEntry(
            evidence_level=evidence_level,
            entity_id=entry.psm.canonical_peptide,
            score=entry.psm.score,
            q_value=entry.q_value,
            fdr=entry.fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.psm.target_decoy_label,
            member_count=entity_index[entry.psm.canonical_peptide][0],
            protein_refs=entity_index[entry.psm.canonical_peptide][1],
        )
        for entry in annotated
    )


def calculate_level_specific_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> LevelSpecificFdrReport:
    """Calculate separate PSM-, peptide-, and protein-level FDR surfaces."""
    psm_entries = tuple(
        FdrLevelEntry(
            evidence_level=FdrEvidenceLevel.PSM,
            entity_id=entry.psm.spectrum_id,
            score=entry.psm.score,
            q_value=entry.q_value,
            fdr=entry.fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.psm.target_decoy_label,
            member_count=1,
            protein_refs=entry.psm.protein_refs,
        )
        for entry in calculate_basic_target_decoy_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
    )
    peptide_rollups = rollup_peptide_evidence(records)
    peptide_entities = tuple(
        (
            rollup.canonical_peptide,
            rollup.best_score,
            rollup.target_decoy_label,
            rollup.psm_count,
            rollup.protein_refs,
        )
        for rollup in peptide_rollups
    )
    protein_rollups = rollup_protein_evidence(records)
    protein_entities = tuple(
        (
            rollup.protein_ref,
            rollup.best_score,
            rollup.target_decoy_label,
            rollup.peptide_count,
            (rollup.protein_ref,),
        )
        for rollup in protein_rollups
    )
    return LevelSpecificFdrReport(
        score_orientation=score_orientation,
        threshold=threshold,
        psm_entries=psm_entries,
        peptide_entries=_entity_fdr_entries(
            peptide_entities,
            evidence_level=FdrEvidenceLevel.PEPTIDE,
            threshold=threshold,
            score_orientation=score_orientation,
        ),
        protein_entries=_entity_fdr_entries(
            protein_entities,
            evidence_level=FdrEvidenceLevel.PROTEIN,
            threshold=threshold,
            score_orientation=score_orientation,
        ),
    )


def calculate_grouped_fdr(
    records: tuple[PsmRecord, ...],
    *,
    group_by: str,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> GroupedFdrReport:
    """Calculate grouped FDR over charge state or modification state."""
    if group_by not in {"charge_state", "modification_state"}:
        raise ValueError("group_by must be 'charge_state' or 'modification_state'")
    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        group_key = (
            f"z{record.charge}"
            if group_by == "charge_state"
            else ("modified" if "[" in record.canonical_peptide else "unmodified")
        )
        grouped[group_key].append(record)
    buckets = [
        GroupedFdrBucket(
            group_key=group_key,
            entries=tuple(
                FdrLevelEntry(
                    evidence_level=FdrEvidenceLevel.PSM,
                    entity_id=entry.psm.spectrum_id,
                    score=entry.psm.score,
                    q_value=entry.q_value,
                    fdr=entry.fdr,
                    rank=entry.rank,
                    accepted=entry.accepted,
                    target_decoy_label=entry.psm.target_decoy_label,
                    member_count=1,
                    protein_refs=entry.psm.protein_refs,
                )
                for entry in calculate_basic_target_decoy_fdr(
                    tuple(group_records),
                    threshold=threshold,
                    score_orientation=score_orientation,
                )
            ),
        )
        for group_key, group_records in sorted(grouped.items())
    ]
    return GroupedFdrReport(
        group_by=group_by,
        score_orientation=score_orientation,
        threshold=threshold,
        groups=tuple(buckets),
    )


def build_protein_groups(
    records: tuple[PsmRecord, ...],
) -> tuple[ProteinGroupEntry, ...]:
    """Group indistinguishable proteins by their peptide evidence sets."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_to_peptides: dict[str, set[str]] = defaultdict(set)
    protein_to_scores: dict[str, list[float]] = defaultdict(list)
    protein_to_q_values: dict[str, list[float]] = defaultdict(list)
    for peptide_rollup in peptide_rollups:
        for protein_ref in peptide_rollup.protein_refs:
            protein_to_peptides[protein_ref].add(peptide_rollup.canonical_peptide)
            protein_to_scores[protein_ref].append(peptide_rollup.best_score)
            if peptide_rollup.best_q_value is not None:
                protein_to_q_values[protein_ref].append(peptide_rollup.best_q_value)

    grouped: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for protein_ref, peptides in protein_to_peptides.items():
        grouped[tuple(sorted(peptides))].append(protein_ref)

    entries: list[ProteinGroupEntry] = []
    for index, (peptide_set, protein_refs) in enumerate(
        sorted(grouped.items()), start=1
    ):
        sorted_proteins = tuple(sorted(protein_refs))
        representative = sorted_proteins[0]
        entries.append(
            ProteinGroupEntry(
                group_id=f"pg-{index:03d}",
                representative_protein=representative,
                protein_refs=sorted_proteins,
                peptides=tuple(peptide_set),
                unique_peptide_count=sum(
                    1
                    for peptide in peptide_set
                    if len(
                        next(
                            rollup.protein_refs
                            for rollup in peptide_rollups
                            if rollup.canonical_peptide == peptide
                        )
                    )
                    == 1
                ),
                shared_peptide_count=sum(
                    1
                    for peptide in peptide_set
                    if len(
                        next(
                            rollup.protein_refs
                            for rollup in peptide_rollups
                            if rollup.canonical_peptide == peptide
                        )
                    )
                    > 1
                ),
                best_score=max(
                    protein_to_scores[protein_ref][0]
                    if len(protein_to_scores[protein_ref]) == 1
                    else max(protein_to_scores[protein_ref])
                    for protein_ref in sorted_proteins
                ),
                best_q_value=min(
                    (
                        q_value
                        for protein_ref in sorted_proteins
                        for q_value in protein_to_q_values[protein_ref]
                    ),
                    default=None,
                ),
                target_decoy_label=_combine_labels(
                    tuple(
                        parse_target_decoy_label(protein_refs=(protein_ref,))
                        for protein_ref in sorted_proteins
                    )
                ),
            )
        )
    return tuple(entries)


def assign_razor_peptides(
    records: tuple[PsmRecord, ...],
) -> tuple[RazorPeptideAssignment, ...]:
    """Assign shared peptides to one representative protein by razor rules."""
    peptide_rollups = rollup_peptide_evidence(records)
    unique_counts: dict[str, int] = defaultdict(int)
    best_scores: dict[str, float] = defaultdict(float)
    for rollup in peptide_rollups:
        for protein_ref in rollup.protein_refs:
            best_scores[protein_ref] = max(best_scores[protein_ref], rollup.best_score)
        if len(rollup.protein_refs) == 1:
            unique_counts[rollup.protein_refs[0]] += 1

    assignments: list[RazorPeptideAssignment] = []
    for rollup in sorted(peptide_rollups, key=lambda entry: entry.canonical_peptide):
        candidates = tuple(sorted(rollup.protein_refs))
        if not candidates:
            continue
        rationale = "unique_peptide"
        assigned = candidates[0]
        if len(candidates) > 1:
            ranked = sorted(
                candidates,
                key=lambda protein_ref: (
                    -unique_counts.get(protein_ref, 0),
                    -best_scores.get(protein_ref, float("-inf")),
                    protein_ref,
                ),
            )
            assigned = ranked[0]
            if unique_counts.get(ranked[0], 0) != unique_counts.get(ranked[-1], 0):
                rationale = "unique_evidence_priority"
            elif best_scores.get(ranked[0], 0.0) != best_scores.get(ranked[-1], 0.0):
                rationale = "best_score_tiebreak"
            else:
                rationale = "lexicographic_tiebreak"
        assignments.append(
            RazorPeptideAssignment(
                canonical_peptide=rollup.canonical_peptide,
                candidate_proteins=candidates,
                assigned_protein=assigned,
                rationale=rationale,
            )
        )
    return tuple(assignments)


def infer_proteins_by_parsimony(
    records: tuple[PsmRecord, ...],
) -> tuple[ParsimonyProteinEntry, ...]:
    """Greedily select a parsimonious protein set that explains observed peptides."""
    protein_groups = build_protein_groups(records)
    remaining = {
        peptide.canonical_peptide
        for peptide in rollup_peptide_evidence(records)
        if peptide.target_decoy_label is not TargetDecoyLabel.DECOY
    }
    selected: list[ParsimonyProteinEntry] = []
    available = list(protein_groups)
    rank = 1
    while remaining:
        scored_candidates = []
        for group in available:
            newly_explained = tuple(sorted(set(group.peptides) & remaining))
            if not newly_explained:
                continue
            scored_candidates.append((group, newly_explained))
        if not scored_candidates:
            break
        scored_candidates.sort(
            key=lambda item: (
                -len(item[1]),
                -item[0].unique_peptide_count,
                -item[0].best_score,
                item[0].representative_protein,
            )
        )
        group, newly_explained = scored_candidates[0]
        selected.append(
            ParsimonyProteinEntry(
                selection_rank=rank,
                protein_ref=group.representative_protein,
                source_group_id=group.group_id,
                covered_peptides=group.peptides,
                newly_explained_peptides=newly_explained,
                best_score=group.best_score,
                best_q_value=group.best_q_value,
                target_decoy_label=group.target_decoy_label,
            )
        )
        remaining -= set(newly_explained)
        available = [entry for entry in available if entry.group_id != group.group_id]
        rank += 1
    return tuple(selected)


def build_protein_coverage_map(
    records: tuple[PsmRecord, ...],
    *,
    protein_sequences: dict[str, str],
) -> tuple[ProteinCoverageEntry, ...]:
    """Build a sequence-aware coverage map for proteins present in evidence."""
    protein_to_peptides: dict[str, set[str]] = defaultdict(set)
    for rollup in rollup_peptide_evidence(records):
        for protein_ref in rollup.protein_refs:
            protein_to_peptides[protein_ref].add(
                rollup.canonical_peptide.replace("[", "").replace("]", "")
            )

    coverage_entries: list[ProteinCoverageEntry] = []
    for protein_ref in sorted(protein_to_peptides):
        sequence = protein_sequences.get(protein_ref)
        if not sequence:
            continue
        covered_positions: set[int] = set()
        covered_ranges: set[tuple[int, int]] = set()
        for peptide in sorted(protein_to_peptides[protein_ref]):
            start = sequence.find(peptide)
            while start != -1:
                end = start + len(peptide)
                covered_ranges.add((start + 1, end))
                covered_positions.update(range(start + 1, end + 1))
                start = sequence.find(peptide, start + 1)
        coverage_entries.append(
            ProteinCoverageEntry(
                protein_ref=protein_ref,
                residue_count=len(sequence),
                covered_residue_count=len(covered_positions),
                coverage_fraction=min(len(covered_positions) / len(sequence), 1.0)
                if sequence
                else 0.0,
                covered_ranges=tuple(sorted(covered_ranges)),
                covered_peptides=tuple(sorted(protein_to_peptides[protein_ref])),
            )
        )
    return tuple(coverage_entries)


def build_peptide_uniqueness_across_database(
    peptides: tuple[str, ...],
    *,
    protein_sequences: dict[str, str],
) -> tuple[DatabasePeptideUniquenessEntry, ...]:
    """Classify peptide uniqueness by direct lookup across a provided database."""
    entries: list[DatabasePeptideUniquenessEntry] = []
    for peptide in sorted(dict.fromkeys(peptides)):
        matching_proteins = tuple(
            sorted(
                protein_ref
                for protein_ref, sequence in protein_sequences.items()
                if peptide in sequence
            )
        )
        entries.append(
            DatabasePeptideUniquenessEntry(
                canonical_peptide=peptide,
                protein_refs=matching_proteins,
                uniqueness=(
                    DatabasePeptideUniqueness.UNIQUE
                    if len(matching_proteins) == 1
                    else DatabasePeptideUniqueness.SHARED
                    if len(matching_proteins) > 1
                    else DatabasePeptideUniqueness.MISSING
                ),
            )
        )
    return tuple(entries)


def calculate_picked_protein_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> tuple[PickedProteinFdrEntry, ...]:
    """Calculate picked protein FDR by pairing targets and decoys with the same base accession."""
    active_policy = decoy_policy or TargetDecoyLabelPolicy()
    protein_rollups = rollup_protein_evidence(records)

    def _base_accession(protein_ref: str) -> str:
        value = protein_ref
        if active_policy.protein_prefix and value.startswith(
            active_policy.protein_prefix
        ):
            value = value[len(active_policy.protein_prefix) :]
        if active_policy.protein_suffix and value.endswith(
            active_policy.protein_suffix
        ):
            value = value[: -len(active_policy.protein_suffix)]
        return value

    paired: dict[str, list[ProteinEvidenceEntry]] = defaultdict(list)
    for rollup in protein_rollups:
        paired[_base_accession(rollup.protein_ref)].append(rollup)

    selected_entities: list[
        tuple[str, float, TargetDecoyLabel, tuple[str, ...], str | None]
    ] = []
    for _base_accession_key, entries in sorted(paired.items()):
        sorted_entries = sorted(
            entries,
            key=lambda entry: (
                -entry.best_score
                if score_orientation == "higher_better"
                else entry.best_score,
                entry.protein_ref,
            ),
        )
        winner = sorted_entries[0]
        partner_ref = next(
            (
                entry.protein_ref
                for entry in sorted_entries[1:]
                if entry.target_decoy_label is not winner.target_decoy_label
            ),
            None,
        )
        selected_entities.append(
            (
                winner.protein_ref,
                winner.best_score,
                winner.target_decoy_label,
                winner.peptides,
                partner_ref,
            )
        )

    pseudo_records = tuple(
        PsmRecord(
            spectrum_id=protein_ref,
            peptide=protein_ref,
            canonical_peptide=protein_ref,
            charge=1,
            score=score,
            protein_refs=(protein_ref,),
            target_decoy_label=label,
        )
        for protein_ref, score, label, _peptides, _partner in selected_entities
    )
    annotated = calculate_basic_target_decoy_fdr(
        pseudo_records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    selected_index = {
        protein_ref: (peptides, partner_ref)
        for protein_ref, _score, _label, peptides, partner_ref in selected_entities
    }
    return tuple(
        PickedProteinFdrEntry(
            protein_ref=entry.psm.protein_refs[0],
            partner_ref=selected_index[entry.psm.protein_refs[0]][1],
            score=entry.psm.score,
            q_value=entry.q_value,
            fdr=entry.fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.psm.target_decoy_label,
            supporting_peptides=selected_index[entry.psm.protein_refs[0]][0],
        )
        for entry in annotated
    )


def assign_confidence_labels(
    entries: tuple[PickedProteinFdrEntry, ...],
    *,
    high_threshold: float = 0.01,
    medium_threshold: float = 0.05,
) -> tuple[ConfidenceAssignment, ...]:
    """Assign high/medium/low confidence labels from q-valued protein evidence."""
    assignments: list[ConfidenceAssignment] = []
    for entry in entries:
        if entry.target_decoy_label is TargetDecoyLabel.DECOY:
            label = ConfidenceLabel.DECOY
            explanation = "decoy evidence is never promoted to biological confidence"
        elif entry.q_value <= high_threshold:
            label = ConfidenceLabel.HIGH
            explanation = f"q-value {entry.q_value:.4f} is at or below the high-confidence threshold"
        elif entry.q_value <= medium_threshold:
            label = ConfidenceLabel.MEDIUM
            explanation = f"q-value {entry.q_value:.4f} is at or below the medium-confidence threshold"
        elif entry.accepted:
            label = ConfidenceLabel.LOW
            explanation = f"q-value {entry.q_value:.4f} passes FDR but misses the medium-confidence threshold"
        else:
            label = ConfidenceLabel.REJECTED
            explanation = f"q-value {entry.q_value:.4f} does not pass the requested acceptance threshold"
        assignments.append(
            ConfidenceAssignment(
                entity_id=entry.protein_ref,
                q_value=entry.q_value,
                label=label,
                explanation=explanation,
            )
        )
    return tuple(assignments)


def build_search_result_provenance_manifest(
    *,
    source_path: Path,
    parse_report: PsmParseReport,
    decoy_policy: TargetDecoyLabelPolicy,
    fdr_policy: FdrPolicy | None = None,
) -> SearchResultProvenanceManifest:
    """Build a stable provenance manifest for one parsed search-result table."""
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_result_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchResultProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=source_sha256,
        total_rows=parse_report.total_rows,
        accepted_rows=len(parse_report.accepted_records),
        rejected_rows=len(parse_report.rejected_rows),
        column_mapping=parse_report.column_mapping,
        decoy_policy=decoy_policy,
        fdr_policy=fdr_policy,
    )
    payload = manifest.to_dict()
    return manifest.model_copy(
        update={"document_schema": manifest.document_schema.with_content_hash(payload)}
    )
